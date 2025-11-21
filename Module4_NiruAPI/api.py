"""
FastAPI Application - REST API for AmaniQuery
"""
import os
import sys
from pathlib import Path
from typing import Optional, List, Dict
import subprocess
import asyncio
import threading
import time
import json
from datetime import datetime

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException, Request, Form, UploadFile, File, Depends
from fastapi import Request as FastAPIRequest
from fastapi.responses import FileResponse
from pydantic import BaseModel
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
from Module4_NiruAPI.research_module import ResearchModule  # Legacy fallback
from Module4_NiruAPI.research_module_agentic import AgenticResearchModule
from Module4_NiruAPI.config_manager import ConfigManager
from Module4_NiruAPI.report_generator import ReportGenerator
from Module4_NiruAPI.cache import get_cache_manager, CacheManager
from Module4_NiruAPI.crawler_models import CrawlerDatabaseManager
from Module5_NiruShare.api import router as share_router
from Module4_NiruAPI.routers.news_router import router as news_router
from Module4_NiruAPI.routers.websocket_router import router as websocket_router, broadcast_new_article
from Module4_NiruAPI.routers.notification_router import router as notification_router
from Module4_NiruAPI.services.notification_service import NotificationService
from Module4_NiruAPI.agents.tools.autocomplete import AutocompleteTool

# Load environment
load_dotenv()

