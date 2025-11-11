"""
RAG Pipeline - Retrieval-Augmented Generation
"""
import os
from typing import List, Dict, Optional
import time
from loguru import logger
from openai import OpenAI
from anthropic import Anthropic
from dotenv import load_dotenv

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from Module3_NiruDB.vector_store import VectorStore
from Module3_NiruDB.metadata_manager import MetadataManager


class RAGPipeline:
    """RAG pipeline for question answering with citations"""
    
    def __init__(
        self,
        vector_store: Optional[VectorStore] = None,
        llm_provider: str = "moonshot",
        model: str = "moonshot-v1-8k",
    ):
        """
        Initialize RAG pipeline
        
        Args:
            vector_store: VectorStore instance (creates new if None)
            llm_provider: LLM provider (openai, anthropic, moonshot, local)
            model: Model name to use
        """
        # Load environment variables
        load_dotenv()
        
        # Initialize vector store
        self.vector_store = vector_store or VectorStore()
        self.metadata_manager = MetadataManager(self.vector_store)
        
        # Initialize LLM
        self.llm_provider = llm_provider
        self.model = model
        
        if llm_provider == "openai":
            api_key = os.getenv("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set in environment")
            self.client = OpenAI(api_key=api_key)
        elif llm_provider == "anthropic":
            api_key = os.getenv("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not set in environment")
            self.client = Anthropic(api_key=api_key)
        elif llm_provider == "gemini":
            api_key = os.getenv("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY not set in environment")
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                self.client = genai.GenerativeModel(self.model)
                logger.info("Using Google Gemini AI")
                
                # Test the connection
                test_response = self.client.generate_content("test")
                logger.info("Gemini AI connection test successful")
                
            except ImportError:
                raise ValueError("google-generativeai package not installed. Install with: pip install google-generativeai")
            except Exception as e:
                error_msg = str(e)
                if "API_KEY_INVALID" in error_msg or "PERMISSION_DENIED" in error_msg:
                    raise ValueError(
                        "Gemini API key is invalid. Please get a new API key from "
                        "https://makersuite.google.com/app/apikey and update GEMINI_API_KEY in your .env file"
                    ) from e
                else:
                    raise
        elif llm_provider == "moonshot":
            api_key = os.getenv("MOONSHOT_API_KEY")
            base_url = os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.ai/v1")
            if not api_key:
                raise ValueError("MOONSHOT_API_KEY not set in environment")
            
            # Initialize OpenAI client for Moonshot
            try:
                self.client = OpenAI(
                    api_key=api_key,
                    base_url=base_url,
                )
                logger.info(f"Using Moonshot AI at {base_url}")
                
                # Test the connection with a simple request
                test_response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": "test"}],
                    max_tokens=5
                )
                logger.info("Moonshot AI connection test successful")
                
            except Exception as e:
                error_msg = str(e)
                if "401" in error_msg or "Invalid Authentication" in error_msg:
                    raise ValueError(
                        "Moonshot AI API key is invalid or expired. "
                        "Please get a new API key from https://platform.moonshot.ai/console "
                        "and update MOONSHOT_API_KEY in your .env file"
                    ) from e
                else:
                    raise
        else:
            # Local model support can be added here
            logger.warning(f"Unknown provider {llm_provider}, defaulting to Moonshot")
            api_key = os.getenv("MOONSHOT_API_KEY")
            base_url = os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.ai/v1")
            if api_key:
                try:
                    self.client = OpenAI(
                        api_key=api_key,
                        base_url=base_url,
                    )
                    logger.info(f"Using Moonshot AI at {base_url}")
                except Exception as e:
                    logger.error(f"Failed to initialize Moonshot client: {e}")
                    raise ValueError("MOONSHOT_API_KEY not set in environment or invalid")
            else:
                raise ValueError("MOONSHOT_API_KEY not set in environment")
        
        logger.info(f"RAG Pipeline initialized with {llm_provider}/{model}")
    
    @property
    def llm_service(self):
        """Expose LLM client for other components"""
        return self.client
    
    def query(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
        source: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1500,
        max_context_length: int = 3000,
    ) -> Dict:
        """
        Run RAG query
        
        Args:
            query: User question
            top_k: Number of documents to retrieve
            category: Filter by category
            source: Filter by source
            temperature: LLM temperature
            max_tokens: Maximum tokens in response
        
        Returns:
            Dictionary with answer and sources
        """
        start_time = time.time()
        
        # 1. Retrieve relevant documents
        logger.info(f"Retrieving documents for query: {query[:50]}...")
        
        filter_dict = {}
        if category:
            filter_dict["category"] = category
        if source:
            filter_dict["source_name"] = source
        
        retrieved_docs = self.vector_store.query(
            query_text=query,
            n_results=top_k,
            filter=filter_dict if filter_dict else None,
        )
        
        if not retrieved_docs:
            return {
                "answer": "I couldn't find any relevant information to answer your question.",
                "sources": [],
                "query_time": time.time() - start_time,
                "retrieved_chunks": 0,
                "model_used": self.model,
            }
        
        # 2. Prepare context
        context = self._prepare_context(retrieved_docs, max_context_length)
        
        # 3. Generate answer
        logger.info("Generating answer with LLM")
        answer = self._generate_answer(query, context, temperature, max_tokens)
        
        # 4. Format sources
        sources = self._format_sources(retrieved_docs)
        
        query_time = time.time() - start_time
        
        logger.info(f"Query completed in {query_time:.2f}s")
        
        return {
            "answer": answer,
            "sources": sources,
            "query_time": query_time,
            "retrieved_chunks": len(retrieved_docs),
            "model_used": self.model,
        }
    
    def _prepare_context(self, docs: List[Dict], max_context_length: int = 3000) -> str:
        """Prepare context from retrieved documents"""
        context_parts = []
        total_length = 0
        
        for i, doc in enumerate(docs, 1):
            meta = doc["metadata"]
            text = doc["text"]
            
            # Truncate individual document text if too long
            if len(text) > 500:
                text = text[:500] + "..."
            
            # Format: [Source #] Title - Category\nText
            context_part = (
                f"[Source {i}] {meta.get('title', 'Untitled')} "
                f"({meta.get('category', 'Unknown')})\n{text}\n"
            )
            
            # Check if adding this would exceed max length
            if total_length + len(context_part) > max_context_length:
                break
                
            context_parts.append(context_part)
            total_length += len(context_part)
        
        return "\n---\n".join(context_parts)
    
    def _generate_answer(
        self,
        query: str,
        context: str,
        temperature: float,
        max_tokens: int,
    ) -> str:
        """Generate answer using LLM"""
        
        # System prompt
        system_prompt = """You are AmaniQuery, an AI assistant specialized in Kenyan law, parliamentary proceedings, and current affairs.

Your role is to provide accurate, well-sourced answers based on the provided context. Always:
1. Base your answer primarily on the provided context when available
2. Cite sources using [Source #] notation when using information from context
3. Be precise and factual
4. If the context contains relevant information, use it with citations
5. If the context doesn't contain enough specific information, provide general knowledge about the topic while noting the limitation
6. Use clear, professional language"""

        # User prompt
        user_prompt = f"""Context from relevant documents:

{context}

Question: {query}

Please provide a detailed answer based on the context above. If the context contains relevant information, cite sources using [Source #] notation. If the context doesn't provide specific details, use your general knowledge to provide a helpful answer while noting that the information comes from general knowledge rather than the provided documents."""

        try:
            if self.llm_provider in ["openai", "moonshot"]:
                # Both OpenAI and Moonshot use the same API format
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt},
                    ],
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                answer = response.choices[0].message.content
                logger.info(f"LLM response length: {len(answer) if answer else 0}")
                if not answer or not answer.strip():
                    logger.warning("LLM returned empty or whitespace-only response")
                    return "I apologize, but I was unable to generate a response. Please try rephrasing your question."
                return answer
            
            elif self.llm_provider == "gemini":
                # Gemini uses a different API format
                import google.generativeai as genai
                
                # Configure generation parameters
                generation_config = genai.types.GenerationConfig(
                    temperature=temperature,
                    max_output_tokens=max_tokens,
                )
                
                # Combine system prompt with user prompt
                full_prompt = f"{system_prompt}\n\n{user_prompt}"
                
                response = self.client.generate_content(
                    full_prompt,
                    generation_config=generation_config
                )
                
                answer = response.text
                logger.info(f"Gemini response length: {len(answer) if answer else 0}")
                if not answer or not answer.strip():
                    logger.warning("Gemini returned empty or whitespace-only response")
                    return "I apologize, but I was unable to generate a response. Please try rephrasing your question."
                return answer
            
            elif self.llm_provider == "anthropic":
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    system=system_prompt,
                    messages=[
                        {"role": "user", "content": user_prompt}
                    ],
                )
                answer = response.content[0].text
                logger.info(f"LLM response length: {len(answer) if answer else 0}")
                if not answer or not answer.strip():
                    logger.warning("LLM returned empty or whitespace-only response")
                    return "I apologize, but I was unable to generate a response. Please try rephrasing your question."
                return answer
            
            else:
                return "LLM provider not supported"
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error generating answer: {error_msg}")
            
            # Provide helpful error messages
            if "401" in error_msg or "Invalid Authentication" in error_msg:
                if self.llm_provider == "moonshot":
                    return ("Error: Moonshot AI API key is invalid. Please get a new API key from "
                           "https://platform.moonshot.cn/console and update MOONSHOT_API_KEY in your .env file")
                elif self.llm_provider == "openai":
                    return ("Error: OpenAI API key is invalid. Please check your OPENAI_API_KEY in the .env file")
                else:
                    return f"Authentication error: {error_msg}"
            elif "429" in error_msg or "rate limit" in error_msg.lower():
                return "Error: API rate limit exceeded. Please try again later."
            elif "insufficient_quota" in error_msg.lower():
                return "Error: API quota exceeded. Please check your account balance."
            else:
                return f"Error generating answer: {error_msg}"
    
    def _format_sources(self, docs: List[Dict]) -> List[Dict]:
        """Format source citations"""
        sources = []
        
        for doc in docs:
            meta = doc["metadata"]
            
            source = {
                "title": meta.get("title", "Untitled"),
                "url": meta.get("source_url", ""),
                "source_name": meta.get("source_name", "Unknown"),
                "category": meta.get("category", "Unknown"),
                "author": meta.get("author"),
                "publication_date": meta.get("publication_date"),
                "relevance_score": 1.0 - doc.get("distance", 0.0),  # Convert distance to similarity
                "excerpt": doc["text"][:200] + "..." if len(doc["text"]) > 200 else doc["text"],
            }
            
            sources.append(source)
        
        return sources
