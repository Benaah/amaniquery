"""
AmaniQuery v2.0 - Persona-Specific Retrieval Strategies
========================================================

Production-ready retrieval logic for Weaviate and Qdrant vector databases
optimized for three Kenyan civic AI personas:

- wanjiku: Hybrid search with recency boost
- wakili: Precision semantic search on legal documents
- mwanahabari: Keyword + metadata filtering for data/statistics

Usage:
    from Module4_NiruAPI.agents.retrieval_strategies import (
        WeaviateRetriever,
        QdrantRetriever
    )
"""

import numpy as np
from typing import List, Dict, Any, Optional, Literal
from datetime import datetime, timedelta
import weaviate
from weaviate.classes.query import MetadataQuery, Filter
from qdrant_client import QdrantClient
from qdrant_client.models import (
    Filter as QFilter,
    FieldCondition,
    MatchValue,
    Range,
    SearchRequest,
    ScoredPoint
)


# ============================================================================
# WEAVIATE RETRIEVAL STRATEGIES
# ============================================================================

class WeaviateRetriever:
    """
    Weaviate-based retrieval with persona-specific optimization.
    
    Schema Assumptions:
    - Collection: "amaniquery_docs"
    - Properties: text, doc_type, date_published, source, mp_name, committee, 
                 has_tables, metadata_tags
    - Vector: 768-dim embeddings (e.g., sentence-transformers)
    """
    
    def __init__(self, client: weaviate.WeaviateClient, collection_name: str = "amaniquery_docs"):
        """
        Initialize Weaviate retriever.
        
        Args:
            client: Weaviate client instance
            collection_name: Name of the collection to search
        """
        self.client = client
        self.collection = client.collections.get(collection_name)
    
    def retrieve_wanjiku(
        self,
        query: str,
        limit: int = 8,  # OPTIMIZATION: Reduced from 10 to 8 for faster synthesis
        recency_months: int = 6,
        alpha: float = 0.5,  # OPTIMIZATION: Configurable hybrid search weight
        min_date: Optional[datetime] = None  # OPTIMIZATION: Zero-cost metadata pre-filter
    ) -> List[Dict[str, Any]]:
        """
        Wanjiku retrieval: Configurable hybrid search with recency boost.
        
        Strategy:
        - Hybrid search (BM25 + vector) with configurable alpha (default 0.5)
        - Metadata pre-filtering for recent docs (default: 2023-01-01+)
        - Boost documents < 6 months old
        - Prioritize documents tagged as "explainer"
        - Reduced chunk limit (8) for 3x faster synthesis
        
        Args:
            query: User query (can be in Sheng/Swahili)
            limit: Number of results to return (default: 8, down from 10)
            recency_months: Boost docs published within this timeframe
            alpha: Hybrid search weight (0=keyword, 1=semantic, default=0.5)
            min_date: Minimum date filter for zero-cost pre-filtering
            
        Returns:
            List of search results with scores
        """
        # OPTIMIZATION: Zero-cost metadata pre-filter (default: recent docs only)
        if min_date is None:
            # Default: Only search docs from 2023-01-01 onwards (most users want recent)
            min_date = datetime(2023, 1, 1)
        
        # Calculate recency cutoff date for boosting
        recency_cutoff = datetime.now() - timedelta(days=recency_months * 30)
        recency_timestamp = int(recency_cutoff.timestamp())
        min_date_timestamp = int(min_date.timestamp())
        
        # Rewrite query to simple English (in production, use LLM)
        simple_query = self._simplify_query_for_search(query)
        
        # Build metadata pre-filter (zero-cost, happens before vector search)
        date_filter = Filter.by_property("date_published").greater_or_equal(min_date_timestamp)
        
        # OPTIMIZATION: Hybrid search with configurable alpha
        response = self.collection.query.hybrid(
            query=simple_query,
            alpha=alpha,  # Configurable: 0=keyword, 1=semantic
            limit=limit * 2,  # Retrieve more for post-processing
            filters=date_filter,  # Pre-filter by date (zero-cost)
            return_metadata=MetadataQuery(score=True, explain_score=True),
            return_properties=["text", "doc_type", "date_published", "source", "metadata_tags"]
        )
        
        # Post-process: Apply recency and explainer boosts
        results = []
        for item in response.objects:
            base_score = item.metadata.score
            
            # Recency boost: +20% if published within recency_months
            recency_boost = 1.0
            if hasattr(item.properties, 'date_published'):
                doc_timestamp = item.properties.get('date_published', 0)
                if doc_timestamp and doc_timestamp >= recency_timestamp:
                    recency_boost = 1.2
            
            # Explainer boost: +15% if tagged as explainer
            explainer_boost = 1.0
            metadata_tags = item.properties.get('metadata_tags', [])
            if 'explainer' in metadata_tags or 'summary' in metadata_tags:
                explainer_boost = 1.15
            
            # Combined score
            final_score = base_score * recency_boost * explainer_boost
            
            results.append({
                'text': item.properties.get('text', ''),
                'doc_type': item.properties.get('doc_type', ''),
                'source': item.properties.get('source', ''),
                'date_published': item.properties.get('date_published'),
                'score': final_score,
                'metadata': item.properties
            })
        
        # Sort by final score and return top results
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]
    
    def retrieve_wakili(
        self,
        query: str,
        limit: int = 4,  # OPTIMIZATION: Lawyers want exact clauses, not many results
        doc_types: List[str] = ["act", "bill", "judgment", "constitution"],
        alpha: float = 0.95,  # OPTIMIZATION: 95% semantic, 5% keyword for precision
        min_date: Optional[datetime] = None  # OPTIMIZATION: Optional date filter
    ) -> List[Dict[str, Any]]:
        """
        Wakili retrieval: High-precision semantic search on legal documents.
        
        Strategy:
        - Hybrid with alpha=0.95 (95% semantic + 5% keyword for precision)
        - Metadata pre-filter by doc_type (zero-cost)
        - Reduced chunk limit (4) - wakili want exact clauses
        - Search clause-level chunks
        
        Args:
            query: Legal query (formal language)
            limit: Number of results (default: 4, down from 10)
            doc_types: Allowed document types for zero-cost pre-filtering
            alpha: Hybrid search weight (default: 0.95 for high semantic precision)
            min_date: Optional minimum date filter
            
        Returns:
            List of legal document chunks with citations
        """
        # OPTIMIZATION: Build zero-cost metadata pre-filter
        filters = [Filter.by_property("doc_type").contains_any(doc_types)]
        
        # Optional date filter
        if min_date:
            filters.append(
                Filter.by_property("date_published").greater_or_equal(int(min_date.timestamp()))
            )
        
        # Combine filters
        combined_filter = filters[0]
        for f in filters[1:]:
            combined_filter = combined_filter & f
        
        # OPTIMIZATION: Hybrid search with high alpha for semantic precision
        response = self.collection.query.hybrid(
            query=query,
            alpha=alpha,  # Default 0.95: 95% semantic (vector) + 5% keyword (BM25)
            limit=limit,
            filters=combined_filter,  # Pre-filter by doc_type and date (zero-cost)
            return_metadata=MetadataQuery(score=True, distance=True),
            return_properties=[
                "text", "doc_type", "source", "section_number", 
                "article_number", "clause_text", "date_enacted"
            ]
        )
        
        # Format results with legal citations
        results = []
        for item in response.objects:
            # Construct formal citation
            citation = self._build_legal_citation(item.properties)
            
            results.append({
                'text': item.properties.get('text', ''),
                'clause_text': item.properties.get('clause_text', ''),
                'citation': citation,
                'doc_type': item.properties.get('doc_type', ''),
                'source': item.properties.get('source', ''),
                'section': item.properties.get('section_number'),
                'article': item.properties.get('article_number'),
                'score': item.metadata.score,
                'distance': item.metadata.distance,
                'metadata': item.properties
            })
        
        return results
    
    def retrieve_mwanahabari(
        self,
        query: str,
        limit: int = 12,  # OPTIMIZATION: Reduced from 20 to 12 for faster synthesis
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        mp_name: Optional[str] = None,
        committee: Optional[str] = None,
        require_tables: bool = True,
        alpha: float = 0.3,  # OPTIMIZATION: 30% semantic, 70% keyword for data precision
        min_date: Optional[datetime] = None  # OPTIMIZATION: Zero-cost metadata pre-filter
    ) -> List[Dict[str, Any]]:
        """
        Mwanahabari retrieval: Keyword-heavy search with metadata filtering for data.
        
        Strategy:
        - Hybrid search with alpha=0.3 (70% keyword, 30% semantic for data precision)
        - Zero-cost metadata pre-filtering (default: 2023-01-01+)
        - Strong metadata filters (dates, MPs, committees)
        - Prioritize documents with tables/statistics
        - Reduced chunk limit (12) for faster data aggregation
        
        Args:
            query: Data-focused query
            limit: Number of results (default: 12, down from 20)
            date_from: Start date filter
            date_to: End date filter
            mp_name: Filter by specific MP
            committee: Filter by parliamentary committee
            require_tables: Only return docs with data tables
            alpha: Hybrid search weight (default: 0.3 for keyword-heavy)
            min_date: Minimum date filter for zero-cost pre-filtering
            
        Returns:
            List of data-rich documents with statistics
        """
        # OPTIMIZATION: Zero-cost metadata pre-filter (default: recent docs)
        if min_date is None:
            min_date = datetime(2023, 1, 1)
        
        # Build complex filter
        filters = [
            Filter.by_property("date_published").greater_or_equal(int(min_date.timestamp()))
        ]
        
        # Date range filter (overrides min_date if provided)
        if date_from:
            filters[-1] = Filter.by_property("date_published").greater_or_equal(
                int(date_from.timestamp())
            )
        if date_to:
            filters.append(
                Filter.by_property("date_published").less_or_equal(
                    int(date_to.timestamp())
                )
            )
        
        # MP name filter (case-insensitive partial match)
        if mp_name:
            filters.append(
                Filter.by_property("mp_name").like(f"*{mp_name}*")
            )
        
        # Committee filter
        if committee:
            filters.append(
                Filter.by_property("committee").equal(committee)
            )
        
        # Tables/data requirement
        if require_tables:
            filters.append(
                Filter.by_property("has_tables").equal(True)
            )
        
        # Combine filters
        combined_filter = None
        if filters:
            combined_filter = filters[0]
            for f in filters[1:]:
                combined_filter = combined_filter & f
        
        # Pure keyword search (alpha=0 = 100% BM25)
        response = self.collection.query.hybrid(
            query=query,
            alpha=0.0,  # 100% keyword search for precision on data queries
            limit=limit,
            filters=combined_filter,
            return_metadata=MetadataQuery(score=True),
            return_properties=[
                "text", "source", "date_published", "mp_name", 
                "committee", "tables", "statistics", "voting_record"
            ]
        )
        
        # Extract and structure data
        results = []
        for item in response.objects:
            # Extract tables and statistics if available
            tables = item.properties.get('tables', [])
            statistics = item.properties.get('statistics', {})
            voting_record = item.properties.get('voting_record', {})
            
            results.append({
                'text': item.properties.get('text', ''),
                'source': item.properties.get('source', ''),
                'date_published': item.properties.get('date_published'),
                'mp_name': item.properties.get('mp_name'),
                'committee': item.properties.get('committee'),
                'tables': tables,
                'statistics': statistics,
                'voting_record': voting_record,
                'score': item.metadata.score,
                'metadata': item.properties
            })
        
        return results
    
    # Helper methods
    
    def _simplify_query_for_search(self, query: str) -> str:
        """
        Simplify Sheng/Swahili query to English for better retrieval.
        
        In production, use Sheng Translator module.
        For now, basic keyword mapping.
        """
        # Basic Sheng → English mapping
        replacements = {
            'kanjo': 'nairobi city county',
            'bunge': 'parliament',
            'mheshimiwa': 'member of parliament MP',
            'doh': 'money fees',
            'serikali': 'government',
            'wabunge': 'members of parliament MPs',
        }
        
        simple = query.lower()
        for sheng, english in replacements.items():
            simple = simple.replace(sheng, english)
        
        return simple
    
    def _build_legal_citation(self, properties: Dict) -> str:
        """Build proper legal citation from document properties"""
        doc_type = properties.get('doc_type', '')
        source = properties.get('source', '')
        
        if doc_type == 'constitution':
            article = properties.get('article_number')
            return f"Constitution of Kenya, 2010, Article {article}"
        
        elif doc_type in ['act', 'bill']:
            section = properties.get('section_number')
            year = properties.get('date_enacted', '')[:4]
            return f"{source}, {year}, Section {section}"
        
        elif doc_type == 'judgment':
            return f"{source}"
        
        else:
            return source


