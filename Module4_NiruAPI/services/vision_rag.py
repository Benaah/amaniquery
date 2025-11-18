"""
Vision RAG Service - Multimodal RAG using Cohere Embed-4 and Gemini 2.5 Flash
"""
import os
from typing import List, Dict, Optional, Union
from pathlib import Path
import numpy as np
from loguru import logger
from PIL import Image
import tempfile
import base64
import io

from Module2_NiruParser.embedders.vision_embedder import VisionEmbedder
from Module4_NiruAPI.services.pdf_page_extractor import PDFPageExtractor

try:
    import google.generativeai as genai
    GEMINI_AVAILABLE = True
except ImportError:
    GEMINI_AVAILABLE = False
    logger.warning("google-generativeai not available. Install with: pip install google-generativeai")


class VisionRAGService:
    """Vision RAG service for multimodal search and visual question answering"""
    
    def __init__(
        self,
        cohere_api_key: Optional[str] = None,
        gemini_api_key: Optional[str] = None,
        vision_embedder: Optional[VisionEmbedder] = None,
    ):
        """
        Initialize Vision RAG service
        
        Args:
            cohere_api_key: Cohere API key (if None, reads from COHERE_API_KEY env var)
            gemini_api_key: Gemini API key (if None, reads from GEMINI_API_KEY env var)
            vision_embedder: Optional pre-initialized VisionEmbedder
        """
        # Initialize vision embedder
        if vision_embedder:
            self.vision_embedder = vision_embedder
        else:
            self.vision_embedder = VisionEmbedder(api_key=cohere_api_key)
        
        # Initialize Gemini for VQA
        if not GEMINI_AVAILABLE:
            raise ImportError("google-generativeai not available. Install with: pip install google-generativeai")
        
        gemini_key = gemini_api_key or os.getenv("GEMINI_API_KEY")
        if not gemini_key:
            raise ValueError("GEMINI_API_KEY not set in environment or provided")
        
        genai.configure(api_key=gemini_key)
        self.gemini_model = genai.GenerativeModel("gemini-2.5-flash")  # Use Gemini 2.5 Flash
        
        logger.info("Vision RAG service initialized")
    
    def _cosine_similarity(self, vec1: np.ndarray, vec2: np.ndarray) -> float:
        """Calculate cosine similarity between two vectors"""
        dot_product = np.dot(vec1, vec2)
        norm1 = np.linalg.norm(vec1)
        norm2 = np.linalg.norm(vec2)
        
        if norm1 == 0 or norm2 == 0:
            return 0.0
        
        return float(dot_product / (norm1 * norm2))
    
    def search_images(
        self,
        query_text: str,
        image_embeddings: List[np.ndarray],
        image_metadata: List[Dict],
        top_k: int = 3,
    ) -> List[Dict]:
        """
        Search for most relevant images using text query
        
        Args:
            query_text: Text query/question
            image_embeddings: List of image embeddings
            image_metadata: List of metadata dicts for each image
            top_k: Number of top results to return
            
        Returns:
            List of dicts with image info and similarity scores, sorted by relevance
        """
        try:
            # Embed the text query
            query_embedding = self.vision_embedder.embed_text(query_text)
            
            # Calculate similarities
            results = []
            for i, (img_emb, metadata) in enumerate(zip(image_embeddings, image_metadata)):
                similarity = self._cosine_similarity(query_embedding, img_emb)
                results.append({
                    "index": i,
                    "metadata": metadata,
                    "similarity": similarity,
                })
            
            # Sort by similarity (descending)
            results.sort(key=lambda x: x["similarity"], reverse=True)
            
            # Return top_k results
            top_results = results[:top_k]
            
            logger.info(f"Found {len(top_results)} relevant images for query: {query_text[:50]}...")
            return top_results
            
        except Exception as e:
            logger.error(f"Error searching images: {e}")
            return []
    
    def answer_visual_question(
        self,
        question: str,
        image_paths: List[Union[str, Path]],
        temperature: float = 0.7,
        max_tokens: int = 1500,
    ) -> str:
        """
        Answer a question about one or more images using Gemini
        
        Args:
            question: Question to ask about the images
            image_paths: List of paths to images to analyze
            temperature: Generation temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            Answer text
        """
        try:
            # Prepare images for Gemini
            image_parts = []
            for img_path in image_paths:
                img_path = Path(img_path)
                if not img_path.exists():
                    logger.warning(f"Image not found: {img_path}")
                    continue
                
                # Read and encode image
                with open(img_path, "rb") as f:
                    image_data = f.read()
                
                image_part = {
                    "mime_type": "image/jpeg" if img_path.suffix.lower() in [".jpg", ".jpeg"] else "image/png",
                    "data": image_data,
                }
                image_parts.append(image_part)
            
            if not image_parts:
                return "No valid images provided for analysis."
            
            # Prepare prompt
            prompt = f"""Analyze the provided image(s) and answer the following question:

Question: {question}

Provide a detailed, accurate answer based on what you see in the image(s). If the question cannot be answered from the images, please state that clearly."""
            
            # Generate response with Gemini
            response = self.gemini_model.generate_content(
                [prompt] + image_parts,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                )
            )
            
            answer = response.text
            logger.info(f"Generated visual answer (length: {len(answer)})")
            return answer
            
        except Exception as e:
            logger.error(f"Error generating visual answer: {e}")
            return f"I encountered an error while analyzing the images: {str(e)}"
    
    def answer_visual_question_stream(
        self,
        question: str,
        image_paths: List[Union[str, Path]],
        temperature: float = 0.7,
        max_tokens: int = 1500,
    ):
        """
        Answer a question about one or more images using Gemini with streaming
        
        Args:
            question: Question to ask about the images
            image_paths: List of paths to images to analyze
            temperature: Generation temperature
            max_tokens: Maximum tokens in response
            
        Yields:
            Text chunks as they are generated
        """
        try:
            # Prepare images for Gemini
            image_parts = []
            for img_path in image_paths:
                img_path = Path(img_path)
                if not img_path.exists():
                    logger.warning(f"Image not found: {img_path}")
                    continue
                
                # Read and encode image
                with open(img_path, "rb") as f:
                    image_data = f.read()
                
                image_part = {
                    "mime_type": "image/jpeg" if img_path.suffix.lower() in [".jpg", ".jpeg"] else "image/png",
                    "data": image_data,
                }
                image_parts.append(image_part)
            
            if not image_parts:
                yield "No valid images provided for analysis."
                return
            
            # Prepare prompt
            prompt = f"""Analyze the provided image(s) and answer the following question:

Question: {question}

Provide a detailed, accurate answer based on what you see in the image(s). If the question cannot be answered from the images, please state that clearly."""
            
            # Generate streaming response with Gemini
            response = self.gemini_model.generate_content(
                [prompt] + image_parts,
                generation_config=genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                ),
                stream=True,  # Enable streaming
            )
            
            # Yield chunks as they arrive
            for chunk in response:
                if chunk.text:
                    yield chunk.text
            
        except Exception as e:
            logger.error(f"Error generating streaming visual answer: {e}")
            yield f"I encountered an error while analyzing the images: {str(e)}"
    
    def query(
        self,
        question: str,
        session_images: List[Dict],
        top_k: int = 3,
        temperature: float = 0.7,
        max_tokens: int = 1500,
        stream: bool = False,
    ) -> Dict:
        """
        Complete Vision RAG query: search for relevant images and answer question
        
        Args:
            question: User's question
            session_images: List of dicts with keys: {id, file_path, embedding, metadata}
            top_k: Number of images to retrieve
            temperature: Generation temperature
            max_tokens: Maximum tokens in response
            
        Returns:
            Dict with answer, sources (images), and metadata
        """
        if not session_images:
            return {
                "answer": "No images available in this session. Please upload images or PDFs first.",
                "sources": [],
                "query_time": 0.0,
                "retrieved_images": 0,
            }
        
        import time
        start_time = time.time()
        
        try:
            # Extract embeddings and metadata
            image_embeddings = []
            image_metadata = []
            
            for img_data in session_images:
                # Convert embedding to numpy array if it's a list
                embedding = img_data.get("embedding")
                if isinstance(embedding, list):
                    embedding = np.array(embedding)
                elif not isinstance(embedding, np.ndarray):
                    logger.warning(f"Invalid embedding type for image {img_data.get('id')}")
                    continue
                
                image_embeddings.append(embedding)
                image_metadata.append(img_data.get("metadata", {}))
            
            if not image_embeddings:
                return {
                    "answer": "No valid image embeddings found. Please re-upload your images.",
                    "sources": [],
                    "query_time": time.time() - start_time,
                    "retrieved_images": 0,
                }
            
            # Search for relevant images
            search_results = self.search_images(
                query_text=question,
                image_embeddings=image_embeddings,
                image_metadata=image_metadata,
                top_k=top_k,
            )
            
            if not search_results:
                return {
                    "answer": "I couldn't find any relevant images for your question.",
                    "sources": [],
                    "query_time": time.time() - start_time,
                    "retrieved_images": 0,
                }
            
            # Get paths to top images
            top_image_paths = []
            top_image_metadata = []
            
            for result in search_results:
                idx = result["index"]
                img_data = session_images[idx]
                file_path = img_data.get("file_path")
                
                if file_path and Path(file_path).exists():
                    top_image_paths.append(file_path)
                    top_image_metadata.append({
                        **img_data.get("metadata", {}),
                        "similarity": result["similarity"],
                    })
            
            # Generate answer using Gemini (streaming or non-streaming)
            if stream:
                # Return streaming generator
                answer_stream = self.answer_visual_question_stream(
                    question=question,
                    image_paths=top_image_paths,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                
                # Format sources
                sources = []
                for meta in top_image_metadata:
                    sources.append({
                        "file_path": meta.get("file_path", ""),
                        "filename": meta.get("filename", ""),
                        "page_number": meta.get("page_number"),
                        "source_file": meta.get("source_file", ""),
                        "similarity": meta.get("similarity", 0.0),
                    })
                
                return {
                    "answer_stream": answer_stream,
                    "sources": sources,
                    "query_time": 0.0,  # Will be calculated after streaming
                    "retrieved_images": len(top_image_paths),
                    "model_used": "gemini-2.5-flash",
                    "stream": True,
                }
            else:
                # Non-streaming
                answer = self.answer_visual_question(
                    question=question,
                    image_paths=top_image_paths,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                
                query_time = time.time() - start_time
                
                # Format sources
                sources = []
                for meta in top_image_metadata:
                    sources.append({
                        "file_path": meta.get("file_path", ""),
                        "filename": meta.get("filename", ""),
                        "page_number": meta.get("page_number"),
                        "source_file": meta.get("source_file", ""),
                        "similarity": meta.get("similarity", 0.0),
                    })
                
                return {
                    "answer": answer,
                    "sources": sources,
                    "query_time": query_time,
                    "retrieved_images": len(top_image_paths),
                    "model_used": "gemini-2.5-flash",
                }
            
        except Exception as e:
            logger.error(f"Error in Vision RAG query: {e}")
            return {
                "answer": f"I encountered an error while processing your question: {str(e)}",
                "sources": [],
                "query_time": time.time() - start_time,
                "retrieved_images": 0,
            }

