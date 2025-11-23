"""
RAG Pipeline - Retrieval-Augmented Generation
"""
import os
from typing import List, Dict, Optional, Any
import time
from loguru import logger
from openai import OpenAI
from anthropic import Anthropic
from dotenv import load_dotenv
import hashlib
import json

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
        config_manager: Optional[Any] = None,
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
        
        self.config_manager = config_manager

        # Initialize vector store
        self.vector_store = vector_store or VectorStore(config_manager=config_manager)
        self.metadata_manager = MetadataManager(self.vector_store)
        
        # Initialize cache
        self.cache = {}
        self.cache_max_size = 100  # Keep last 100 queries
        
        # Initialize LLM
        self.llm_provider = llm_provider
        self.model = model
        
        if llm_provider == "openai":
            api_key = self._get_secret("OPENAI_API_KEY")
            if not api_key:
                raise ValueError("OPENAI_API_KEY not set in environment")
            self.client = OpenAI(api_key=api_key)
        elif llm_provider == "anthropic":
            api_key = self._get_secret("ANTHROPIC_API_KEY")
            if not api_key:
                raise ValueError("ANTHROPIC_API_KEY not set in environment")
            self.client = Anthropic(api_key=api_key)
        elif llm_provider == "gemini":
            api_key = self._get_secret("GEMINI_API_KEY")
            if not api_key:
                raise ValueError("GEMINI_API_KEY not set in environment")
            try:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                # Update deprecated model names
                gemini_model = self.model
                if gemini_model == "gemini-pro":
                    gemini_model = "gemini-2.5-flash"  # Use flash as default (faster)
                elif gemini_model not in ["gemini-2.5-pro", "gemini-2.5-flash", "gemini-flash"]:
                    # If model not specified or unknown, default to flash
                    gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
                self.model = gemini_model  # Update self.model to the correct name
                self.client = genai.GenerativeModel(self.model)
                logger.info(f"Using Google Gemini AI with model: {self.model}")
                
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
            api_key = self._get_secret("MOONSHOT_API_KEY")
            base_url = (
                os.getenv("MOONSHOT_BASE_URL")
                or self._get_secret("MOONSHOT_BASE_URL")
                or "https://api.moonshot.ai/v1"
            )
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
            api_key = self._get_secret("MOONSHOT_API_KEY")
            base_url = (
                os.getenv("MOONSHOT_BASE_URL")
                or self._get_secret("MOONSHOT_BASE_URL")
                or "https://api.moonshot.ai/v1"
            )
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
        
        # Initialize ensemble clients (for multi-model responses when context is limited)
        self.ensemble_clients = self._initialize_ensemble_clients()

    def _initialize_ensemble_clients(self) -> Dict[str, Any]:
        """Initialize all available model clients for ensemble responses"""
        clients = {}
        
        # OpenAI
        try:
            api_key = self._get_secret("OPENAI_API_KEY")
            if api_key:
                clients["openai"] = {
                    "client": OpenAI(api_key=api_key),
                    "model": os.getenv("OPENAI_MODEL", "gpt-4o-mini")
                }
                logger.info("Ensemble: OpenAI client initialized")
        except Exception as e:
            logger.warning(f"Ensemble: Failed to initialize OpenAI: {e}")
        
        # Moonshot
        try:
            api_key = self._get_secret("MOONSHOT_API_KEY")
            if api_key:
                base_url = os.getenv("MOONSHOT_BASE_URL") or "https://api.moonshot.ai/v1"
                clients["moonshot"] = {
                    "client": OpenAI(api_key=api_key, base_url=base_url),
                    "model": os.getenv("MOONSHOT_MODEL", "moonshot-v1-8k")
                }
                logger.info("Ensemble: Moonshot client initialized")
        except Exception as e:
            logger.warning(f"Ensemble: Failed to initialize Moonshot: {e}")
        
        # Anthropic
        try:
            api_key = self._get_secret("ANTHROPIC_API_KEY")
            if api_key:
                clients["anthropic"] = {
                    "client": Anthropic(api_key=api_key),
                    "model": os.getenv("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")
                }
                logger.info("Ensemble: Anthropic client initialized")
        except Exception as e:
            logger.warning(f"Ensemble: Failed to initialize Anthropic: {e}")
        
        # Gemini
        try:
            api_key = self._get_secret("GEMINI_API_KEY")
            if api_key:
                import google.generativeai as genai
                genai.configure(api_key=api_key)
                # Use gemini-2.5-flash as default (faster) or gemini-2.5-pro (more capable)
                gemini_model = os.getenv("GEMINI_MODEL", "gemini-2.5-flash")
                # Fallback to gemini-2.5-pro if flash not available
                if gemini_model == "gemini-2.5-pro":
                    gemini_model = "gemini-2.5-flash"
                clients["gemini"] = {
                    "client": genai.GenerativeModel(gemini_model),
                    "model": gemini_model
                }
                logger.info(f"Ensemble: Gemini client initialized with {gemini_model}")
        except Exception as e:
            logger.warning(f"Ensemble: Failed to initialize Gemini: {e}")
        
        logger.info(f"Ensemble: {len(clients)} model(s) available for ensemble responses")
        return clients

    def _is_context_limited(self, retrieved_docs: List[Dict], min_relevance: float = 0.5) -> bool:
        """Check if retrieved context is limited or insufficient"""
        if not retrieved_docs:
            return True
        
        # Check if relevance scores are too low
        if len(retrieved_docs) < 3:
            return True
        
        # Check average relevance (if available)
        scores = [doc.get("score", 0) for doc in retrieved_docs if "score" in doc]
        if scores and sum(scores) / len(scores) < min_relevance:
            return True
        
        return False

    def _get_secret(self, key: str, default: Optional[str] = None) -> Optional[str]:
        """Fetch secret values from environment variables with ConfigManager fallback."""
        value = os.getenv(key)
        if value:
            return value

        if self.config_manager:
            try:
                secret = self.config_manager.get_config(key)
                if secret:
                    return secret
            except Exception as exc:
                logger.warning(f"Failed to fetch {key} from config store: {exc}")

        return default
    
    def _get_cache_key(self, query: str, top_k: int, category: Optional[str], source: Optional[str]) -> str:
        """Generate cache key for query"""
        key_data = {
            "query": query.strip().lower(),
            "top_k": top_k,
            "category": category,
            "source": source,
        }
        key_str = json.dumps(key_data, sort_keys=True)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def _get_cache(self, key: str) -> Optional[Dict]:
        """Get cached result if exists"""
        if key in self.cache:
            logger.info("Cache hit!")
            return self.cache[key]
        return None
    
    def _set_cache(self, key: str, result: Dict):
        """Store result in cache"""
        if len(self.cache) >= self.cache_max_size:
            # Remove oldest entry (simple FIFO)
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        self.cache[key] = result
        logger.info("Result cached")
    
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
        session_id: Optional[str] = None,
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
        
        # Check cache first
        cache_key = self._get_cache_key(query, top_k, category, source)
        cached_result = self._get_cache(cache_key)
        if cached_result:
            logger.info("Cache hit for query!")
            return cached_result
        
        # Retrieve from main vector store
        retrieved_docs = self.vector_store.query(
            query_text=query,
            n_results=top_k,
            filter=filter_dict if filter_dict else None,
        )
        
        # If session_id provided, also retrieve from session-specific collection
        if session_id:
            try:
                collection_name = f"chat_session_{session_id}"
                # Try to query session-specific collection
                if hasattr(self.vector_store, 'get_collection'):
                    collection = self.vector_store.get_collection(collection_name)
                    if collection:
                        session_docs = collection.query(
                            query_texts=[query],
                            n_results=min(3, top_k),  # Limit session docs
                        )
                        # Merge session docs with main docs
                        if session_docs and len(session_docs) > 0:
                            # Format session docs to match main docs format
                            if isinstance(session_docs, dict) and "documents" in session_docs:
                                for i, doc_text in enumerate(session_docs["documents"][0] if session_docs["documents"] else []):
                                    session_doc = {
                                        "text": doc_text,
                                        "source": session_docs.get("metadatas", [[]])[0][i] if session_docs.get("metadatas") else {},
                                        "score": session_docs.get("distances", [[]])[0][i] if session_docs.get("distances") else 0.0,
                                    }
                                    retrieved_docs.append(session_doc)
                            logger.info(f"Retrieved {len(session_docs) if isinstance(session_docs, list) else 1} documents from session collection")
            except Exception as e:
                logger.warning(f"Failed to retrieve session documents: {e}")
        
        # Check if context is limited - use ensemble if so
        use_ensemble = self._is_context_limited(retrieved_docs)
        
        if not retrieved_docs or use_ensemble:
            if use_ensemble and len(self.ensemble_clients) > 0:
                logger.info("Context limited - using multi-model ensemble")
                return self._query_with_ensemble(
                    query=query,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    start_time=start_time
                )
            else:
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
        
        result = {
            "answer": answer,
            "sources": sources,
            "query_time": query_time,
            "retrieved_chunks": len(retrieved_docs),
            "model_used": self.model,
        }
        
        # Store in cache
        self._set_cache(cache_key, result)
        
        return result
    
    def _query_with_ensemble(
        self,
        query: str,
        temperature: float = 0.7,
        max_tokens: int = 1500,
        start_time: float = None
    ) -> Dict:
        """Query all available models and combine responses"""
        if start_time is None:
            start_time = time.time()
        
        # Generate responses from all models
        responses = self._generate_ensemble_responses(query, temperature, max_tokens)
        
        if not responses:
            return {
                "answer": "I couldn't generate a response. Please try again.",
                "sources": [],
                "query_time": time.time() - start_time,
                "retrieved_chunks": 0,
                "model_used": "ensemble",
            }
        
        # Combine responses into concise answer
        combined_answer = self._combine_ensemble_responses(responses, query)
        
        return {
            "answer": combined_answer,
            "sources": [],
            "query_time": time.time() - start_time,
            "retrieved_chunks": 0,
            "model_used": f"ensemble({len(responses)} models)",
            "ensemble_responses": len(responses)
        }
    
    def _generate_ensemble_responses(
        self,
        query: str,
        temperature: float = 0.7,
        max_tokens: int = 1500
    ) -> Dict[str, str]:
        """Generate responses from all available models in parallel"""
        import concurrent.futures
        
        system_prompt = """You are AmaniQuery, an AI assistant specialized in Kenyan law, parliamentary proceedings, and current affairs.

Provide a concise, accurate answer to the question. Focus on factual information and be brief."""
        
        user_prompt = f"""Question: {query}

Provide a concise answer based on your knowledge of Kenyan law and current affairs."""
        
        responses = {}
        
        def query_model(provider: str, client_info: Dict):
            """Query a single model"""
            try:
                client = client_info["client"]
                model = client_info["model"]
                
                if provider in ["openai", "moonshot"]:
                    response = client.chat.completions.create(
                        model=model,
                        messages=[
                            {"role": "system", "content": system_prompt},
                            {"role": "user", "content": user_prompt}
                        ],
                        temperature=temperature,
                        max_tokens=max_tokens
                    )
                    return response.choices[0].message.content
                
                elif provider == "anthropic":
                    response = client.messages.create(
                        model=model,
                        max_tokens=max_tokens,
                        temperature=temperature,
                        system=system_prompt,
                        messages=[{"role": "user", "content": user_prompt}]
                    )
                    return response.content[0].text
                
                elif provider == "gemini":
                    import google.generativeai as genai
                    full_prompt = f"{system_prompt}\n\n{user_prompt}"
                    response = client.generate_content(
                        full_prompt,
                        generation_config=genai.types.GenerationConfig(
                            temperature=temperature,
                            max_output_tokens=max_tokens
                        )
                    )
                    return response.text
                
            except Exception as e:
                logger.warning(f"Ensemble: {provider} failed: {e}")
                return None
        
        # Query all models in parallel
        with concurrent.futures.ThreadPoolExecutor(max_workers=len(self.ensemble_clients)) as executor:
            futures = {
                executor.submit(query_model, provider, client_info): provider
                for provider, client_info in self.ensemble_clients.items()
            }
            
            for future in concurrent.futures.as_completed(futures):
                provider = futures[future]
                try:
                    response = future.result()
                    if response:
                        responses[provider] = response
                except Exception as e:
                    logger.warning(f"Ensemble: Error getting {provider} response: {e}")
        
        logger.info(f"Ensemble: Generated {len(responses)} responses")
        return responses
    
    def _combine_ensemble_responses(self, responses: Dict[str, str], query: str) -> str:
        """Intelligently combine multiple model responses into a concise answer"""
        if len(responses) == 1:
            return list(responses.values())[0]
        
        # Use the primary model to synthesize responses
        if self.llm_provider in ["openai", "moonshot"] and self.llm_provider in responses:
            synthesizer = self.client
            model = self.model
        elif "openai" in responses:
            synthesizer = self.ensemble_clients["openai"]["client"]
            model = self.ensemble_clients["openai"]["model"]
        elif "moonshot" in responses:
            synthesizer = self.ensemble_clients["moonshot"]["client"]
            model = self.ensemble_clients["moonshot"]["model"]
        else:
            # Fallback: return the longest response
            return max(responses.values(), key=len)
        
        # Prepare synthesis prompt
        responses_text = "\n\n".join([
            f"**{provider.upper()}:**\n{response}"
            for provider, response in responses.items()
        ])
        
        synthesis_prompt = f"""You are synthesizing responses from multiple AI models to answer a question about Kenyan law.

Original Question: {query}

Responses from multiple models:
{responses_text}

Create a concise, accurate combined response that:
1. Integrates the best information from all responses
2. Removes redundancy and contradictions
3. Maintains factual accuracy
4. Is well-structured and easy to read
5. Follows the format: Summary → Key Points → Important Details

Combined Response:"""
        
        try:
            if hasattr(synthesizer, 'chat'):
                # OpenAI/Moonshot format
                response = synthesizer.chat.completions.create(
                    model=model,
                    messages=[{"role": "user", "content": synthesis_prompt}],
                    temperature=0.3,  # Lower temperature for synthesis
                    max_tokens=2000
                )
                return response.choices[0].message.content
            else:
                # Fallback: return longest response
                return max(responses.values(), key=len)
        except Exception as e:
            logger.warning(f"Ensemble synthesis failed: {e}, returning longest response")
            return max(responses.values(), key=len)
    
    def _create_simple_stream(self, text: str):
        """Create a simple stream from text"""
        class SimpleStream:
            def __init__(self, text):
                self.words = text.split()
                self.index = 0
            
            def __iter__(self):
                return self
            
            def __next__(self):
                if self.index >= len(self.words):
                    raise StopIteration
                
                chunk_size = 3
                end_idx = min(self.index + chunk_size, len(self.words))
                chunk_text = " ".join(self.words[self.index:end_idx])
                if end_idx < len(self.words):
                    chunk_text += " "
                self.index = end_idx
                
                # Return in OpenAI format
                class Chunk:
                    def __init__(self, content):
                        class Delta:
                            def __init__(self, c):
                                self.content = c
                        class Choice:
                            def __init__(self, c):
                                self.delta = Delta(c)
                        self.choices = [Choice(content)]
                
                return Chunk(chunk_text)
        
        return SimpleStream(text)
    
    def _query_stream_with_ensemble(
        self,
        query: str,
        temperature: float = 0.7,
        max_tokens: int = 1500,
        start_time: float = None
    ) -> Dict:
        """Query all models, combine responses, and stream the result"""
        if start_time is None:
            start_time = time.time()
        
        # Generate responses from all models
        responses = self._generate_ensemble_responses(query, temperature, max_tokens)
        
        if not responses:
            return {
                "answer": "I couldn't generate a response. Please try again.",
                "sources": [],
                "query_time": time.time() - start_time,
                "retrieved_chunks": 0,
                "model_used": "ensemble",
                "stream": False,
            }
        
        # Combine responses
        combined_answer = self._combine_ensemble_responses(responses, query)
        
        # Create a streaming response from the combined answer
        # Chunk the combined answer and stream it
        answer_stream = self._create_simple_stream(combined_answer)
        
        query_time = time.time() - start_time
        
        return {
            "answer_stream": answer_stream,
            "sources": [],
            "query_time": query_time,
            "retrieved_chunks": 0,
            "model_used": f"ensemble({len(responses)} models)",
            "stream": True,
            "ensemble_responses": len(responses)
        }
    
    def query_stream(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
        source: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1500,
        max_context_length: int = 3000,
        session_id: Optional[str] = None,
    ):
        """
        Run RAG query with streaming response
        
        Args:
            query: User question
            top_k: Number of documents to retrieve
            category: Filter by category
            source: Filter by source
            temperature: LLM temperature
            max_tokens: Maximum tokens in response
            max_context_length: Maximum context length
            session_id: Optional session ID for session-specific document retrieval
        
        Returns:
            Dictionary with answer stream and sources
        """
        start_time = time.time()
        
        try:
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
            
            # If session_id provided, also retrieve from session-specific collection
            if session_id:
                try:
                    collection_name = f"chat_session_{session_id}"
                    # Try to query session-specific collection
                    if hasattr(self.vector_store, 'get_collection'):
                        collection = self.vector_store.get_collection(collection_name)
                        if collection:
                            session_docs = collection.query(
                                query_texts=[query],
                                n_results=min(3, top_k),  # Limit session docs
                            )
                            # Merge session docs with main docs
                            if session_docs and len(session_docs) > 0:
                                # Format session docs to match main docs format
                                if isinstance(session_docs, dict) and "documents" in session_docs:
                                    for i, doc_text in enumerate(session_docs["documents"][0] if session_docs["documents"] else []):
                                        session_doc = {
                                            "text": doc_text,
                                            "source": session_docs.get("metadatas", [[]])[0][i] if session_docs.get("metadatas") else {},
                                            "score": session_docs.get("distances", [[]])[0][i] if session_docs.get("distances") else 0.0,
                                        }
                                        retrieved_docs.append(session_doc)
                                logger.info(f"Retrieved {len(session_docs) if isinstance(session_docs, list) else 1} documents from session collection")
                except Exception as e:
                    logger.warning(f"Failed to retrieve session documents: {e}")
            
            # Check if context is limited - use ensemble if so
            use_ensemble = self._is_context_limited(retrieved_docs)
            
            if use_ensemble and len(self.ensemble_clients) > 0:
                logger.info("Context limited - using multi-model ensemble with streaming")
                return self._query_stream_with_ensemble(
                    query=query,
                    temperature=temperature,
                    max_tokens=max_tokens,
                    start_time=start_time
                )
            
            # 2. Prepare context (use available docs or empty)
            context = self._prepare_context(retrieved_docs, max_context_length)
            
            # 3. Generate answer with streaming (always provide response)
            logger.info("Generating streaming answer with LLM")
            answer_stream = self._generate_answer_stream(query, context, temperature, max_tokens)
            
            # 4. Format sources
            sources = self._format_sources(retrieved_docs)
            
            query_time = time.time() - start_time
            
            return {
                "answer_stream": answer_stream,
                "sources": sources,
                "query_time": query_time,
                "retrieved_chunks": len(retrieved_docs),
                "model_used": self.model,
                "stream": True,
            }
            
        except Exception as e:
            logger.error(f"Error in query_stream: {e}")
            # Return non-streaming fallback response
            return {
                "answer": f"I encountered an error while processing your query: {str(e)}. Please try again.",
                "sources": [],
                "query_time": time.time() - start_time,
                "retrieved_chunks": 0,
                "model_used": self.model,
                "stream": False,
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
    ) -> Dict[str, Any]:
        """Generate answer using LLM, potentially with interactive widgets"""
        
        # System prompt with Impact Agent instructions
        system_prompt = """You are AmaniQuery, an AI assistant specialized in Kenyan law, parliamentary proceedings, and current affairs.

CRITICAL INSTRUCTION: DETECT QUANTITATIVE POLICY QUERIES
If the user's query involves calculating costs, levies, taxes, fines, or statutory deductions (Housing Levy, NSSF, NHIF/SHIF, PAYE, Fuel Levy, Parking Fees, etc.), you MUST output a JSON response containing an interactive widget definition.

OUTPUT FORMAT:
If a widget is needed, output ONLY a JSON object with this structure:
{
  "answer": "Brief text explanation...",
  "interactive_widgets": [
    {
      "type": "salary_calculator" | "fine_calculator" | "levy_breakdown" | "loan_repayment",
      "title": "Widget Title",
      "description": "Widget Description",
      "formula": "JavaScript evaluable formula (use input names as variables)",
      "inputs": [{"name": "var_name", "label": "Label", "type": "number", "placeholder": "Example"}],
      "outputs": [{"label": "Output Label", "format": "KES {value}"}],
      "source_citation": "Source of the formula"
    }
  ]
}

If NO widget is needed, output a standard text response following these formatting rules:
1. **Keep responses concise** - Maximum 3-4 main sections
2. **Use clear spacing** - Add blank lines between sections
3. **Limit section length** - Each section should be 2-3 short paragraphs or bullet points
4. **Only cite sources when using specific context**
5. **Use bullet points**

FEW-SHOT EXAMPLES FOR WIDGETS:

Example 1: Housing Levy
User: "Housing levy inanipunguza kitu gani kwa 60K salary?"
Response:
{
  "answer": "The Affordable Housing Levy is set at 1.5% of your gross monthly salary. For a salary of KES 60,000, the deduction is calculated as 1.5% of 60,000.",
  "interactive_widgets": [{
    "type": "salary_calculator",
    "title": "Housing Levy Calculator",
    "description": "Calculate your monthly Housing Levy deduction",
    "formula": "salary * 0.015",
    "inputs": [{"name": "salary", "label": "Gross Monthly Salary (KES)", "type": "number", "placeholder": "60000"}],
    "outputs": [{"label": "Monthly Deduction", "format": "KES {value}"}],
    "source_citation": "Finance Act 2023"
  }]
}

Example 2: NSSF (Tier I & II)
User: "How much NSSF will I pay if I earn 50k?"
Response:
{
  "answer": "Under the new NSSF Act, contributions are 6% of pensionable earnings. For a salary of KES 50,000, you pay Tier I (on first 6,000) and Tier II (on balance up to 18,000 limit).",
  "interactive_widgets": [{
    "type": "salary_calculator",
    "title": "NSSF Contribution Calculator",
    "description": "Estimate your NSSF Tier I and Tier II contributions",
    "formula": "let tier1 = Math.min(salary, 6000) * 0.06; let tier2 = (salary > 6000) ? Math.min(salary - 6000, 12000) * 0.06 : 0; tier1 + tier2",
    "inputs": [{"name": "salary", "label": "Gross Monthly Salary (KES)", "type": "number", "placeholder": "50000"}],
    "outputs": [{"label": "Total NSSF Contribution", "format": "KES {value}"}],
    "source_citation": "NSSF Act 2013"
  }]
}

Example 3: Parking Fees
User: "Parking fees CBD sasa ni ngapi per hour?"
Response:
{
  "answer": "Parking fees in Nairobi CBD vary by vehicle type. For private cars, the daily rate is typically KES 200, but hourly zones exist.",
  "interactive_widgets": [{
    "type": "fine_calculator",
    "title": "Nairobi CBD Parking Calculator",
    "description": "Calculate parking fees based on duration",
    "formula": "hours * rate",
    "inputs": [
      {"name": "hours", "label": "Duration (Hours)", "type": "number", "placeholder": "2"},
      {"name": "rate", "label": "Hourly Rate (KES)", "type": "number", "placeholder": "100", "default_value": "100"}
    ],
    "outputs": [{"label": "Total Parking Fee", "format": "KES {value}"}],
    "source_citation": "Nairobi City County Finance Act"
  }]
}

Example 4: PAYE
User: "Calculate PAYE for 100k income"
Response:
{
  "answer": "PAYE is calculated on a graduated scale. For KES 100,000, bands apply: 10% on first 24k, 25% on next 8.3k, 30% on balance (simplified).",
  "interactive_widgets": [{
    "type": "salary_calculator",
    "title": "PAYE Estimator",
    "description": "Estimate PAYE (approximate, excluding relief)",
    "formula": "let taxable = salary; let tax = 0; if(taxable > 24000) { tax += 24000 * 0.1; taxable -= 24000; } else { return taxable * 0.1; } if(taxable > 8333) { tax += 8333 * 0.25; taxable -= 8333; } else { return tax + taxable * 0.25; } tax += taxable * 0.3; tax",
    "inputs": [{"name": "salary", "label": "Taxable Income (KES)", "type": "number", "placeholder": "100000"}],
    "outputs": [{"label": "Estimated PAYE", "format": "KES {value}"}],
    "source_citation": "Income Tax Act"
  }]
}

Example 5: SHIF
User: "SHIF itakata pesa ngapi?"
Response:
{
  "answer": "The Social Health Insurance Fund (SHIF) deduction is proposed at 2.75% of gross household income.",
  "interactive_widgets": [{
    "type": "salary_calculator",
    "title": "SHIF Deduction Calculator",
    "description": "Calculate 2.75% SHIF deduction",
    "formula": "income * 0.0275",
    "inputs": [{"name": "income", "label": "Gross Income (KES)", "type": "number", "placeholder": "50000"}],
    "outputs": [{"label": "SHIF Contribution", "format": "KES {value}"}],
    "source_citation": "Social Health Insurance Act 2023"
  }]
}

Example 6: Traffic Fines
User: "Fine ya overlapping ni how much?"
Response:
{
  "answer": "Traffic fines are stipulated in the Traffic Act. Obstruction or overlapping often attracts a fine.",
  "interactive_widgets": [{
    "type": "fine_calculator",
    "title": "Traffic Fine Calculator",
    "description": "Estimate potential fines for offenses",
    "formula": "offense_count * fine_amount",
    "inputs": [
        {"name": "fine_amount", "label": "Fine per Offense (KES)", "type": "number", "placeholder": "5000", "default_value": "5000"},
        {"name": "offense_count", "label": "Number of Offenses", "type": "number", "placeholder": "1"}
    ],
    "outputs": [{"label": "Total Fine", "format": "KES {value}"}],
    "source_citation": "Traffic Act Cap 403"
  }]
}

Example 7: Sugar Levy
User: "How much will the new sugar levy add to a 1kg packet?"
Response:
{
  "answer": "The proposed sugar levy is KES 5 per kilogram.",
  "interactive_widgets": [{
    "type": "levy_breakdown",
    "title": "Sugar Levy Calculator",
    "description": "Calculate additional cost due to sugar levy",
    "formula": "weight * 5",
    "inputs": [{"name": "weight", "label": "Sugar Weight (kg)", "type": "number", "placeholder": "1"}],
    "outputs": [{"label": "Levy Amount", "format": "KES {value}"}],
    "source_citation": "Finance Bill 2023"
  }]
}

Example 8: County Cess
User: "County cess for potato lorry entering Nairobi?"
Response:
{
  "answer": "Cess charges depend on the county and vehicle tonnage. For Nairobi, charges apply per entry.",
  "interactive_widgets": [{
    "type": "fine_calculator",
    "title": "County Cess Calculator",
    "description": "Estimate cess charges for goods entry",
    "formula": "lorries * rate",
    "inputs": [
        {"name": "lorries", "label": "Number of Lorries", "type": "number", "placeholder": "1"},
        {"name": "rate", "label": "Cess Rate per Lorry (KES)", "type": "number", "placeholder": "3000", "default_value": "3000"}
    ],
    "outputs": [{"label": "Total Cess", "format": "KES {value}"}],
    "source_citation": "Nairobi City County Finance Act"
  }]
}"""

        # User prompt
        user_prompt = f"""Context from relevant documents:

{context}

Question: {query}

Provide a concise answer. If the query is quantitative/policy-related (taxes, levies, fines), output JSON with an interactive widget. Otherwise, output standard text."""

        try:
            raw_answer = ""
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
                raw_answer = response.choices[0].message.content
            
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
                
                raw_answer = response.text
            
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
                raw_answer = response.content[0].text
            
            else:
                return {"answer": "LLM provider not supported"}

            # Parse response
            logger.info(f"LLM response length: {len(raw_answer) if raw_answer else 0}")
            if not raw_answer or not raw_answer.strip():
                logger.warning("LLM returned empty or whitespace-only response")
                return {"answer": "I apologize, but I was unable to generate a response. Please try rephrasing your question."}

            # Try to parse as JSON
            try:
                # Clean up potential markdown code blocks
                clean_answer = raw_answer.strip()
                if clean_answer.startswith("```json"):
                    clean_answer = clean_answer[7:]
                if clean_answer.endswith("```"):
                    clean_answer = clean_answer[:-3]
                
                parsed_json = json.loads(clean_answer)
                
                # If valid JSON with answer and widgets
                if isinstance(parsed_json, dict) and "answer" in parsed_json:
                    return {
                        "answer": parsed_json["answer"],
                        "interactive_widgets": parsed_json.get("interactive_widgets")
                    }
                else:
                    # JSON but not our expected format, treat as text
                    return {"answer": raw_answer}
            except json.JSONDecodeError:
                # Not JSON, treat as standard text response
                return {"answer": raw_answer}
                
        except Exception as e:
            error_msg = str(e)
            logger.error(f"Error generating answer: {error_msg}")
            return {"answer": f"Error generating answer: {error_msg}"}
    
    def _generate_answer_stream(
        self,
        query: str,
        context: str,
        temperature: float,
        max_tokens: int,
    ):
        """Generate answer using LLM with streaming"""
        # NOTE: For Impact Agent (widgets), we currently prioritize correctness over streaming.
        # We generate the full response (including widgets) and then yield the text answer.
        # This ensures widgets are generated if needed, even if we can't stream them yet.
        
        # Generate full response using the widget-aware method
        response = self._generate_answer(query, context, temperature, max_tokens)
        
        # If it's a dict (standard response), extract answer
        if isinstance(response, dict):
            answer = response.get("answer", "")
            # We yield the answer as a single chunk. 
            # This simulates streaming but allows us to reuse the widget logic.
            yield answer
        else:
            # Fallback if something went wrong and it returned a string
            yield str(response)
    
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
