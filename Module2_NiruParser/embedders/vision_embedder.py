"""
Vision Embedder using Cohere Embed-4 for multimodal embeddings
"""
import os
from typing import List, Union, Optional
import numpy as np
from pathlib import Path
from loguru import logger
from PIL import Image
import base64
import io

try:
    import cohere
    COHERE_AVAILABLE = True
except ImportError:
    COHERE_AVAILABLE = False
    logger.warning("Cohere package not available. Install with: pip install cohere")


class VisionEmbedder:
    """Generate multimodal embeddings using Cohere Embed-4 API"""
    
    def __init__(
        self,
        api_key: Optional[str] = None,
        model: str = "embed-english-v4.0",  # Cohere Embed-4 model name
    ):
        """
        Initialize vision embedder
        
        Args:
            api_key: Cohere API key (if None, reads from COHERE_API_KEY env var)
            model: Cohere model name (default: embed-english-v3.0, but Embed-4 is embed-multilingual-v3.0 or embed-english-v3.0)
        """
        if not COHERE_AVAILABLE:
            raise ImportError("Cohere package not available. Install with: pip install cohere")
        
        self.api_key = api_key or os.getenv("COHERE_API_KEY")
        if not self.api_key:
            raise ValueError("COHERE_API_KEY not set in environment or provided")
        
        self.model = model
        self.client = cohere.Client(api_key=self.api_key)
        
        # Embed-4 dimension is 1024
        self.dimension = 1024
        
        logger.info(f"Vision embedder initialized with model: {model}")
    
    def _image_to_base64(self, image: Union[str, Path, Image.Image]) -> str:
        """
        Convert image to base64 string for API
        
        Args:
            image: Image path (str/Path) or PIL Image object
            
        Returns:
            Base64 encoded image string
        """
        if isinstance(image, (str, Path)):
            image_path = Path(image)
            if not image_path.exists():
                raise FileNotFoundError(f"Image not found: {image_path}")
            img = Image.open(image_path)
        elif isinstance(image, Image.Image):
            img = image
        else:
            raise ValueError(f"Unsupported image type: {type(image)}")
        
        # Convert to RGB if needed
        if img.mode != "RGB":
            img = img.convert("RGB")
        
        # Convert to base64
        buffered = io.BytesIO()
        img.save(buffered, format="JPEG", quality=85)
        img_base64 = base64.b64encode(buffered.getvalue()).decode("utf-8")
        
        return img_base64
    
    def embed_text(self, text: str) -> np.ndarray:
        """
        Generate embedding for text query
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector as numpy array
        """
        try:
            response = self.client.embed(
                texts=[text],
                model=self.model,
                input_type="search_query",  # For query embeddings
            )
            
            embedding = np.array(response.embeddings[0])
            return embedding
        except Exception as e:
            logger.error(f"Error generating text embedding: {e}")
            return np.zeros(self.dimension)
    
    def embed_image(self, image: Union[str, Path, Image.Image]) -> np.ndarray:
        """
        Generate embedding for image
        
        Args:
            image: Image path (str/Path) or PIL Image object
            
        Returns:
            Embedding vector as numpy array
        """
        try:
            # Get image bytes
            if isinstance(image, (str, Path)):
                image_path = Path(image)
                if not image_path.exists():
                    raise FileNotFoundError(f"Image not found: {image_path}")
                with open(image_path, "rb") as f:
                    image_bytes = f.read()
            elif isinstance(image, Image.Image):
                # Convert PIL Image to bytes
                buffered = io.BytesIO()
                if image.mode != "RGB":
                    image = image.convert("RGB")
                image.save(buffered, format="JPEG", quality=85)
                image_bytes = buffered.getvalue()
            else:
                raise ValueError(f"Unsupported image type: {type(image)}")
            
            # Use Cohere Embed-4 multimodal embedding
            # Cohere Embed-4 accepts images as bytes
            response = self.client.embed(
                images=[image_bytes],
                model=self.model,
                input_type="search_document",  # For document/image embeddings
            )
            
            embedding = np.array(response.embeddings[0])
            return embedding
        except Exception as e:
            logger.error(f"Error generating image embedding: {e}")
            return np.zeros(self.dimension)
    
    def embed_images_batch(self, images: List[Union[str, Path, Image.Image]]) -> np.ndarray:
        """
        Generate embeddings for batch of images
        
        Args:
            images: List of image paths or PIL Image objects
            
        Returns:
            Array of embeddings
        """
        if not images:
            return np.array([])
        
        try:
            # Convert all images to bytes
            image_bytes_list = []
            for img in images:
                if isinstance(img, (str, Path)):
                    image_path = Path(img)
                    with open(image_path, "rb") as f:
                        image_bytes_list.append(f.read())
                elif isinstance(img, Image.Image):
                    buffered = io.BytesIO()
                    if img.mode != "RGB":
                        img = img.convert("RGB")
                    img.save(buffered, format="JPEG", quality=85)
                    image_bytes_list.append(buffered.getvalue())
                else:
                    raise ValueError(f"Unsupported image type: {type(img)}")
            
            # Batch embed
            response = self.client.embed(
                images=image_bytes_list,
                model=self.model,
                input_type="search_document",
            )
            
            embeddings = np.array(response.embeddings)
            return embeddings
        except Exception as e:
            logger.error(f"Error generating batch image embeddings: {e}")
            return np.zeros((len(images), self.dimension))
    
    def embed_text_batch(self, texts: List[str]) -> np.ndarray:
        """
        Generate embeddings for batch of texts
        
        Args:
            texts: List of texts to embed
            
        Returns:
            Array of embeddings
        """
        if not texts:
            return np.array([])
        
        try:
            response = self.client.embed(
                texts=texts,
                model=self.model,
                input_type="search_query",
            )
            
            embeddings = np.array(response.embeddings)
            return embeddings
        except Exception as e:
            logger.error(f"Error generating batch text embeddings: {e}")
            return np.zeros((len(texts), self.dimension))
    
    def get_model_info(self) -> dict:
        """Get information about the embedding model"""
        return {
            "model_name": self.model,
            "dimension": self.dimension,
            "provider": "cohere",
            "multimodal": True,
        }

