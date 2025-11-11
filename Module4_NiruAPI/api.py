"""
FastAPI Application - REST API for AmaniQuery
"""
import os
import sys
from pathlib import Path
from typing import Optional

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from loguru import logger

from Module4_NiruAPI.rag_pipeline import RAGPipeline
from Module4_NiruAPI.models import (
    QueryRequest,
    QueryResponse,
    Source,
    HealthResponse,
    StatsResponse,
)
from Module3_NiruDB import VectorStore

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

# Initialize components
vector_store = None
rag_pipeline = None


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    global vector_store, rag_pipeline
    
    logger.info("Starting AmaniQuery API")
    
    # Initialize vector store
    vector_store = VectorStore()
    
    # Initialize RAG pipeline
    llm_provider = os.getenv("LLM_PROVIDER", "openai")
    model = os.getenv("DEFAULT_MODEL", "gpt-3.5-turbo")
    
    rag_pipeline = RAGPipeline(
        vector_store=vector_store,
        llm_provider=llm_provider,
        model=model,
    )
    
    logger.info("AmaniQuery API ready")


@app.get("/", tags=["General"])
async def root():
    """Root endpoint"""
    return {
        "name": "AmaniQuery API",
        "version": "1.0.0",
        "description": "RAG-powered API for Kenyan intelligence",
        "endpoints": {
            "query": "POST /query",
            "health": "GET /health",
            "stats": "GET /stats",
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
        llm_provider=os.getenv("LLM_PROVIDER", "openai"),
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
    print(f"🔧 Provider: {os.getenv('LLM_PROVIDER', 'openai')}")
    print("=" * 60)
    
    uvicorn.run(
        "api:app",
        host=host,
        port=port,
        reload=reload,
    )