# ============================================================================
# QDRANT RETRIEVAL STRATEGIES
# ============================================================================

class QdrantRetriever:
    """
    Qdrant-based retrieval with persona-specific optimization.
    
    Collection Schema:
    - Collection: "kenyan_civic_docs"
    - Payload: {
        text, doc_type, date_published, source, mp_name, committee,
        has_tables, metadata_tags, section_number, article_number
      }
    - Vector: 768-dim
    """
    
    def __init__(self, client: QdrantClient, collection_name: str = "amaniquery_docs", embedder=None):
        """
        Initialize Qdrant retriever.
        
        Args:
            client: Qdrant client instance
            collection_name: Collection to search
            embedder: Optional embedding model/function
        """
        self.client = client
        self.collection_name = collection_name
        self.embedder = embedder
        
    def _get_embedding(self, text: str) -> List[float]:
        """Generate embedding for text using the provided embedder"""
        if not self.embedder:
            raise ValueError("Embedder not initialized, cannot generate vector from text")
        
        if hasattr(self.embedder, 'encode'):
            # SentenceTransformer style
            return self.embedder.encode(text).tolist()
        elif callable(self.embedder):
            # Function style
            return self.embedder(text)
        else:
            raise ValueError(f"Unsupported embedder type: {type(self.embedder)}")

    def _cosine_similarity(self, v1: List[float], v2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        a = np.array(v1)
        b = np.array(v2)
        norm_a = np.linalg.norm(a)
        norm_b = np.linalg.norm(b)
        if norm_a == 0 or norm_b == 0:
            return 0.0
        return np.dot(a, b) / (norm_a * norm_b)

    def _mmr(self, query_vector: List[float], docs: List[Any], diversity: float, limit: int) -> List[Any]:
        """
        Maximal Marginal Relevance (MMR) re-ranking.
        
        Args:
            query_vector: Query embedding
            docs: List of Qdrant ScoredPoint objects (must have vectors)
            diversity: Diversity parameter (0.0 = pure relevance, 1.0 = pure diversity)
            limit: Number of documents to select
            
        Returns:
            Selected documents
        """
        if not docs:
            return []
            
        selected = []
        candidates = docs[:]
        
        while len(selected) < limit and candidates:
            best_score = -float('inf')
            best_doc = None
            
            for doc in candidates:
                # Relevance: Cosine similarity to query (already in doc.score)
                relevance = doc.score
                
                # Diversity: Max similarity to already selected docs
                if not selected:
                    max_sim_selected = 0.0
                else:
                    # Calculate max similarity to any selected doc
                    # Note: doc.vector must be available (use with_vectors=True in search)
                    if doc.vector is None:
                        # Fallback if vector missing
                        max_sim_selected = 0.0
                    else:
                        sims = [self._cosine_similarity(doc.vector, s.vector) for s in selected]
                        max_sim_selected = max(sims) if sims else 0.0
                
                # MMR Score = (1-lambda)*Relevance - lambda*MaxSim
                mmr_score = (1 - diversity) * relevance - diversity * max_sim_selected
                
                if mmr_score > best_score:
                    best_score = mmr_score
                    best_doc = doc
            
            if best_doc:
                selected.append(best_doc)
                candidates.remove(best_doc)
            else:
                break
                
        return selected
    
    def retrieve_wanjiku(
        self,
        query: str = None,
        query_vector: List[float] = None,
        query_text: str = None,
        limit: int = 8,  # OPTIMIZATION: Reduced from 10 to 8
        recency_months: int = 6,
        diversity: float = 0.5,  # MMR Diversity parameter
        min_date: Optional[datetime] = None  # OPTIMIZATION: Zero-cost metadata pre-filter
    ) -> List[Dict[str, Any]]:
        """
        Wanjiku retrieval: Hybrid search with recency boost and MMR diversity.
        
        Note: Qdrant requires separate dense + sparse vectors for hybrid.
        This implementation uses dense vector + payload filtering.
        
        Args:
            query: Query text (alias for query_text)
            query_vector: Dense embedding of query
            query_text: Original query text for keyword matching
            limit: Number of results
            recency_months: Boost recent documents
            diversity: MMR diversity parameter (0.5 = balanced)
            min_date: Minimum date filter
            
        Returns:
            List of search results
        """
        # Handle arguments
        text_query = query or query_text
        if not text_query and not query_vector:
            raise ValueError("Must provide either query text or vector")
            
        # Generate vector if missing
        if not query_vector and text_query:
            query_vector = self._get_embedding(text_query)
            
        # OPTIMIZATION: Zero-cost metadata pre-filter
        if min_date is None:
            min_date = datetime(2023, 1, 1)
            
        # Calculate recency cutoff
        recency_cutoff = datetime.now() - timedelta(days=recency_months * 30)
        recency_timestamp = int(recency_cutoff.timestamp())
        min_date_timestamp = int(min_date.timestamp())
        
        # Build filter
        must_conditions = [
            FieldCondition(
                key="date_published",
                range=Range(gte=min_date_timestamp)
            )
        ]
        filter_condition = QFilter(must=must_conditions)
        
        # Search with dense vector
        # Fetch more candidates for MMR (limit * 4)
        search_limit = limit * 4 if diversity > 0 else limit * 2
        
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=filter_condition,
            limit=search_limit,
            with_payload=True,
            with_vectors=True if diversity > 0 else False,  # Need vectors for MMR
            score_threshold=0.5  # Minimum relevance
        )
        
        # Apply boosts to base scores BEFORE MMR
        for hit in search_result:
            base_score = hit.score
            payload = hit.payload
            
            # Recency boost
            recency_boost = 1.0
            doc_date = payload.get('date_published', 0)
            if doc_date and doc_date >= recency_timestamp:
                recency_boost = 1.2
            
            # Explainer boost
            explainer_boost = 1.0
            tags = payload.get('metadata_tags', [])
            if tags and ('explainer' in tags or 'summary' in tags):
                explainer_boost = 1.15
            
            # Update score in place
            hit.score = base_score * recency_boost * explainer_boost

        # Apply MMR if diversity > 0
        if diversity > 0:
            search_result = self._mmr(query_vector, search_result, diversity, limit)
        else:
            # Sort by boosted score and take top limit
            search_result.sort(key=lambda x: x.score, reverse=True)
            search_result = search_result[:limit]
        
        # Format results
        results = []
        for hit in search_result:
            payload = hit.payload
            results.append({
                'id': hit.id,
                'text': payload.get('text', ''),
                'doc_type': payload.get('doc_type', ''),
                'source': payload.get('source', ''),
                'date_published': payload.get('date_published'),
                'score': hit.score,
                'payload': payload
            })
        
        return results
    
    def retrieve_wakili(
        self,
        query: str = None,
        query_vector: List[float] = None,
        query_text: str = None,
        limit: int = 4,  # OPTIMIZATION: Reduced from 10 to 4
        doc_types: List[str] = ["act", "bill", "judgment", "constitution"],
        min_date: Optional[datetime] = None  # OPTIMIZATION: Optional date filter
    ) -> List[Dict[str, Any]]:
        """
        Wakili retrieval: Pure semantic search on legal docs.
        
        Strategy:
        - Dense vector search (no hybrid needed - semantic only)
        - Strong filter on legal document types
        
        Args:
            query: Query text (alias for query_text)
            query_vector: Dense embedding
            query_text: Original query text
            limit: Number of results
            doc_types: Allowed document types
            min_date: Optional minimum date filter
            
        Returns:
            Legal document chunks
        """
        # Handle arguments
        text_query = query or query_text
        if not text_query and not query_vector:
            raise ValueError("Must provide either query text or vector")
            
        # Generate vector if missing
        if not query_vector and text_query:
            query_vector = self._get_embedding(text_query)
            
        # Build filter for legal documents
        must_conditions = [
            FieldCondition(
                key="doc_type",
                match=MatchValue(any=doc_types)
            )
        ]
        
        # Optional date filter
        if min_date:
            must_conditions.append(
                FieldCondition(
                    key="date_published",
                    range=Range(gte=int(min_date.timestamp()))
                )
            )
            
        filter_condition = QFilter(must=must_conditions)
        
        # Pure semantic search
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=filter_condition,
            limit=limit,
            with_payload=True,
            score_threshold=0.7  # High threshold for precision
        )
        
        # Format with legal citations
        results = []
        for hit in search_result:
            payload = hit.payload
            citation = self._build_legal_citation_qdrant(payload)
            
            results.append({
                'id': hit.id,
                'text': payload.get('text', ''),
                'citation': citation,
                'doc_type': payload.get('doc_type', ''),
                'source': payload.get('source', ''),
                'section': payload.get('section_number'),
                'article': payload.get('article_number'),
                'score': hit.score,
                'payload': payload
            })
        
        return results
    
    def retrieve_mwanahabari(
        self,
        query: str = None,
        query_vector: List[float] = None,
        query_text: str = None,
        limit: int = 12,  # OPTIMIZATION: Reduced from 20 to 12
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        mp_name: Optional[str] = None,
        committee: Optional[str] = None,
        require_tables: bool = True,
        min_date: Optional[datetime] = None  # OPTIMIZATION: Zero-cost metadata pre-filter
    ) -> List[Dict[str, Any]]:
        """
        Mwanahabari retrieval: Metadata-heavy filtering for data.
        
        Strategy:
        - Vector search with strict metadata filters
        - Prioritize documents with tables/statistics
        
        Args:
            query: Query text (alias for query_text)
            query_vector: Dense embedding
            query_text: Original query text
            limit: Number of results
            date_from: Start date
            date_to: End date
            mp_name: Filter by MP
            committee: Filter by committee
            require_tables: Only docs with tables
            min_date: Minimum date filter
            
        Returns:
            Data-rich documents
        """
        # Handle arguments
        text_query = query or query_text
        if not text_query and not query_vector:
            raise ValueError("Must provide either query text or vector")
            
        # Generate vector if missing
        if not query_vector and text_query:
            query_vector = self._get_embedding(text_query)
            
        # OPTIMIZATION: Zero-cost metadata pre-filter
        if min_date is None:
            min_date = datetime(2023, 1, 1)
            
        # Build complex filter
        must_conditions = []
        
        # Date range (overrides min_date if provided)
        start_timestamp = int(min_date.timestamp())
        if date_from:
            start_timestamp = int(date_from.timestamp())
            
        range_condition = {'gte': start_timestamp}
        if date_to:
            range_condition['lte'] = int(date_to.timestamp())
        
        must_conditions.append(
            FieldCondition(
                key="date_published",
                range=Range(**range_condition)
            )
        )
        
        # MP name (case-insensitive partial match for production)
        if mp_name:
            must_conditions.append(
                FieldCondition(
                    key="mp_name",
                    match=MatchValue(text=f"{mp_name}", operator="contains", case_sensitive=False)
                )
            )
        
        # Committee
        if committee:
            must_conditions.append(
                FieldCondition(
                    key="committee",
                    match=MatchValue(value=committee)
                )
            )
        
        # Tables requirement
        if require_tables:
            must_conditions.append(
                FieldCondition(
                    key="has_tables",
                    match=MatchValue(value=True)
                )
            )
        
        # Combine filters
        filter_condition = QFilter(must=must_conditions) if must_conditions else None
        
        # Search with filters
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            query_filter=filter_condition,
            limit=limit,
            with_payload=True
        )
        
        # Extract structured data
        results = []
        for hit in search_result:
            payload = hit.payload
            
            results.append({
                'id': hit.id,
                'text': payload.get('text', ''),
                'source': payload.get('source', ''),
                'date_published': payload.get('date_published'),
                'mp_name': payload.get('mp_name'),
                'committee': payload.get('committee'),
                'tables': payload.get('tables', []),
                'statistics': payload.get('statistics', {}),
                'voting_record': payload.get('voting_record', {}),
                'score': hit.score,
                'payload': payload
            })
        
        return results
    
    def _build_legal_citation_qdrant(self, payload: Dict) -> str:
        """Build legal citation from Qdrant payload"""
        doc_type = payload.get('doc_type', '')
        source = payload.get('source', '')
        
        if doc_type == 'constitution':
            article = payload.get('article_number')
            return f"Constitution of Kenya, 2010, Article {article}"
        elif doc_type in ['act', 'bill']:
            section = payload.get('section_number')
            return f"{source}, Section {section}"
        else:
            return source


