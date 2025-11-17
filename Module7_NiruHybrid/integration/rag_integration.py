"""
RAG Integration Layer 
Integrates hybrid encoder, diffusion models, adaptive retrieval, and agentic components
with the existing RAGPipeline.
"""
import torch
from typing import List, Dict, Optional, Any
import time
from datetime import datetime
from loguru import logger
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from Module4_NiruAPI.rag_pipeline import RAGPipeline
from Module3_NiruDB.vector_store import VectorStore
from Module7_NiruHybrid.agents.hybrid_retrieval import HybridRetrieval
from Module7_NiruHybrid.agents.multi_agent_composition import MultiAgentComposition
from Module7_NiruHybrid.agents.structured_outputs import StructuredOutputs
from ..hybrid_encoder import HybridEncoder
from ..retention.adaptive_retriever import AdaptiveRetriever
from ..retention.memory_manager import MemoryManager
from ..retention.continual_learner import ContinualLearner
from ..diffusion.text_diffusion import TextDiffusionModel
from ..diffusion.embedding_diffusion import EmbeddingDiffusionModel
from ..streaming.stream_processor import StreamProcessor, AsyncStreamProcessor
from ..integration.vector_store_adapter import HybridVectorStoreAdapter
from ..config import HybridPipelineConfig, default_config