# Lifespan context manager for startup/shutdown
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Handle application startup and shutdown"""
    global vector_store, rag_pipeline, alignment_pipeline, sms_pipeline, sms_service, metadata_manager, chat_manager, crawler_manager, research_module, agentic_research_module, report_generator, config_manager, notification_service, hybrid_rag_pipeline, autocomplete_tool, vision_storage, vision_rag_service, database_storage, cache_manager
    
    logger.info("Starting AmaniQuery API")
    
    # Initialize config manager
    try:
        config_manager = ConfigManager()
        logger.info("Config manager initialized")
    except Exception as e:
        logger.error(f"Failed to initialize config manager: {e}")
        config_manager = None
    
    # Initialize vector store
    try:
        backend = os.getenv("VECTOR_STORE_BACKEND", "chromadb")  # upstash, qdrant, chromadb
        vector_store = VectorStore(backend=backend, config_manager=config_manager)
        logger.info("Vector store initialized")
    except Exception as e:
        logger.error(f"Failed to initialize vector store: {e}")
        vector_store = None
    
    # Initialize metadata manager
    try:
        if vector_store:
            metadata_manager = MetadataManager(vector_store)
            logger.info("Metadata manager initialized")
        else:
            metadata_manager = None
    except Exception as e:
        logger.error(f"Failed to initialize metadata manager: {e}")
        metadata_manager = None
    
    # Initialize RAG pipeline
    try:
        if vector_store:
            llm_provider = os.getenv("LLM_PROVIDER", "moonshot")
            model = os.getenv("DEFAULT_MODEL", "moonshot-v1-8k")
            
            rag_pipeline = RAGPipeline(
                vector_store=vector_store,
                llm_provider=llm_provider,
                model=model,
            )
            logger.info("RAG pipeline initialized")
        else:
            rag_pipeline = None
    except Exception as e:
        logger.error(f"Failed to initialize RAG pipeline: {e}")
        rag_pipeline = None
    
    # Initialize Constitutional Alignment Pipeline
    try:
        if vector_store and rag_pipeline:
            alignment_pipeline = ConstitutionalAlignmentPipeline(
                vector_store=vector_store,
                rag_pipeline=rag_pipeline,
            )
            logger.info("Alignment pipeline initialized")
        else:
            alignment_pipeline = None
    except Exception as e:
        logger.error(f"Failed to initialize alignment pipeline: {e}")
        alignment_pipeline = None
    
    # Initialize SMS Pipeline
    try:
        if vector_store and rag_pipeline:
            sms_pipeline = SMSPipeline(
                vector_store=vector_store,
                llm_service=rag_pipeline.llm_service
            )
            logger.info("SMS pipeline initialized")
        else:
            sms_pipeline = None
    except Exception as e:
        logger.error(f"Failed to initialize SMS pipeline: {e}")
        sms_pipeline = None
    
    # Initialize SMS Service (Africa's Talking)
    try:
        sms_service = AfricasTalkingSMSService()
        if sms_service.available:
            logger.info("SMS service initialized and available")
        else:
            logger.warning("SMS service initialized but not available (check credentials)")
    except Exception as e:
        logger.error(f"Failed to initialize SMS service: {e}")
        sms_service = None
    
    # Initialize Hybrid RAG Pipeline (optional - for enhanced retrieval)
    try:
        if vector_store and rag_pipeline:
            from Module7_NiruHybrid.integration.rag_integration import HybridRAGPipeline
            from Module7_NiruHybrid.hybrid_encoder import HybridEncoder
            from Module7_NiruHybrid.retention.adaptive_retriever import AdaptiveRetriever
            from Module7_NiruHybrid.config import default_config
            
            # Initialize components
            hybrid_encoder = HybridEncoder(config=default_config.encoder)
            adaptive_retriever = AdaptiveRetriever(
                hybrid_encoder=hybrid_encoder,
                vector_store=vector_store,
                config=default_config.retention
            )
            
            # Create hybrid RAG pipeline
            hybrid_rag_pipeline = HybridRAGPipeline(
                base_rag_pipeline=rag_pipeline,
                hybrid_encoder=hybrid_encoder,
                adaptive_retriever=adaptive_retriever,
                use_hybrid=True,
                use_adaptive_retrieval=True,
                config=default_config
            )
            logger.info("Hybrid RAG pipeline initialized")
        else:
            hybrid_rag_pipeline = None
            logger.warning("Hybrid RAG pipeline not initialized: vector_store or rag_pipeline not available")
    except Exception as e:
        logger.warning(f"Hybrid RAG pipeline not available: {e}")
        hybrid_rag_pipeline = None
    
    # Initialize chat database manager
    try:
        chat_manager = ChatDatabaseManager()
        logger.info("Chat manager initialized")
    except Exception as e:
        logger.error(f"Failed to initialize chat manager: {e}")
        chat_manager = None
    
    # Initialize cache manager
    try:
        cache_manager = get_cache_manager(config_manager)
        logger.info("Cache manager initialized")
    except Exception as e:
        logger.warning(f"Failed to initialize cache manager: {e}")
        cache_manager = None
    
    # Initialize crawler manager
    try:
        crawler_manager = CrawlerManager()
        logger.info("Crawler manager initialized")
    except Exception as e:
        logger.error(f"Failed to initialize crawler manager: {e}")
        crawler_manager = None
    
    # Initialize research module (try agentic first, fallback to legacy)
    agentic_research_module = None
    research_module = None
    try:
        # Try agentic research module first
        agentic_research_module = AgenticResearchModule(config_manager=config_manager)
        logger.info("Agentic research module initialized")
    except Exception as e:
        logger.warning(f"Agentic research module not available: {e}, falling back to legacy module")
        try:
            research_module = ResearchModule()
            logger.info("Legacy research module initialized")
        except Exception as e2:
            logger.warning(f"Legacy research module also not available: {e2}")
            research_module = None
    
    # Initialize report generator (optional - only if Gemini API key is available)
    try:
        report_generator = ReportGenerator()
        logger.info("Report generator initialized")
    except Exception as e:
        logger.warning(f"Report generator not available: {e}")
        report_generator = None
    
    # Initialize authentication module (if enabled)
    auth_enabled = os.getenv("ENABLE_AUTH", "false").lower() == "true"
    if auth_enabled:
        try:
            logger.info("Initializing authentication module...")
            
            # Check and create auth database tables if needed
            try:
                from Module3_NiruDB.chat_models import create_database_engine
                from Module8_NiruAuth.models.auth_models import Base
                from sqlalchemy import inspect
                
                database_url = os.getenv("DATABASE_URL")
                if database_url:
                    engine = create_database_engine(database_url)
                    with engine.connect() as conn:
                        inspector = inspect(conn)
                        existing_tables = inspector.get_table_names()
                        
                        # Check if auth tables exist
                        required_tables = ["users", "roles", "api_keys"]
                        missing_tables = [t for t in required_tables if t not in existing_tables]
                        
                        if missing_tables:
                            logger.info(f"Creating missing auth tables: {missing_tables}")
                            Base.metadata.create_all(engine)
                            logger.info("✅ Auth tables created successfully")
                            
                            # Initialize default roles
                            try:
                                from sqlalchemy.orm import sessionmaker
                                from Module8_NiruAuth.authorization.role_manager import RoleManager
                                Session = sessionmaker(bind=engine)
                                db = Session()
                                try:
                                    RoleManager.get_or_create_default_roles(db)
                                    logger.info("✅ Default roles initialized")
                                finally:
                                    db.close()
                            except Exception as e:
                                logger.warning(f"Could not initialize default roles: {e}")
                        else:
                            logger.info("✅ Auth tables already exist")
            except Exception as e:
                logger.warning(f"Auth database initialization check failed: {e}")
                logger.warning("You may need to run 'python migrate_auth_db.py' manually")
            
            logger.info("✅ Authentication module initialized")
        except Exception as e:
            logger.error(f"Failed to initialize authentication module: {e}")
            logger.error("Auth features will not be available")
    else:
        logger.info("Authentication module disabled (set ENABLE_AUTH=true to enable)")
    
    # Initialize notification service
    try:
        notification_service = NotificationService(config_manager=config_manager)
        # Set global instance for router
        from Module4_NiruAPI.routers import notification_router as nr_module
        nr_module.notification_service = notification_service
        nr_module.news_service = None  # Will be lazy-loaded
        
        # Create notification callback function for database storage
        def notification_callback(article: Dict):
            """Callback function to send notifications for new articles"""
            try:
                if notification_service:
                    notification_service.send_article_notification(article)
            except Exception as e:
                logger.error(f"Error in notification callback: {e}")
        
        # Make callback available globally for database storage
        import Module3_NiruDB.database_storage as db_storage_module
        db_storage_module.default_notification_callback = notification_callback
        
        logger.info("Notification service initialized")
        
        # Start background task for daily digest
        def daily_digest_worker():
            """Background worker for daily digest notifications"""
            import time
            while True:
                try:
                    time.sleep(3600)  # Check every hour
                    current_hour = datetime.utcnow().hour
                    if current_hour == 8:  # Send at 8 AM UTC (adjust as needed)
                        notification_service.send_digest_notifications()
                except Exception as e:
                    logger.error(f"Error in daily digest worker: {e}")
        
        digest_thread = threading.Thread(target=daily_digest_worker, daemon=True)
        digest_thread.start()
        logger.info("Daily digest background worker started")
        
    except Exception as e:
        logger.warning(f"Notification service not available: {e}")
        notification_service = None
    
    # Initialize autocomplete tool
    try:
        autocomplete_tool = AutocompleteTool()
        logger.info("Autocomplete tool initialized")
    except Exception as e:
        logger.warning(f"Autocomplete tool not available: {e}")
        autocomplete_tool = None
    
    # Initialize Vision RAG service and storage
    vision_storage = {}  # In-memory storage: {session_id: [image_data, ...]}
    vision_rag_service = None
    try:
        from Module4_NiruAPI.services.vision_rag import VisionRAGService
        vision_rag_service = VisionRAGService()
        logger.info("Vision RAG service initialized")
    except Exception as e:
        logger.warning(f"Vision RAG service not available: {e}. Vision RAG features will be disabled.")
        vision_rag_service = None
    
    # Initialize DatabaseStorage (reused across requests to avoid blocking)
    try:
        from Module3_NiruDB.database_storage import DatabaseStorage
        database_storage = DatabaseStorage()
        logger.info("Database storage initialized")
    except Exception as e:
        logger.warning(f"Database storage not available: {e}")
        database_storage = None
    
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
# Default origins include localhost for development and Vercel for production frontend
cors_origins = os.getenv("CORS_ORIGINS", "http://localhost:3000,http://localhost:3001,http://localhost:8000,http://frontend:3000,https://amaniquery.vercel.app,https://www.amaniquery.vercel.app,https://api-amaniquery.onrender.com")
origins = [origin.strip() for origin in cors_origins.split(",")]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add authentication middleware (optional - can be enabled via env var)
if os.getenv("ENABLE_AUTH", "false").lower() == "true":
    from Module8_NiruAuth.middleware.auth_middleware import AuthMiddleware
    from Module8_NiruAuth.middleware.rate_limit_middleware import RateLimitMiddleware
    from Module8_NiruAuth.middleware.usage_tracking_middleware import UsageTrackingMiddleware
    
    # Add middleware in order (FastAPI executes in reverse order)
    # So we add: UsageTracking -> RateLimit -> Auth
    # They execute: Auth -> RateLimit -> UsageTracking
    app.add_middleware(UsageTrackingMiddleware)
    app.add_middleware(RateLimitMiddleware)
    app.add_middleware(AuthMiddleware)  # This executes first
    
    # Include auth routers
    from Module8_NiruAuth.routers import (
        user_router, admin_router, integration_router,
        api_key_router, oauth_router, analytics_router, blog_router
    )
    from Module8_NiruAuth.routers.phone_verification_router import router as phone_verification_router
    
    app.include_router(user_router)
    app.include_router(admin_router)
    app.include_router(integration_router)
    app.include_router(api_key_router)
    app.include_router(oauth_router)
    app.include_router(analytics_router)
    app.include_router(blog_router)
    app.include_router(phone_verification_router)

app.include_router(share_router)
app.include_router(news_router)
app.include_router(websocket_router)
app.include_router(notification_router)

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
    """Health check endpoint - cached for 30 seconds"""
    if vector_store is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    # Try to get from cache
    cache_key = "cache:health"
    if cache_manager:
        cached_result = cache_manager.get(cache_key)
        if cached_result is not None:
            logger.debug("Cache hit for health check")
            return HealthResponse(**cached_result)
    
    stats = vector_store.get_stats()
    
    # Handle case where total_chunks might be "unknown" string
    total_chunks = stats["total_chunks"]
    if isinstance(total_chunks, str) and total_chunks == "unknown":
        total_chunks = 0
    elif not isinstance(total_chunks, int):
        total_chunks = 0
    
    result = HealthResponse(
        status="healthy",
        database_chunks=total_chunks,
        embedding_model=os.getenv("EMBEDDING_MODEL", "all-MiniLM-L6-v2"),
        llm_provider=os.getenv("LLM_PROVIDER", "moonshot"),
    )
    
    # Cache for 30 seconds
    if cache_manager:
        cache_manager.set(cache_key, result.dict(), ttl=30)
    
    return result


@app.get("/api/autocomplete", tags=["Query"])
async def get_autocomplete(
    q: str,
    max_results: int = 10,
    location: Optional[str] = None,
    language: str = "en"
):
    """
    Get Google autocomplete suggestions
    
    Args:
        q: Partial search query
        max_results: Maximum number of suggestions (default: 10)
        location: Location for localized suggestions (e.g., "Kenya")
        language: Language code (e.g., "en", "sw")
    
    Returns:
        Autocomplete suggestions
    """
    if autocomplete_tool is None:
        raise HTTPException(status_code=503, detail="Autocomplete service not available")
    
    try:
        result = autocomplete_tool.execute(
            query=q,
            max_results=max_results,
            location=location,
            language=language
        )
        return result
    except Exception as e:
        logger.error(f"Error in autocomplete: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/news/health", tags=["news"])
async def news_crawler_health():
    """Health check for news crawler system"""
    try:
        from Module1_NiruSpider.niruspider.monitoring import CrawlerMonitor
        monitor = CrawlerMonitor()
        health = monitor.get_health_status()
        return health
    except Exception as e:
        logger.error(f"Error getting crawler health: {e}")
        return {
            "status": "error",
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@app.get("/api/v1/news/sources/status", tags=["news"])
async def news_sources_status(days: int = 7):
    """Get status of news sources"""
    try:
        from Module1_NiruSpider.niruspider.monitoring import CrawlerMonitor
        monitor = CrawlerMonitor()
        status = monitor.get_source_status(days=days)
        return status
    except Exception as e:
        logger.error(f"Error getting source status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/news/stats", tags=["news"])
async def news_crawler_stats():
    """Get crawler statistics"""
    try:
        from Module1_NiruSpider.niruspider.monitoring import CrawlerMonitor
        monitor = CrawlerMonitor()
        stats = monitor.get_crawler_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting crawler stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/stats", response_model=StatsResponse, tags=["General"])
async def get_stats():
    """Get database statistics - cached for 60 seconds"""
    try:
        if vector_store is None:
            raise HTTPException(status_code=503, detail="Service not initialized")
        
        # Try to get from cache
        cache_key = "cache:stats"
        if cache_manager:
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug("Cache hit for stats")
                return StatsResponse(**cached_result)
        
        # Run blocking operations in thread pool to avoid blocking event loop
        import asyncio
        loop = asyncio.get_event_loop()
        
        # Run vector_store.get_stats() in thread pool
        stats = await loop.run_in_executor(None, vector_store.get_stats)
        
        # Ensure stats is a dict and has expected keys
        if not isinstance(stats, dict):
            logger.warning(f"vector_store.get_stats() returned non-dict type: {type(stats)}, defaulting to empty stats")
            stats = {"sample_categories": {}, "total_chunks": 0}
        
        # Ensure stats has required keys with defaults
        if "sample_categories" not in stats:
            stats["sample_categories"] = {}
        if "total_chunks" not in stats:
            stats["total_chunks"] = 0
        
        # Get categories and sources - also run in thread pool
        try:
            from Module3_NiruDB.metadata_manager import MetadataManager
            
            def get_metadata():
                meta_manager = MetadataManager(vector_store)
                categories_list = meta_manager.get_categories()
                sources_list = meta_manager.get_sources()
                return categories_list, sources_list
            
            categories_list, sources_list = await loop.run_in_executor(None, get_metadata)
        except Exception as e:
            logger.error(f"Error getting metadata: {e}")
            categories_list = ["Unknown"]
            sources_list = ["Unknown"]
        
        # Convert to dict with counts - safely access sample_categories
        sample_categories = stats.get("sample_categories", {})
        categories_dict = {cat: sample_categories.get(cat, 0) for cat in categories_list}
        
        # Handle case where total_chunks might be "unknown" string
        total_chunks = stats["total_chunks"]
        if isinstance(total_chunks, str) and total_chunks == "unknown":
            total_chunks = 0
        elif not isinstance(total_chunks, int):
            total_chunks = 0
        
        result = StatsResponse(
            total_chunks=total_chunks,
            categories=categories_dict,
            sources=sources_list,
        )
        
        # Cache for 60 seconds
        if cache_manager:
            cache_manager.set(cache_key, result.dict(), ttl=60)
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error in get_stats: {e}")
        # Return default stats to prevent fetch failure
        return StatsResponse(
            total_chunks=0,
            categories={},
            sources=[],
        )


def save_query_to_chat(session_id: str, query: str, result: Dict, role: str = "user"):
    """Helper function to save query and response to chat database"""
    if chat_manager is None or not session_id:
        return
    
    try:
        # Validate session exists
        session = chat_manager.get_session(session_id)
        if not session:
            logger.warning(f"Session {session_id} not found, skipping message save")
            return
        
        # Save user message
        user_msg_id = chat_manager.add_message(
            session_id=session_id,
            content=query,
            role="user"
        )
        
        # Save assistant response
        assistant_msg_id = chat_manager.add_message(
            session_id=session_id,
            content=result.get("answer", ""),
            role="assistant",
            token_count=result.get("retrieved_chunks", 0),
            model_used=result.get("model_used", "unknown"),
            sources=result.get("sources", [])
        )
        
        # Generate session title if needed
        if not session.title:
            title = chat_manager.generate_session_title(session_id)
            chat_manager.update_session_title(session_id, title)
        
        logger.debug(f"Saved query to chat session {session_id}")
    except Exception as e:
        logger.warning(f"Failed to save query to chat: {e}")


@app.post("/query", response_model=QueryResponse, tags=["Query"])
async def query(request: QueryRequest):
    """
    Main query endpoint - Ask questions about Kenyan law, parliament, and news
    
    **Example queries:**
    - "What does the Kenyan Constitution say about freedom of speech?"
    - "What are the recent parliamentary debates on finance?"
    - "Latest news on AI policy in Kenya"
    
    **Vision RAG:** If session has uploaded images/PDFs, automatically uses Vision RAG for visual question answering.
    """
    if rag_pipeline is None:
        raise HTTPException(status_code=503, detail="Service not initialized")
    
    try:
        # Check if session has vision data and use Vision RAG if available
        use_vision_rag = False
        if request.session_id and vision_rag_service and vision_storage:
            session_images = vision_storage.get(request.session_id, [])
            if session_images:
                use_vision_rag = True
                logger.info(f"Using Vision RAG for session {request.session_id} with {len(session_images)} image(s)")
        
        if use_vision_rag:
            # Use Vision RAG
            result = vision_rag_service.query(
                question=request.query,
                session_images=session_images,
                top_k=min(request.top_k, 3),  # Limit to 3 images for Vision RAG
                temperature=request.temperature,
                max_tokens=request.max_tokens,
            )
            
            # Convert vision sources to Source format
            sources = []
            for src in result.get("sources", []):
                sources.append(Source(
                    title=src.get("filename", "Image"),
                    url="",  # No URL for uploaded images
                    source_name=src.get("source_file", "Uploaded Image"),
                    category="vision",
                    excerpt=f"Image similarity: {src.get('similarity', 0):.2f}",
                ))
        else:
            # Use regular RAG
            result = rag_pipeline.query(
                query=request.query,
                top_k=request.top_k,
                category=request.category,
                source=request.source,
                temperature=request.temperature,
                max_tokens=request.max_tokens,
                session_id=request.session_id
            )
            
            # Format sources
            sources = [Source(**src) for src in result["sources"]]
        
        # Save to chat if session_id provided
        if request.session_id:
            save_query_to_chat(request.session_id, request.query, result)
        
        return QueryResponse(
            answer=result["answer"],
            sources=sources if request.include_sources else [],
            query_time=result["query_time"],
            retrieved_chunks=result.get("retrieved_chunks", result.get("retrieved_images", 0)),
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
            session_id=request.session_id,
        )
        
        if not result.get("stream", False):
            # Fallback to regular response
            # Save to chat if session_id provided
            if request.session_id:
                save_query_to_chat(request.session_id, request.query, result)
            
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
            full_answer = ""
            try:
                answer_stream = result["answer_stream"]
                
                if rag_pipeline.llm_provider in ["openai", "moonshot"]:
                    # OpenAI-style streaming
                    async for chunk in answer_stream:
                        if chunk.choices and chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            full_answer += content
                            yield f"data: {content}\n\n"
                
                elif rag_pipeline.llm_provider == "anthropic":
                    # Anthropic streaming
                    async for chunk in answer_stream:
                        if chunk.type == "content_block_delta" and chunk.delta.text:
                            text = chunk.delta.text
                            full_answer += text
                            yield f"data: {text}\n\n"
                
                # Send sources at the end
                sources_data = {
                    "sources": [Source(**src).model_dump() for src in result["sources"]] if request.include_sources else [],
                    "query_time": result["query_time"],
                    "retrieved_chunks": result["retrieved_chunks"],
                    "model_used": result["model_used"],
                }
                yield f"data: [DONE]{json.dumps(sources_data)}\n\n"
                
                # Save to chat if session_id provided
                if request.session_id and full_answer:
                    result["answer"] = full_answer
                    save_query_to_chat(request.session_id, request.query, result)
                
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


# Global variables (initialized in lifespan)
cache_manager = None
vector_store = None
rag_pipeline = None
alignment_pipeline = None
sms_pipeline = None
sms_service = None
metadata_manager = None
chat_manager = None
crawler_manager = None
research_module = None
agentic_research_module = None
report_generator = None
vision_storage = {}  # In-memory vision storage: {session_id: [image_data, ...]}
vision_rag_service = None
config_manager = None
notification_service = None
hybrid_rag_pipeline = None
autocomplete_tool = None
database_storage = None

@app.post("/query/hybrid", response_model=QueryResponse, tags=["Hybrid RAG"])
async def query_hybrid(request: QueryRequest):
    """
    Hybrid RAG query with enhanced encoder and adaptive retrieval
    
    Uses hybrid convolutional-transformer encoder for improved embeddings
    and adaptive retrieval for context-aware document selection.
    """
    if hybrid_rag_pipeline is None:
        raise HTTPException(status_code=503, detail="Hybrid RAG pipeline not initialized")
    
    try:
        result = hybrid_rag_pipeline.query(
            query=request.query,
            top_k=request.top_k,
            category=request.category,
            source=request.source,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            use_hybrid=True,
            use_adaptive=True
        )
        
        # Save to chat if session_id provided
        if request.session_id:
            save_query_to_chat(request.session_id, request.query, result)
        
        sources = [Source(**src) for src in result["sources"]]
        return QueryResponse(
            answer=result["answer"],
            sources=sources if request.include_sources else [],
            query_time=result["query_time"],
            retrieved_chunks=result["retrieved_chunks"],
            model_used=result["model_used"]
        )
    except Exception as e:
        logger.error(f"Error processing hybrid query: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/diffusion/generate", tags=["Hybrid RAG"])
async def generate_synthetic_documents(
    query: Optional[str] = None,
    num_docs: int = 10,
    add_to_store: bool = True
):
    """
    Generate synthetic documents using diffusion models
    
    Args:
        query: Optional query context for generation
        num_docs: Number of documents to generate
        add_to_store: Whether to add generated documents to vector store
    """
    global hybrid_rag_pipeline
    
    if hybrid_rag_pipeline is None:
        raise HTTPException(status_code=503, detail="Hybrid RAG pipeline not initialized")
    
    try:
        generated_texts = hybrid_rag_pipeline.generate_synthetic_documents(
            query=query,
            num_docs=num_docs,
            add_to_store=add_to_store
        )
        
        return {
            "generated_documents": generated_texts,
            "count": len(generated_texts),
            "added_to_store": add_to_store
        }
    except Exception as e:
        logger.error(f"Error generating synthetic documents: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/retention/update", tags=["Hybrid RAG"])
async def trigger_retention_update():
    """
    Trigger retention update (continual learning)
    
    Updates model weights using generated data for dynamic retention.
    """
    global hybrid_rag_pipeline
    
    if hybrid_rag_pipeline is None:
        raise HTTPException(status_code=503, detail="Hybrid RAG pipeline not initialized")
    
    try:
        hybrid_rag_pipeline.trigger_retention_update()
        return {"status": "success", "message": "Retention update completed"}
    except Exception as e:
        logger.error(f"Error updating retention: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/stream/query", tags=["Hybrid RAG"])
async def stream_query(request: QueryRequest):
    """
    Real-time streaming query endpoint
    
    Processes queries in real-time with streaming response for both
    queries and generated data.
    """
    if hybrid_rag_pipeline is None:
        raise HTTPException(status_code=503, detail="Hybrid RAG pipeline not initialized")
    
    try:
        result = hybrid_rag_pipeline.query_stream(
            query=request.query,
            top_k=request.top_k,
            category=request.category,
            source=request.source,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            use_hybrid=True
        )
        
        if not result.get("stream", False):
            # Fallback to regular response
            # Save to chat if session_id provided
            if request.session_id:
                save_query_to_chat(request.session_id, request.query, result)
            
            sources = [Source(**src) for src in result["sources"]]
            return QueryResponse(
                answer=result.get("answer", ""),
                sources=sources if request.include_sources else [],
                query_time=result["query_time"],
                retrieved_chunks=result["retrieved_chunks"],
                model_used=result["model_used"]
            )
        
        # Return streaming response
        from fastapi.responses import StreamingResponse
        
        async def generate():
            full_answer = ""
            try:
                answer_stream = result["answer_stream"]
                
                # Get LLM provider from hybrid pipeline's base RAG
                llm_provider = hybrid_rag_pipeline.base_rag.llm_provider
                
                # Convert synchronous stream to async iterator
                import asyncio
                
                if llm_provider in ["openai", "moonshot"]:
                    # Iterate synchronously but yield asynchronously
                    for chunk in answer_stream:
                        if chunk.choices and chunk.choices[0].delta.content:
                            content = chunk.choices[0].delta.content
                            full_answer += content
                            yield f"data: {content}\n\n"
                            # Yield control to event loop periodically
                            await asyncio.sleep(0)
                
                elif llm_provider == "anthropic":
                    # Iterate synchronously but yield asynchronously
                    for chunk in answer_stream:
                        if chunk.type == "content_block_delta" and chunk.delta.text:
                            text = chunk.delta.text
                            full_answer += text
                            yield f"data: {text}\n\n"
                            # Yield control to event loop periodically
                            await asyncio.sleep(0)
                
                # Send sources at the end
                sources_data = {
                    "sources": [Source(**src).model_dump() for src in result["sources"]] if request.include_sources else [],
                    "query_time": result["query_time"],
                    "retrieved_chunks": result["retrieved_chunks"],
                    "model_used": result["model_used"],
                    "hybrid_used": result.get("hybrid_used", False)
                }
                yield f"data: [DONE]{json.dumps(sources_data)}\n\n"
                
                # Save to chat if session_id provided
                if request.session_id and full_answer:
                    result["answer"] = full_answer
                    save_query_to_chat(request.session_id, request.query, result)
                
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


@app.get("/hybrid/stats", tags=["Hybrid RAG"])
async def get_hybrid_stats():
    """Get statistics for hybrid RAG pipeline"""
    global hybrid_rag_pipeline
    
    if hybrid_rag_pipeline is None:
        raise HTTPException(status_code=503, detail="Hybrid RAG pipeline not initialized")
    
    try:
        stats = hybrid_rag_pipeline.get_stats()
        return stats
    except Exception as e:
        logger.error(f"Error getting hybrid stats: {e}")
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


# Chat API Endpoints - Helper Functions
def get_current_user_id(request: Request) -> Optional[str]:
    """Get current user ID from auth context if available"""
    try:
        auth_context = getattr(request.state, "auth_context", None)
        if auth_context and auth_context.user_id:
            return auth_context.user_id
    except Exception:
        pass
    return None

def verify_session_ownership(session_id: str, user_id: Optional[str], chat_manager: ChatDatabaseManager) -> bool:
    """Verify that a session belongs to the specified user"""
    if not user_id:
        # If no user_id provided, allow access (for backward compatibility when auth is disabled)
        return True
    
    session = chat_manager.get_session_with_user(session_id)
    if not session:
        return False
    
    # Session must belong to the user
    return session.user_id == user_id


# Chat API Endpoints
@app.post("/chat/sessions", response_model=ChatSessionResponse, tags=["Chat"])
async def create_chat_session(session: ChatSessionCreate, request: Request):
    """Create a new chat session"""
    if chat_manager is None:
        raise HTTPException(status_code=503, detail="Chat service not initialized")
    
    try:
        # Get user_id from auth context if available, otherwise use provided user_id
        user_id = get_current_user_id(request) or session.user_id
        
        session_id = chat_manager.create_session(session.title, user_id)
        session_data = chat_manager.get_session(session_id)
        return session_data
    except Exception as e:
        logger.error(f"Error creating chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chat/sessions", response_model=List[ChatSessionResponse], tags=["Chat"])
async def list_chat_sessions(request: Request, limit: int = 50):
    """List chat sessions for the current user"""
    if chat_manager is None:
        raise HTTPException(status_code=503, detail="Chat service not initialized")
    
    try:
        # Get user_id from auth context - only show sessions for authenticated user
        user_id = get_current_user_id(request)
        
        return chat_manager.list_sessions(user_id, limit)
    except Exception as e:
        logger.error(f"Error listing chat sessions: {e}")
        # Return empty list instead of crashing
        return []


@app.get("/chat/sessions/{session_id}", response_model=ChatSessionResponse, tags=["Chat"])
async def get_chat_session(session_id: str, request: Request):
    """Get a specific chat session"""
    if chat_manager is None:
        raise HTTPException(status_code=503, detail="Chat service not initialized")
    
    try:
        # Verify session ownership
        user_id = get_current_user_id(request)
        if not verify_session_ownership(session_id, user_id, chat_manager):
            raise HTTPException(status_code=403, detail="Access denied: You don't have permission to access this session")
        
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
async def delete_chat_session(session_id: str, request: Request):
    """Delete a chat session"""
    if chat_manager is None:
        raise HTTPException(status_code=503, detail="Chat service not initialized")
    
    try:
        # Verify session ownership
        user_id = get_current_user_id(request)
        if not verify_session_ownership(session_id, user_id, chat_manager):
            raise HTTPException(status_code=403, detail="Access denied: You don't have permission to delete this session")
        
        chat_manager.delete_session(session_id)
        return {"message": "Session deleted successfully"}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting chat session: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/sessions/{session_id}/messages", response_model=ChatMessageResponse, tags=["Chat"])
async def add_chat_message(session_id: str, message: ChatMessageCreate, request: Request):
    """Add a message to a chat session"""
    if chat_manager is None:
        raise HTTPException(status_code=503, detail="Chat service not initialized")
    
    try:
        # Verify session ownership
        user_id = get_current_user_id(request)
        if not verify_session_ownership(session_id, user_id, chat_manager):
            raise HTTPException(status_code=403, detail="Access denied: You don't have permission to access this session")
        
        # If this is the first user message and session has no title, generate one
        session = chat_manager.get_session(session_id)
        if not session:
            raise HTTPException(status_code=404, detail="Session not found")
        
        if message.role == "user":
            # Check if streaming is requested
            stream = message.stream
            
            # Check if session has vision data and use Vision RAG if available
            use_vision_rag = False
            session_images = []
            if vision_rag_service and vision_storage:
                session_images = vision_storage.get(session_id, [])
                if session_images:
                    use_vision_rag = True
                    logger.info(f"Using Vision RAG for chat session {session_id} with {len(session_images)} image(s)")
            
            # Check if we need RAG pipeline (only if not using Vision RAG)
            if not use_vision_rag and rag_pipeline is None:
                raise HTTPException(status_code=503, detail="RAG service not initialized")
            
            if stream:
                # Use streaming RAG
                if use_vision_rag:
                    # Use Vision RAG with streaming
                    result = vision_rag_service.query(
                        question=message.content,
                        session_images=session_images,
                        top_k=3,
                        temperature=0.7,
                        max_tokens=1000,
                        stream=True,  # Enable streaming
                    )
                    # Convert vision sources to standard format
                    vision_sources = []
                    for src in result.get("sources", []):
                        vision_sources.append({
                            "title": src.get("filename", "Image"),
                            "url": "",
                            "source_name": src.get("source_file", "Uploaded Image"),
                            "category": "vision",
                            "excerpt": f"Image similarity: {src.get('similarity', 0):.2f}",
                        })
                    result["sources"] = vision_sources
                    result["retrieved_chunks"] = result.get("retrieved_images", 0)
                else:
                    result = rag_pipeline.query_stream(
                        query=message.content,
                        top_k=3,  # Reduced for faster chat responses
                        max_tokens=1000,  # Shorter responses for chat
                        max_context_length=2000,  # Smaller context for chat
                        temperature=0.7,
                        session_id=session_id,
                    )
                
                # Process attachments if provided
                attachments_data = None
                if message.attachment_ids:
                    # Retrieve attachment metadata from messages
                    session_messages = chat_manager.get_messages(session_id)
                    attachments_data = []
                    for msg in session_messages:
                        if msg.attachments:
                            for att in msg.attachments:
                                if att.get("id") in message.attachment_ids:
                                    attachments_data.append(att)
                
                # Add user message with attachments
                user_msg_id = chat_manager.add_message(
                    session_id=session_id,
                    content=message.content,
                    role="user",
                    attachments=attachments_data
                )
                
                # Return streaming response
                from fastapi.responses import StreamingResponse
                import json
                
                async def generate_stream():
                    full_answer = ""
                    try:
                        # First send sources
                        sources_data = {
                            "type": "sources",
                            "sources": result["sources"],
                            "retrieved_chunks": result["retrieved_chunks"],
                            "model_used": result["model_used"]
                        }
                        yield f"data: {json.dumps(sources_data)}\n\n"
                        
                        # Then stream the answer
                        
                        # Check if we have streaming response or fallback to regular answer
                        if "answer_stream" in result and result["answer_stream"] is not None:
                            # Handle streaming response
                            if hasattr(result["answer_stream"], '__iter__') and not isinstance(result["answer_stream"], str):
                                # Check if it's a generator/iterator (Gemini streaming or other)
                                try:
                                    # Try Gemini streaming format first (yields text chunks directly)
                                    for chunk in result["answer_stream"]:
                                        if isinstance(chunk, str):
                                            # Gemini streaming format - direct text chunks
                                            content = chunk
                                            full_answer += content
                                            chunk_data = {
                                                "type": "content",
                                                "content": content
                                            }
                                            yield f"data: {json.dumps(chunk_data)}\n\n"
                                        elif hasattr(chunk, 'choices') and chunk.choices:
                                            # OpenAI/Moonshot format
                                            delta = chunk.choices[0].delta
                                            if hasattr(delta, 'content') and delta.content:
                                                content = delta.content
                                                full_answer += content
                                                chunk_data = {
                                                    "type": "content",
                                                    "content": content
                                                }
                                                yield f"data: {json.dumps(chunk_data)}\n\n"
                                        elif hasattr(chunk, 'delta') and hasattr(chunk.delta, 'text'):
                                            # Anthropic format
                                            content = chunk.delta.text
                                            full_answer += content
                                            chunk_data = {
                                                "type": "content",
                                                "content": content
                                            }
                                            yield f"data: {json.dumps(chunk_data)}\n\n"
                                        elif hasattr(chunk, 'text'):
                                            # Gemini chunk format
                                            content = chunk.text
                                            if content:
                                                full_answer += content
                                                chunk_data = {
                                                    "type": "content",
                                                    "content": content
                                                }
                                                yield f"data: {json.dumps(chunk_data)}\n\n"
                                except Exception as stream_error:
                                    logger.error(f"Error in streaming loop: {stream_error}")
                                    # Fallback to sending as single chunk
                                    content = str(result.get("answer", "Error in streaming response"))
                                    full_answer = content
                                    chunk_data = {
                                        "type": "content",
                                        "content": content
                                    }
                                    yield f"data: {json.dumps(chunk_data)}\n\n"
                            else:
                                # Fallback for non-streaming providers - send as single chunk
                                content = str(result["answer_stream"])
                                full_answer = content
                                chunk_data = {
                                    "type": "content",
                                    "content": content
                                }
                                yield f"data: {json.dumps(chunk_data)}\n\n"
                        elif "answer" in result:
                            # Fallback to regular answer when no streaming available
                            content = str(result["answer"])
                            full_answer = content
                            chunk_data = {
                                "type": "content",
                                "content": content
                            }
                            yield f"data: {json.dumps(chunk_data)}\n\n"
                        else:
                            # No answer available
                            error_content = "I apologize, but I was unable to generate a response. Please try again."
                            full_answer = error_content
                            chunk_data = {
                                "type": "content",
                                "content": error_content
                            }
                            yield f"data: {json.dumps(chunk_data)}\n\n"
                        
                        # Send completion
                        completion_data = {
                            "type": "done",
                            "full_answer": full_answer
                        }
                        yield f"data: {json.dumps(completion_data)}\n\n"
                        
                    except Exception as e:
                        logger.error(f"Error in streaming: {e}")
                        error_data = {
                            "type": "error",
                            "error": str(e)
                        }
                        yield f"data: {json.dumps(error_data)}\n\n"
                    finally:
                        # Always save assistant message, even if streaming failed
                        try:
                            if full_answer.strip():  # Only save if we have content
                                assistant_msg_id = chat_manager.add_message(
                                    session_id=session_id,
                                    content=full_answer,
                                    role="assistant",
                                    token_count=result.get("retrieved_chunks", 0),
                                    model_used=result.get("model_used", "unknown"),
                                    sources=result.get("sources", [])
                                )
                                logger.info(f"Saved assistant message {assistant_msg_id} to session {session_id}")
                                
                                # Generate session title if needed
                                if not session.title:
                                    title = chat_manager.generate_session_title(session_id)
                                    chat_manager.update_session_title(session_id, title)
                        except Exception as save_error:
                            logger.error(f"Failed to save assistant message: {save_error}")
                
                return StreamingResponse(
                    generate_stream(),
                    media_type="text/event-stream",
                    headers={
                        "Cache-Control": "no-cache",
                        "Connection": "keep-alive",
                    }
                )
            else:
                # Regular non-streaming response
                if use_vision_rag:
                    # Use Vision RAG
                    result = vision_rag_service.query(
                        question=message.content,
                        session_images=session_images,
                        top_k=3,
                        temperature=0.7,
                        max_tokens=1000,
                    )
                    # Convert vision sources to standard format
                    vision_sources = []
                    for src in result.get("sources", []):
                        vision_sources.append({
                            "title": src.get("filename", "Image"),
                            "url": "",
                            "source_name": src.get("source_file", "Uploaded Image"),
                            "category": "vision",
                            "excerpt": f"Image similarity: {src.get('similarity', 0):.2f}",
                        })
                    result["sources"] = vision_sources
                    result["retrieved_chunks"] = result.get("retrieved_images", 0)
                else:
                    result = rag_pipeline.query(
                        query=message.content,
                        top_k=3,  # Reduced for faster chat responses
                        max_tokens=1000,  # Shorter responses for chat
                        max_context_length=2000,  # Smaller context for chat
                        temperature=0.7,
                        session_id=session_id  # Include session for document context
                    )
                
                # Process attachments if provided
                attachments_data = None
                if message.attachment_ids:
                    # Retrieve attachment metadata from messages
                    session_messages = chat_manager.get_messages(session_id)
                    attachments_data = []
                    for msg in session_messages:
                        if msg.attachments:
                            for att in msg.attachments:
                                if att.get("id") in message.attachment_ids:
                                    attachments_data.append(att)
                
                # Add user message with attachments
                user_msg_id = chat_manager.add_message(
                    session_id=session_id,
                    content=message.content,
                    role="user",
                    attachments=attachments_data
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
            # Process attachments if provided
            attachments_data = None
            if message.attachment_ids:
                # Retrieve attachment metadata from messages
                session_messages = chat_manager.get_messages(session_id)
                attachments_data = []
                for msg in session_messages:
                    if msg.attachments:
                        for att in msg.attachments:
                            if att.get("id") in message.attachment_ids:
                                attachments_data.append(att)
            
            # Add assistant message directly
            msg_id = chat_manager.add_message(
                session_id=session_id,
                content=message.content,
                role=message.role,
                attachments=attachments_data
            )
            messages = chat_manager.get_messages(session_id, limit=1)
            return messages[-1] if messages else None
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error adding chat message: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chat/sessions/{session_id}/messages", response_model=List[ChatMessageResponse], tags=["Chat"])
async def get_chat_messages(session_id: str, request: Request, limit: int = 100):
    """Get messages for a chat session"""
    if chat_manager is None:
        raise HTTPException(status_code=503, detail="Chat service not initialized")
    
    try:
        # Verify session ownership
        user_id = get_current_user_id(request)
        if not verify_session_ownership(session_id, user_id, chat_manager):
            raise HTTPException(status_code=403, detail="Access denied: You don't have permission to access this session")
        
        return chat_manager.get_messages(session_id, limit)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting chat messages: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/sessions/{session_id}/attachments", tags=["Chat"])
async def upload_chat_attachment(
    request: Request,
    session_id: str,
    file: UploadFile = File(...)
):
    """Upload a document attachment for a chat session"""
    if chat_manager is None or vector_store is None:
        raise HTTPException(status_code=503, detail="Services not initialized")
    
    # Verify session ownership
    user_id = get_current_user_id(request) if request else None
    if not verify_session_ownership(session_id, user_id, chat_manager):
        raise HTTPException(status_code=403, detail="Access denied: You don't have permission to access this session")
    
    # Validate session exists
    session = chat_manager.get_session(session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
    
    # Validate file size (10MB limit)
    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB
    file_content = await file.read()
    if len(file_content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail="File size exceeds 10MB limit")
    
    # Validate file type
    allowed_extensions = [".pdf", ".png", ".jpg", ".jpeg", ".txt", ".md"]
    file_ext = Path(file.filename).suffix.lower()
    if file_ext not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=f"File type not supported. Allowed: {', '.join(allowed_extensions)}"
        )
    
    try:
        # Initialize document processor
        from Module4_NiruAPI.services.document_processor import DocumentProcessor
        processor = DocumentProcessor()
        
        # Process file
        result = processor.process_file(
            file_content=file_content,
            filename=file.filename,
            session_id=session_id
        )
        
        # Store chunks in vector store with session-specific collection (only if chunks exist)
        if result["chunks"]:
            collection_name = f"chat_session_{session_id}"
            processor.store_chunks_in_vector_store(
                chunks=result["chunks"],
                vector_store=vector_store,
                collection_name=collection_name
            )
        else:
            logger.info(f"No text chunks to store for {file.filename} (Vision RAG only)")
        
        # Store vision data if available
        vision_data = result.get("vision_data")
        if vision_data and vision_data.get("images"):
            # Initialize session storage if needed
            if session_id not in vision_storage:
                vision_storage[session_id] = []
            
            # Add vision images to session storage
            vision_storage[session_id].extend(vision_data["images"])
            logger.info(f"Stored {len(vision_data['images'])} vision item(s) for session {session_id}")
        
        logger.info(f"Processed attachment {result['attachment']['id']} for session {session_id}")
        
        return {
            "attachment": result["attachment"],
            "message": "File processed and stored successfully",
            "vision_processed": vision_data is not None and vision_data.get("count", 0) > 0,
        }
        
    except Exception as e:
        logger.error(f"Error processing attachment: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to process file: {str(e)}")


@app.get("/chat/sessions/{session_id}/attachments/{attachment_id}", tags=["Chat"])
async def get_chat_attachment(session_id: str, attachment_id: str, request: Request):
    """Get attachment metadata"""
    if chat_manager is None:
        raise HTTPException(status_code=503, detail="Chat service not initialized")
    
    try:
        # Verify session ownership
        user_id = get_current_user_id(request)
        if not verify_session_ownership(session_id, user_id, chat_manager):
            raise HTTPException(status_code=403, detail="Access denied: You don't have permission to access this session")
        
        # Get messages for session
        messages = chat_manager.get_messages(session_id)
        
        # Find attachment in messages
        for message in messages:
            if message.attachments:
                for attachment in message.attachments:
                    if attachment.get("id") == attachment_id:
                        return attachment
        
        raise HTTPException(status_code=404, detail="Attachment not found")
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error getting attachment: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/chat/sessions/{session_id}/vision-content", tags=["Chat"])
async def get_vision_content(session_id: str, request: Request):
    """Get vision content (images/PDF pages) for a session"""
    if vision_storage is None:
        raise HTTPException(status_code=503, detail="Vision storage not initialized")
    
    try:
        # Verify session ownership
        user_id = get_current_user_id(request)
        if chat_manager and not verify_session_ownership(session_id, user_id, chat_manager):
            raise HTTPException(status_code=403, detail="Access denied: You don't have permission to access this session")
        
        session_images = vision_storage.get(session_id, [])
        
        # Return metadata only (not full embeddings)
        content_list = []
        for img_data in session_images:
            content_list.append({
                "id": img_data.get("id"),
                "filename": img_data.get("metadata", {}).get("filename", ""),
                "file_path": img_data.get("file_path", ""),
                "type": img_data.get("metadata", {}).get("type", ""),
                "page_number": img_data.get("metadata", {}).get("page_number"),
                "source_file": img_data.get("metadata", {}).get("source_file", ""),
            })
        
        return {
            "session_id": session_id,
            "count": len(content_list),
            "content": content_list,
        }
        
    except Exception as e:
        logger.error(f"Error getting vision content: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/chat/feedback", response_model=FeedbackResponse, tags=["Chat"])
async def add_feedback(feedback: FeedbackCreate, request: Request):
    """Add feedback for a chat message"""
    if chat_manager is None:
        raise HTTPException(status_code=503, detail="Chat service not initialized")
    
    try:
        # Verify that the message belongs to a session owned by the user
        user_id = get_current_user_id(request)
        if user_id:
            # Get the message to find its session
            messages = chat_manager.get_messages_by_message_id(feedback.message_id)
            if not messages:
                raise HTTPException(status_code=404, detail="Message not found")
            
            message = messages[0]
            # Verify session ownership
            if not verify_session_ownership(message.session_id, user_id, chat_manager):
                raise HTTPException(status_code=403, detail="Access denied: You don't have permission to provide feedback for this message")
        
        # Validate message exists (add_feedback will also check, but we can provide better error here)
        feedback_id = chat_manager.add_feedback(
            message_id=feedback.message_id,
            feedback_type=feedback.feedback_type,
            comment=feedback.comment,
            user_id=user_id
        )
        
        # Return feedback response
        return FeedbackResponse(
            id=feedback_id,
            message_id=feedback.message_id,
            feedback_type=feedback.feedback_type,
            comment=feedback.comment,
            created_at=datetime.utcnow()
        )
    except ValueError as e:
        # Message not found
        logger.warning(f"Feedback rejected: {e}")
        raise HTTPException(status_code=404, detail=str(e))
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
async def share_chat_session(session_id: str, request: Request, share_type: str = "link"):
    """Generate a shareable link for a chat session"""
    if chat_manager is None:
        raise HTTPException(status_code=503, detail="Chat service not initialized")
    
    try:
        # Verify session ownership
        user_id = get_current_user_id(request)
        if not verify_session_ownership(session_id, user_id, chat_manager):
            raise HTTPException(status_code=403, detail="Access denied: You don't have permission to share this session")
        
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
# Note: Admin endpoints are protected by require_admin dependency when ENABLE_AUTH=true

def get_admin_dependency():
    """Get admin dependency - conditional based on ENABLE_AUTH"""
    if os.getenv("ENABLE_AUTH", "false").lower() == "true":
        from Module8_NiruAuth.dependencies import require_admin
        from Module8_NiruAuth.models.auth_models import User
        # Return the actual require_admin dependency
        return require_admin
    else:
        # Return a no-op dependency when auth is disabled
        def no_auth_required(request: Request):
            return None
        return no_auth_required

# Create the dependency instance
_admin_dependency = get_admin_dependency()

@app.get("/admin/crawlers", tags=["Admin"])
async def get_crawler_status(
    request: Request,
    admin = Depends(_admin_dependency)
):
    """Get status of all crawlers (admin only) - cached for 5 seconds"""
    if crawler_manager is None:
        raise HTTPException(status_code=503, detail="Crawler manager not initialized")
    
    # Try to get from cache
    cache_key = "cache:admin:crawlers"
    if cache_manager:
        cached_result = cache_manager.get(cache_key)
        if cached_result is not None:
            logger.debug("Cache hit for crawler status")
            return cached_result
    
    try:
        crawlers = crawler_manager.get_crawler_status()
        result = {"crawlers": crawlers}
        
        # Cache for 5 seconds (crawler status changes frequently)
        if cache_manager:
            cache_manager.set(cache_key, result, ttl=5)
        
        return result
    except Exception as e:
        logger.error(f"Error getting crawler status: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/crawlers/{crawler_name}/start", tags=["Admin"])
async def start_crawler(
    crawler_name: str,
    request: Request,
    admin = Depends(_admin_dependency)
):
    """Start a specific crawler"""
    if crawler_manager is None:
        raise HTTPException(status_code=503, detail="Crawler manager not initialized")
    
    try:
        result = crawler_manager.start_crawler(crawler_name)
        
        # Invalidate cache when crawler starts
        if cache_manager:
            cache_manager.invalidate_crawler_cache()
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error starting crawler {crawler_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/admin/crawlers/{crawler_name}/stop", tags=["Admin"])
async def stop_crawler(
    crawler_name: str,
    request: Request,
    admin = Depends(_admin_dependency)
):
    """Stop a specific crawler"""
    if crawler_manager is None:
        raise HTTPException(status_code=503, detail="Crawler manager not initialized")
    
    try:
        result = crawler_manager.stop_crawler(crawler_name)
        
        # Invalidate cache when crawler stops
        if cache_manager:
            cache_manager.invalidate_crawler_cache()
        
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error stopping crawler {crawler_name}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/documents", tags=["Admin"])
async def search_documents(
    request: Request,
    query: str = "",
    category: Optional[str] = None,
    source: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    admin = Depends(_admin_dependency)
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
async def get_document(
    doc_id: str,
    request: Request,
    admin = Depends(_admin_dependency)
):
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
async def execute_command(
    command: str,
    request: Request,
    cwd: Optional[str] = None,
    admin = Depends(_admin_dependency)
):
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


@app.get("/admin/config", tags=["Admin"])
async def get_config_list(
    request: Request,
    admin = Depends(_admin_dependency)
):
    """Get list of all configuration keys - cached for 300 seconds"""
    if config_manager is None:
        return {
            "error": "Config manager not initialized",
            "message": "PostgreSQL database connection required for configuration management",
            "status": "unavailable"
        }
    
    # Try to get from cache
    cache_key = "cache:admin:config"
    if cache_manager:
        cached_result = cache_manager.get(cache_key)
        if cached_result is not None:
            logger.debug("Cache hit for config list")
            return cached_result
    
    try:
        result = config_manager.list_configs()
        
        # Cache for 5 minutes (configs don't change often)
        if cache_manager:
            cache_manager.set(cache_key, result, ttl=300)
        
        return result
    except Exception as e:
        logger.error(f"Error getting config list: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ConfigSetRequest(BaseModel):
    key: str
    value: str
    description: Optional[str] = ""


@app.post("/admin/config", tags=["Admin"])
async def set_config(
    config: ConfigSetRequest,
    request: Request,
    admin = Depends(_admin_dependency)
):
    """Set a configuration value"""
    if config_manager is None:
        raise HTTPException(
            status_code=503,
            detail="Config manager not initialized - PostgreSQL database connection required",
        )

    try:
        config_manager.set_config(config.key, config.value, config.description or "")
        
        # Invalidate config cache
        if cache_manager:
            cache_manager.delete("cache:admin:config")
        
        return {"message": f"Config {config.key} set successfully"}
    except Exception as e:
        logger.error(f"Error setting config {config.key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.put("/admin/config/{key}", tags=["Admin"])
async def update_config_entry(
    key: str,
    request: FastAPIRequest,
    admin = Depends(_admin_dependency)
):
    """Update a configuration value"""
    if config_manager is None:
        raise HTTPException(
            status_code=503,
            detail="Config manager not initialized - PostgreSQL database connection required",
        )

    try:
        body = await request.json()
        value = body.get("value", "")
        description = body.get("description", "")
        config_manager.set_config(key, value, description)
        
        # Invalidate config cache
        if cache_manager:
            cache_manager.delete("cache:admin:config")
        
        return {"message": f"Config {key} updated successfully"}
    except Exception as e:
        logger.error(f"Error updating config {key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.delete("/admin/config/{key}", tags=["Admin"])
async def delete_config_entry(
    key: str,
    request: Request,
    admin = Depends(_admin_dependency)
):
    """Delete a configuration value"""
    if config_manager is None:
        raise HTTPException(
            status_code=503,
            detail="Config manager not initialized - PostgreSQL database connection required",
        )

    try:
        config_manager.delete_config(key)
        
        # Invalidate config cache
        if cache_manager:
            cache_manager.delete("cache:admin:config")
        
        return {"message": f"Config {key} deleted successfully"}
    except Exception as e:
        logger.error(f"Error deleting config {key}: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/databases", tags=["Admin"])
async def get_database_stats(
    request: Request,
    admin = Depends(_admin_dependency)
):
    """Get statistics for all vector database backends - cached for 60 seconds"""
    if vector_store is None:
        raise HTTPException(status_code=503, detail="Vector store not initialized")
    
    # Try to get from cache
    cache_key = "cache:admin:databases"
    if cache_manager:
        cached_result = cache_manager.get(cache_key)
        if cached_result is not None:
            logger.debug("Cache hit for database stats")
            return cached_result
    
    try:
        # Run blocking operations in thread pool to avoid blocking event loop
        import asyncio
        loop = asyncio.get_event_loop()
        
        # Run vector_store.get_stats() in thread pool
        stats = await loop.run_in_executor(None, vector_store.get_stats)
        
        # Format the response with detailed backend information
        databases = []
        used_names = set()  # Track used names to avoid duplicates
        
        # Primary backend
        primary_name = stats.get("backend", "unknown")
        if primary_name not in used_names:
            primary_db = {
                "name": primary_name,
                "type": "primary",
                "status": "active" if stats.get("total_chunks", 0) > 0 else "inactive",
                "total_chunks": stats.get("total_chunks", 0),
                "categories": stats.get("sample_categories", {}),
                "persist_directory": stats.get("persist_directory", ""),
                "elasticsearch_docs": stats.get("elasticsearch_docs", 0),
                "elasticsearch_enabled": stats.get("elasticsearch_enabled", False)
            }
            databases.append(primary_db)
            used_names.add(primary_name)
        
        # Cloud backends
        cloud_backends = stats.get("cloud_backends", [])
        for backend_name in cloud_backends:
            if backend_name not in used_names:
                # Get individual stats for each cloud backend - also run in thread pool
                backend_stats = await loop.run_in_executor(None, get_individual_backend_stats, backend_name)
                db_info = {
                    "name": backend_name,
                    "type": "cloud",
                    "status": "active",  # Assume active if configured
                    "total_chunks": backend_stats.get("total_chunks", 0),
                    "categories": backend_stats.get("categories", {}),
                    "persist_directory": "",
                    "elasticsearch_docs": 0,
                    "elasticsearch_enabled": False
                }
                databases.append(db_info)
                used_names.add(backend_name)
        
        result = {
            "databases": databases,
            "total_databases": len(databases),
            "active_databases": len([db for db in databases if db["status"] == "active"])
        }
        
        # Cache for 60 seconds
        if cache_manager:
            cache_manager.set(cache_key, result, ttl=60)
        
        return result
        
    except Exception as e:
        logger.error(f"Error getting database stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


def get_individual_backend_stats(backend_name: str) -> Dict:
    """Get statistics for an individual backend"""
    try:
        if backend_name == "upstash" and hasattr(vector_store, 'backends') and "upstash" in vector_store.backends:
            # Upstash doesn't provide count API, return basic info
            return {"total_chunks": 0, "categories": {}}
        elif backend_name == "qdrant" and hasattr(vector_store, 'backends') and "qdrant" in vector_store.backends:
            # Try to get QDrant collection count
            try:
                count_result = vector_store.backends["qdrant"].count(vector_store.collection_name)
                return {"total_chunks": count_result.count, "categories": {}}
            except:
                return {"total_chunks": 0, "categories": {}}
        else:
            return {"total_chunks": 0, "categories": {}}
    except Exception as e:
        logger.error(f"Error getting stats for {backend_name}: {e}")
        return {"total_chunks": 0, "categories": {}}


@app.get("/admin/database-storage", tags=["Admin"])
async def get_database_storage_stats(
    request: Request,
    admin = Depends(_admin_dependency)
):
    """Get database storage statistics - cached for 60 seconds"""
    try:
        if database_storage is None:
            raise HTTPException(status_code=503, detail="Database storage not initialized")
        
        # Try to get from cache
        cache_key = "cache:admin:database-storage"
        if cache_manager:
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug("Cache hit for database storage stats")
                return cached_result
        
        # Run blocking operation in thread pool to avoid blocking event loop
        import asyncio
        loop = asyncio.get_event_loop()
        stats = await loop.run_in_executor(None, database_storage.get_stats)
        
        # Cache for 60 seconds
        if cache_manager:
            cache_manager.set(cache_key, stats, ttl=60)
        
        return stats
    except Exception as e:
        logger.error(f"Error getting database storage stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/admin/system-info", tags=["Admin"])
async def get_system_info(
    request: Request,
    admin = Depends(_admin_dependency)
):
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
    if sms_service is None:
        raise HTTPException(
            status_code=503, 
            detail="SMS service not initialized. Please restart the FastAPI server."
        )
    
    if not sms_service.available:
        # Provide more detailed error message
        error_detail = "SMS service not available"
        if hasattr(sms_service, 'test_mode') and sms_service.test_mode:
            error_detail += " (test mode is enabled - SMS will be simulated)"
        elif hasattr(sms_service, 'use_direct_api') and sms_service.use_direct_api:
            error_detail += " (using direct API fallback)"
        else:
            error_detail += ". Check AT_USERNAME and AT_API_KEY environment variables."
        
        raise HTTPException(status_code=503, detail=error_detail)
    
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
            error_msg = result.get("error", "Unknown error")
            logger.error(f"Failed to send SMS: {error_msg}")
            # Check if it's an SSL/network error
            if "SSL" in str(error_msg) or "Connection" in str(error_msg):
                raise HTTPException(
                    status_code=503,
                    detail=f"Network error connecting to SMS service: {error_msg}. This may be due to proxy/firewall settings."
                )
            raise HTTPException(status_code=500, detail=f"Failed to send SMS: {error_msg}")
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error sending manual SMS: {e}")
        error_str = str(e)
        if "SSL" in error_str or "Connection" in error_str:
            raise HTTPException(
                status_code=503,
                detail=f"Network error: {error_str}. Check proxy/firewall settings."
            )
        raise HTTPException(status_code=500, detail=f"Internal error: {error_str}")


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
    context: Optional[str] = Form(None),
    session_id: Optional[str] = Form(None)
):
    """
    Analyze a legal query about Kenya's laws using Gemini AI

    This endpoint performs deep analysis of legal questions, providing information
    about applicable laws, legal procedures, and practical guidance.

    **Parameters:**
    - query: The legal question or query to analyze
    - context: Optional additional context about the query (JSON string)
    - session_id: Optional chat session ID to save messages

    **Returns:**
    - Comprehensive legal analysis covering applicable laws, legal reasoning, and practical guidance
    """
    # Use agentic module if available, otherwise fall back to legacy
    module = agentic_research_module if 'agentic_research_module' in globals() and agentic_research_module else research_module
    
    if module is None:
        raise HTTPException(status_code=503, detail="Research module not available. Ensure API keys are configured.")

    try:
        # Parse context if provided
        context_data = None
        if context:
            try:
                context_data = json.loads(context)
            except json.JSONDecodeError:
                context_data = {"additional_info": context}

        # Use async method for agentic module
        if hasattr(module, 'analyze_legal_query') and asyncio.iscoroutinefunction(module.analyze_legal_query):
            result = await module.analyze_legal_query(query, context_data)
        else:
            result = module.analyze_legal_query(query, context_data)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        # Save to chat if session_id provided
        if session_id:
            # Format result for chat saving
            chat_result = {
                "answer": result.get("analysis", result.get("summary", str(result))),
                "sources": result.get("sources", []),
                "retrieved_chunks": result.get("chunks_used", 0),
                "model_used": result.get("model_used", "gemini")
            }
            save_query_to_chat(session_id, query, chat_result)

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
    # Use agentic module if available
    module = agentic_research_module if 'agentic_research_module' in globals() and agentic_research_module else research_module
    
    if module is None:
        raise HTTPException(status_code=503, detail="Research module not available. Ensure API keys are configured.")

    try:
        # Parse the analysis results
        analysis_data = json.loads(analysis_results)

        result = module.generate_legal_report(analysis_data, report_focus)

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
    research_questions: str = Form(...),
    session_id: Optional[str] = Form(None)
):
    """
    Conduct legal research on specific topics related to Kenya's laws

    **Parameters:**
    - legal_topics: JSON string array of legal topics to research
    - research_questions: JSON string array of specific research questions
    - session_id: Optional chat session ID to save messages

    **Returns:**
    - Legal research findings with analysis of Kenyan laws and practical guidance
    """
    # Use agentic module if available
    module = agentic_research_module if 'agentic_research_module' in globals() and agentic_research_module else research_module
    
    if module is None:
        raise HTTPException(status_code=503, detail="Research module not available. Ensure API keys are configured.")

    try:
        # Parse the input data
        topics = json.loads(legal_topics)
        questions = json.loads(research_questions)

        if not isinstance(topics, list) or not isinstance(questions, list):
            raise HTTPException(status_code=400, detail="legal_topics and research_questions must be JSON arrays")

        result = module.conduct_legal_research(topics, questions)

        if "error" in result:
            raise HTTPException(status_code=500, detail=result["error"])

        # Save to chat if session_id provided
        if session_id:
            # Format query and result for chat saving
            query_text = f"Research on topics: {', '.join(topics)}. Questions: {', '.join(questions)}"
            chat_result = {
                "answer": result.get("summary", result.get("findings", str(result))),
                "sources": result.get("sources", []),
                "retrieved_chunks": result.get("chunks_used", 0),
                "model_used": result.get("model_used", "gemini")
            }
            save_query_to_chat(session_id, query_text, chat_result)

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
        "research_module_available": (research_module is not None) or (agentic_research_module is not None if 'agentic_research_module' in globals() else False),
        "agentic_research_available": agentic_research_module is not None if 'agentic_research_module' in globals() else False,
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
        
        # Initialize database manager
        try:
            self.db_manager = CrawlerDatabaseManager()
            if self.db_manager._initialized:
                logger.info("Using PostgreSQL for crawler status storage")
            else:
                logger.warning("PostgreSQL not available, using in-memory storage")
        except Exception as e:
            logger.warning(f"Failed to initialize crawler database manager: {e}")
            self.db_manager = None
        
        # Load status from database or migrate from file
        self.load_status()
        
        # Start background status checker
        self.status_thread = threading.Thread(target=self._status_checker, daemon=True)
        self.status_thread.start()
    
    def load_status(self):
        """Load crawler status from database or migrate from file"""
        # Initialize default crawlers
        default_crawlers = {
            "kenya_law": {"status": "idle", "last_run": None},
            "parliament": {"status": "idle", "last_run": None},
            "news_rss": {"status": "idle", "last_run": None},
            "global_trends": {"status": "idle", "last_run": None}
        }
        
        if self.db_manager and self.db_manager._initialized:
            # Load from database
            try:
                db_statuses = self.db_manager.get_crawler_status()
                for name, default_status in default_crawlers.items():
                    if name in db_statuses:
                        self.crawlers[name] = db_statuses[name]
                    else:
                        # Initialize new crawler in database
                        self.crawlers[name] = default_status
                        self.db_manager.update_crawler_status(
                            name,
                            default_status["status"],
                            last_run=None
                        )
                
                # Load logs from database
                for name in self.crawlers.keys():
                    self.logs[name] = self.db_manager.get_logs(name, limit=100)
                
                logger.info("Loaded crawler status from PostgreSQL database")
                
                # Migrate from file if it exists (one-time migration)
                if self.status_file.exists():
                    self._migrate_from_file()
                    
            except Exception as e:
                logger.error(f"Error loading crawler status from database: {e}")
                self.crawlers = default_crawlers.copy()
                self.logs = {name: [] for name in default_crawlers.keys()}
        else:
            # Fallback to file-based storage
            try:
                if self.status_file.exists():
                    with open(self.status_file, 'r') as f:
                        data = json.load(f)
                        self.crawlers = data.get('crawlers', default_crawlers)
                        self.logs = data.get('logs', {name: [] for name in default_crawlers.keys()})
                else:
                    self.crawlers = default_crawlers.copy()
                    self.logs = {name: [] for name in default_crawlers.keys()}
            except Exception as e:
                logger.error(f"Error loading crawler status from file: {e}")
                self.crawlers = default_crawlers.copy()
                self.logs = {name: [] for name in default_crawlers.keys()}
    
    def _migrate_from_file(self):
        """Migrate data from JSON file to database (one-time operation)"""
        try:
            if not self.status_file.exists():
                return
            
            logger.info("Migrating crawler status from JSON file to database...")
            with open(self.status_file, 'r') as f:
                data = json.load(f)
                file_crawlers = data.get('crawlers', {})
                file_logs = data.get('logs', {})
            
            # Migrate crawler statuses
            for name, status in file_crawlers.items():
                last_run = None
                if status.get('last_run'):
                    try:
                        # Try parsing ISO format datetime string
                        last_run_str = status['last_run']
                        if isinstance(last_run_str, str):
                            # Remove 'Z' suffix if present and parse
                            if last_run_str.endswith('Z'):
                                last_run_str = last_run_str[:-1] + '+00:00'
                            last_run = datetime.fromisoformat(last_run_str.replace('Z', ''))
                    except Exception:
                        pass
                
                self.db_manager.update_crawler_status(
                    name,
                    status.get('status', 'idle'),
                    last_run=last_run,
                    pid=status.get('pid'),
                    start_time=None
                )
            
            # Migrate logs
            for name, logs in file_logs.items():
                for log_entry in logs:
                    # Parse timestamp from log entry
                    try:
                        if log_entry.startswith('['):
                            timestamp_str = log_entry.split(']')[0][1:]
                            message = log_entry.split(']', 1)[1].strip()
                            try:
                                # Try parsing ISO format
                                if timestamp_str.endswith('Z'):
                                    timestamp_str = timestamp_str[:-1] + '+00:00'
                                timestamp = datetime.fromisoformat(timestamp_str.replace('Z', ''))
                            except Exception:
                                # Fallback to current time if parsing fails
                                timestamp = datetime.utcnow()
                            self.db_manager.add_log(name, message, timestamp)
                        else:
                            self.db_manager.add_log(name, log_entry)
                    except Exception as e:
                        logger.warning(f"Error migrating log entry: {e}")
                        self.db_manager.add_log(name, log_entry)
            
            # Backup and remove old file
            backup_file = self.status_file.with_suffix('.json.backup')
            if not backup_file.exists():
                import shutil
                shutil.copy2(self.status_file, backup_file)
                logger.info(f"Backed up old status file to {backup_file}")
            
            logger.info("Migration completed successfully")
        except Exception as e:
            logger.error(f"Error migrating from file to database: {e}")
    
    def save_status(self):
        """Save crawler status to database"""
        if self.db_manager and self.db_manager._initialized:
            # Save to database
            try:
                for name, status in self.crawlers.items():
                    last_run = None
                    if status.get('last_run'):
                        try:
                            last_run_str = status['last_run']
                            if isinstance(last_run_str, str):
                                if last_run_str.endswith('Z'):
                                    last_run_str = last_run_str[:-1] + '+00:00'
                                last_run = datetime.fromisoformat(last_run_str.replace('Z', ''))
                        except Exception:
                            pass
                    
                    start_time = None
                    if status.get('start_time'):
                        try:
                            start_time_str = status['start_time']
                            if isinstance(start_time_str, str):
                                if start_time_str.endswith('Z'):
                                    start_time_str = start_time_str[:-1] + '+00:00'
                                start_time = datetime.fromisoformat(start_time_str.replace('Z', ''))
                        except Exception:
                            pass
                    
                    self.db_manager.update_crawler_status(
                        name,
                        status.get('status', 'idle'),
                        last_run=last_run,
                        pid=status.get('pid'),
                        start_time=start_time
                    )
            except Exception as e:
                logger.error(f"Error saving crawler status to database: {e}")
        else:
            # Fallback to file
            try:
                data = {
                    'crawlers': self.crawlers,
                    'logs': self.logs
                }
                with open(self.status_file, 'w') as f:
                    json.dump(data, f, indent=2)
            except Exception as e:
                logger.error(f"Error saving crawler status to file: {e}")
    
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
                            last_run_time = datetime.utcnow()
                            if exit_code == 0:
                                self.crawlers[crawler_name]['status'] = 'idle'
                                self._add_log(crawler_name, f"Process completed successfully (PID: {pid})")
                            else:
                                self.crawlers[crawler_name]['status'] = 'failed'
                                self._add_log(crawler_name, f"Process failed with exit code {exit_code} (PID: {pid})")
                            
                            # Clean up
                            del self.processes[crawler_name]
                            self.crawlers[crawler_name]['last_run'] = last_run_time.isoformat() + 'Z'
                            self.crawlers[crawler_name]['pid'] = None
                            self.crawlers[crawler_name]['start_time'] = None
                            self.save_status()
                        else:
                            # Process still running
                            self.crawlers[crawler_name]['status'] = 'running'
                            self.save_status()  # Update status periodically
                    except Exception as e:
                        logger.error(f"Error checking process {pid}: {e}")
                        self.crawlers[crawler_name]['status'] = 'failed'
                        self.crawlers[crawler_name]['pid'] = None
                        self.crawlers[crawler_name]['start_time'] = None
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
        timestamp = datetime.utcnow()
        timestamp_str = timestamp.isoformat() + 'Z'
        
        if self.db_manager and self.db_manager._initialized:
            # Save to database
            try:
                self.db_manager.add_log(crawler_name, message, timestamp)
                # Update in-memory cache (last 100)
                if crawler_name not in self.logs:
                    self.logs[crawler_name] = []
                self.logs[crawler_name].append(f"[{timestamp_str}] {message}")
                if len(self.logs[crawler_name]) > 100:
                    self.logs[crawler_name] = self.logs[crawler_name][-100:]
            except Exception as e:
                logger.error(f"Error adding log to database: {e}")
                # Fallback to in-memory
                if crawler_name not in self.logs:
                    self.logs[crawler_name] = []
                self.logs[crawler_name].append(f"[{timestamp_str}] {message}")
                if len(self.logs[crawler_name]) > 100:
                    self.logs[crawler_name] = self.logs[crawler_name][-100:]
        else:
            # Fallback to in-memory
            if crawler_name not in self.logs:
                self.logs[crawler_name] = []
            self.logs[crawler_name].append(f"[{timestamp_str}] {message}")
            if len(self.logs[crawler_name]) > 100:
                self.logs[crawler_name] = self.logs[crawler_name][-100:]
    
    def get_crawler_status(self):
        """Get status of all crawlers"""
        # Initialize default crawlers if not exists
        default_crawlers = {
            "kenya_law": {"status": "idle", "last_run": None},
            "parliament": {"status": "idle", "last_run": None},
            "news_rss": {"status": "idle", "last_run": None},
            "global_trends": {"status": "idle", "last_run": None}
        }
        
        # Load from database if available
        if self.db_manager and self.db_manager._initialized:
            try:
                db_statuses = self.db_manager.get_crawler_status()
                for name, default_status in default_crawlers.items():
                    if name in db_statuses:
                        self.crawlers[name] = db_statuses[name]
                    else:
                        self.crawlers[name] = default_status
                
                # Load logs from database
                for name in self.crawlers.keys():
                    self.logs[name] = self.db_manager.get_logs(name, limit=100)
            except Exception as e:
                logger.error(f"Error loading crawler status from database: {e}")
                # Fallback to in-memory
                for name, default_status in default_crawlers.items():
                    if name not in self.crawlers:
                        self.crawlers[name] = default_status
                        self.logs[name] = []
        else:
            # Merge with saved status (in-memory)
            for name, default_status in default_crawlers.items():
                if name not in self.crawlers:
                    self.crawlers[name] = default_status
                    self.logs[name] = []
        
        # Try to get actual last run times from database
        self._update_last_run_times()
        
        # Return current status with logs
        result = {}
        for name, status in self.crawlers.items():
            result[name] = {
                **status,
                "logs": self.logs.get(name, [])
            }
        
        return result
    
    def _update_last_run_times(self):
        """Update last run times from database"""
        try:
            if database_storage is None:
                logger.warning("Database storage not available, skipping last run times update")
                return
            
            # Map crawler names to database categories/sources
            crawler_mapping = {
                "kenya_law": {"category": "Kenyan Law"},
                "parliament": {"category": "Parliament"},
                "news_rss": {"source_name": "News RSS"},
                "global_trends": {"category": "Global Trend"}
            }
            
            with database_storage.get_db_session() as db:
                for crawler_name, filters in crawler_mapping.items():
                    try:
                        # Query the most recent crawl_date for this crawler type
                        from sqlalchemy import func
                        from Module3_NiruDB.database_storage import RawDocument
                        
                        query = db.query(func.max(RawDocument.crawl_date))
                        
                        if "category" in filters:
                            query = query.filter(RawDocument.category == filters["category"])
                        if "source_name" in filters:
                            query = query.filter(RawDocument.source_name == filters["source_name"])
                        
                        last_run = query.scalar()
                        
                        if last_run:
                            self.crawlers[crawler_name]["last_run"] = last_run.isoformat() + 'Z'
                        else:
                            # No data found, keep as None or set to never
                            self.crawlers[crawler_name]["last_run"] = None
                            
                    except Exception as e:
                        logger.warning(f"Error getting last run time for {crawler_name}: {e}")
                        self.crawlers[crawler_name]["last_run"] = None
                        
        except Exception as e:
            logger.warning(f"Error updating last run times from database: {e}")
    
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
                "kenya_law": "kenya_law_spider",
                "parliament": "parliament_spider", 
                "news_rss": "news_rss_spider",
                "global_trends": "global_trends_spider"
            }
            
            if crawler_name not in spider_mapping:
                raise HTTPException(status_code=404, detail=f"Unknown crawler: {crawler_name}")
            
            spider_name = spider_mapping[crawler_name]
            
            # Start subprocess with log capture
            cmd = [sys.executable, "crawl_spider.py", spider_name]
            
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
            start_time = datetime.utcnow()
            self.crawlers[crawler_name]['status'] = 'running'
            self.crawlers[crawler_name]['pid'] = process.pid
            self.crawlers[crawler_name]['start_time'] = start_time.isoformat() + 'Z'
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
            self.crawlers[crawler_name]['pid'] = None
            self.crawlers[crawler_name]['start_time'] = None
            self.crawlers[crawler_name]['last_run'] = datetime.utcnow().isoformat() + 'Z'
            self._add_log(crawler_name, f"Process stopped (PID: {process_info['pid']})")
            self.save_status()
            
            return {"status": "stopped", "message": f"Crawler {crawler_name} stopped successfully"}
            
        except Exception as e:
            logger.error(f"Error stopping crawler {crawler_name}: {e}")
            raise HTTPException(status_code=500, detail=f"Failed to stop crawler: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    import platform
    
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", 8000))
    
    # Disable reload on Windows to avoid multiprocessing import issues
    is_windows = platform.system() == "Windows"
    default_reload = "False" if is_windows else "True"
    reload = os.getenv("API_RELOAD", default_reload).lower() == "true"
    
    print("=" * 60)
    print("🚀 Starting AmaniQuery API")
    print("=" * 60)
    print(f"📍 Server: http://{host}:{port}")
    print(f"📚 Docs: http://{host}:{port}/docs")
    print(f"🔧 Provider: {os.getenv('LLM_PROVIDER', 'moonshot')}")
    print(f"🔄 Reload: {'Enabled' if reload else 'Disabled'}")
    if is_windows and reload:
        print("⚠️  Warning: Reload enabled on Windows may cause import issues")
    print("=" * 60)
    
    # Exclude setup.py and other non-source files from reload watch
    reload_excludes = [
        "setup.py",
        "*.pyc",
        "__pycache__",
        "*.log",
        ".env",
        "venv/**",
        "node_modules/**",
    ] if reload else None
    
    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        reload=reload,
        reload_excludes=reload_excludes,
    )
