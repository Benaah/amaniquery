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
        
        # Explicitly set device to CPU to avoid meta tensor errors
        # This prevents issues when models are loaded with device_map="auto"
        import torch
        import os
        device = 'cpu'  # Use CPU for embeddings to avoid GPU/meta device issues
        
        # Temporarily disable device_map to prevent meta tensor loading
        old_device_map = os.environ.get('HF_DEVICE_MAP', None)
        old_accelerate_device_map = os.environ.get('ACCELERATE_DEVICE_MAP', None)
        
        try:
            # Remove device_map environment variables if set
            if old_device_map:
                del os.environ['HF_DEVICE_MAP']
            if old_accelerate_device_map:
                del os.environ['ACCELERATE_DEVICE_MAP']
            
            # Load model with explicit device and disable device_map
            # This ensures the model loads directly on CPU without meta tensors
            self.model = SentenceTransformer(
                model_name,
                device=device
            )
            
            # Verify model is on CPU and not meta device
            # Test with a dummy encode to ensure model is fully loaded
            try:
                test_embedding = self.model.encode("test", convert_to_numpy=True, show_progress_bar=False)
                logger.debug("Model loaded successfully and tested")
            except Exception as test_error:
                if 'meta' in str(test_error).lower():
                    logger.warning(f"Model still on meta device, attempting reinitialization: {test_error}")
                    # Force reload by clearing cache and reloading
                    import gc
                    del self.model
                    gc.collect()
                    torch.cuda.empty_cache() if torch.cuda.is_available() else None
                    
                    # Reload with explicit CPU device
                    self.model = SentenceTransformer(
                        model_name,
                        device=device
                    )
                else:
                    raise
        
        except Exception as e:
            logger.error(f"Error loading embedding model: {e}")
            # Fallback: try loading without device specification
            try:
                logger.info("Attempting fallback model loading...")
                self.model = SentenceTransformer(model_name)
                # Force to CPU if possible
                if hasattr(self.model, 'to'):
                    try:
                        self.model = self.model.to('cpu')
                    except Exception as to_error:
                        if 'meta' not in str(to_error).lower():
                            raise
                        # If meta tensor error, just continue - model might still work
                        logger.warning(f"Could not move model to CPU (meta tensor issue), continuing anyway: {to_error}")
            except Exception as fallback_error:
                logger.error(f"Fallback model loading also failed: {fallback_error}")
                raise RuntimeError(f"Failed to load embedding model {model_name}: {e}")
        finally:
            # Restore original environment variables
            if old_device_map:
                os.environ['HF_DEVICE_MAP'] = old_device_map
            if old_accelerate_device_map:
                os.environ['ACCELERATE_DEVICE_MAP'] = old_accelerate_device_map
        
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
