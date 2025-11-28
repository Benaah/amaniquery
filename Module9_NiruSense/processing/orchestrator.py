import asyncio
import json
import time
import signal
from typing import Dict, Any
from minio import Minio
import redis.asyncio as redis
from .config import settings
from .storage.postgres import postgres
from .storage.qdrant import qdrant_storage
from .embedding import embedding_generator
from .monitoring import logger, metrics
from .agents.core import LanguageIdentifier, SlangDecoder
from .agents.analysis import TopicClassifier, EntityExtractor, SentimentAnalyzer, EmotionDetector
from .agents.high_level import BiasDetector, Summarizer, QualityScorer

# Initialize Agents
logger.info("Initializing NiruSense agents...")
lang_id = LanguageIdentifier()
slang_decoder = SlangDecoder()
topic_classifier = TopicClassifier()
entity_extractor = EntityExtractor()
sentiment_analyzer = SentimentAnalyzer()
emotion_detector = EmotionDetector()
bias_detector = BiasDetector()
summarizer = Summarizer()
quality_scorer = QualityScorer()

# Initialize MinIO Client
minio_client = Minio(
    settings.MINIO_ENDPOINT,
    access_key=settings.MINIO_ACCESS_KEY,
    secret_key=settings.MINIO_SECRET_KEY,
    secure=settings.MINIO_SECURE
)

# Shutdown flag
shutdown_event = asyncio.Event()

def signal_handler(sig, frame):
    """Handle shutdown signals gracefully"""
    logger.info("Shutdown signal received, initiating graceful shutdown...")
    shutdown_event.set()

