"""
FastAPI Application - REST API for AmaniQuery
"""
import os
import sys
from pathlib import Path
from typing import Optional, List
import subprocess
import asyncio
import threading
import time
import json
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from dotenv import load_dotenv
from loguru import logger

from Module4_NiruAPI.rag_pipeline import RAGPipeline
from Module4_NiruAPI.alignment_pipeline import ConstitutionalAlignmentPipeline
from Module4_NiruAPI.sms_pipeline import SMSPipeline
from Module4_NiruAPI.sms_service import AfricasTalkingSMSService
from Module3_NiruDB.chat_manager import ChatDatabaseManager
from Module3_NiruDB.vector_store import VectorStore
from Module3_NiruDB.metadata_manager import MetadataManager
from Module3_NiruDB.chat_models import (
    ChatSession, ChatMessage, UserFeedback,  # SQLAlchemy models
    ChatSessionCreate, ChatSessionResponse, ChatMessageCreate,
    ChatMessageResponse, FeedbackCreate, FeedbackResponse
)
from Module4_NiruAPI.models import (
    QueryRequest,
    QueryResponse,
    Source,
    HealthResponse,
    StatsResponse,
    AlignmentRequest,
    AlignmentResponse,
    BillContext,
    ConstitutionContext,
    AlignmentMetadata,
    SentimentRequest,
    SentimentResponse,
)
from Module4_NiruAPI.research_module import ResearchModule
from Module4_NiruAPI.report_generator import ReportGenerator

# Load environment
load_dotenv()

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    global vector_store, rag_pipeline, alignment_pipeline, sms_pipeline, sms_service, metadata_manager, chat_manager, crawler_manager, research_module, report_generator
    
    logger.info("Starting AmaniQuery API")
    
    # Initialize vector store
    vector_store = VectorStore()
    
    # Initialize metadata manager
    metadata_manager = MetadataManager(vector_store)
    
    # Initialize RAG pipeline
    llm_provider = os.getenv("LLM_PROVIDER", "moonshot")
    model = os.getenv("DEFAULT_MODEL", "moonshot-v1-8k")
    
    rag_pipeline = RAGPipeline(
        vector_store=vector_store,
        llm_provider=llm_provider,
        model=model,
    )
    
    # Initialize Constitutional Alignment Pipeline
    alignment_pipeline = ConstitutionalAlignmentPipeline(
        vector_store=vector_store,
        rag_pipeline=rag_pipeline,
    )
    
    # Initialize SMS Pipeline
    sms_pipeline = SMSPipeline(
        vector_store=vector_store,
        llm_service=rag_pipeline.llm_service
    )
    
    # Initialize chat database manager
    chat_manager = ChatDatabaseManager()
    
    # Initialize crawler manager
    crawler_manager = CrawlerManager()
    
    # Initialize research module (optional - only if Gemini API key is available)
    try:
        research_module = ResearchModule()
        logger.info("Research module initialized")
    except Exception as e:
        logger.warning(f"Research module not available: {e}")
        research_module = None
    
    # Initialize report generator (optional - only if Gemini API key is available)
    try:
        report_generator = ReportGenerator()
        logger.info("Report generator initialized")
    except Exception as e:
        logger.warning(f"Report generator not available: {e}")
        report_generator = None
    
    logger.info("AmaniQuery API ready")
    
    yield
    
    # Shutdown cleanup
    logger.info("Shutting down AmaniQuery API")

