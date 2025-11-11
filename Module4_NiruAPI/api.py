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
from Module4_NiruAPI.alignment_pipeline import ConstitutionalAlignmentPipeline
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
)
from Module3_NiruDB import VectorStore
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


@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    global vector_store, rag_pipeline, alignment_pipeline
    
    logger.info("Starting AmaniQuery API")
    
    # Initialize vector store
    vector_store = VectorStore()
    
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
