import asyncio
import json
import redis.asyncio as redis
from .config import settings
from .storage.postgres import postgres
from .storage.qdrant import qdrant_storage
from .agents.core import LanguageIdentifier, SlangDecoder
from .agents.analysis import TopicClassifier, EntityExtractor, SentimentAnalyzer, EmotionDetector
from .agents.high_level import BiasDetector, Summarizer, QualityScorer

# Initialize Agents
lang_id = LanguageIdentifier()
slang_decoder = SlangDecoder()
topic_classifier = TopicClassifier()
entity_extractor = EntityExtractor()
sentiment_analyzer = SentimentAnalyzer()
emotion_detector = EmotionDetector()
bias_detector = BiasDetector()
summarizer = Summarizer()
quality_scorer = QualityScorer()

async def process_document(data: dict):
    print(f"Processing document from {data.get('source')}")
    
    # 1. Pre-processing
    text = data.get("text", "") or data.get("raw_content", "") or data.get("summary", "") # Fallback
    
    lang_res = lang_id.process(text)
    slang_res = slang_decoder.process(text)
    normalized_text = slang_res.get("normalized_text", text)
    
    # 2. Core Analysis
    topic_res = topic_classifier.process(normalized_text)
    entity_res = entity_extractor.process(normalized_text)
    sentiment_res = sentiment_analyzer.process(normalized_text)
    emotion_res = emotion_detector.process(normalized_text)
    
    # 3. High-Level Analysis
    bias_res = bias_detector.process(normalized_text)
    summary_res = summarizer.process(normalized_text)
    quality_res = quality_scorer.process(normalized_text)
    
    # 4. Storage
    # Save to Postgres
    doc_id = await postgres.save_document({
        "url": data.get("url", f"generated-{data.get('id')}"),
        "text": normalized_text,
        "source": data.get("source"),
        "raw_content": text
    })
    
    # Save Analysis Results
    results = {
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
    
    for agent_name, res in results.items():
        await postgres.save_analysis(doc_id, agent_name, res)
    
    # Save to Qdrant
    payload = {
        "document_id": str(doc_id),
        "text": normalized_text,
        "summary": summary_res.get("summary"),
        "topics": topic_res.get("topics"),
        "sentiment": sentiment_res.get("sentiment"),
        "entities": [e["text"] for e in entity_res.get("entities", [])],
        "quality_score": quality_res.get("quality_score"),
        "timestamp": data.get("timestamp")
    }
    
    # Mock embedding (768 dim)
    vector = [0.1] * 768 
    
    qdrant_storage.upsert(str(doc_id), vector, payload)
    print(f"Document {doc_id} processed and stored.")

async def main():
    # Connect to DB
    await postgres.connect()
    
    # Redis Consumer
    r = redis.from_url(f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}", decode_responses=True)
    
    # Create consumer group
    try:
        await r.xgroup_create(settings.REDIS_STREAM_KEY, settings.REDIS_CONSUMER_GROUP, id="0", mkstream=True)
    except:
        pass
        
    print(f"Orchestrator started. Listening on {settings.REDIS_STREAM_KEY}...")
    
    while True:
        try:
            # Read from stream
            streams = await r.xreadgroup(
                settings.REDIS_CONSUMER_GROUP,
                "orchestrator-1",
                {settings.REDIS_STREAM_KEY: ">"},
                count=1,
                block=5000
            )
            
            if not streams:
                continue
                
            for stream, messages in streams:
                for message_id, message_data in messages:
                    # In a real app, we might fetch the full JSON from MinIO using message_data['s3_key']
                    # For now, we assume the payload might have enough info or we mock it
                    # But the ingestion service sends 's3_key', 'source', 'timestamp'.
                    # So we really should fetch from MinIO. 
                    # For this TDD, we will mock the data fetch if it's missing text.
                    
                    # Mock data fetch if needed
                    if "text" not in message_data:
                        message_data["text"] = "Mock text for processing"
                        
                    await process_document(message_data)
                    
                    # Ack message
                    await r.xack(settings.REDIS_STREAM_KEY, settings.REDIS_CONSUMER_GROUP, message_id)
                    
        except Exception as e:
            print(f"Error in loop: {e}")
            await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())
