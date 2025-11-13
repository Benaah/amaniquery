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
        # Use query method with filter instead of direct collection access
        return self.vector_store.query("", n_results=limit, filter={"category": category})
    
    def filter_by_source(self, source_name: str, limit: int = 100) -> List[Dict]:
        """Get documents by source"""
        # Use query method with filter instead of direct collection access
        return self.vector_store.query("", n_results=limit, filter={"source_name": source_name})
    
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
        # Note: Date filtering requires backend-specific implementation
        # For now, return empty list as this needs backend-specific logic
        logger.warning("Date range filtering not implemented for current vector store backend")
        return []
    
    def get_categories(self) -> List[str]:
        """Get list of all unique categories"""
        try:
            # Use a sample query to get categories from any backend
            sample_docs = self.vector_store.query("", n_results=1000)
            categories = set()
            for doc in sample_docs:
                meta = doc.get("metadata", {})
                categories.add(meta.get("category", "Unknown"))
            
            return sorted(list(categories))
        except Exception as e:
            logger.error(f"Error getting categories: {e}")
            return ["Unknown"]
    
    def get_sources(self) -> List[str]:
        """Get list of all unique sources"""
        try:
            # Use a sample query to get sources from any backend
            sample_docs = self.vector_store.query("", n_results=1000)
            sources = set()
            for doc in sample_docs:
                meta = doc.get("metadata", {})
                sources.add(meta.get("source_name", "Unknown"))
            
            return sorted(list(sources))
        except Exception as e:
            logger.error(f"Error getting sources: {e}")
            return ["Unknown"]
    
    def get_citation(self, chunk_id: str) -> Optional[Dict]:
        """
        Get citation information for a chunk
        
        Args:
            chunk_id: Chunk identifier
        
        Returns:
            Citation dictionary
        """
        try:
            if hasattr(self.vector_store, 'collection') and self.vector_store.backend == "chromadb":
                # ChromaDB specific method
                result = self.vector_store.collection.get(
                    ids=[chunk_id],
                    include=["metadatas", "documents"]
                )
                
                if not result["ids"]:
                    return None
                
                meta = result["metadatas"][0]
            else:
                # For other backends, we can't easily get by ID
                # Return a basic citation or None
                logger.warning(f"get_citation not implemented for {self.vector_store.backend} backend")
                return None
            
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
