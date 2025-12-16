"""
WeKnora Tool for NiruSense Agent

Provides WeKnora search as a tool that can be called by the NiruSense agent
during query processing, allowing access to WeKnora's advanced features:
- Hybrid search (BM25 + vector + knowledge graph)
- Multi-type knowledge bases
- ReACT agent capabilities
"""

import os
from typing import Dict, Any, List, Optional
from loguru import logger


class WeKnoraTool:
    """
    Tool adapter for NiruSense agent to use WeKnora search
    
    This allows the agent to:
    1. Search WeKnora knowledge bases alongside AmaniQuery's RAG
    2. Leverage WeKnora's hybrid retrieval
    3. Access specialized knowledge bases (e.g., legal documents)
    """
    
    name = "weknora_search"
    description = (
        "Search WeKnora knowledge bases for relevant information. "
        "Use this when you need to find information about Kenyan law, "
        "constitution, or legal documents that may be stored in WeKnora."
    )
    
    def __init__(self, default_kb_id: Optional[str] = None):
        """Initialize WeKnora tool"""
        self.default_kb_id = default_kb_id or os.getenv(
            "WEKNORA_KNOWLEDGE_BASE_ID", "kb-00000001"
        )
        self._client = None
    
    async def _get_client(self):
        """Lazy initialize client"""
        if self._client is None:
            from Module7_NiruHybrid.weknora_client import WeKnoraClient
            self._client = WeKnoraClient()
        return self._client
    
    async def execute(
        self,
        query: str,
        kb_id: Optional[str] = None,
        top_k: int = 5,
    ) -> Dict[str, Any]:
        """
        Execute WeKnora search
        
        Args:
            query: Search query
            kb_id: Optional knowledge base ID
            top_k: Number of results to return
            
        Returns:
            Search results with sources
        """
        try:
            client = await self._get_client()
            kb_id = kb_id or self.default_kb_id
            
            logger.info(f"[WeKnora] Searching: {query[:50]}...")
            
            results = await client.hybrid_search(
                kb_id=kb_id,
                query=query,
                match_count=top_k,
            )
            
            # Format results for agent consumption
            formatted = []
            for i, chunk in enumerate(results):
                formatted.append({
                    "rank": i + 1,
                    "content": chunk.get("content", ""),
                    "title": chunk.get("knowledge_title", ""),
                    "source": chunk.get("knowledge_source", ""),
                    "score": chunk.get("score", 0),
                    "chunk_id": chunk.get("id", ""),
                })
            
            logger.info(f"[WeKnora] Found {len(formatted)} results")
            
            return {
                "success": True,
                "query": query,
                "kb_id": kb_id,
                "results": formatted,
                "count": len(formatted),
            }
            
        except Exception as e:
            logger.error(f"[WeKnora] Search failed: {e}")
            return {
                "success": False,
                "query": query,
                "error": str(e),
                "results": [],
            }
    
    async def health_check(self) -> Dict[str, Any]:
        """Check if WeKnora is available"""
        try:
            client = await self._get_client()
            return await client.health_check()
        except Exception as e:
            return {
                "status": "error",
                "error": str(e),
            }
    
    def get_tool_definition(self) -> Dict[str, Any]:
        """Get tool definition for agent registration"""
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
                        "description": "Optional knowledge base ID (uses default if not specified)",
                    },
                    "top_k": {
                        "type": "integer",
                        "description": "Number of results to return (default: 5)",
                        "default": 5,
                    },
                },
                "required": ["query"],
            },
        }


# Tool registry for NiruSense
_weknora_tool: Optional[WeKnoraTool] = None


def get_weknora_tool() -> WeKnoraTool:
    """Get or create WeKnora tool singleton"""
    global _weknora_tool
    if _weknora_tool is None:
        _weknora_tool = WeKnoraTool()
    return _weknora_tool


async def weknora_search(query: str, kb_id: Optional[str] = None, top_k: int = 5) -> Dict[str, Any]:
    """Quick search function for direct use"""
    tool = get_weknora_tool()
    return await tool.execute(query, kb_id, top_k)