# ============================================================================
# UNIFIED RETRIEVER (AUTO-DETECTS BACKEND)
# ============================================================================

class UnifiedRetriever:
    """
    Unified interface that auto-detects Weaviate or Qdrant backend.
    """
    
    def __init__(self, backend: Literal["weaviate", "qdrant"], client, collection_name: str, embedder=None):
        """
        Initialize unified retriever.
        
        Args:
            backend: "weaviate" or "qdrant"
            client: Weaviate or Qdrant client instance
            collection_name: Collection to search
            embedder: Optional embedding model/function (required for Qdrant)
        """
        if backend == "weaviate":
            self.retriever = WeaviateRetriever(client, collection_name)
        elif backend == "qdrant":
            self.retriever = QdrantRetriever(client, collection_name, embedder=embedder)
        else:
            raise ValueError(f"Unsupported backend: {backend}")
        
        self.backend = backend
    
    def retrieve(
        self,
        query_type: Literal["wanjiku", "wakili", "mwanahabari"],
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Route to appropriate retrieval strategy based on query_type.
        
        Args:
            query_type: User persona
            **kwargs: Strategy-specific arguments
            
        Returns:
            Search results
        """
        if query_type == "wanjiku":
            return self.retriever.retrieve_wanjiku(**kwargs)
        elif query_type == "wakili":
            return self.retriever.retrieve_wakili(**kwargs)
        elif query_type == "mwanahabari":
            return self.retriever.retrieve_mwanahabari(**kwargs)
        else:
            raise ValueError(f"Invalid query_type: {query_type}")


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    print("="*80)
    print("RETRIEVAL STRATEGIES - USAGE EXAMPLES")
    print("="*80)
    
    # Example 1: Weaviate for Wanjiku
    print("\n1. WEAVIATE - WANJIKU RETRIEVAL")
    print("-"*80)
    print("""
    import weaviate
    from retrieval_strategies import WeaviateRetriever
    
    client = weaviate.connect_to_local()
    retriever = WeaviateRetriever(client)
    
    results = retriever.retrieve_wanjiku(
        query="Kanjo wameongeza parking fees aje?",
        limit=10,
        recency_months=6
    )
    
    for r in results:
        print(f"Source: {r['source']}")
        print(f"Score: {r['score']:.3f}")
        print(f"Text: {r['text'][:200]}...")
    """)
    
    # Example 2: Qdrant for Wakili
    print("\n2. QDRANT - WAKILI RETRIEVAL")
    print("-"*80)
    print("""
    from qdrant_client import QdrantClient
    from retrieval_strategies import QdrantRetriever
    
    client = QdrantClient("localhost", port=6333)
    retriever = QdrantRetriever(client)
    
    # Get query embedding (use your embedding model)
    query_vector = embedding_model.encode("Article 201 public finance principles")
    
    results = retriever.retrieve_wakili(
        query_vector=query_vector,
        limit=10,
        doc_types=["constitution", "act"]
    )
    
    for r in results:
        print(f"Citation: {r['citation']}")
        print(f"Score: {r['score']:.3f}")
        print(f"Text: {r['text'][:200]}...")
    """)
    
    # Example 3: Unified retriever
    print("\n3. UNIFIED RETRIEVER")
    print("-"*80)
    print("""
    from retrieval_strategies import UnifiedRetriever
    
    # Works with either backend
    retriever = UnifiedRetriever(
        backend="weaviate",  # or "qdrant"
        client=client,
        collection_name="amaniquery_docs"
    )
    
    # Auto-routes based on query_type
    results = retriever.retrieve(
        query_type="mwanahabari",
        query_vector=query_vec,
        date_from=datetime(2024, 1, 1),
        committee="Finance Committee",
        require_tables=True
    )
    """)
    
    print("\n" + "="*80)
    print("CONFIGURATION COMPLETE")
    print("="*80)