class HybridRAGPipeline:
    """
    Enhanced RAG pipeline with hybrid encoder, diffusion models,
    adaptive retrieval, and agentic components.
    
    Implements error handling, retry logic, multi-agent composition,
    structured output validation, and graceful degradation.
    """
    
    def __init__(
        self,
        base_rag_pipeline: RAGPipeline,
        hybrid_encoder: Optional[HybridEncoder] = None,
        text_diffusion: Optional[TextDiffusionModel] = None,
        embedding_diffusion: Optional[EmbeddingDiffusionModel] = None,
        adaptive_retriever: Optional[AdaptiveRetriever] = None,
        memory_manager: Optional[MemoryManager] = None,
        continual_learner: Optional[ContinualLearner] = None,
        stream_processor: Optional[StreamProcessor] = None,
        use_hybrid: bool = True,
        use_diffusion: bool = True,
        use_adaptive_retrieval: bool = True,
        use_agents: bool = True,
        use_structured_outputs: bool = True,
        max_retries: int = 3,
        timeout: float = 30.0,
        config: Optional[HybridPipelineConfig] = None
    ):
        """
        Initialize hybrid RAG pipeline
        
        Args:
            base_rag_pipeline: Existing RAGPipeline instance
            hybrid_encoder: Hybrid encoder for enhanced embeddings
            text_diffusion: Text-to-text diffusion model
            embedding_diffusion: Text-to-embedding diffusion model
            adaptive_retriever: Adaptive retriever for context-aware retrieval
            memory_manager: Memory manager for pattern retention
            continual_learner: Continual learning system
            stream_processor: Stream processor for real-time processing
            use_hybrid: Whether to use hybrid encoder
            use_diffusion: Whether to use diffusion models
            use_adaptive_retrieval: Whether to use adaptive retrieval
            config: Configuration
        """
        self.base_rag = base_rag_pipeline
        self.hybrid_encoder = hybrid_encoder
        self.text_diffusion = text_diffusion
        self.embedding_diffusion = embedding_diffusion
        self.adaptive_retriever = adaptive_retriever
        self.memory_manager = memory_manager
        self.continual_learner = continual_learner
        self.stream_processor = stream_processor
        
        self.use_hybrid = use_hybrid
        self.use_diffusion = use_diffusion
        self.use_adaptive_retrieval = use_adaptive_retrieval
        self.use_agents = use_agents
        self.use_structured_outputs = use_structured_outputs
        self.max_retries = max_retries
        self.timeout = timeout
        self.config = config or default_config
        
        # Initialize enhanced hybrid retrieval
        try:
            self.hybrid_retrieval = HybridRetrieval(
                vector_store=self.base_rag.vector_store,
                enable_agents=use_agents,
                enable_structured_outputs=use_structured_outputs,
                max_retries=max_retries,
                timeout=timeout
            )
            logger.info("Enhanced hybrid retrieval initialized")
        except Exception as e:
            logger.warning(f"Failed to initialize enhanced hybrid retrieval: {e}")
            self.hybrid_retrieval = None
        
        # Initialize multi-agent composition
        if use_agents:
            try:
                self.multi_agent = MultiAgentComposition()
                logger.info("Multi-agent composition initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize multi-agent composition: {e}")
                self.multi_agent = None
                self.use_agents = False
        else:
            self.multi_agent = None
        
        # Initialize structured outputs
        if use_structured_outputs:
            try:
                self.structured_outputs = StructuredOutputs()
                logger.info("Structured outputs initialized")
            except Exception as e:
                logger.warning(f"Failed to initialize structured outputs: {e}")
                self.structured_outputs = None
                self.use_structured_outputs = False
        else:
            self.structured_outputs = None
        
        # Create vector store adapter if hybrid encoder is available
        if self.hybrid_encoder is not None and self.base_rag.vector_store is not None:
            try:
                self.vector_store_adapter = HybridVectorStoreAdapter(
                    vector_store=self.base_rag.vector_store,
                    hybrid_encoder=self.hybrid_encoder,
                    use_hybrid=use_hybrid
                )
            except Exception as e:
                logger.warning(f"Failed to initialize vector store adapter: {e}")
                self.vector_store_adapter = None
        else:
            self.vector_store_adapter = None
        
        # Statistics
        self.hybrid_queries = 0
        self.diffusion_generations = 0
        self.adaptive_retrievals = 0
        self.agent_processed_queries = 0
        self.structured_output_queries = 0
        self.error_count = 0
        self.success_count = 0
    
    def query(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
        source: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1500,
        use_hybrid: Optional[bool] = None,
        use_adaptive: Optional[bool] = None,
        generate_augmentation: bool = False,
        use_agents: Optional[bool] = None,
        return_structured: bool = False
    ) -> Dict:
        """
        Enhanced query with hybrid encoder, adaptive retrieval, and agentic components
        
        Args:
            query: User question
            top_k: Number of documents to retrieve (validated and clamped)
            category: Filter by category
            source: Filter by source
            temperature: LLM temperature (0-2)
            max_tokens: Maximum tokens in response
            use_hybrid: Whether to use hybrid encoder (overrides default)
            use_adaptive: Whether to use adaptive retrieval (overrides default)
            generate_augmentation: Whether to generate synthetic documents
            use_agents: Whether to use multi-agent processing (overrides default)
            return_structured: Whether to return structured output (ResearchReport)
        
        Returns:
            Dictionary with answer, sources, and metadata
        """
        if not query or not query.strip():
            logger.warning("Empty query provided")
            return {
                "answer": "Please provide a valid query.",
                "sources": [],
                "error": "Empty query"
            }
        
        # Validate inputs
        top_k = max(1, min(top_k, 100))
        temperature = max(0.0, min(temperature, 2.0))
        max_tokens = max(1, min(max_tokens, 4000))
        
        start_time = time.time()
        use_hybrid = use_hybrid if use_hybrid is not None else self.use_hybrid
        use_adaptive = use_adaptive if use_adaptive is not None else self.use_adaptive_retrieval
        use_agents = use_agents if use_agents is not None else self.use_agents
        
        try:
            # Generate synthetic documents if requested
            if generate_augmentation and self.use_diffusion:
                try:
                    synthetic_docs = self._generate_synthetic_documents(query, num_docs=3)
                    if self.vector_store_adapter is not None and synthetic_docs:
                        self.vector_store_adapter.add_diffusion_generated_documents(
                            generated_texts=synthetic_docs,
                            metadata=[{"category": category or "Generated"} for _ in synthetic_docs]
                        )
                        self.diffusion_generations += len(synthetic_docs)
                except Exception as e:
                    logger.warning(f"Failed to generate synthetic documents: {e}")
            
            # Retrieve documents using enhanced hybrid retrieval if available
            if self.hybrid_retrieval is not None:
                try:
                    filters = {}
                    if category:
                        filters['category'] = category
                    if source:
                        filters['source'] = source
                    
                    retrieved_docs = self.hybrid_retrieval.retrieve(
                        query=query,
                        top_k=top_k,
                        use_reranking=True,
                        use_summary_chunking=True,
                        use_query_expansion=True,
                        use_agents=use_agents
                    )
                    
                    # Convert to expected format
                    retrieved_docs = [
                        {
                            'content': r.get('content', ''),
                            'metadata': r.get('metadata', {}),
                            'score': r.get('combined_score', r.get('score', 0.0))
                        }
                        for r in retrieved_docs
                    ]
                except Exception as e:
                    logger.warning(f"Enhanced retrieval failed, falling back: {e}")
                    retrieved_docs = self._fallback_retrieval(query, top_k, category, use_hybrid, use_adaptive)
            else:
                retrieved_docs = self._fallback_retrieval(query, top_k, category, use_hybrid, use_adaptive)
            
            # Prepare context
            context = self.base_rag._prepare_context(retrieved_docs) if hasattr(self.base_rag, '_prepare_context') else ""
            
            # Generate answer
            answer = self.base_rag._generate_answer(
                query=query,
                context=context,
                temperature=temperature,
                max_tokens=max_tokens
            ) if hasattr(self.base_rag, '_generate_answer') else "Answer generation not available"
            
            # Process with agents if enabled
            if use_agents and self.multi_agent:
                try:
                    sources_list = self.base_rag._format_sources(retrieved_docs) if hasattr(self.base_rag, '_format_sources') else []
                    agent_result = self.multi_agent.process_with_agents(
                        content=answer,
                        sources=sources_list,
                        use_citer=True,
                        use_editor=True,
                        use_validator=True
                    )
                    if agent_result and 'final_result' in agent_result:
                        answer = agent_result['final_result'].get('content', answer)
                        self.agent_processed_queries += 1
                except Exception as e:
                    logger.warning(f"Agent processing failed: {e}")
            
            # Format sources
            sources = self.base_rag._format_sources(retrieved_docs) if hasattr(self.base_rag, '_format_sources') else []
            
            query_time = time.time() - start_time
            
            # Update memory manager if available
            if self.memory_manager is not None:
                try:
                    query_emb = self.hybrid_encoder.encode(text=query, return_pooled=True) if self.hybrid_encoder else None
                    if query_emb is not None:
                        self.memory_manager.add_pattern(
                            pattern_id=f"query_{int(time.time())}",
                            embeddings=query_emb,
                            metadata={"query": query, "num_results": len(retrieved_docs)}
                        )
                except Exception as e:
                    logger.warning(f"Failed to add pattern to memory: {e}")
            
            # Build result
            result = {
                "answer": answer,
                "sources": sources,
                "query_time": query_time,
                "retrieved_chunks": len(retrieved_docs),
                "model_used": getattr(self.base_rag, 'model', 'unknown'),
                "hybrid_used": use_hybrid,
                "adaptive_used": use_adaptive,
                "agents_used": use_agents,
                "timestamp": datetime.utcnow().isoformat()
            }
            
            # Return structured output if requested
            if return_structured and self.structured_outputs:
                try:
                    structured = self.structured_outputs.create_dossier(
                        title=f"Research: {query[:50]}",
                        summary=answer[:500],
                        key_findings=[s.get('title', '')[:100] for s in sources[:5]],
                        sources=[{"title": s.get('title', ''), "url": s.get('url', '')} for s in sources],
                        recommendations=["Review sources", "Verify information"]
                    )
                    result['structured_output'] = structured.dict()
                    self.structured_output_queries += 1
                except Exception as e:
                    logger.warning(f"Structured output generation failed: {e}")
            
            self.success_count += 1
            if use_hybrid:
                self.hybrid_queries += 1
            if use_adaptive:
                self.adaptive_retrievals += 1
            
            return result
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"Error in hybrid RAG query: {e}", exc_info=True)
            return {
                "answer": f"An error occurred while processing your query: {str(e)}",
                "sources": [],
                "error": str(e),
                "query_time": time.time() - start_time
            }
    
    def _fallback_retrieval(
        self,
        query: str,
        top_k: int,
        category: Optional[str],
        use_hybrid: bool,
        use_adaptive: bool
    ) -> List[Dict[str, Any]]:
        """Fallback retrieval method"""
        if use_adaptive and self.adaptive_retriever is not None:
            try:
                return self.adaptive_retriever.retrieve(query_text=query, use_hybrid=use_hybrid)
            except Exception as e:
                logger.warning(f"Adaptive retrieval failed: {e}")
        
        if use_hybrid and self.vector_store_adapter is not None:
            try:
                return self.vector_store_adapter.query(
                    query_text=query,
                    n_results=top_k,
                    filter={"category": category} if category else None,
                    use_hybrid=True
                )
            except Exception as e:
                logger.warning(f"Hybrid retrieval failed: {e}")
        
        # Final fallback to base RAG
        try:
            return self.base_rag.vector_store.query(
                query_text=query,
                n_results=top_k,
                filter={"category": category} if category else None
            )
        except Exception as e:
            logger.error(f"Base retrieval also failed: {e}")
            return []
    
    def query_stream(
        self,
        query: str,
        top_k: int = 5,
        category: Optional[str] = None,
        source: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: int = 1500,
        use_hybrid: Optional[bool] = None
    ):
        """
        Streaming query with hybrid encoder
        
        Args:
            query: User question
            top_k: Number of documents to retrieve
            category: Filter by category
            source: Filter by source
            temperature: LLM temperature
            max_tokens: Maximum tokens in response
            use_hybrid: Whether to use hybrid encoder
        
        Returns:
            Dictionary with answer stream and sources
        """
        start_time = time.time()
        use_hybrid = use_hybrid if use_hybrid is not None else self.use_hybrid
        
        # Retrieve documents (same as query)
        if use_hybrid and self.vector_store_adapter is not None:
            retrieved_docs = self.vector_store_adapter.query(
                query_text=query,
                n_results=top_k,
                filter={"category": category} if category else None,
                use_hybrid=True
            )
        else:
            retrieved_docs = self.base_rag.vector_store.query(
                query_text=query,
                n_results=top_k,
                filter={"category": category} if category else None
            )
        
        # Prepare context
        context = self.base_rag._prepare_context(retrieved_docs)
        
        # Generate streaming answer
        answer_stream = self.base_rag._generate_answer_stream(
            query=query,
            context=context,
            temperature=temperature,
            max_tokens=max_tokens
        )
        
        # Format sources
        sources = self.base_rag._format_sources(retrieved_docs)
        
        query_time = time.time() - start_time
        
        return {
            "answer_stream": answer_stream,
            "sources": sources,
            "query_time": query_time,
            "retrieved_chunks": len(retrieved_docs),
            "model_used": self.base_rag.model,
            "stream": True,
            "hybrid_used": use_hybrid
        }
    
    def _generate_synthetic_documents(
        self,
        query: str,
        num_docs: int = 3
    ) -> List[str]:
        """
        Generate synthetic documents using diffusion models
        
        Args:
            query: Query context
            num_docs: Number of documents to generate
        
        Returns:
            generated_texts: List of generated text documents
        """
        generated_texts = []
        
        # Generate using text diffusion
        if self.text_diffusion is not None:
            for _ in range(num_docs):
                try:
                    generated_text = self.text_diffusion.generate(
                        condition=query,
                        num_steps=50
                    )
                    generated_texts.append(generated_text)
                except Exception as e:
                    logger.warning(f"Failed to generate text: {e}")
        
        return generated_texts
    
    def generate_synthetic_documents(
        self,
        query: Optional[str] = None,
        num_docs: int = 10,
        add_to_store: bool = True
    ) -> List[str]:
        """
        Generate synthetic documents and optionally add to vector store
        
        Args:
            query: Optional query context
            num_docs: Number of documents to generate
            add_to_store: Whether to add to vector store
        
        Returns:
            generated_texts: List of generated documents
        """
        generated_texts = self._generate_synthetic_documents(query or "", num_docs)
        
        if add_to_store and self.vector_store_adapter is not None:
            self.vector_store_adapter.add_diffusion_generated_documents(
                generated_texts=generated_texts,
                metadata=[{"category": "Generated", "query": query} for _ in generated_texts]
            )
        
        self.diffusion_generations += len(generated_texts)
        return generated_texts
    
    def trigger_retention_update(self):
        """Trigger retention update (continual learning)"""
        if self.continual_learner is not None:
            try:
                self.continual_learner.update_model()
                logger.info("Retention update completed")
            except Exception as e:
                logger.error(f"Failed to update retention: {e}")
        else:
            logger.warning("Continual learner not available")
    
    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive pipeline statistics"""
        stats = {
            "hybrid_queries": self.hybrid_queries,
            "diffusion_generations": self.diffusion_generations,
            "adaptive_retrievals": self.adaptive_retrievals,
            "agent_processed_queries": self.agent_processed_queries,
            "structured_output_queries": self.structured_output_queries,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "success_rate": self.success_count / (self.success_count + self.error_count) if (self.success_count + self.error_count) > 0 else 0.0,
            "use_hybrid": self.use_hybrid,
            "use_diffusion": self.use_diffusion,
            "use_adaptive_retrieval": self.use_adaptive_retrieval,
            "use_agents": self.use_agents,
            "use_structured_outputs": self.use_structured_outputs
        }
        
        if self.hybrid_retrieval is not None:
            stats["hybrid_retrieval"] = self.hybrid_retrieval.get_stats()
        
        if self.vector_store_adapter is not None:
            try:
                stats["vector_store_adapter"] = self.vector_store_adapter.get_stats()
            except:
                pass
        
        if self.memory_manager is not None:
            try:
                stats["memory_manager"] = self.memory_manager.get_stats()
            except:
                pass
        
        if self.adaptive_retriever is not None:
            try:
                stats["adaptive_retriever"] = self.adaptive_retriever.get_stats()
            except:
                pass
        
        if self.continual_learner is not None:
            try:
                stats["continual_learner"] = self.continual_learner.get_stats()
            except:
                pass
        
        return stats

