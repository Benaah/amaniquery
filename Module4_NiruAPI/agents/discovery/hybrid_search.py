"""
Hybrid Search - Combines BM25 (keyword) and embeddings (semantic) search
"""
from typing import List, Dict, Any, Optional
from loguru import logger

try:
    from rank_bm25 import BM25Okapi
except ImportError:
    BM25Okapi = None
    logger.warning("rank-bm25 not installed. Install with: pip install rank-bm25")

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from Module3_NiruDB.vector_store import VectorStore


class HybridSearch:
    """
    Hybrid search combining BM25 (keyword) and vector (semantic) search
    """
    
    def __init__(self, vector_store: Optional[VectorStore] = None):
        """
        Initialize hybrid search
        
        Args:
            vector_store: Vector store for semantic search
        """
        self.vector_store = vector_store or VectorStore()
        self.bm25_index = None
        self.documents = []
        
        if BM25Okapi is None:
            logger.warning("BM25 search will not be available")
    
    def build_bm25_index(self, documents: List[str]):
        """
        Build BM25 index from documents
        
        Args:
            documents: List of document texts
        """
        if BM25Okapi is None:
            return
        
        try:
            # Tokenize documents
            tokenized_docs = [doc.lower().split() for doc in documents]
            
            # Build BM25 index
            self.bm25_index = BM25Okapi(tokenized_docs)
            self.documents = documents
            
            logger.info(f"Built BM25 index for {len(documents)} documents")
        except Exception as e:
            logger.error(f"Error building BM25 index: {e}")
    
    def search(
        self,
        query: str,
        top_k: int = 10,
        bm25_weight: float = 0.4,
        vector_weight: float = 0.6
    ) -> List[Dict[str, Any]]:
        """
        Perform hybrid search
        
        Args:
            query: Search query
            top_k: Number of results to return
            bm25_weight: Weight for BM25 scores (0-1)
            vector_weight: Weight for vector scores (0-1)
            
        Returns:
            List of search results with combined scores
        """
        results = []
        
        # Vector search
        try:
            vector_results = self.vector_store.search(query, top_k=top_k * 2)
        except Exception as e:
            logger.error(f"Error in vector search: {e}")
            vector_results = []
        
        # BM25 search
        bm25_results = []
        if self.bm25_index and BM25Okapi is not None:
            try:
                tokenized_query = query.lower().split()
                bm25_scores = self.bm25_index.get_scores(tokenized_query)
                
                # Get top BM25 results
                top_indices = sorted(
                    range(len(bm25_scores)),
                    key=lambda i: bm25_scores[i],
                    reverse=True
                )[:top_k * 2]
                
                for idx in top_indices:
                    bm25_results.append({
                        'content': self.documents[idx],
                        'score': float(bm25_scores[idx]),
                        'index': idx
                    })
            except Exception as e:
                logger.error(f"Error in BM25 search: {e}")
        
        # Combine results
        combined = {}
        
        # Add vector results
        for i, result in enumerate(vector_results):
            content = result.get('content', '')
            if content:
                if content not in combined:
                    combined[content] = {
                        'content': content,
                        'vector_score': result.get('score', 0.0),
                        'bm25_score': 0.0,
                        'metadata': result.get('metadata', {})
                    }
                else:
                    combined[content]['vector_score'] = result.get('score', 0.0)
        
        # Add BM25 results
        for result in bm25_results:
            content = result.get('content', '')
            if content:
                if content not in combined:
                    combined[content] = {
                        'content': content,
                        'vector_score': 0.0,
                        'bm25_score': result.get('score', 0.0),
                        'metadata': {}
                    }
                else:
                    combined[content]['bm25_score'] = result.get('score', 0.0)
        
        # Calculate combined scores
        for item in combined.values():
            # Normalize scores (assuming they're in similar ranges)
            vector_norm = item['vector_score']
            bm25_norm = item['bm25_score'] / 10.0 if item['bm25_score'] > 0 else 0  # Rough normalization
            
            # Weighted combination
            item['combined_score'] = (
                vector_norm * vector_weight +
                bm25_norm * bm25_weight
            )
        
        # Sort by combined score
        sorted_results = sorted(
            combined.values(),
            key=lambda x: x['combined_score'],
            reverse=True
        )[:top_k]
        
        return sorted_results

