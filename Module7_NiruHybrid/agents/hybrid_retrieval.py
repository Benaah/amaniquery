"""
Hybrid Retrieval for Hybrid Module
BM25 + embeddings, reranking, summary chunking
"""
from typing import List, Dict, Any, Optional
from loguru import logger

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from Module4_NiruAPI.agents.discovery.hybrid_search import HybridSearch
from Module4_NiruAPI.agents.discovery.rag_retriever import RAGRetriever
from Module3_NiruDB.vector_store import VectorStore


class HybridRetrieval:
    """
    Enhanced hybrid retrieval for hybrid module
    Combines BM25 + embeddings with reranking and summary chunking
    """
    
    def __init__(self, vector_store: Optional[VectorStore] = None):
        """
        Initialize hybrid retrieval
        
        Args:
            vector_store: Vector store instance
        """
        self.vector_store = vector_store or VectorStore()
        self.hybrid_search = HybridSearch(vector_store=vector_store)
        self.rag_retriever = RAGRetriever(vector_store=vector_store)
    
    def retrieve(
        self,
        query: str,
        top_k: int = 5,
        use_reranking: bool = True,
        use_summary_chunking: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Retrieve documents with hybrid search and enhancements
        
        Args:
            query: Search query
            top_k: Number of results
            use_reranking: Whether to rerank results
            use_summary_chunking: Whether to use summary chunking
            
        Returns:
            Retrieved documents
        """
        # Use RAG retriever which includes hybrid search
        results = self.rag_retriever.retrieve(
            query=query,
            top_k=top_k * 2,  # Get more for reranking
            use_hybrid=True,
            use_expansion=True,
            rerank=use_reranking
        )
        
        # Apply summary chunking if requested
        if use_summary_chunking:
            results = self._apply_summary_chunking(results)
        
        return results[:top_k]
    
    def _apply_summary_chunking(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Apply summary chunking to results
        
        Args:
            results: Search results
            
        Returns:
            Results with summary chunks
        """
        for result in results:
            content = result.get('content', '')
            if len(content) > 1000:
                # Create summary chunk (first 500 chars + last 200 chars)
                summary = content[:500] + "..." + content[-200:]
                result['summary_chunk'] = summary
            else:
                result['summary_chunk'] = content
        
        return results
    
    def retrieve_with_filters(
        self,
        query: str,
        filters: Dict[str, Any],
        top_k: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Retrieve with metadata filters
        
        Args:
            query: Search query
            filters: Metadata filters
            top_k: Number of results
            
        Returns:
            Filtered results
        """
        # Get results
        results = self.retrieve(query, top_k=top_k * 2)
        
        # Apply filters
        filtered = []
        for result in results:
            metadata = result.get('metadata', {})
            match = True
            
            for key, value in filters.items():
                if metadata.get(key) != value:
                    match = False
                    break
            
            if match:
                filtered.append(result)
        
        return filtered[:top_k]

