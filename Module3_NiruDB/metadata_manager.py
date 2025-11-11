"""
Metadata Manager - Query and manage document metadata
"""
from typing import List, Dict, Optional
from datetime import datetime
from loguru import logger


class MetadataManager:
    """Manage and query document metadata"""
    
    def __init__(self, vector_store):
        """
        Initialize metadata manager
        
        Args:
            vector_store: VectorStore instance
        """
        self.vector_store = vector_store
    
    def filter_by_category(self, category: str, limit: int = 100) -> List[Dict]:
        """Get documents by category"""
        return self.vector_store.collection.get(
            where={"category": category},
            limit=limit,
        )
    
    def filter_by_source(self, source_name: str, limit: int = 100) -> List[Dict]:
        """Get documents by source"""
        return self.vector_store.collection.get(
            where={"source_name": source_name},
            limit=limit,
        )
    
    def filter_by_date_range(
        self,
        start_date: str,
        end_date: str,
        limit: int = 100
    ) -> List[Dict]:
        """
        Get documents within date range
        
        Args:
            start_date: ISO format date string
            end_date: ISO format date string
            limit: Maximum results
        """
        # Note: ChromaDB date filtering requires the dates to be stored as strings
        # This is a simple implementation - can be enhanced
        return self.vector_store.collection.get(
            where={
                "$and": [
                    {"publication_date": {"$gte": start_date}},
                    {"publication_date": {"$lte": end_date}},
                ]
            },
            limit=limit,
        )
    
    def get_categories(self) -> List[str]:
        """Get list of all unique categories"""
        # Get all documents (or large sample)
        docs = self.vector_store.collection.get(limit=10000)
        
        categories = set()
        for meta in docs["metadatas"]:
            categories.add(meta.get("category", "Unknown"))
        
        return sorted(list(categories))
    
    def get_sources(self) -> List[str]:
        """Get list of all unique sources"""
        docs = self.vector_store.collection.get(limit=10000)
        
        sources = set()
        for meta in docs["metadatas"]:
            sources.add(meta.get("source_name", "Unknown"))
        
        return sorted(list(sources))
    
    def get_citation(self, chunk_id: str) -> Optional[Dict]:
        """
        Get citation information for a chunk
        
        Args:
            chunk_id: Chunk identifier
        
        Returns:
            Citation dictionary
        """
        try:
            result = self.vector_store.collection.get(
                ids=[chunk_id],
                include=["metadatas", "documents"]
            )
            
            if not result["ids"]:
                return None
            
            meta = result["metadatas"][0]
            
            citation = {
                "title": meta.get("title", "Untitled"),
                "source_url": meta.get("source_url", ""),
                "source_name": meta.get("source_name", "Unknown"),
                "author": meta.get("author", ""),
                "publication_date": meta.get("publication_date", ""),
                "category": meta.get("category", ""),
            }
            
            return citation
            
        except Exception as e:
            logger.error(f"Error getting citation: {e}")
            return None
    
    def format_citation(self, citation: Dict) -> str:
        """Format citation as a string"""
        parts = []
        
        if citation.get("author"):
            parts.append(citation["author"])
        
        parts.append(f'"{citation["title"]}"')
        parts.append(citation["source_name"])
        
        if citation.get("publication_date"):
            parts.append(citation["publication_date"][:10])  # Just date part
        
        parts.append(citation["source_url"])
        
        return ". ".join(parts)
