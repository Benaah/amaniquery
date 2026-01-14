import time
import json
import hashlib
import numpy as np
from typing import Dict, Optional, List, Any
from loguru import logger
from sklearn.metrics.pairwise import cosine_similarity

class SemanticCache:
    """
    Semantic Cache for RAG Pipeline.
    Uses cosine similarity to find cached responses for similar queries.
    """
    
    def __init__(self, threshold: float = 0.9, max_size: int = 1000):
        self.cache: List[Dict[str, Any]] = []
        self.threshold = threshold
        self.max_size = max_size
        self.embedding_model = None

    def set_embedding_model(self, model):
        """Set the embedding model to be used for query encoding"""
        self.embedding_model = model

    def _get_embedding(self, text: str) -> Optional[np.ndarray]:
        """Generate embedding for text using the vector store's model"""
        if not self.embedding_model:
            return None
        try:
            # Assume model has encode method (SentenceTransformer)
            embedding = self.embedding_model.encode(text)
            if isinstance(embedding, list):
                return np.array(embedding)
            return embedding
        except Exception as e:
            logger.warning(f"Failed to generate embedding for cache: {e}")
            return None

    def get(self, query: str, top_k: int = 5, category: Optional[str] = None) -> Optional[Dict]:
        """Retrieve cached result if semantically similar query exists"""
        if not self.embedding_model:
            return None

        query_embedding = self._get_embedding(query)
        if query_embedding is None:
            return None

        best_score = -1
        best_entry = None

        # Iterate through cache (could be optimized with FAISS/VectorDB for large cache)
        # For < 1000 items, linear scan is fast enough (~1-2ms)
        for entry in self.cache:
            # Check filters first
            if entry.get("top_k") != top_k:
                continue
            if category and entry.get("category") != category:
                continue

            # Calculate similarity
            score = cosine_similarity(
                query_embedding.reshape(1, -1), 
                entry["embedding"].reshape(1, -1)
            )[0][0]

            if score > best_score:
                best_score = score
                best_entry = entry

        if best_score >= self.threshold:
            logger.info(f"Semantic cache hit! Score: {best_score:.4f} for query: '{query}'")
            return best_entry["result"]
        
        return None

    def set(self, query: str, result: Dict, top_k: int = 5, category: Optional[str] = None):
        """Cache the result for a query"""
        if not self.embedding_model:
            return

        query_embedding = self._get_embedding(query)
        if query_embedding is None:
            return

        # Evict if full (Simple LRU - remove first)
        if len(self.cache) >= self.max_size:
            self.cache.pop(0)

        entry = {
            "query": query,
            "embedding": query_embedding,
            "result": result,
            "top_k": top_k,
            "category": category,
            "timestamp": time.time()
        }
        self.cache.append(entry)
