"""
WeKnora Search Tool for AmaniQ Agent

LangGraph-compatible tool for WeKnora hybrid search integration.
Uses WeKnora's advanced RAG capabilities:
- BM25 keyword search
- Dense vector similarity
- Knowledge graph relationships (Neo4j)
"""

import os
from typing import Dict, Any, List, Optional
from loguru import logger
import httpx


class WeKnoraSearchTool:
    """
    WeKnora hybrid search tool for ToolRegistry.
    
    Compatible with AmaniQ agent tool execution pattern.
    """
    
    name = "weknora_search"
    description = (
        "Search WeKnora knowledge bases for legal documents, constitutional law, "
        "and Kenyan legal information. Uses hybrid retrieval (BM25 + vector + graph). "
        "Best for: Constitutional queries, legal case law, statute interpretation."
    )
    
    def __init__(
        self,
        api_url: Optional[str] = None,
        api_key: Optional[str] = None,
        default_kb_id: Optional[str] = None,
    ):
        """
        Initialize WeKnora search tool.
        
        Args:
            api_url: WeKnora API URL (default from env)
            api_key: WeKnora API key (default from env)
            default_kb_id: Default knowledge base ID
        """
        self.api_url = api_url or os.getenv("WEKNORA_API_URL", "http://localhost:8081/api/v1")
        self.api_key = api_key or os.getenv("WEKNORA_API_KEY", "")
        self.default_kb_id = default_kb_id or os.getenv("WEKNORA_KNOWLEDGE_BASE_ID", "kb-00000001")
        self.enabled = os.getenv("WEKNORA_ENABLED", "false").lower() == "true"
        
        logger.info(f"WeKnora tool initialized: {self.api_url} (enabled: {self.enabled})")
    
    async def execute(
        self,
        query: str,
        kb_id: Optional[str] = None,
        top_k: int = 5,
        vector_threshold: float = 0.5,
        keyword_threshold: float = 0.3,
        **kwargs
    ) -> Dict[str, Any]:
        """
        Execute WeKnora hybrid search.
        
        Args:
            query: Search query
            kb_id: Knowledge base ID (uses default if not specified)
            top_k: Number of results to return
            vector_threshold: Minimum vector similarity score
            keyword_threshold: Minimum keyword match score
            
        Returns:
            Search results with metadata
        """
        if not self.enabled:
            logger.warning("WeKnora is not enabled, returning empty results")
            return {
                "success": False,
                "error": "WeKnora is not enabled. Set WEKNORA_ENABLED=true",
                "results": [],
            }
        
        kb_id = kb_id or self.default_kb_id
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                headers = {
                    "X-API-Key": self.api_key,
                    "Content-Type": "application/json",
                }
                
                payload = {
                    "query_text": query,
                    "vector_threshold": vector_threshold,
                    "keyword_threshold": keyword_threshold,
                    "match_count": top_k,
                }
                
                response = await client.request(
                    "GET",
                    f"{self.api_url}/knowledge-bases/{kb_id}/hybrid-search",
                    headers=headers,
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
                
                results = data.get("data", [])
                
                # Format results for agent consumption
                formatted_results = []
                for i, chunk in enumerate(results):
                    formatted_results.append({
                        "rank": i + 1,
                        "content": chunk.get("content", ""),
                        "title": chunk.get("knowledge_title", ""),
                        "source": chunk.get("knowledge_source", "weknora"),
                        "filename": chunk.get("knowledge_filename", ""),
                        "score": chunk.get("score", 0),
                        "chunk_type": chunk.get("chunk_type", "text"),
                        "chunk_id": chunk.get("id", ""),
                        "knowledge_id": chunk.get("knowledge_id", ""),
                    })
                
                logger.info(f"[WeKnora] Found {len(formatted_results)} results for: {query[:50]}...")
                
                return {
                    "success": True,
                    "query": query,
                    "kb_id": kb_id,
                    "results": formatted_results,
                    "count": len(formatted_results),
                    "source": "weknora",
                }
                
        except httpx.HTTPStatusError as e:
            logger.error(f"[WeKnora] HTTP error: {e}")
            return {
                "success": False,
                "error": f"HTTP {e.response.status_code}: {e.response.text}",
                "results": [],
            }
        except Exception as e:
            logger.error(f"[WeKnora] Search failed: {e}")
            return {
                "success": False,
                "error": str(e),
                "results": [],
            }
    
    def get_tool_schema(self) -> Dict[str, Any]:
        """Get tool schema for LLM function calling"""
        return {
            "name": self.name,
            "description": self.description,
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query for WeKnora knowledge base",
                    },
                    "kb_id": {
                        "type": "string",
                        "description": "Optional knowledge base ID",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results (default: 5)",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check WeKnora service health"""
        if not self.enabled:
            return {"status": "disabled", "message": "WeKnora is not enabled"}
        
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                headers = {"X-API-Key": self.api_key}
                response = await client.get(
                    f"{self.api_url}/knowledge-bases",
                    headers=headers,
                )
                response.raise_for_status()
                data = response.json()
                kbs = data.get("data", [])
                
                return {
                    "status": "healthy",
                    "api_url": self.api_url,
                    "knowledge_bases": len(kbs),
                }
        except Exception as e:
            return {
                "status": "error",
                "api_url": self.api_url,
                "error": str(e),
            }
