"""
RAG Pipeline - Retrieval-Augmented Generation
"""
import os
from typing import List, Dict, Optional
import time
from loguru import logger
from openai import OpenAI
from anthropic import Anthropic

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from Module3_NiruDB import VectorStore, MetadataManager


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
        elif llm_provider == "moonshot":
            api_key = os.getenv("MOONSHOT_API_KEY")
            base_url = os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.cn/v1")
            if not api_key:
                raise ValueError("MOONSHOT_API_KEY not set in environment")
            self.client = OpenAI(
                api_key=api_key,
                base_url=base_url
            )
            logger.info(f"Using Moonshot AI at {base_url}")
        else:
            # Local model support can be added here
            logger.warning(f"Unknown provider {llm_provider}, defaulting to Moonshot")
            self.client = OpenAI(
                api_key=os.getenv("MOONSHOT_API_KEY"),
                base_url=os.getenv("MOONSHOT_BASE_URL", "https://api.moonshot.cn/v1")
            )
        
        logger.info(f"RAG Pipeline initialized with {llm_provider}/{model}")
    
    def query(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
        source: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1500,
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
        context = self._prepare_context(retrieved_docs)
        
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
    
    def _prepare_context(self, docs: List[Dict]) -> str:
        """Prepare context from retrieved documents"""
        context_parts = []
        
        for i, doc in enumerate(docs, 1):
            meta = doc["metadata"]
            text = doc["text"]
            
            # Format: [Source #] Title - Category\nText
            context_part = (
                f"[Source {i}] {meta.get('title', 'Untitled')} "
                f"({meta.get('category', 'Unknown')})\n{text}\n"
            )
            context_parts.append(context_part)
        
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
1. Base your answer on the provided context
2. Cite sources using [Source #] notation
3. Be precise and factual
4. If the context doesn't contain enough information, say so
5. Use clear, professional language"""

        # User prompt
        user_prompt = f"""Context from relevant documents:

{context}

Question: {query}

Please provide a detailed answer based on the context above. Include source citations using [Source #] notation."""

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
                return response.choices[0].message.content
            
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
                return response.content[0].text
            
            else:
                return "LLM provider not supported"
                
        except Exception as e:
            logger.error(f"Error generating answer: {e}")
            return f"Error generating answer: {str(e)}"
    
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
