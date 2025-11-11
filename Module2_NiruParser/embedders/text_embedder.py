"""
Text Embedder using Sentence Transformers
"""
from typing import List, Dict
import numpy as np
from sentence_transformers import SentenceTransformer
from loguru import logger
from tqdm import tqdm


class TextEmbedder:
    """Generate vector embeddings for text"""
    
    def __init__(
        self,
        model_name: str = "all-MiniLM-L6-v2",
        batch_size: int = 32,
        normalize: bool = True,
    ):
        """
        Initialize embedder
        
        Args:
            model_name: Name of the Sentence Transformer model
            batch_size: Batch size for encoding
            normalize: Whether to normalize embeddings
        """
        self.model_name = model_name
        self.batch_size = batch_size
        self.normalize = normalize
        
        logger.info(f"Loading embedding model: {model_name}")
        self.model = SentenceTransformer(model_name)
        
        # Get embedding dimension
        self.dimension = self.model.get_sentence_embedding_dimension()
        logger.info(f"Embedding dimension: {self.dimension}")
    
    def embed(self, text: str) -> np.ndarray:
        """
        Generate embedding for single text
        
        Args:
            text: Text to embed
        
        Returns:
            Embedding vector
        """
        try:
            embedding = self.model.encode(
                text,
                normalize_embeddings=self.normalize,
                show_progress_bar=False,
            )
            return embedding
        except Exception as e:
            logger.error(f"Error generating embedding: {e}")
            return np.zeros(self.dimension)
    
    def embed_batch(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for batch of texts
        
        Args:
            texts: List of texts to embed
        
        Returns:
            Array of embeddings
        """
        try:
            embeddings = self.model.encode(
                texts,
                batch_size=self.batch_size,
                normalize_embeddings=self.normalize,
                show_progress_bar=True,
            )
            return embeddings
        except Exception as e:
            logger.error(f"Error generating batch embeddings: {e}")
            return np.zeros((len(texts), self.dimension))
    
    def embed_chunks(self, chunks: List[Dict]) -> List[Dict]:
        """
        Add embeddings to chunk dictionaries
        
        Args:
            chunks: List of chunk dictionaries with 'text' field
        
        Returns:
            Chunks with added 'embedding' field
        """
        if not chunks:
            return []
        
        logger.info(f"Generating embeddings for {len(chunks)} chunks")
        
        # Extract texts
        texts = [chunk.get("text", "") for chunk in chunks]
        
        # Generate embeddings
        embeddings = self.embed_batch(texts)
        
        # Add to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk["embedding"] = embedding.tolist()  # Convert to list for JSON serialization
        
        logger.info("Embeddings generated successfully")
        return chunks
    
    def get_model_info(self) -> Dict:
        """Get information about the embedding model"""
        return {
            "model_name": self.model_name,
            "dimension": self.dimension,
            "max_seq_length": self.model.max_seq_length,
            "normalize": self.normalize,
        }
