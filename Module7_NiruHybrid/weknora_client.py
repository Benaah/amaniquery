"""
WeKnora API Client for AmaniQuery

Provides integration with Tencent's WeKnora RAG framework for:
- Hybrid search (BM25 + vector + knowledge graph)
- Knowledge base management
- Document processing
- Chat sessions with ReACT Agent

This client can be used directly or as a tool for NiruSense agent.
"""

import os
from typing import Any, Dict, List, Optional
from loguru import logger
import httpx


class WeKnoraClient:
    """
    Client for interacting with WeKnora API
    
    Usage:
        client = WeKnoraClient()
        results = await client.hybrid_search("kb-00000001", "Kenyan constitution")
    """
    
    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        timeout: float = 30.0,
    ):
        """
        Initialize WeKnora client
        
        Args:
            base_url: WeKnora API base URL (default from env)
            api_key: WeKnora API key (default from env)
            timeout: Request timeout in seconds
        """
        self.base_url = base_url or os.getenv("WEKNORA_API_URL", "http://localhost:8081/api/v1")
        self.api_key = api_key or os.getenv("WEKNORA_API_KEY", "")
        self.timeout = timeout
        
        self._client = httpx.AsyncClient(
            base_url=self.base_url,
            headers={
                "X-API-Key": self.api_key,
                "Content-Type": "application/json",
            },
            timeout=timeout,
        )
        
        logger.info(f"WeKnora client initialized: {self.base_url}")
    
    async def close(self):
        """Close the HTTP client"""
        await self._client.aclose()
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, *args):
        await self.close()
    
    # =========================================================================
    # KNOWLEDGE BASE MANAGEMENT
    # =========================================================================
    
    async def list_knowledge_bases(self) -> List[Dict[str, Any]]:
        """List all knowledge bases"""
        try:
            response = await self._client.get("/knowledge-bases")
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except Exception as e:
            logger.error(f"Failed to list knowledge bases: {e}")
            raise
    
    async def get_knowledge_base(self, kb_id: str) -> Dict[str, Any]:
        """Get knowledge base details"""
        try:
            response = await self._client.get(f"/knowledge-bases/{kb_id}")
            response.raise_for_status()
            data = response.json()
            return data.get("data", {})
        except Exception as e:
            logger.error(f"Failed to get knowledge base {kb_id}: {e}")
            raise
    
    async def create_knowledge_base(
        self,
        name: str,
        description: str,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
    ) -> Dict[str, Any]:
        """Create a new knowledge base"""
        try:
            payload = {
                "name": name,
                "description": description,
                "chunking_config": {
                    "chunk_size": chunk_size,
                    "chunk_overlap": chunk_overlap,
                    "separators": ["\n\n", "\n", ".", "!", "?"],
                    "enable_multimodal": True,
                },
            }
            response = await self._client.post("/knowledge-bases", json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("data", {})
        except Exception as e:
            logger.error(f"Failed to create knowledge base: {e}")
            raise
    
    # =========================================================================
    # HYBRID SEARCH
    # =========================================================================
    
    async def hybrid_search(
        self,
        kb_id: str,
        query: str,
        vector_threshold: float = 0.5,
        keyword_threshold: float = 0.3,
        match_count: int = 5,
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search (vector + keyword) on knowledge base
        
        This is the main search method combining:
        - BM25 keyword matching
        - Dense vector similarity
        - Optional knowledge graph relations
        
        Args:
            kb_id: Knowledge base ID
            query: Search query
            vector_threshold: Minimum vector similarity (0-1)
            keyword_threshold: Minimum keyword match score
            match_count: Number of results to return
            
        Returns:
            List of matching chunks with scores
        """
        try:
            payload = {
                "query_text": query,
                "vector_threshold": vector_threshold,
                "keyword_threshold": keyword_threshold,
                "match_count": match_count,
            }
            response = await self._client.request(
                "GET",
                f"/knowledge-bases/{kb_id}/hybrid-search",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", [])
        except Exception as e:
            logger.error(f"Hybrid search failed: {e}")
            raise
    
    # =========================================================================
    # KNOWLEDGE MANAGEMENT
    # =========================================================================
    
    async def add_knowledge_from_url(
        self,
        kb_id: str,
        url: str,
        enable_multimodal: bool = True,
    ) -> Dict[str, Any]:
        """Add knowledge from a URL"""
        try:
            payload = {
                "url": url,
                "enable_multimodel": enable_multimodal,
            }
            response = await self._client.post(
                f"/knowledge-bases/{kb_id}/knowledge/url",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", {})
        except Exception as e:
            logger.error(f"Failed to add knowledge from URL: {e}")
            raise
    
    async def list_knowledge(
        self,
        kb_id: str,
        page: int = 1,
        page_size: int = 20,
    ) -> Dict[str, Any]:
        """List knowledge in a knowledge base"""
        try:
            response = await self._client.get(
                f"/knowledge-bases/{kb_id}/knowledge",
                params={"page": page, "page_size": page_size},
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", {})
        except Exception as e:
            logger.error(f"Failed to list knowledge: {e}")
            raise
    
    # =========================================================================
    # CHAT SESSIONS
    # =========================================================================
    
    async def create_session(
        self,
        kb_id: str,
        max_rounds: int = 5,
        enable_rewrite: bool = True,
    ) -> Dict[str, Any]:
        """Create a new chat session"""
        try:
            payload = {
                "knowledge_base_id": kb_id,
                "session_strategy": {
                    "max_rounds": max_rounds,
                    "enable_rewrite": enable_rewrite,
                    "fallback_strategy": "FIXED_RESPONSE",
                    "fallback_response": "I couldn't find relevant information to answer your question.",
                    "embedding_top_k": 10,
                    "keyword_threshold": 0.5,
                    "vector_threshold": 0.7,
                },
            }
            response = await self._client.post("/sessions", json=payload)
            response.raise_for_status()
            data = response.json()
            return data.get("data", {})
        except Exception as e:
            logger.error(f"Failed to create session: {e}")
            raise
    
    async def chat(self, session_id: str, query: str) -> Dict[str, Any]:
        """Send a chat message"""
        try:
            payload = {"query": query}
            response = await self._client.post(
                f"/knowledge-chat/{session_id}",
                json=payload,
            )
            response.raise_for_status()
            data = response.json()
            return data.get("data", {})
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            raise
    
    # =========================================================================
    # HEALTH CHECK
    # =========================================================================
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if WeKnora is available"""
        try:
            # Try to list knowledge bases as a health check
            kbs = await self.list_knowledge_bases()
            return {
                "status": "healthy",
                "base_url": self.base_url,
                "knowledge_bases": len(kbs),
            }
        except Exception as e:
            return {
                "status": "error",
                "base_url": self.base_url,
                "error": str(e),
            }


# Singleton client instance
_weknora_client: Optional[WeKnoraClient] = None


def get_weknora_client() -> WeKnoraClient:
    """Get or create WeKnora client singleton"""
    global _weknora_client
    if _weknora_client is None:
        _weknora_client = WeKnoraClient()
    return _weknora_client


async def weknora_search(query: str, kb_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Quick search function for use in RAG pipeline
    
    Args:
        query: Search query
        kb_id: Knowledge base ID (uses default if not provided)
        
    Returns:
        List of matching chunks
    """
    client = get_weknora_client()
    
    # Use default KB if not specified
    if kb_id is None:
        kb_id = os.getenv("WEKNORA_KNOWLEDGE_BASE_ID", "kb-00000001")
    
    return await client.hybrid_search(kb_id, query)
