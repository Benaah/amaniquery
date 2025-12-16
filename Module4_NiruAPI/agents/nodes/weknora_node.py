"""
WeKnora Retrieval Node for AmaniQ v2 LangGraph

Dedicated LangGraph node for WeKnora hybrid search integration.
Provides enhanced retrieval for:
- Constitutional law queries
- Legal case references
- Statute interpretation
- Multi-document reasoning

Uses WeKnora's advanced features:
- BM25 keyword search
- Dense vector similarity
- Knowledge graph relationships (Neo4j)
"""

import os
import time
from typing import Dict, Any, List, Optional, TypedDict
from datetime import datetime
from loguru import logger

# Import WeKnora client
try:
    from Module7_NiruHybrid.weknora_client import WeKnoraClient
    WEKNORA_CLIENT_AVAILABLE = True
except ImportError:
    WEKNORA_CLIENT_AVAILABLE = False
    logger.warning("WeKnora client not available")


# State schema (must match AmaniQState)
class WeKnoraNodeState(TypedDict, total=False):
    """State fields used by WeKnora node"""
    current_query: str
    original_question: str
    weknora_results: List[Dict[str, Any]]
    weknora_kb_id: Optional[str]
    weknora_used: bool
    weknora_graph_data: Optional[Dict]
    weknora_latency_ms: float
    tool_results: List[Dict[str, Any]]
    error_details: List[str]


# Configuration
WEKNORA_ENABLED = os.getenv("WEKNORA_ENABLED", "false").lower() == "true"
WEKNORA_KB_ID = os.getenv("WEKNORA_KNOWLEDGE_BASE_ID", "kb-00000001")
WEKNORA_TOP_K = int(os.getenv("WEKNORA_TOP_K", "5"))


async def weknora_retrieval_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    WeKnora retrieval node for LangGraph.
    
    Uses WeKnora's hybrid search to retrieve relevant documents,
    then merges results with existing tool_results.
    
    Args:
        state: Current graph state
        
    Returns:
        Updated state with WeKnora results
    """
    logger.info("=== WEKNORA RETRIEVAL NODE ===")
    
    # Check if WeKnora is enabled
    if not WEKNORA_ENABLED:
        logger.debug("WeKnora is not enabled, skipping")
        return {
            **state,
            "weknora_used": False,
            "weknora_results": [],
        }
    
    if not WEKNORA_CLIENT_AVAILABLE:
        logger.warning("WeKnora client not available")
        return {
            **state,
            "weknora_used": False,
            "weknora_results": [],
            "error_details": state.get("error_details", []) + ["WeKnora client not available"],
        }
    
    # Get query
    query = state.get("current_query") or state.get("original_question", "")
    if not query:
        logger.warning("No query provided to WeKnora node")
        return {**state, "weknora_used": False}
    
    # Get knowledge base ID (can be overridden per query)
    kb_id = state.get("weknora_kb_id") or WEKNORA_KB_ID
    
    try:
        start_time = time.time()
        
        # Create client and search
        async with WeKnoraClient() as client:
            results = await client.hybrid_search(
                kb_id=kb_id,
                query=query,
                vector_threshold=0.5,
                keyword_threshold=0.3,
                match_count=WEKNORA_TOP_K,
            )
        
        latency_ms = (time.time() - start_time) * 1000
        
        # Format results
        weknora_results = []
        for i, chunk in enumerate(results):
            weknora_results.append({
                "rank": i + 1,
                "content": chunk.get("content", ""),
                "title": chunk.get("knowledge_title", ""),
                "url": "",  # WeKnora doesn't have URLs
                "source": "weknora",
                "source_name": chunk.get("knowledge_filename", "WeKnora KB"),
                "score": chunk.get("score", 0),
                "chunk_id": chunk.get("id", ""),
                "metadata": {
                    "chunk_type": chunk.get("chunk_type", "text"),
                    "knowledge_id": chunk.get("knowledge_id", ""),
                    "kb_id": kb_id,
                },
            })
        
        logger.info(f"[WeKnora] Retrieved {len(weknora_results)} results in {latency_ms:.0f}ms")
        
        # Merge with existing tool results
        existing_results = state.get("tool_results", [])
        
        # Add WeKnora as a tool result for responder
        weknora_tool_result = {
            "tool_name": "weknora_search",
            "query": query,
            "status": "success",
            "data": {
                "search_results": weknora_results,
                "source": "weknora_hybrid_search",
                "kb_id": kb_id,
            },
            "latency_ms": latency_ms,
        }
        
        merged_results = existing_results + [weknora_tool_result]
        
        return {
            **state,
            "weknora_used": True,
            "weknora_results": weknora_results,
            "weknora_kb_id": kb_id,
            "weknora_latency_ms": latency_ms,
            "tool_results": merged_results,
        }
        
    except Exception as e:
        logger.error(f"[WeKnora] Retrieval failed: {e}")
        return {
            **state,
            "weknora_used": False,
            "weknora_results": [],
            "error_details": state.get("error_details", []) + [f"WeKnora: {e}"],
        }


def should_use_weknora(state: Dict[str, Any]) -> bool:
    """
    Determine if WeKnora should be used for this query.
    
    Called by supervisor or routing logic.
    
    Args:
        state: Current graph state
        
    Returns:
        True if WeKnora should be used
    """
    if not WEKNORA_ENABLED:
        return False
    
    # Check intent from supervisor
    intent = state.get("intent", "")
    
    # Always use WeKnora for legal queries
    legal_intents = ["LEGAL_RESEARCH", "CONSTITUTION", "CASE_LAW", "STATUTE"]
    if intent in legal_intents:
        return True
    
    # Check for legal keywords in query
    query = (state.get("current_query") or "").lower()
    legal_keywords = [
        "constitution", "article", "section", "act",
        "law", "legal", "court", "ruling", "judgment",
        "statute", "regulation", "bill", "parliament",
        "katiba", "sheria", "mahakama",  # Swahili
    ]
    
    for keyword in legal_keywords:
        if keyword in query:
            return True
    
    return False


async def weknora_health_check() -> Dict[str, Any]:
    """Check WeKnora service health"""
    if not WEKNORA_ENABLED:
        return {"status": "disabled"}
    
    if not WEKNORA_CLIENT_AVAILABLE:
        return {"status": "client_unavailable"}
    
    try:
        async with WeKnoraClient() as client:
            return await client.health_check()
    except Exception as e:
        return {"status": "error", "error": str(e)}
