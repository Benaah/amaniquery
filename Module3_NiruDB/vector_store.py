"""
Vector Store using ChromaDB
"""
import os
from pathlib import Path
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from loguru import logger
from sentence_transformers import SentenceTransformer


class VectorStore:
    """Manage vector embeddings with ChromaDB"""
    
    def __init__(
        self,
        persist_directory: Optional[str] = None,
        collection_name: str = "amaniquery_docs",
        embedding_model: str = "all-MiniLM-L6-v2",
    ):
        """
        Initialize vector store
        
        Args:
            persist_directory: Directory to persist database
            collection_name: Name of the collection
            embedding_model: Sentence transformer model name
        """
        if persist_directory is None:
            persist_directory = str(Path(__file__).parent.parent / "data" / "chroma_db")
        
        self.persist_directory = persist_directory
        self.collection_name = collection_name
        
        # Initialize ChromaDB client
        logger.info(f"Initializing ChromaDB at {persist_directory}")
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            )
        )
        
        # Load embedding model for queries
        logger.info(f"Loading embedding model: {embedding_model}")
        self.embedding_model = SentenceTransformer(embedding_model)
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"description": "AmaniQuery document embeddings"}
        )
        
        logger.info(f"Collection '{collection_name}' ready with {self.collection.count()} documents")
    
    def add_documents(self, chunks: List[Dict], batch_size: int = 100):
        """
        Add document chunks to vector store
        
        Args:
            chunks: List of chunk dictionaries with embeddings
            batch_size: Number of chunks to add at once
        """
        if not chunks:
            logger.warning("No chunks to add")
            return
        
        logger.info(f"Adding {len(chunks)} chunks to vector store")
        
        # Process in batches
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            
            # Prepare data
            ids = [chunk["chunk_id"] for chunk in batch]
            embeddings = [chunk["embedding"] for chunk in batch]
            documents = [chunk["text"] for chunk in batch]
            
            # Prepare metadata (ChromaDB requires all values to be simple types)
            metadatas = []
            for chunk in batch:
                metadata = {
                    "title": str(chunk.get("title", "")),
                    "category": str(chunk.get("category", "")),
                    "source_url": str(chunk.get("source_url", "")),
                    "source_name": str(chunk.get("source_name", "")),
                    "chunk_index": int(chunk.get("chunk_index", 0)),
                    "total_chunks": int(chunk.get("total_chunks", 1)),
                }
                
                # Add optional fields if available
                if chunk.get("author"):
                    metadata["author"] = str(chunk["author"])
                if chunk.get("publication_date"):
                    metadata["publication_date"] = str(chunk["publication_date"])
                if chunk.get("keywords"):
                    metadata["keywords"] = str(chunk["keywords"])
                
                metadatas.append(metadata)
            
            # Add to collection
            try:
                self.collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas,
                )
                logger.info(f"Added batch {i // batch_size + 1} ({len(batch)} chunks)")
            except Exception as e:
                logger.error(f"Error adding batch: {e}")
        
        logger.info(f"Total documents in collection: {self.collection.count()}")
    
    def query(
        self,
        query_text: str,
        n_results: int = 5,
        filter: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Query vector store for similar documents
        
        Args:
            query_text: Query string
            n_results: Number of results to return
            filter: Metadata filter (e.g., {"category": "Parliament"})
        
        Returns:
            List of similar documents with metadata
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query_text).tolist()
            
            # Query collection
            results = self.collection.query(
                query_embeddings=[query_embedding],
                n_results=n_results,
                where=filter,
            )
            
            # Format results
            formatted_results = []
            for i in range(len(results["ids"][0])):
                formatted_results.append({
                    "id": results["ids"][0][i],
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "distance": results["distances"][0][i] if "distances" in results else None,
                })
            
            logger.info(f"Query returned {len(formatted_results)} results")
            return formatted_results
            
        except Exception as e:
            logger.error(f"Error querying vector store: {e}")
            return []
    
    def delete_collection(self):
        """Delete the entire collection"""
        self.client.delete_collection(self.collection_name)
        logger.info(f"Deleted collection: {self.collection_name}")
    
    def get_stats(self) -> Dict:
        """Get collection statistics"""
        count = self.collection.count()
        
        # Get sample to analyze categories
        sample = self.collection.get(limit=1000)
        categories = {}
        
        if sample["metadatas"]:
            for meta in sample["metadatas"]:
                cat = meta.get("category", "Unknown")
                categories[cat] = categories.get(cat, 0) + 1
        
        return {
            "total_chunks": count,
            "collection_name": self.collection_name,
            "persist_directory": self.persist_directory,
            "sample_categories": categories,
        }
