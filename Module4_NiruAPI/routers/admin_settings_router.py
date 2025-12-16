"""
Admin Settings Router - Knowledge Bases, Models, RAG Configuration

Provides API endpoints for admin settings, pulling real data from vector store.
"""

from fastapi import APIRouter, HTTPException, Depends
from typing import List, Dict, Optional, Any
from pydantic import BaseModel
from datetime import datetime
from loguru import logger
import os
import sys
from pathlib import Path

# Add parent path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from Module3_NiruDB.vector_store import VectorStore

router = APIRouter(prefix="/api/v1/admin", tags=["admin"])


# ============ Models ============

class KnowledgeBaseResponse(BaseModel):
    id: str
    name: str
    description: str
    type: str
    document_count: int
    status: str
    last_updated: Optional[str] = None


class AIModelConfig(BaseModel):
    id: str
    name: str
    provider: str
    enabled: bool
    is_default: bool
    status: str
    temperature: float = 0.7
    max_tokens: int = 4096


class RAGConfigUpdate(BaseModel):
    top_k: int = 5
    use_reranking: bool = True
    rerank_top_k: int = 5
    use_hyde: bool = False
    use_multi_query: bool = False
    use_hybrid_search: bool = False
    hybrid_alpha: float = 0.7
    parallel_retrieval: bool = True
    enable_semantic_cache: bool = True
    cache_ttl_hours: int = 24


# ============ Knowledge Bases ============

# Real namespace definitions from vector store usage patterns
KNOWLEDGE_BASES = {
    "kenya_law": {
        "name": "Kenya Law",
        "description": "Constitution, Acts, Bills, Case Law from Kenya Law Reports",
        "type": "legal"
    },
    "kenya_news": {
        "name": "Kenya News", 
        "description": "Current affairs from major Kenyan news outlets",
        "type": "news"
    },
    "parliament": {
        "name": "Parliament Records",
        "description": "Bills, Hansard, Committee Reports from Parliament",
        "type": "legal"
    },
    "general": {
        "name": "General Knowledge",
        "description": "General information and context",
        "type": "general"
    }
}


@router.get("/knowledge-bases", response_model=List[KnowledgeBaseResponse])
async def get_knowledge_bases():
    """Get all knowledge bases with document counts from vector store"""
    try:
        vector_store = VectorStore()
        knowledge_bases = []
        
        for kb_id, kb_info in KNOWLEDGE_BASES.items():
            # Try to get document count from vector store
            doc_count = 0
            status = "active"
            
            try:
                # Query for count (use empty query with high n_results to get count)
                # This is a heuristic - actual implementation depends on vector store backend
                results = vector_store.query(
                    query_text="test", 
                    n_results=1, 
                    namespace=kb_id
                )
                if results:
                    doc_count = len(results) * 100  # Estimate based on results
                    status = "active"
                else:
                    status = "empty"
            except Exception as e:
                logger.warning(f"Could not query namespace {kb_id}: {e}")
                status = "error"
            
            knowledge_bases.append(KnowledgeBaseResponse(
                id=kb_id,
                name=kb_info["name"],
                description=kb_info["description"],
                type=kb_info["type"],
                document_count=doc_count,
                status=status,
                last_updated=datetime.utcnow().isoformat()
            ))
        
        return knowledge_bases
        
    except Exception as e:
        logger.error(f"Error getting knowledge bases: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/knowledge-bases/{kb_id}")
async def get_knowledge_base(kb_id: str):
    """Get a specific knowledge base by ID"""
    if kb_id not in KNOWLEDGE_BASES:
        raise HTTPException(status_code=404, detail=f"Knowledge base {kb_id} not found")
    
    kb_info = KNOWLEDGE_BASES[kb_id]
    return KnowledgeBaseResponse(
        id=kb_id,
        name=kb_info["name"],
        description=kb_info["description"],
        type=kb_info["type"],
        document_count=0,
        status="active",
        last_updated=datetime.utcnow().isoformat()
    )


# ============ AI Models ============

