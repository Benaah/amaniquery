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
    QueryVector,
    ScoredPoint
)


# ============================================================================
# WEAVIATE RETRIEVAL STRATEGIES
# ============================================================================

class WeaviateRetriever:
    """
    Weaviate-based retrieval with persona-specific optimization.
    
    Schema Assumptions:
    - Collection: "KenyanCivicDocs"
    - Properties: text, doc_type, date_published, source, mp_name, committee, 
                 has_tables, metadata_tags
    - Vector: 768-dim embeddings (e.g., sentence-transformers)
    """
    
    def __init__(self, client: weaviate.WeaviateClient, collection_name: str = "KenyanCivicDocs"):
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
        limit: int = 10,
        recency_months: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Wanjiku retrieval: 50% keyword + 50% semantic with recency boost.
        
        Strategy:
        - Hybrid search (BM25 + vector) with alpha=0.5
        - Boost documents < 6 months old
        - Prioritize documents tagged as "explainer"
        
        Args:
            query: User query (can be in Sheng/Swahili)
            limit: Number of results to return
            recency_months: Boost docs published within this timeframe
            
        Returns:
            List of search results with scores
        """
        # Calculate recency cutoff date
        recency_cutoff = datetime.now() - timedelta(days=recency_months * 30)
        recency_timestamp = int(recency_cutoff.timestamp())
        
        # Rewrite query to simple English (in production, use LLM)
        simple_query = self._simplify_query_for_search(query)
        
        # Hybrid search with equal weights (alpha=0.5)
        response = self.collection.query.hybrid(
            query=simple_query,
            alpha=0.5,  # 50% keyword (BM25) + 50% semantic (vector)
            limit=limit * 2,  # Retrieve more for filtering
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
        limit: int = 10,
        doc_types: List[str] = ["act", "bill", "judgment", "constitution"]
    ) -> List[Dict[str, Any]]:
        """
        Wakili retrieval: 95% semantic search on legal documents.
        
        Strategy:
        - Hybrid with alpha=0.95 (heavily favor semantic)
        - Filter by legal document types
        - Search clause-level chunks
        
        Args:
            query: Legal query (formal language)
            limit: Number of results
            doc_types: Allowed document types
            
        Returns:
            List of legal document chunks with citations
        """
        # Build filter for legal documents
        doc_type_filter = Filter.by_property("doc_type").contains_any(doc_types)
        
        # Hybrid search heavily weighted toward semantic
        response = self.collection.query.hybrid(
            query=query,
            alpha=0.95,  # 95% semantic (vector) + 5% keyword (BM25)
            limit=limit,
            filters=doc_type_filter,
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
        limit: int = 20,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        mp_name: Optional[str] = None,
        committee: Optional[str] = None,
        require_tables: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Mwanahabari retrieval: Keyword + metadata filtering for data.
        
        Strategy:
        - Pure keyword search (BM25) for precision
        - Strong metadata filters (dates, MPs, committees)
        - Prioritize documents with tables/statistics
        
        Args:
            query: Data-focused query
            limit: Number of results
            date_from: Start date filter
            date_to: End date filter
            mp_name: Filter by specific MP
            committee: Filter by parliamentary committee
            require_tables: Only return docs with data tables
            
        Returns:
            List of data-rich documents with statistics
        """
        # Build complex filter
        filters = []
        
        # Date range filter
        if date_from:
            filters.append(
                Filter.by_property("date_published").greater_or_equal(
                    int(date_from.timestamp())
                )
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
    
    def __init__(self, client: QdrantClient, collection_name: str = "kenyan_civic_docs"):
        """
        Initialize Qdrant retriever.
        
        Args:
            client: Qdrant client instance
            collection_name: Collection to search
        """
        self.client = client
        self.collection_name = collection_name
    
    def retrieve_wanjiku(
        self,
        query_vector: List[float],
        query_text: str,
        limit: int = 10,
        recency_months: int = 6
    ) -> List[Dict[str, Any]]:
        """
        Wanjiku retrieval: Hybrid search with recency boost.
        
        Note: Qdrant requires separate dense + sparse vectors for hybrid.
        This implementation uses dense vector + payload filtering.
        
        Args:
            query_vector: Dense embedding of query
            query_text: Original query text for keyword matching
            limit: Number of results
            recency_months: Boost recent documents
            
        Returns:
            List of search results
        """
        # Calculate recency cutoff
        recency_cutoff = datetime.now() - timedelta(days=recency_months * 30)
        recency_timestamp = int(recency_cutoff.timestamp())
        
        # Build filter for explainer boost
        filter_condition = None  # Optional: can filter by tags
        
        # Search with dense vector
        search_result = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_vector,
            limit=limit * 2,  # Retrieve more for post-processing
            with_payload=True,
            score_threshold=0.5  # Minimum relevance
        )
        
        # Post-process with boosts
        results = []
        for hit in search_result:
            base_score = hit.score
            payload = hit.payload
            
            # Recency boost
            recency_boost = 1.0
            doc_date = payload.get('date_published', 0)
            if doc_date >= recency_timestamp:
                recency_boost = 1.2
            
            # Explainer boost
            explainer_boost = 1.0
            tags = payload.get('metadata_tags', [])
            if 'explainer' in tags or 'summary' in tags:
                explainer_boost = 1.15
            
            final_score = base_score * recency_boost * explainer_boost
            
            results.append({
                'id': hit.id,
                'text': payload.get('text', ''),
                'doc_type': payload.get('doc_type', ''),
                'source': payload.get('source', ''),
                'date_published': payload.get('date_published'),
                'score': final_score,
                'payload': payload
            })
        
        # Sort and return top results
        results.sort(key=lambda x: x['score'], reverse=True)
        return results[:limit]
    
    def retrieve_wakili(
        self,
        query_vector: List[float],
        limit: int = 10,
        doc_types: List[str] = ["act", "bill", "judgment", "constitution"]
    ) -> List[Dict[str, Any]]:
        """
        Wakili retrieval: Pure semantic search on legal docs.
        
        Strategy:
        - Dense vector search (no hybrid needed - semantic only)
        - Strong filter on legal document types
        
        Args:
            query_vector: Dense embedding
            limit: Number of results
            doc_types: Allowed document types
            
        Returns:
            Legal document chunks
        """
        # Build filter for legal documents
        filter_condition = QFilter(
            must=[
                FieldCondition(
                    key="doc_type",
                    match=MatchValue(any=doc_types)
                )
            ]
        )
        
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
        query_vector: List[float],
        limit: int = 20,
        date_from: Optional[datetime] = None,
        date_to: Optional[datetime] = None,
        mp_name: Optional[str] = None,
        committee: Optional[str] = None,
        require_tables: bool = True
    ) -> List[Dict[str, Any]]:
        """
        Mwanahabari retrieval: Metadata-heavy filtering for data.
        
        Strategy:
        - Vector search with strict metadata filters
        - Prioritize documents with tables/statistics
        
        Args:
            query_vector: Dense embedding
            limit: Number of results
            date_from: Start date
            date_to: End date
            mp_name: Filter by MP
            committee: Filter by committee
            require_tables: Only docs with tables
            
        Returns:
            Data-rich documents
        """
        # Build complex filter
        must_conditions = []
        
        # Date range
        if date_from or date_to:
            range_condition = {}
            if date_from:
                range_condition['gte'] = int(date_from.timestamp())
            if date_to:
                range_condition['lte'] = int(date_to.timestamp())
            
            must_conditions.append(
                FieldCondition(
                    key="date_published",
                    range=Range(**range_condition)
                )
            )
        
        # MP name (exact match - extend with fuzzy in production)
        if mp_name:
            must_conditions.append(
                FieldCondition(
                    key="mp_name",
                    match=MatchValue(value=mp_name)
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
    
    def __init__(self, backend: Literal["weaviate", "qdrant"], client, collection_name: str):
        """
        Initialize unified retriever.
        
        Args:
            backend: "weaviate" or "qdrant"
            client: Weaviate or Qdrant client instance
            collection_name: Collection to search
        """
        if backend == "weaviate":
            self.retriever = WeaviateRetriever(client, collection_name)
        elif backend == "qdrant":
            self.retriever = QdrantRetriever(client, collection_name)
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
        collection_name="KenyanCivicDocs"
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
