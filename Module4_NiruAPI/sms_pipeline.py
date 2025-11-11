"""
SMS-Optimized RAG Pipeline
Handles SMS queries with 160-character response limit and simple language
"""
from typing import Dict, Optional
from loguru import logger
import re


class SMSPipeline:
    """RAG pipeline optimized for SMS responses"""
    
    def __init__(self, vector_store, llm_service):
        """
        Initialize SMS pipeline
        
        Args:
            vector_store: ChromaDB vector store instance
            llm_service: Moonshot LLM service instance
        """
        self.vector_store = vector_store
        self.llm_service = llm_service
        self.max_sms_length = 160
        
    def process_sms_query(
        self,
        query: str,
        language: str = "en",
        phone_number: Optional[str] = None
    ) -> Dict:
        """
        Process SMS query and return concise response
        
        Args:
            query: User's SMS query text
            language: Response language ('en' for English, 'sw' for Swahili)
            phone_number: User's phone number for logging
            
        Returns:
            Dictionary with response, sources, and metadata
        """
        try:
            logger.info(f"SMS query from {phone_number}: {query}")
            
            # Detect query type for better retrieval
            query_type = self._detect_query_type(query)
            
            # Retrieve relevant context
            results = self.vector_store.search(
                query_text=query,
                top_k=3,  # Fewer results for SMS context
                filter_dict=self._get_category_filter(query_type)
            )
            
            if not results:
                return {
                    "response": "No information found. Try rephrasing your question." if language == "en" else "Hakuna taarifa. Jaribu kuuliza kwa njia nyingine.",
                    "sources": [],
                    "query_type": query_type,
                    "truncated": False
                }
            
            # Generate SMS-optimized response
            response_text = self._generate_sms_response(
                query=query,
                context_chunks=results,
                language=language,
                query_type=query_type
            )
            
            # Extract source info
            sources = self._extract_sources(results)
            
            return {
                "response": response_text,
                "sources": sources,
                "query_type": query_type,
                "truncated": len(response_text) >= self.max_sms_length,
                "phone_number": phone_number
            }
            
        except Exception as e:
            logger.error(f"Error processing SMS query: {e}")
            error_msg = "Service error. Please try again." if language == "en" else "Kosa la huduma. Jaribu tena."
            return {
                "response": error_msg,
                "sources": [],
                "query_type": "error",
                "truncated": False
            }
    
    def _detect_query_type(self, query: str) -> str:
        """Detect the type of query for better filtering"""
        query_lower = query.lower()
        
        # Legal/Constitutional queries
        if any(word in query_lower for word in ["bill", "law", "constitution", "article", "act", "legal"]):
            return "legal"
        
        # Parliament queries
        if any(word in query_lower for word in ["parliament", "mp", "debate", "hansard", "senator"]):
            return "parliament"
        
        # News queries
        if any(word in query_lower for word in ["news", "latest", "today", "happening", "current"]):
            return "news"
        
        # Default
        return "general"
    
    def _get_category_filter(self, query_type: str) -> Optional[Dict]:
        """Get category filter based on query type"""
        filters = {
            "legal": {"category": {"$in": ["Kenya Law", "Constitutional Document"]}},
            "parliament": {"category": "Parliamentary Record"},
            "news": {"category": {"$in": ["Kenyan News", "Global Trend"]}},
            "general": None  # No filter for general queries
        }
        return filters.get(query_type)
    
    def _generate_sms_response(
        self,
        query: str,
        context_chunks: list,
        language: str,
        query_type: str
    ) -> str:
        """Generate concise SMS response using LLM"""
        
        # Build minimal context
        context_text = "\n\n".join([
            f"Source: {chunk['metadata'].get('source_name', 'Unknown')}\n{chunk['text'][:200]}"
            for chunk in context_chunks[:2]  # Only use top 2 for SMS
        ])
        
        # SMS-specific prompt
        if language == "en":
            prompt = f"""Answer this question in EXACTLY 160 characters or less. Be direct and simple.

Question: {query}

Context:
{context_text}

Rules:
- Maximum 160 characters
- Simple words only
- No jargon
- Direct answer
- Include key fact or number if relevant

Answer:"""
        else:  # Swahili
            prompt = f"""Jibu swali hili kwa UREFU wa vibambo 160 au chini. Kuwa moja kwa moja na rahisi.

Swali: {query}

Muktadha:
{context_text}

Sheria:
- Vibambo 160 tu
- Maneno rahisi
- Jibu moja kwa moja
- Pamoja na ukweli muhimu

Jibu:"""
        
        try:
            # Call LLM with strict parameters
            response = self.llm_service.generate(
                prompt=prompt,
                temperature=0.3,  # Low temperature for consistency
                max_tokens=100,   # Strict token limit
            )
            
            # Clean and truncate response
            response = response.strip()
            response = re.sub(r'\s+', ' ', response)  # Remove extra whitespace
            
            # Hard truncate to SMS limit
            if len(response) > self.max_sms_length:
                response = response[:157] + "..."
            
            return response
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            # Fallback to simple extraction
            return self._fallback_response(context_chunks, language)
    
    def _fallback_response(self, context_chunks: list, language: str) -> str:
        """Fallback response if LLM fails"""
        if not context_chunks:
            return "No info found" if language == "en" else "Hakuna taarifa"
        
        # Extract first sentence from top result
        text = context_chunks[0]['text']
        sentences = re.split(r'[.!?]', text)
        first_sentence = sentences[0].strip() if sentences else text
        
        # Truncate to SMS limit
        if len(first_sentence) > self.max_sms_length:
            return first_sentence[:157] + "..."
        
        return first_sentence
    
    def _extract_sources(self, results: list) -> list:
        """Extract source information from results"""
        sources = []
        for chunk in results[:2]:  # Only top 2 sources
            metadata = chunk.get("metadata", {})
            sources.append({
                "title": metadata.get("title", "Unknown"),
                "source_name": metadata.get("source_name", "Unknown"),
                "url": metadata.get("url", ""),
            })
        return sources
    
    def format_multi_sms(self, long_response: str) -> list:
        """
        Split long response into multiple SMS messages
        
        Args:
            long_response: Response text longer than 160 chars
            
        Returns:
            List of SMS messages, each ≤160 characters
        """
        if len(long_response) <= self.max_sms_length:
            return [long_response]
        
        messages = []
        words = long_response.split()
        current_msg = ""
        
        for word in words:
            if len(current_msg) + len(word) + 1 <= self.max_sms_length - 5:  # Reserve space for "(1/2)"
                current_msg += word + " "
            else:
                messages.append(current_msg.strip())
                current_msg = word + " "
        
        if current_msg:
            messages.append(current_msg.strip())
        
        # Add part indicators
        if len(messages) > 1:
            total = len(messages)
            messages = [f"({i+1}/{total}) {msg}" for i, msg in enumerate(messages)]
        
        return messages