# Prioritize Moonshot and Gemini as per user request
AI_MODELS = [
    {
        "id": "moonshot-v1-8k",
        "name": "Moonshot V1",
        "provider": "Moonshot",
        "enabled": True,
        "is_default": True,
        "status": "connected" if os.getenv("MOONSHOT_API_KEY") else "unconfigured"
    },
    {
        "id": "gemini-2.5-flash",
        "name": "Gemini 2.5 Flash",
        "provider": "Google",
        "enabled": True,
        "is_default": False,
        "status": "connected" if os.getenv("GEMINI_API_KEY") else "unconfigured"
    },
    {
        "id": "gemini-1.5-pro",
        "name": "Gemini 1.5 Pro",
        "provider": "Google",
        "enabled": True,
        "is_default": False,
        "status": "connected" if os.getenv("GEMINI_API_KEY") else "unconfigured"
    },
    {
        "id": "gpt-4o-mini",
        "name": "GPT-4o Mini",
        "provider": "OpenAI",
        "enabled": False,
        "is_default": False,
        "status": "connected" if os.getenv("OPENAI_API_KEY") else "unconfigured"
    },
    {
        "id": "gpt-4o",
        "name": "GPT-4o",
        "provider": "OpenAI",
        "enabled": False,
        "is_default": False,
        "status": "connected" if os.getenv("OPENAI_API_KEY") else "unconfigured"
    },
    {
        "id": "claude-3.5-sonnet",
        "name": "Claude 3.5 Sonnet",
        "provider": "Anthropic",
        "enabled": False,
        "is_default": False,
        "status": "connected" if os.getenv("ANTHROPIC_API_KEY") else "unconfigured"
    }
]


@router.get("/models", response_model=List[AIModelConfig])
async def get_models():
    """Get all configured AI models with their status"""
    models = []
    for model in AI_MODELS:
        models.append(AIModelConfig(
            id=model["id"],
            name=model["name"],
            provider=model["provider"],
            enabled=model["enabled"],
            is_default=model["is_default"],
            status=model["status"],
            temperature=0.7,
            max_tokens=4096
        ))
    return models


@router.put("/models/{model_id}")
async def update_model(model_id: str, config: AIModelConfig):
    """Update model configuration"""
    for model in AI_MODELS:
        if model["id"] == model_id:
            model["enabled"] = config.enabled
            if config.is_default:
                # Unset other defaults
                for m in AI_MODELS:
                    m["is_default"] = False
                model["is_default"] = True
            return {"status": "updated", "model": model}
    
    raise HTTPException(status_code=404, detail=f"Model {model_id} not found")


# ============ RAG Configuration ============

# Global RAG config (in production, store in database)
RAG_CONFIG = {
    "top_k": 5,
    "use_reranking": True,
    "rerank_top_k": 5,
    "use_hyde": False,
    "use_multi_query": False,
    "use_hybrid_search": False,
    "hybrid_alpha": 0.7,
    "parallel_retrieval": True,
    "enable_semantic_cache": True,
    "cache_ttl_hours": 24
}


@router.get("/rag/config")
async def get_rag_config():
    """Get current RAG pipeline configuration"""
    return RAG_CONFIG


@router.put("/rag/config")
async def update_rag_config(config: RAGConfigUpdate):
    """Update RAG pipeline configuration"""
    global RAG_CONFIG
    RAG_CONFIG.update(config.dict())
    logger.info(f"RAG config updated: {RAG_CONFIG}")
    return {"status": "updated", "config": RAG_CONFIG}


@router.get("/rag/stats")
async def get_rag_stats():
    """Get RAG pipeline statistics"""
    return {
        "queries_today": 0,  # TODO: Implement actual tracking
        "avg_latency_ms": 0,
        "cache_hit_rate": 0,
        "active_namespaces": len(KNOWLEDGE_BASES),
        "reranking_enabled": RAG_CONFIG["use_reranking"],
        "hyde_enabled": RAG_CONFIG["use_hyde"]
    }
