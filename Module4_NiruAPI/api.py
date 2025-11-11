"""
FastAPI Application - REST API for AmaniQuery
"""
import os
import sys
from pathlib import Path
from typing import Optional, List
import subprocess
import asyncio
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Request, Form
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from loguru import logger

from Module4_NiruAPI.rag_pipeline import RAGPipeline
from Module4_NiruAPI.alignment_pipeline import ConstitutionalAlignmentPipeline
from Module4_NiruAPI.sms_pipeline import SMSPipeline
from Module4_NiruAPI.sms_service import AfricasTalkingSMSService
from Module3_NiruDB.chat_manager import ChatDatabaseManager
from Module3_NiruDB.chat_models import (
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
from Module5_NiruShare.api import router as share_router

# Load environment
load_dotenv()

# Initialize FastAPI app
app = FastAPI(
    title="AmaniQuery API",
    description="RAG-powered API for Kenyan legal, parliamentary, and news intelligence",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:8000").split(","),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include sharing router
app.include_router(share_router)

# Initialize components
vector_store = None
rag_pipeline = None
alignment_pipeline = None
sms_pipeline = None
sms_service = None
metadata_manager = None
chat_manager = None


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    global vector_store, rag_pipeline, alignment_pipeline, sms_pipeline, sms_service, metadata_manager
    
    logger.info("Starting AmaniQuery API")
    
    # Initialize vector store
    vector_store = VectorStore()
    
    # Initialize metadata manager
    metadata_manager = MetadataManager()
    
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
    
    logger.info("AmaniQuery API ready")


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
    from Module3_NiruDB import MetadataManager
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


@app.get("/categories", tags=["Metadata"])
async def get_categories():
    """Get list of all categories"""
    if vector_store is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    from Module3_NiruDB import MetadataManager
    meta_manager = MetadataManager(vector_store)
    
    return {"categories": meta_manager.get_categories()}


@app.get("/sources", tags=["Metadata"])
async def get_sources():
    """Get list of all sources"""
    if vector_store is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    from Module3_NiruDB import MetadataManager
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
        results = vector_store.search(
            query_text=topic,
            top_k=100,  # Get up to 100 articles
            filter_dict=filter_dict
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
        raise HTTPException(status_code=500, detail=str(e))


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
            # Process user message with RAG
            result = rag_pipeline.query(
                query=message.content,
                top_k=5
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
    crawlers = {
        "kenya_law": {"status": "idle", "last_run": "2024-01-15T10:30:00Z", "logs": []},
        "parliament": {"status": "idle", "last_run": "2024-01-15T09:15:00Z", "logs": []},
        "nation_news": {"status": "idle", "last_run": "2024-01-15T11:00:00Z", "logs": []},
        "global_trends": {"status": "idle", "last_run": "2024-01-14T16:45:00Z", "logs": []}
    }
    return {"crawlers": crawlers}


@app.post("/admin/crawlers/{crawler_name}/start", tags=["Admin"])
async def start_crawler(crawler_name: str):
    """Start a specific crawler"""
    try:
        # Import crawler modules dynamically
        if crawler_name == "kenya_law":
            from Module1_NiruSpider.kenya_law_spider import KenyaLawSpider
            # This would start the spider in background
            # For now, just return success
            return {"status": "started", "message": f"Crawler {crawler_name} started"}
        elif crawler_name == "parliament":
            from Module1_NiruSpider.parliament_spider import ParliamentSpider
            return {"status": "started", "message": f"Crawler {crawler_name} started"}
        elif crawler_name == "nation_news":
            from Module1_NiruSpider.news_rss_spider import NewsRSSSpider
            return {"status": "started", "message": f"Crawler {crawler_name} started"}
        else:
            raise HTTPException(status_code=404, detail=f"Crawler {crawler_name} not found")
    except Exception as e:
        logger.error(f"Error starting crawler {crawler_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/crawlers/{crawler_name}/stop", tags=["Admin"])
async def stop_crawler(crawler_name: str):
    """Stop a specific crawler"""
    return {"status": "stopped", "message": f"Crawler {crawler_name} stopped"}


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
            results = vector_store.search(
                query_text=query,
                top_k=limit,
                filter_dict=filter_dict if filter_dict else None
            )
        else:
            # Get all documents if no query
            results = vector_store.search(
                query_text="",
                top_k=limit,
                filter_dict=filter_dict if filter_dict else None
            )
        
        # Format results
        documents = []
        for chunk in results:
            metadata = chunk.get("metadata", {})
            documents.append({
                "id": chunk.get("id", ""),
                "content": chunk.get("content", ""),
                "metadata": {
                    "title": metadata.get("title", ""),
                    "url": metadata.get("url", ""),
                    "source": metadata.get("source", ""),
                    "category": metadata.get("category", ""),
                    "date": metadata.get("date", ""),
                    "author": metadata.get("author", ""),
                    "sentiment_polarity": metadata.get("sentiment_polarity"),
                    "sentiment_label": metadata.get("sentiment_label")
                },
                "score": chunk.get("score", 0)
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