async def process_document(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Process a single document through the full NiruSense pipeline.
    
    Steps:
    1. Pre-processing (Language ID, Slang Decoding)
    2. Core Analysis (Topic, Entity, Sentiment, Emotion)
    3. High-Level Analysis (Bias, Summary, Quality)
    4. Embedding Generation
    5. Storage (PostgreSQL + Qdrant)
    """
    start_time = time.time()
    source = data.get('source', 'unknown')
    
    logger.info(f"Processing document from {source}", extra={
        "source": source,
        "url": data.get("url", "N/A")
    })
    
    try:
        # 1. Pre-processing
        text = data.get("text", "") or data.get("raw_content", "") or data.get("summary", "")
        
        if not text or len(text) < 10:
            raise ValueError("Document text too short or empty")
        
        # Truncate if too long
        if len(text) > settings.MAX_TEXT_LENGTH:
            text = text[:settings.MAX_TEXT_LENGTH]
            logger.warning("Document truncated to MAX_TEXT_LENGTH")
        
        # Language identification and slang decoding
        lang_res = lang_id.execute(text)
        slang_res = slang_decoder.execute(text)
        normalized_text = slang_res.get("normalized_text", text)
        
        # 2. Core Analysis (can run in parallel)
        if settings.ENABLE_PARALLEL_AGENTS:
            # Parallel execution for independent agents
            topic_task = asyncio.to_thread(topic_classifier.execute, normalized_text)
            entity_task = asyncio.to_thread(entity_extractor.execute, normalized_text)
            sentiment_task = asyncio.to_thread(sentiment_analyzer.execute, normalized_text)
            emotion_task = asyncio.to_thread(emotion_detector.execute, normalized_text)
            
            results = await asyncio.gather(
                topic_task, entity_task, sentiment_task, emotion_task,
                return_exceptions=True
            )
            topic_res, entity_res, sentiment_res, emotion_res = results
        else:
            # Sequential execution
            topic_res = topic_classifier.execute(normalized_text)
            entity_res = entity_extractor.execute(normalized_text)
            sentiment_res = sentiment_analyzer.execute(normalized_text)
            emotion_res = emotion_detector.execute(normalized_text)
        
        # 3. High-Level Analysis
        bias_res = bias_detector.execute(normalized_text)
        summary_res = summarizer.execute(normalized_text)
        quality_res = quality_scorer.execute(normalized_text)
        
        # 4. Generate Embedding
        # Combine text and summary for better embeddings
        embed_text = f"{normalized_text}\n\nSummary: {summary_res.get('summary', '')}"
        vector = embedding_generator.embed(embed_text)
        
        logger.info("Generated embedding", extra={"vector_dim": len(vector)})
        
        # 5. Storage
        # Save to PostgreSQL
        doc_id = await postgres.save_document({
            "url": data.get("url", f"generated-{int(time.time())}"),
            "raw_content": text,
            "normalized_content": normalized_text,
            "source": source,
            "source_domain": data.get("source_domain", source),
            "published_at": data.get("published_at", data.get("timestamp"))
        })
        
        # Save analysis results
        analysis_results = {
            "language": lang_res,
            "slang": slang_res,
            "topics": topic_res,
            "entities": entity_res,
            "sentiment": sentiment_res,
            "emotion": emotion_res,
            "bias": bias_res,
            "summary": summary_res,
            "quality": quality_res
        }
        
        for agent_name, res in analysis_results.items():
            if not isinstance(res, dict) or res.get("error"):
                logger.warning(f"Agent {agent_name} returned error: {res}")
            await postgres.save_analysis(doc_id, agent_name, res)
        
        # Save to Qdrant
        payload = {
            "document_id": str(doc_id),
            "text": normalized_text[:1000],  # Truncate for payload
            "summary": summary_res.get("summary", "")[:500],
            "topics": topic_res.get("topics", []),
            "sentiment": sentiment_res.get("sentiment", "unknown"),
            "entities": [e.get("text", "") for e in entity_res.get("entities", [])][:10],
            "quality_score": quality_res.get("quality_score", 0),
            "language": lang_res.get("lang", "unknown"),
            "source": source,
            "timestamp": data.get("timestamp", int(time.time()))
        }
        
        qdrant_storage.upsert(str(doc_id), vector, payload)
        
        # Record success metrics
        processing_time = time.time() - start_time
        metrics.record_document_processed(processing_time)
        
        logger.info(f"Document {doc_id} processed successfully", extra={
            "doc_id": str(doc_id),
            "processing_time": processing_time,
            "quality_score": quality_res.get("quality_score", 0)
        })
        
        return {
            "status": "success",
            "doc_id": str(doc_id),
            "processing_time": processing_time
        }
        
    except Exception as e:
        metrics.record_document_failed()
        logger.error(f"Document processing failed: {e}", extra={
            "source": source,
            "error": str(e),
            "error_type": type(e).__name__
        })
        return {
            "status": "error",
            "error": str(e)
        }

async def main():
    """Main orchestrator loop - consumes from Redis stream and processes documents"""
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    # Connect to database
    logger.info("Connecting to PostgreSQL...")
    await postgres.connect()
    
    # Connect to Redis
    logger.info(f"Connecting to Redis at {settings.REDIS_HOST}:{settings.REDIS_PORT}...")
    r = redis.from_url(
        f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}",
        decode_responses=True,
        socket_timeout=10
    )
    
    # Create consumer group
    try:
        await r.xgroup_create(
            settings.REDIS_STREAM_KEY,
            settings.REDIS_CONSUMER_GROUP,
            id="0",
            mkstream=True
        )
        logger.info(f"Created consumer group: {settings.REDIS_CONSUMER_GROUP}")
    except Exception as e:
        logger.info(f"Consumer group already exists: {e}")
    
    logger.info(f"NiruSense Orchestrator started. Listening on {settings.REDIS_STREAM_KEY}...")
    logger.info(f"Press Ctrl+C to shutdown gracefully")
    
    retry_count = 0
    max_retries = settings.REDIS_MAX_RETRIES
    
    while not shutdown_event.is_set():
        try:
            # Read from stream
            streams = await r.xreadgroup(
                settings.REDIS_CONSUMER_GROUP,
                "orchestrator-1",
                {settings.REDIS_STREAM_KEY: ">"},
                count=1,
                block=5000  # 5 second timeout
            )
            
            if not streams:
                continue
            
            for stream, messages in streams:
                for message_id, message_data in messages:
                    s3_key = message_data.get('s3_key')
                    
                    if s3_key:
                        try:
                            # Fetch from MinIO
                            response = minio_client.get_object(settings.MINIO_BUCKET, s3_key)
                            file_data = response.read()
                            response.close()
                            response.release_conn()
                            
                            # Parse JSON payload
                            full_payload = json.loads(file_data)
                            full_payload.update(message_data)
                            
                            # Process document
                            result = await process_document(full_payload)
                            
                            # Acknowledge message
                            await r.xack(settings.REDIS_STREAM_KEY, settings.REDIS_CONSUMER_GROUP, message_id)
                            
                            logger.info(f"Message {message_id} acknowledged")
                            
                        except Exception as e:
                            logger.error(f"Error processing message {message_id}: {e}")
                            
                            # Move to DLQ after max retries
                            retry_count += 1
                            if retry_count >= max_retries:
                                logger.error(f"Moving message {message_id} to DLQ after {max_retries} retries")
                                await r.xadd(settings.REDIS_DLQ_KEY, message_data)
                                await r.xack(settings.REDIS_STREAM_KEY, settings.REDIS_CONSUMER_GROUP, message_id)
                                retry_count = 0
                    else:
                        logger.warning(f"Missing s3_key in message: {message_id}")
                        await r.xack(settings.REDIS_STREAM_KEY, settings.REDIS_CONSUMER_GROUP, message_id)
        
        except asyncio.CancelledError:
            logger.info("Orchestrator task cancelled")
            break
        except Exception as e:
            logger.error(f"Error in main loop: {e}")
            await asyncio.sleep(1)
    
    # Cleanup
    logger.info("Shutting down orchestrator...")
    await postgres.close()
    await r.close()
    logger.info("Orchestrator shutdown complete")

if __name__ == "__main__":
    asyncio.run(main())