# Initialize FastAPI app
app = FastAPI(
    title="AmaniQuery API",
    description="RAG-powered API for Kenyan legal, parliamentary, and news intelligence",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001,http://localhost:8000,http://frontend:3000,https://amaniquery.vercel.app,https://api-amaniquery.vercel.app,https://amaniquery.onrender.com,https://api.amaniquery.onrender.com")
origins = [origin.strip() for origin in cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/", tags=["General"])
async def root():
    """Root endpoint"""
    return {
        "name": "AmaniQuery API",
        "version": "1.0.0",
        "description": "RAG-powered API for Kenyan intelligence with Constitutional Alignment Analysis",
        "endpoints": {
            "query": "POST /query",
            "alignment_check": "POST /alignment-check",
            "quick_alignment": "POST /alignment-quick-check",
            "sentiment": "GET /sentiment",
            "sms_webhook": "POST /sms-webhook",
            "sms_send": "POST /sms-send",
            "sms_query_preview": "GET /sms-query",
            "health": "GET /health",
            "stats": "GET /stats",
            "share": "POST /share/*",
            "docs": "GET /docs",
        }
    }


@app.get("/health", response_model=HealthResponse, tags=["General"])
async def health_check():
    """Health check endpoint"""
    if vector_store is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    stats = vector_store.get_stats()
    
    return HealthResponse(
        status="healthy",
        database_chunks=stats["total_chunks"],
        embedding_model=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
        llm_provider=os.getenv("LLM_PROVIDER", "moonshot"),
    )


@app.get("/stats", response_model=StatsResponse, tags=["General"])
async def get_stats():
    """Get database statistics"""
    if vector_store is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    stats = vector_store.get_stats()
    
    # Get categories and sources
    from Module3_NiruDB.metadata_manager import MetadataManager
    meta_manager = MetadataManager(vector_store)
    
    categories_list = meta_manager.get_categories()
    sources_list = meta_manager.get_sources()
    
    # Convert to dict with counts
    categories_dict = {cat: stats["sample_categories"].get(cat, 0) for cat in categories_list}
    
    return StatsResponse(
        total_chunks=stats["total_chunks"],
        categories=categories_dict,
        sources=sources_list,
    )


@app.post("/query", response_model=QueryResponse, tags=["Query"])
async def query(request: QueryRequest):
    """
    Main query endpoint - Ask questions about Kenyan law, parliament, and news
    
    **Example queries:**
    - "What does the Kenyan Constitution say about freedom of speech?"
    - "What are the recent parliamentary debates on finance?"
    - "Latest news on AI policy in Kenya"
    """
    if rag_pipeline is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        # Run RAG query
        result = rag_pipeline.query(
            query=request.query,
            top_k=request.top_k,
            category=request.category,
            source=request.source,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        
        # Format sources
        sources = [Source(**src) for src in result["sources"]]
        
        return QueryResponse(
            answer=result["answer"],
            sources=sources if request.include_sources else [],
            query_time=result["query_time"],
            retrieved_chunks=result["retrieved_chunks"],
            model_used=result["model_used"],
        )
        
    except Exception as e:
        logger.error(f"Error processing query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/query/stream", tags=["Query"])
async def query_stream(request: QueryRequest):
    """
    Main query endpoint with streaming response - Fastest perceived speed
    
    **Example queries:**
    - "What does the Kenyan Constitution say about freedom of speech?"
    - "What are the recent parliamentary debates on finance?"
    - "Latest news on AI policy in Kenya"
    
    **Streaming Benefits:**
    - Time to first token: <1 second (vs 5-10 seconds)
    - User sees response immediately as it's generated
    - Best for user experience in hackathons
    """
    if rag_pipeline is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        # Run RAG query with streaming
        result = rag_pipeline.query_stream(
            query=request.query,
            top_k=request.top_k,
            category=request.category,
            source=request.source,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
        )
        
        if not result.get("stream", False):
            # Fallback to regular response
            sources = [Source(**src) for src in result["sources"]]
            return QueryResponse(
                answer=result["answer"],
                sources=sources if request.include_sources else [],
                query_time=result["query_time"],
                retrieved_chunks=result["retrieved_chunks"],
                model_used=result["model_used"],
            )
        
        # Return streaming response
        from fastapi.responses import StreamingResponse
        
        async def generate():
            try:
                answer_stream = result["answer_stream"]
                
                if rag_pipeline.llm_provider in ["openai", "moonshot"]:
                    # OpenAI-style streaming
                    async for chunk in answer_stream:
                        if chunk.choices and chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            yield f"data: {content}\n\n"
                
                elif rag_pipeline.llm_provider == "anthropic":
                    # Anthropic streaming
                    async for chunk in answer_stream:
                        if chunk.type == "content_block_delta" and chunk.delta.text:
                            yield f"data: {chunk.delta.text}\n\n"
                
                # Send sources at the end
                sources_data = {
                    "sources": [Source(**src).dict() for src in result["sources"]] if request.include_sources else [],
                    "query_time": result["query_time"],
                    "retrieved_chunks": result["retrieved_chunks"],
                    "model_used": result["model_used"],
                }
                yield f"data: [DONE]{json.dumps(sources_data)}\n\n"
                
            except Exception as e:
                logger.error(f"Error in streaming: {e}")
                yield f"data: [ERROR]{str(e)}\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
        
    except Exception as e:
        logger.error(f"Error processing streaming query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/categories", tags=["Metadata"])
async def get_categories():
    """Get list of all categories"""
    if vector_store is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    from Module3_NiruDB.metadata_manager import MetadataManager
    meta_manager = MetadataManager(vector_store)
    
    return {"categories": meta_manager.get_categories()}


@app.get("/sources", tags=["Metadata"])
async def get_sources():
    """Get list of all sources"""
    if vector_store is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    from Module3_NiruDB.metadata_manager import MetadataManager
    meta_manager = MetadataManager(vector_store)
    
    return {"sources": meta_manager.get_sources()}


@app.post("/alignment-check", response_model=AlignmentResponse, tags=["Constitutional Alignment"])
async def check_constitutional_alignment(request: AlignmentRequest):
    """
    Constitutional Alignment Analysis - Compare Bills/Acts with Constitution
    
    This endpoint performs specialized dual-retrieval RAG analysis to compare 
    proposed or enacted legislation with relevant constitutional provisions.
    
    **How it works:**
    1. Analyzes your query to identify the Bill and constitutional concepts
    2. Retrieves relevant Bill/Act sections
    3. Retrieves relevant Constitutional articles
    4. Generates structured comparative analysis with citations
    
    **Example queries:**
    - "How does the Finance Bill 2025 housing levy align with the constitution?"
    - "Does the Data Protection Act comply with constitutional privacy rights?"
    - "What does the Constitution say about the new taxation measures in the Finance Bill?"
    
    **Important:** This provides factual analysis, NOT legal opinions. The analysis
    highlights areas of alignment, overlap, and potential tension for expert review.
    """
    if alignment_pipeline is None:
        raise HTTPException(status_code=503, detail="Alignment service not initialized")
    
    try:
        import time
        start_time = time.time()
        
        # Run alignment analysis
        result = alignment_pipeline.analyze_alignment(
            query=request.query,
            bill_top_k=request.bill_top_k,
            constitution_top_k=request.constitution_top_k,
        )
        
        query_time = time.time() - start_time
        
        # Convert to response model
        return AlignmentResponse(
            analysis=result["analysis"],
            bill_context=[BillContext(**ctx) for ctx in result["bill_context"]],
            constitution_context=[ConstitutionContext(**ctx) for ctx in result["constitution_context"]],
            metadata=AlignmentMetadata(**result["metadata"]),
            query_time=query_time,
        )
        
    except Exception as e:
        logger.error(f"Error in constitutional alignment analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/alignment-quick-check", tags=["Constitutional Alignment"])
async def quick_alignment_check(bill_name: str, constitutional_topic: str):
    """
    Quick Constitutional Alignment Check
    
    Simplified endpoint for checking specific bill against constitutional topic.
    
    **Parameters:**
    - bill_name: Name of the bill (e.g., "Finance Bill 2025")
    - constitutional_topic: Topic to check (e.g., "taxation", "housing rights", "privacy")
    
    **Example:**
    - bill_name: "Finance Bill 2025"
    - constitutional_topic: "taxation and revenue"
    """
    if alignment_pipeline is None:
        raise HTTPException(status_code=503, detail="Alignment service not initialized")
    
    try:
        result = alignment_pipeline.quick_check(
            bill_name=bill_name,
            constitutional_topic=constitutional_topic,
        )
        
        return AlignmentResponse(
            analysis=result["analysis"],
            bill_context=[BillContext(**ctx) for ctx in result["bill_context"]],
            constitution_context=[ConstitutionContext(**ctx) for ctx in result["constitution_context"]],
            metadata=AlignmentMetadata(**result["metadata"]),
            query_time=result.get("query_time"),
        )
        
    except Exception as e:
        logger.error(f"Error in quick alignment check: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sentiment", response_model=SentimentResponse, tags=["Sentiment Analysis"])
async def get_topic_sentiment(
    topic: str,
    category: Optional[str] = None,
    days: int = 30
):
    """
    Public Sentiment Gauge - Analyze sentiment for a topic from news sources
    
    This endpoint analyzes the sentiment of news articles discussing a specific topic.
    It aggregates sentiment scores from all relevant articles and returns a percentage
    breakdown of positive, negative, and neutral coverage.
    
    **Use Cases:**
    - Track public sentiment on legislation (e.g., "Finance Bill")
    - Monitor news tone on policies or events
    - Understand media coverage sentiment
    
    **Example queries:**
    - topic: "Finance Bill"
    - topic: "Housing Levy"  
    - topic: "Climate Policy"
    - topic: "Healthcare Reform"
    
    **Parameters:**
    - topic: The topic to analyze (e.g., "Finance Bill", "Housing Policy")
    - category: Filter by category ("Kenyan News" or "Global Trend")
    - days: Number of days to look back (default: 30)
    
    **Returns:**
    - Sentiment percentages (positive, negative, neutral)
    - Average polarity score (-1.0 to 1.0)
    - Total articles analyzed
    """
    if vector_store is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        from datetime import datetime, timedelta
        import time
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Build filter
        filter_dict = {}
        if category:
            filter_dict["category"] = category
        else:
            # Only analyze news categories
            filter_dict["category"] = {"$in": ["Kenyan News", "Global Trend"]}
        
        # Search for relevant articles
        results = vector_store.query(
            query_text=topic,
            n_results=100,  # Get up to 100 articles
            filter=filter_dict if filter_dict else None
        )
        
        if not results:
            return SentimentResponse(
                topic=topic,
                sentiment_percentages={"positive": 0.0, "negative": 0.0, "neutral": 0.0},
                sentiment_distribution={"positive": 0, "negative": 0, "neutral": 0},
                average_polarity=0.0,
                average_subjectivity=0.0,
                total_articles=0,
                category_filter=category,
                time_period_days=days
            )
        
        # Extract sentiment data
        sentiments = []
        for chunk in results:
            metadata = chunk.get("metadata", {})
            if "sentiment_polarity" in metadata:
                sentiments.append({
                    "polarity": metadata["sentiment_polarity"],
                    "subjectivity": metadata.get("sentiment_subjectivity", 0.0),
                    "label": metadata.get("sentiment_label", "neutral")
                })
        
        if not sentiments:
            return SentimentResponse(
                topic=topic,
                sentiment_percentages={"positive": 0.0, "negative": 0.0, "neutral": 0.0},
                sentiment_distribution={"positive": 0, "negative": 0, "neutral": 0},
                average_polarity=0.0,
                average_subjectivity=0.0,
                total_articles=len(results),
                category_filter=category,
                time_period_days=days
            )
        
        # Calculate aggregates
        avg_polarity = sum(s["polarity"] for s in sentiments) / len(sentiments)
        avg_subjectivity = sum(s["subjectivity"] for s in sentiments) / len(sentiments)
        
        # Count labels
        label_counts = {
            "positive": sum(1 for s in sentiments if s["label"] == "positive"),
            "negative": sum(1 for s in sentiments if s["label"] == "negative"),
            "neutral": sum(1 for s in sentiments if s["label"] == "neutral"),
        }
        
        # Calculate percentages
        total = len(sentiments)
        percentages = {
            "positive": round((label_counts["positive"] / total) * 100, 1),
            "negative": round((label_counts["negative"] / total) * 100, 1),
            "neutral": round((label_counts["neutral"] / total) * 100, 1),
        }
        
        return SentimentResponse(
            topic=topic,
            sentiment_percentages=percentages,
            sentiment_distribution=label_counts,
            average_polarity=round(avg_polarity, 3),
            average_subjectivity=round(avg_subjectivity, 3),
            total_articles=total,
            category_filter=category,
            time_period_days=days
        )
        
    except Exception as e:
        logger.error(f"Error analyzing sentiment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Chat API Endpoints
@app.post("/chat/sessions", response_model=ChatSessionResponse, tags=["Chat"])
async def create_chat_session(session: ChatSessionCreate):
    """Create a new chat session"""
    if chat_manager is None:
        raise HTTPException(status_code=503, detail="Chat service not initialized")
    
    try:
        session_id = chat_manager.create_session(session.title, session.user_id)
        session_data = chat_manager.get_session(session_id)
        return session_data
    except Exception as e:
        logger.error(f"Error creating chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chat/sessions", response_model=List[ChatSessionResponse], tags=["Chat"])
async def list_chat_sessions(user_id: Optional[str] = None, limit: int = 50):
    """List chat sessions"""
    if chat_manager is None:
        raise HTTPException(status_code=503, detail="Chat service not initialized")
    
    try:
        return chat_manager.list_sessions(user_id, limit)
    except Exception as e:
        logger.error(f"Error listing chat sessions: {e}")
        # Return empty list instead of crashing
        return []


@app.get("/chat/sessions/{session_id}", response_model=ChatSessionResponse, tags=["Chat"])
async def get_chat_session(session_id: str):
    """Get a specific chat session"""
    if chat_manager is None:
        raise HTTPException(status_code=503, detail="Chat service not initialized")
    
    try:
        session = chat_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        return session
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/chat/sessions/{session_id}", tags=["Chat"])
async def delete_chat_session(session_id: str):
    """Delete a chat session"""
    if chat_manager is None:
        raise HTTPException(status_code=503, detail="Chat service not initialized")
    
    try:
        chat_manager.delete_session(session_id)
        return {"message": "Session deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/sessions/{session_id}/messages", response_model=ChatMessageResponse, tags=["Chat"])
async def add_chat_message(session_id: str, message: ChatMessageCreate):
    """Add a message to a chat session"""
    if chat_manager is None or rag_pipeline is None:
        raise HTTPException(status_code=503, detail="Services not initialized")
    
    try:
        # If this is the first user message and session has no title, generate one
        session = chat_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if message.role == "user":
            # Process user message with RAG (optimized for chat)
            result = rag_pipeline.query(
                query=message.content,
                top_k=3,  # Reduced for faster chat responses
                max_tokens=1000,  # Shorter responses for chat
                max_context_length=2000,  # Smaller context for chat
                temperature=0.7
            )
            
            # Add user message
            user_msg_id = chat_manager.add_message(
                session_id=session_id,
                content=message.content,
                role="user"
            )
            
            # Add assistant response
            assistant_msg_id = chat_manager.add_message(
                session_id=session_id,
                content=result["answer"],
                role="assistant",
                token_count=result.get("retrieved_chunks", 0),
                model_used=result.get("model_used", "unknown"),
                sources=result.get("sources", [])
            )
            
            # Generate session title if needed
            if not session.title:
                title = chat_manager.generate_session_title(session_id)
                chat_manager.update_session_title(session_id, title)
            
            # Return the assistant message
            messages = chat_manager.get_messages(session_id, limit=1)
            return messages[-1] if messages else None
            
        else:
            # Add assistant message directly
            msg_id = chat_manager.add_message(
                session_id=session_id,
                content=message.content,
                role=message.role
            )
            messages = chat_manager.get_messages(session_id, limit=1)
            return messages[-1] if messages else None
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chat/sessions/{session_id}/messages", response_model=List[ChatMessageResponse], tags=["Chat"])
async def get_chat_messages(session_id: str, limit: int = 100):
    """Get messages for a chat session"""
    if chat_manager is None:
        raise HTTPException(status_code=503, detail="Chat service not initialized")
    
    try:
        return chat_manager.get_messages(session_id, limit)
    except Exception as e:
        logger.error(f"Error getting chat messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/feedback", response_model=FeedbackResponse, tags=["Chat"])
async def add_feedback(feedback: FeedbackCreate):
    """Add feedback for a chat message"""
    if chat_manager is None:
        raise HTTPException(status_code=503, detail="Chat service not initialized")
    
    try:
        # First check if the message exists
        with chat_manager.get_db_session() as db:
            message = db.query(ChatMessage).filter(ChatMessage.id == feedback.message_id).first()
            if not message:
                logger.error(f"Message {feedback.message_id} not found in database")
                raise HTTPException(status_code=404, detail="Message not found")
        
        feedback_id = chat_manager.add_feedback(
            message_id=feedback.message_id,
            feedback_type=feedback.feedback_type,
            comment=feedback.comment
        )
        
        # Return feedback response
        return FeedbackResponse(
            id=feedback_id,
            message_id=feedback.message_id,
            feedback_type=feedback.feedback_type,
            comment=feedback.comment,
            created_at=datetime.utcnow()
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding feedback: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chat/feedback/stats", tags=["Chat"])
async def get_feedback_stats():
    """Get feedback statistics"""
    if chat_manager is None:
        raise HTTPException(status_code=503, detail="Chat service not initialized")
    
    try:
        return chat_manager.get_feedback_stats()
    except Exception as e:
        logger.error(f"Error getting feedback stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/share", tags=["Chat"])
async def share_chat_session(session_id: str, share_type: str = "link"):
    """Generate a shareable link for a chat session"""
    if chat_manager is None:
        raise HTTPException(status_code=503, detail="Chat service not initialized")
    
    try:
        session = chat_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        # Generate shareable link (in a real app, this would be a unique URL)
        share_link = f"/shared/{session_id}"
        
        return {
            "share_link": share_link,
            "session_title": session.title,
            "message_count": session.message_count,
            "share_type": share_type
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sharing chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Admin Endpoints
@app.get("/admin/crawlers", tags=["Admin"])
async def get_crawler_status():
    """Get status of all crawlers"""
    if crawler_manager is None:
        raise HTTPException(status_code=503, detail="Crawler manager not initialized")
    
    try:
        return crawler_manager.get_crawler_status()
    except Exception as e:
        logger.error(f"Error getting crawler status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/crawlers/{crawler_name}/start", tags=["Admin"])
async def start_crawler(crawler_name: str):
    """Start a specific crawler"""
    if crawler_manager is None:
        raise HTTPException(status_code=503, detail="Crawler manager not initialized")
    
    try:
        return crawler_manager.start_crawler(crawler_name)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting crawler {crawler_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/crawlers/{crawler_name}/stop", tags=["Admin"])
async def stop_crawler(crawler_name: str):
    """Stop a specific crawler"""
    if crawler_manager is None:
        raise HTTPException(status_code=503, detail="Crawler manager not initialized")
    
    try:
        return crawler_manager.stop_crawler(crawler_name)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping crawler {crawler_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/documents", tags=["Admin"])
async def search_documents(
    query: str = "",
    category: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 50,
    offset: int = 0
):
    """Search and retrieve documents from the database"""
    if vector_store is None:
        raise HTTPException(status_code=503, detail="Vector store not initialized")
    
    try:
        # Build filter
        filter_dict = {}
        if category:
            filter_dict["category"] = category
        if source:
            filter_dict["source"] = source
        
        # Search documents
        if query:
            results = vector_store.query(
                query_text=query,
                n_results=limit,
                filter=filter_dict if filter_dict else None
            )
        else:
            # Get all documents if no query
            results = vector_store.query(
                query_text="",
                n_results=limit,
                filter=filter_dict if filter_dict else None
            )
        
        # Format results
        documents = []
        for chunk in results:
            metadata = chunk.get("metadata", {})
            documents.append({
                "id": chunk.get("id", ""),
                "content": chunk.get("text", ""),
                "metadata": {
                    "title": metadata.get("title", ""),
                    "url": metadata.get("source_url", ""),
                    "source": metadata.get("source_name", ""),
                    "category": metadata.get("category", ""),
                    "date": metadata.get("publication_date", ""),
                    "author": metadata.get("author", ""),
                    "sentiment_polarity": metadata.get("sentiment_polarity"),
                    "sentiment_label": metadata.get("sentiment_label")
                },
                "score": 1.0 - chunk.get("distance", 0.0) if chunk.get("distance") is not None else 0
            })
        
        return {
            "documents": documents,
            "total": len(documents),
            "query": query,
            "filters": filter_dict
        }
        
    except Exception as e:
        logger.error(f"Error searching documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/documents/{doc_id}", tags=["Admin"])
async def get_document(doc_id: str):
    """Get a specific document by ID"""
    if vector_store is None:
        raise HTTPException(status_code=503, detail="Vector store not initialized")
    
    try:
        # This would need a method to get document by ID
        # For now, return mock data
        return {
            "id": doc_id,
            "content": "Document content would be here...",
            "metadata": {
                "title": "Sample Document",
                "url": "https://example.com",
                "source": "Sample Source",
                "category": "Legal",
                "date": "2024-01-15"
            }
        }
    except Exception as e:
        logger.error(f"Error getting document {doc_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/execute", tags=["Admin"])
async def execute_command(command: str, cwd: Optional[str] = None):
    """Execute a shell command (admin only)"""
    try:
        # Security check - only allow safe commands
        allowed_commands = [
            "ls", "pwd", "ps", "top", "df", "du", "free", "uptime",
            "python", "pip", "npm", "node", "git", "docker"
        ]
        
        cmd_parts = command.split()
        if not cmd_parts:
            raise HTTPException(status_code=400, detail="Empty command")
        
        base_cmd = cmd_parts[0]
        if base_cmd not in allowed_commands:
            raise HTTPException(status_code=403, detail=f"Command '{base_cmd}' not allowed")
        
        # Execute command
        working_dir = cwd or str(Path(__file__).parent.parent.parent)
        
        process = await asyncio.create_subprocess_shell(
            command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            cwd=working_dir,
            shell=True
        )
        
        stdout, stderr = await process.communicate()
        
        return {
            "command": command,
            "exit_code": process.returncode,
            "stdout": stdout.decode('utf-8', errors='replace'),
            "stderr": stderr.decode('utf-8', errors='replace'),
            "cwd": working_dir
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error executing command: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/system", tags=["Admin"])
async def get_system_info():
    """Get system information"""
    try:
        # Get basic system info
        import platform
        import psutil
        
        return {
            "platform": platform.platform(),
            "python_version": sys.version,
            "cpu_count": psutil.cpu_count(),
            "memory": {
                "total": psutil.virtual_memory().total,
                "available": psutil.virtual_memory().available,
                "percent": psutil.virtual_memory().percent
            },
            "disk": {
                "total": psutil.disk_usage('/').total,
                "free": psutil.disk_usage('/').free,
                "percent": psutil.disk_usage('/').percent
            },
            "uptime": psutil.boot_time()
        }
    except ImportError:
        # Fallback if psutil not available
        return {
            "platform": platform.platform(),
            "python_version": sys.version,
            "note": "Install psutil for detailed system info"
        }
    except Exception as e:
        logger.error(f"Error getting system info: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sms-webhook", tags=["SMS Gateway"])
async def sms_webhook(
    request: Request,
    from_: str = Form(..., alias="from"),
    to: str = Form(...),
    text: str = Form(...),
    date: str = Form(None),
    id_: str = Form(None, alias="id"),
    linkId: str = Form(None),
    networkCode: str = Form(None)
):
    """
    Africa's Talking SMS Webhook
    
    Receives incoming SMS messages and sends intelligent responses.
    This endpoint is called by Africa's Talking when an SMS is received.
    
    **How it works:**
    1. User sends SMS to your Africa's Talking shortcode/number
    2. Africa's Talking forwards the SMS to this webhook
    3. AmaniQuery processes the query using RAG pipeline
    4. Response is sent back via SMS (max 160 characters)
    
    **Example SMS queries:**
    - "What is the Finance Bill about?"
    - "Latest news on housing"
    - "Constitution Article 10"
    
    **Setup:**
    1. Sign up at https://africastalking.com
    2. Get API key and username
    3. Set environment variables: AT_USERNAME, AT_API_KEY
    4. Configure webhook URL in Africa's Talking dashboard
    5. Webhook URL: https://your-domain.com/sms-webhook
    """
    if sms_pipeline is None or sms_service is None:
        logger.error("SMS services not initialized")
        return {"status": "error", "message": "SMS service unavailable"}
    
    try:
        # Parse incoming SMS
        phone_number = sms_service.format_kenyan_phone(from_)
        query_text = text.strip()
        
        logger.info(f"📱 Incoming SMS from {phone_number}: {query_text}")
        
        # Detect language (basic detection)
        language = "sw" if any(word in query_text.lower() for word in ["nini", "habari", "tafadhali", "je"]) else "en"
        
        # Process query through SMS-optimized RAG
        result = sms_pipeline.process_sms_query(
            query=query_text,
            language=language,
            phone_number=phone_number
        )
        
        response_text = result["response"]
        
        # Send SMS response
        if sms_service.available:
            send_result = sms_service.send_sms(phone_number, response_text)
            
            if send_result.get("success"):
                logger.info(f"✓ SMS sent to {phone_number}")
                return {
                    "status": "success",
                    "message": "Response sent",
                    "response_text": response_text,
                    "query_type": result.get("query_type"),
                    "message_id": send_result.get("message_id")
                }
            else:
                logger.error(f"Failed to send SMS: {send_result.get('error')}")
                return {
                    "status": "error",
                    "message": "Failed to send response",
                    "error": send_result.get("error")
                }
        else:
            # SMS service not available, just log
            logger.warning(f"SMS service unavailable. Would send: {response_text}")
            return {
                "status": "success",
                "message": "Query processed (SMS sending disabled)",
                "response_text": response_text,
                "query_type": result.get("query_type")
            }
            
    except Exception as e:
        logger.error(f"Error handling SMS webhook: {e}")
        return {
            "status": "error",
            "message": str(e)
        }


@app.post("/sms-send", tags=["SMS Gateway"])
async def send_sms_manual(phone_number: str, message: str):
    """
    Send SMS manually (for testing)
    
    **Parameters:**
    - phone_number: Recipient phone number (+254XXXXXXXXX)
    - message: SMS message text (max 160 characters recommended)
    
    **Example:**
    ```
    POST /sms-send
    {
        "phone_number": "+254712345678",
        "message": "Finance Bill 2025 aims to raise revenue through new taxes on digital services."
    }
    ```
    """
    if sms_service is None or not sms_service.available:
        raise HTTPException(status_code=503, detail="SMS service not available")
    
    try:
        # Format phone number
        formatted_phone = sms_service.format_kenyan_phone(phone_number)
        
        # Send SMS
        result = sms_service.send_sms(formatted_phone, message)
        
        if result.get("success"):
            return {
                "status": "success",
                "phone_number": formatted_phone,
                "message": message,
                "message_id": result.get("message_id"),
                "cost": result.get("cost")
            }
        else:
            raise HTTPException(status_code=500, detail=result.get("error"))
            
    except Exception as e:
        logger.error(f"Error sending manual SMS: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/sms-query", tags=["SMS Gateway"])
async def sms_query_preview(query: str, language: str = "en"):
    """
    Preview SMS response without sending
    
    Test what response would be sent via SMS for a given query.
    Useful for testing before deploying webhook.
    
    **Parameters:**
    - query: Question to ask
    - language: Response language ('en' or 'sw')
    
    **Example:**
    - query: "What is the Finance Bill?"
    - language: "en"
    """
    if sms_pipeline is None:
        raise HTTPException(status_code=503, detail="SMS pipeline not initialized")
    
    try:
        result = sms_pipeline.process_sms_query(
            query=query,
            language=language
        )
        
        return {
            "query": query,
            "response": result["response"],
            "character_count": len(result["response"]),
            "within_sms_limit": len(result["response"]) <= 160,
            "query_type": result.get("query_type"),
            "sources": result.get("sources", []),
            "language": language
        }
        
    except Exception as e:
        logger.error(f"Error previewing SMS query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Research and Report Generation Endpoints
@app.post("/research/analyze-legal-query", tags=["Research"])
async def analyze_legal_query(
    query: str = Form(...),
    context: Optional[str] = Form(None)
):
    """
    Analyze a legal query about Kenya's laws using Gemini AI

    This endpoint performs deep analysis of legal questions, providing information
    about applicable laws, legal procedures, and practical guidance.

    **Parameters:**
    - query: The legal question or query to analyze
    - context: Optional additional context about the query (JSON string)

    **Returns:**
    - Comprehensive legal analysis covering applicable laws, legal reasoning, and practical guidance
    """
    if research_module is None:
        raise HTTPException(status_code=503, detail="Research module not available. Ensure GEMINI_API_KEY is configured.")

    try:
        # Parse context if provided
        context_data = None
        if context:
            try:
                context_data = json.loads(context)
            except json.JSONDecodeError:
                context_data = {"additional_info": context}

        result = research_module.analyze_legal_query(query, context_data)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return result

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in legal query analysis: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/research/generate-legal-report", tags=["Research"])
async def generate_legal_report(
    analysis_results: str = Form(...),
    report_focus: str = Form("comprehensive")
):
    """
    Generate a comprehensive legal report based on query analysis

    **Parameters:**
    - analysis_results: JSON string of analysis results from /research/analyze-legal-query
    - report_focus: Type of legal focus (comprehensive, constitutional, criminal, civil, administrative)

    **Returns:**
    - Structured legal report with analysis, applicable laws, and recommendations
    """
    if research_module is None:
        raise HTTPException(status_code=503, detail="Research module not available. Ensure GEMINI_API_KEY is configured.")

    try:
        # Parse the analysis results
        analysis_data = json.loads(analysis_results)

        result = research_module.generate_legal_report(analysis_data, report_focus)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return result

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in analysis_results")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating legal report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/research/legal-research", tags=["Research"])
async def conduct_legal_research(
    legal_topics: str = Form(...),
    research_questions: str = Form(...)
):
    """
    Conduct legal research on specific topics related to Kenya's laws

    **Parameters:**
    - legal_topics: JSON string array of legal topics to research
    - research_questions: JSON string array of specific research questions

    **Returns:**
    - Legal research findings with analysis of Kenyan laws and practical guidance
    """
    if research_module is None:
        raise HTTPException(status_code=503, detail="Research module not available. Ensure GEMINI_API_KEY is configured.")

    try:
        # Parse the input data
        topics = json.loads(legal_topics)
        questions = json.loads(research_questions)

        if not isinstance(topics, list) or not isinstance(questions, list):
            raise HTTPException(status_code=400, detail="legal_topics and research_questions must be JSON arrays")

        result = research_module.conduct_legal_research(topics, questions)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return result

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON format: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error conducting legal research: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/research/generate-pdf-report", tags=["Research"])
async def generate_pdf_report(
    analysis_results: str = Form(...),
    report_title: str = Form("Legal Research Report")
):
    """
    Generate a PDF report from legal analysis results

    **Parameters:**
    - analysis_results: JSON string of analysis results from /research/analyze-legal-query
    - report_title: Title for the PDF report

    **Returns:**
    - PDF file as downloadable content
    """
    if research_module is None:
        raise HTTPException(status_code=503, detail="Research module not available. Ensure GEMINI_API_KEY is configured.")

    try:
        # Parse the analysis results
        analysis_data = json.loads(analysis_results)

        # Generate PDF
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as tmp_file:
            pdf_path = research_module.generate_pdf_report(analysis_data, tmp_file.name)
        
        # Read the PDF content
        with open(pdf_path, 'rb') as f:
            pdf_content = f.read()
        
        # Return as file download
        from fastapi.responses import Response
        return Response(
            content=pdf_content,
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={report_title.replace(' ', '_')}.pdf"}
        )

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in analysis_results")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating PDF report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/research/generate-word-report", tags=["Research"])
async def generate_word_report(
    analysis_results: str = Form(...),
    report_title: str = Form("Legal Research Report")
):
    """
    Generate a Word document report from legal analysis results

    **Parameters:**
    - analysis_results: JSON string of analysis results from /research/analyze-legal-query
    - report_title: Title for the Word document

    **Returns:**
    - Word document (.docx) as downloadable content
    """
    if research_module is None:
        raise HTTPException(status_code=503, detail="Research module not available. Ensure GEMINI_API_KEY is configured.")

    try:
        # Parse the analysis results
        analysis_data = json.loads(analysis_results)

        # Generate Word document
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix='.docx') as tmp_file:
            word_path = research_module.generate_word_report(analysis_data, tmp_file.name)
        
        # Read the Word content
        with open(word_path, 'rb') as f:
            word_content = f.read()
        
        # Return as file download
        from fastapi.responses import Response
        return Response(
            content=word_content,
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={report_title.replace(' ', '_')}.docx"}
        )

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in analysis_results")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating Word report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reports/legal-query", tags=["Reports"])
async def generate_legal_query_report(query_analysis: str = Form(...)):
    """
    Generate a comprehensive legal query report

    **Parameters:**
    - query_analysis: JSON string containing legal query analysis results

    **Returns:**
    - Professional legal query report with analysis, applicable laws, and guidance
    """
    if report_generator is None:
        raise HTTPException(status_code=503, detail="Report generator not available. Ensure GEMINI_API_KEY is configured.")

    try:
        # Parse the query analysis
        analysis = json.loads(query_analysis)

        result = report_generator.generate_legal_query_report(analysis)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return result

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in query_analysis")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating legal query report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reports/legal-research", tags=["Reports"])
async def generate_legal_research_report(
    research_data: str = Form(...),
    research_findings: str = Form(...)
):
    """
    Generate a legal research report

    **Parameters:**
    - research_data: JSON string of legal topics and research parameters
    - research_findings: JSON string of research findings from legal analysis

    **Returns:**
    - Comprehensive legal research report with analysis of Kenyan laws and recommendations
    """
    if report_generator is None:
        raise HTTPException(status_code=503, detail="Report generator not available. Ensure GEMINI_API_KEY is configured.")

    try:
        # Parse the input data
        research_info = json.loads(research_data)
        findings = json.loads(research_findings)

        result = report_generator.generate_legal_research_report(research_info, findings)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return result

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON format: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating legal research report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reports/constitutional-law", tags=["Reports"])
async def generate_constitutional_law_report(constitutional_analysis: str = Form(...)):
    """
    Generate a constitutional law report

    **Parameters:**
    - constitutional_analysis: JSON string of constitutional law analysis

    **Returns:**
    - Specialized constitutional law report with references to the Constitution of Kenya 2010
    """
    if report_generator is None:
        raise HTTPException(status_code=503, detail="Report generator not available. Ensure GEMINI_API_KEY is configured.")

    try:
        # Parse the constitutional analysis
        analysis = json.loads(constitutional_analysis)

        result = report_generator.generate_constitutional_law_report(analysis)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return result

    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="Invalid JSON in constitutional_analysis")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating constitutional law report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reports/compliance", tags=["Reports"])
async def generate_compliance_report(
    legal_requirements: str = Form(...),
    compliance_data: str = Form(...)
):
    """
    Generate a legal compliance report

    **Parameters:**
    - legal_requirements: JSON string of legal requirements and obligations
    - compliance_data: JSON string of current compliance status

    **Returns:**
    - Legal compliance assessment report with gaps, risks, and action plans
    """
    if report_generator is None:
        raise HTTPException(status_code=503, detail="Report generator not available. Ensure GEMINI_API_KEY is configured.")

    try:
        # Parse the input data
        requirements = json.loads(legal_requirements)
        compliance = json.loads(compliance_data)

        result = report_generator.generate_compliance_report(requirements, compliance)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        return result

    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON format: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating compliance report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reports/technical-audit", tags=["Reports"])
async def generate_technical_audit_report(
    system_metrics: str = Form(...),
    performance_data: str = Form(...)
):
    """
    Generate a technical audit report
    
    **Parameters:**
    - system_metrics: JSON string of system performance and health metrics
    - performance_data: JSON string of detailed performance measurements
    
    **Returns:**
    - Technical audit report with performance analysis, security assessment, and recommendations
    """
    if report_generator is None:
        raise HTTPException(status_code=503, detail="Report generator not available. Ensure GEMINI_API_KEY is configured.")
    
    try:
        # Parse the input data
        metrics = json.loads(system_metrics)
        performance = json.loads(performance_data)
        
        result = report_generator.generate_technical_audit_report(metrics, performance)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON format: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating technical audit report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/reports/impact-assessment", tags=["Reports"])
async def generate_impact_assessment_report(
    usage_data: str = Form(...),
    impact_metrics: str = Form(...)
):
    """
    Generate an impact assessment report
    
    **Parameters:**
    - usage_data: JSON string of user usage and engagement data
    - impact_metrics: JSON string of social and economic impact metrics
    
    **Returns:**
    - Impact assessment report covering social, economic, and educational impacts
    """
    if report_generator is None:
        raise HTTPException(status_code=503, detail="Report generator not available. Ensure GEMINI_API_KEY is configured.")
    
    try:
        # Parse the input data
        usage = json.loads(usage_data)
        impact = json.loads(impact_metrics)
        
        result = report_generator.generate_impact_assessment_report(usage, impact)
        
        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])
        
        return result
        
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON format: {str(e)}")
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error generating impact assessment report: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/research/status", tags=["Research"])
async def get_research_status():
    """Get the status of research and report generation capabilities"""
    return {
        "research_module_available": research_module is not None,
        "report_generator_available": report_generator is not None,
        "gemini_api_configured": bool(os.getenv("GEMINI_API_KEY")),
        "available_endpoints": [
            "/research/analyze-legal-query",
            "/research/generate-legal-report",
            "/research/legal-research",
            "/research/generate-pdf-report",
            "/research/generate-word-report",
            "/reports/legal-query",
            "/reports/legal-research",
            "/reports/constitutional-law",
            "/reports/compliance",
            "/reports/technical-audit",
            "/reports/impact-assessment"
        ] if (research_module is not None and report_generator is not None) else []
    }


# Crawler Manager Class
class CrawlerManager:
    def __init__(self):
        self.crawlers = {}
        self.processes = {}
        self.logs = {}
        self.status_file = Path(__file__).parent / "crawler_status.json"
        self.load_status()
        
        # Start background status checker
        self.status_thread = threading.Thread(target=self._status_checker, daemon=True)
        self.status_thread.start()
    
    def load_status(self):
        """Load crawler status from file"""
        try:
            if self.status_file.exists():
                with open(self.status_file, 'r') as f:
                    data = json.load(f)
                    self.crawlers = data.get('crawlers', {})
                    self.logs = data.get('logs', {})
        except Exception as e:
            logger.error(f"Error loading crawler status: {e}")
            self.crawlers = {}
            self.logs = {}
    
    def save_status(self):
        """Save crawler status to file"""
        try:
            data = {
                'crawlers': self.crawlers,
                'logs': self.logs
            }
            with open(self.status_file, 'w') as f:
                json.dump(data, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving crawler status: {e}")
    
    def _status_checker(self):
        """Background thread to check process status"""
        while True:
            try:
                for crawler_name, process_info in list(self.processes.items()):
                    pid = process_info['pid']
                    try:
                        # Check if process is still running
                        process = process_info['process']
                        if process.poll() is not None:
                            # Process finished
                            exit_code = process.returncode
                            if exit_code == 0:
                                self.crawlers[crawler_name]['status'] = 'idle'
                                self._add_log(crawler_name, f"Process completed successfully (PID: {pid})")
                            else:
                                self.crawlers[crawler_name]['status'] = 'failed'
                                self._add_log(crawler_name, f"Process failed with exit code {exit_code} (PID: {pid})")
                            
                            # Clean up
                            del self.processes[crawler_name]
                            self.crawlers[crawler_name]['last_run'] = datetime.utcnow().isoformat() + 'Z'
                            self.save_status()
                        else:
                            # Process still running
                            self.crawlers[crawler_name]['status'] = 'running'
                    except Exception as e:
                        logger.error(f"Error checking process {pid}: {e}")
                        self.crawlers[crawler_name]['status'] = 'failed'
                        self._add_log(crawler_name, f"Error monitoring process: {e}")
                        if crawler_name in self.processes:
                            del self.processes[crawler_name]
                        self.save_status()
                
                time.sleep(5)  # Check every 5 seconds
            except Exception as e:
                logger.error(f"Error in status checker: {e}")
                time.sleep(10)
    
    def _add_log(self, crawler_name: str, message: str):
        """Add a log entry for a crawler"""
        if crawler_name not in self.logs:
            self.logs[crawler_name] = []
        
        timestamp = datetime.utcnow().isoformat() + 'Z'
        self.logs[crawler_name].append(f"[{timestamp}] {message}")
        
        # Keep only last 100 logs
        if len(self.logs[crawler_name]) > 100:
            self.logs[crawler_name] = self.logs[crawler_name][-100:]
    
    def get_crawler_status(self):
        """Get status of all crawlers"""
        # Initialize default crawlers if not exists
        default_crawlers = {
            "kenya_law": {"status": "idle", "last_run": "2024-01-15T10:30:00Z"},
            "parliament": {"status": "idle", "last_run": "2024-01-15T09:15:00Z"},
            "news_rss": {"status": "idle", "last_run": "2024-01-15T11:00:00Z"},
            "global_trends": {"status": "idle", "last_run": "2024-01-14T16:45:00Z"}
        }
        
        # Merge with saved status
        for name, default_status in default_crawlers.items():
            if name not in self.crawlers:
                self.crawlers[name] = default_status
                self.logs[name] = []
        
        # Return current status with logs
        result = {}
        for name, status in self.crawlers.items():
            result[name] = {
                **status,
                "logs": self.logs.get(name, [])
            }
        
        return result
    
    def start_crawler(self, crawler_name: str):
        """Start a specific crawler"""
        if crawler_name not in self.crawlers:
            raise HTTPException(status_code=404, detail=f"Crawler {crawler_name} not found")
        
        # Check if already running
        if crawler_name in self.processes:
            return {"status": "already_running", "message": f"Crawler {crawler_name} is already running"}
        
        try:
            # Get spider directory
            spider_dir = Path(__file__).parent.parent / "Module1_NiruSpider"
            
            # Map crawler names to spider names
            spider_mapping = {
                "kenya_law": "kenya_law",
                "parliament": "parliament", 
                "news_rss": "news_rss",
                "global_trends": "global_trends"
            }
            
            if crawler_name not in spider_mapping:
                raise HTTPException(status_code=404, detail=f"Unknown crawler: {crawler_name}")
            
            spider_name = spider_mapping[crawler_name]
            
            # Start subprocess with log capture
            cmd = [sys.executable, "-m", "scrapy", "crawl", spider_name, "-L", "INFO"]
            
            # Create subprocess with pipes for log capture
            process = subprocess.Popen(
                cmd,
                cwd=str(spider_dir),
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,  # Merge stderr with stdout
                bufsize=1,
                universal_newlines=True
            )
            
            # Store process info
            self.processes[crawler_name] = {
                'process': process,
                'pid': process.pid,
                'start_time': datetime.utcnow().isoformat() + 'Z'
            }
            
            # Update status
            self.crawlers[crawler_name]['status'] = 'running'
            self._add_log(crawler_name, f"Started crawler process (PID: {process.pid})")
            self.save_status()
            
            # Start log reader thread
            log_thread = threading.Thread(
                target=self._read_process_logs, 
                args=(crawler_name, process), 
                daemon=True
            )
            log_thread.start()
            
            logger.info(f"Started {crawler_name} crawler subprocess (PID: {process.pid})")
            return {
                "status": "started", 
                "message": f"Crawler {crawler_name} started successfully", 
                "pid": process.pid
            }
            
        except Exception as e:
            logger.error(f"Error starting crawler {crawler_name}: {e}")
            self.crawlers[crawler_name]['status'] = 'failed'
            self._add_log(crawler_name, f"Failed to start: {str(e)}")
            self.save_status()
            raise HTTPException(status_code=500, detail=f"Failed to start crawler: {str(e)}")
    
    def _read_process_logs(self, crawler_name: str, process: subprocess.Popen):
        """Read logs from subprocess and store them"""
        try:
            while True:
                line = process.stdout.readline()
                if not line:
                    break
                # Clean and store log line
                clean_line = line.strip()
                if clean_line:
                    self._add_log(crawler_name, clean_line)
        except Exception as e:
            self._add_log(crawler_name, f"Error reading logs: {str(e)}")
    
    def stop_crawler(self, crawler_name: str):
        """Stop a specific crawler"""
        if crawler_name not in self.crawlers:
            raise HTTPException(status_code=404, detail=f"Crawler {crawler_name} not found")
        
        if crawler_name not in self.processes:
            return {"status": "not_running", "message": f"Crawler {crawler_name} is not running"}
        
        try:
            process_info = self.processes[crawler_name]
            process = process_info['process']
            
            # Terminate process
            process.terminate()
            
            # Wait a bit for graceful shutdown
            try:
                process.wait(timeout=10)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't respond
                process.kill()
                process.wait()
            
            # Clean up
            del self.processes[crawler_name]
            self.crawlers[crawler_name]['status'] = 'idle'
            self.crawlers[crawler_name]['last_run'] = datetime.utcnow().isoformat() + 'Z'
            self._add_log(crawler_name, f"Process stopped (PID: {process_info['pid']})")
            self.save_status()
            
            return {"status": "stopped", "message": f"Crawler {crawler_name} stopped successfully"}
            
        except Exception as e:
            logger.error(f"Error stopping crawler {crawler_name}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to stop crawler: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    reload = os.getenv("API_RELOAD", "True").lower() == "true"
    
    print("=" * 60)
    print("🚀 Starting AmaniQuery API")
    print("=" * 60)
    print(f"📍 Server: http://{host}:{port}")
    print(f"📚 Docs: http://{host}:{port}/docs")
    print(f"🔧 Provider: {os.getenv('LLM_PROVIDER', 'moonshot')}")
    print("=" * 60)
    
    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        reload=reload,
    )
