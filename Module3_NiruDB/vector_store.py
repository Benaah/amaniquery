"""
Vector Store with multiple backend support: Upstash, QDrant, ChromaDB
"""
import os
from pathlib import Path
from typing import List, Dict, Optional
import chromadb
from chromadb.config import Settings
from loguru import logger
from elasticsearch import Elasticsearch
from upstash_vector import Index
from qdrant_client import QdrantClient
from qdrant_client.http import models
from upstash_redis import Redis
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class VectorStore:
    """Manage vector embeddings with multiple backends: Upstash, QDrant, ChromaDB"""
    
    def __init__(
        self,
        backend: str = "auto",  # upstash, qdrant, chromadb, auto
        persist_directory: Optional[str] = None,
        collection_name: str = "amaniquery_docs",
        embedding_model: str = "all-MiniLM-L6-v2",
        config_manager = None,
    ):
        """
        Initialize vector store
        
        Args:
            backend: Vector store backend ('upstash', 'qdrant', 'chromadb', 'auto')
            persist_directory: Directory to persist ChromaDB database
            collection_name: Name of the collection
            embedding_model: Sentence transformer model name
            config_manager: ConfigManager instance for API keys
        """
        self.collection_name = collection_name
        self.embedding_model_name = embedding_model  # Store name, load lazily
        self._embedding_model = None  # Lazy loaded
        self.config_manager = config_manager
        
        # Initialize all available cloud backends
        self.backends = {}
        self._init_all_cloud_backends()
        
        if backend == "auto":
            self.backend = self._init_with_fallback()
        else:
            self.backend = backend
            if backend == "upstash":
                self._init_upstash()
            elif backend == "qdrant":
                self._init_qdrant()
            elif backend == "chromadb":
                self._init_chromadb(persist_directory)
            else:
                raise ValueError(f"Unsupported backend: {backend}")
        
        # Initialize Elasticsearch for document storage
        self._init_elasticsearch()
        
        # Initialize Upstash Redis for caching
        self._init_redis()
        
        logger.info(f"Vector store initialized with primary backend: {self.backend}, cloud backends: {list(self.backends.keys())}")
    
    @property
    def embedding_model(self):
        """Lazy load the embedding model"""
        if self._embedding_model is None:
            try:
                from sentence_transformers import SentenceTransformer
                self._embedding_model = SentenceTransformer(self.embedding_model_name)
                logger.info(f"Loaded embedding model: {self.embedding_model_name}")
            except ImportError as e:
                logger.error(f"Failed to import SentenceTransformer: {e}")
                raise
        return self._embedding_model
    
    def _init_with_fallback(self) -> str:
        """Initialize with fallback: Upstash -> QDrant -> ChromaDB"""
        backends = ["upstash", "qdrant", "chromadb"]
        
        for backend in backends:
            try:
                logger.info(f"Trying to initialize {backend}")
                if backend == "upstash":
                    self._init_upstash()
                elif backend == "qdrant":
                    self._init_qdrant()
                elif backend == "chromadb":
                    self._init_chromadb(None)
                logger.info(f"Successfully initialized {backend}")
                return backend
            except Exception as e:
                logger.warning(f"Failed to initialize {backend}: {e}")
                continue
        
        raise ValueError("All vector store backends failed to initialize")
    
    def _init_all_cloud_backends(self):
        """Initialize all available cloud backends for multi-cloud storage"""
        cloud_backends = ["upstash", "qdrant"]
        
        for backend in cloud_backends:
            try:
                logger.info(f"Trying to initialize cloud backend: {backend}")
                if backend == "upstash":
                    # Try environment variables first, then config manager
                    url = os.getenv("UPSTASH_VECTOR_URL") or (self.config_manager.get_config("UPSTASH_VECTOR_URL") if self.config_manager else None)
                    token = os.getenv("UPSTASH_VECTOR_TOKEN") or (self.config_manager.get_config("UPSTASH_VECTOR_TOKEN") if self.config_manager else None)
                    
                    if url and token:
                        self.backends["upstash"] = Index(url=url, token=token)
                        logger.info("Upstash Vector backend initialized")
                    else:
                        logger.warning("Upstash Vector credentials not found")
                        
                elif backend == "qdrant":
                    # Try environment variables first, then config manager
                    url = os.getenv("QDRANT_URL") or (self.config_manager.get_config("QDRANT_URL") if self.config_manager else None)
                    api_key = os.getenv("QDRANT_API_KEY") or (self.config_manager.get_config("QDRANT_API_KEY") if self.config_manager else None)
                    
                    if url:
                        client = QdrantClient(url=url, api_key=api_key)
                        # Create collection if not exists
                        try:
                            client.get_collection(self.collection_name)
                        except:
                            client.create_collection(
                                collection_name=self.collection_name,
                                vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
                            )
                        self.backends["qdrant"] = client
                        logger.info("QDrant backend initialized")
                    else:
                        logger.warning("QDrant URL not found")
                        
            except Exception as e:
                logger.warning(f"Failed to initialize cloud backend {backend}: {e}")
                continue
        
        logger.info(f"Initialized {len(self.backends)} cloud backends: {list(self.backends.keys())}")
    
    def _init_elasticsearch(self):
        """Initialize Elasticsearch client"""
        es_url = os.getenv("ELASTICSEARCH_URL") or (self.config_manager.get_config("ELASTICSEARCH_URL") if self.config_manager else None)
        es_api_key = os.getenv("ELASTICSEARCH_API_KEY") or (self.config_manager.get_config("ELASTICSEARCH_API_KEY") if self.config_manager else None)
        
        if es_url:
            self.es_client = Elasticsearch(es_url, api_key=es_api_key)
            # Create index if not exists
            if not self.es_client.indices.exists(index=self.collection_name):
                self.es_client.indices.create(index=self.collection_name)
            logger.info("Elasticsearch initialized")
        else:
            self.es_client = None
            logger.info("Elasticsearch not configured")
    
    def _init_redis(self):
        """Initialize Upstash Redis for caching"""
        redis_url = os.getenv("UPSTASH_REDIS_URL") or (self.config_manager.get_config("UPSTASH_REDIS_URL") if self.config_manager else None)
        redis_token = os.getenv("UPSTASH_REDIS_TOKEN") or (self.config_manager.get_config("UPSTASH_REDIS_TOKEN") if self.config_manager else None)
        
        if redis_url and redis_token:
            self.redis_client = Redis(url=redis_url, token=redis_token)
            logger.info("Upstash Redis initialized for caching")
        else:
            self.redis_client = None
            logger.info("Upstash Redis not configured")
    
    def _init_upstash(self):
        """Initialize Upstash Vector"""
        url = os.getenv("UPSTASH_VECTOR_URL") or (self.config_manager.get_config("UPSTASH_VECTOR_URL") if self.config_manager else None)
        token = os.getenv("UPSTASH_VECTOR_TOKEN") or (self.config_manager.get_config("UPSTASH_VECTOR_TOKEN") if self.config_manager else None)
        
        if not url or not token:
            raise ValueError("Upstash Vector URL and token required")
        
        self.client = Index(url=url, token=token)
    
    def _init_qdrant(self):
        """Initialize QDrant"""
        url = os.getenv("QDRANT_URL") or (self.config_manager.get_config("QDRANT_URL") if self.config_manager else None)
        api_key = os.getenv("QDRANT_API_KEY") or (self.config_manager.get_config("QDRANT_API_KEY") if self.config_manager else None)
        
        if not url:
            raise ValueError("QDrant URL required")
        
        self.client = QdrantClient(url=url, api_key=api_key)
        
        # Create collection if not exists
        try:
            self.client.get_collection(self.collection_name)
        except:
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
            )
    
    def _init_chromadb(self, persist_directory):
        """Initialize ChromaDB"""
        if persist_directory is None:
            persist_directory = str(Path(__file__).parent.parent / "data" / "chroma_db")
        
        self.persist_directory = persist_directory
        
        # Disable telemetry
        os.environ["CHROMA_TELEMETRY_ENABLED"] = "false"
        
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(
                anonymized_telemetry=False,
                allow_reset=True,
            )
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=self.collection_name,
            metadata={"description": "AmaniQuery document embeddings"}
        )
    
    def add_documents(self, chunks: List[Dict], batch_size: int = 100):
        """
        Add document chunks to all available vector stores and Elasticsearch
        
        Args:
            chunks: List of chunk dictionaries with embeddings
            batch_size: Number of chunks to add at once
        """
        if not chunks:
            logger.warning("No chunks to add")
            return
        
        logger.info(f"Adding {len(chunks)} chunks to all available backends and Elasticsearch")
        
        # Add to all available cloud backends
        for backend_name, backend_client in self.backends.items():
            try:
                if backend_name == "upstash":
                    self._add_upstash(chunks, client=backend_client)
                elif backend_name == "qdrant":
                    self._add_qdrant(chunks, batch_size, client=backend_client)
                logger.info(f"Added {len(chunks)} chunks to {backend_name}")
            except Exception as e:
                logger.error(f"Failed to add chunks to {backend_name}: {e}")
        
        # Add to primary backend (ChromaDB or selected backend)
        try:
            if self.backend == "upstash":
                self._add_upstash(chunks)
            elif self.backend == "qdrant":
                self._add_qdrant(chunks, batch_size)
            elif self.backend == "chromadb":
                self._add_chromadb(chunks, batch_size)
        except Exception as e:
            logger.error(f"Failed to add chunks to primary backend {self.backend}: {e}")
        
        # Index full documents in Elasticsearch
        self._index_documents_in_elasticsearch(chunks)
    
    def _index_documents_in_elasticsearch(self, chunks: List[Dict]):
        """Index document chunks in Elasticsearch for full-text search"""
        if not self.es_client:
            logger.warning("Elasticsearch not configured, skipping document indexing")
            return
        
        try:
            # Group chunks by document for full document indexing
            documents_by_id = {}
            
            for chunk in chunks:
                doc_id = chunk.get("doc_id") or chunk.get("chunk_id", "").rsplit("_", 1)[0]  # Remove chunk suffix
                
                if doc_id not in documents_by_id:
                    documents_by_id[doc_id] = {
                        "id": doc_id,
                        "title": str(chunk.get("title", "")),
                        "content": "",
                        "category": str(chunk.get("category", "")),
                        "source_url": str(chunk.get("source_url", "")),
                        "source_name": str(chunk.get("source_name", "")),
                        "author": str(chunk.get("author", "")),
                        "publication_date": str(chunk.get("publication_date", "")),
                        "crawl_date": str(chunk.get("crawl_date", "")),
                        "content_type": str(chunk.get("content_type", "")),
                        "language": str(chunk.get("language", "")),
                        "chunk_count": 0,
                        "total_text_length": 0
                    }
                
                # Add chunk content
                chunk_text = str(chunk.get("text", ""))
                if documents_by_id[doc_id]["content"]:
                    documents_by_id[doc_id]["content"] += "\n\n"
                documents_by_id[doc_id]["content"] += chunk_text
                
                # Update counters
                documents_by_id[doc_id]["chunk_count"] += 1
                documents_by_id[doc_id]["total_text_length"] += len(chunk_text)
            
            # Index each document in Elasticsearch
            for doc_id, document in documents_by_id.items():
                try:
                    # Ensure all fields are strings to avoid Elasticsearch mapping issues
                    clean_document = {}
                    for key, value in document.items():
                        if isinstance(value, (int, float)):
                            clean_document[key] = str(value)
                        elif isinstance(value, str):
                            clean_document[key] = value
                        else:
                            # Convert complex objects to strings
                            clean_document[key] = str(value)
                    
                    self.es_client.index(
                        index=self.collection_name,
                        id=doc_id,
                        document=clean_document
                    )
                    logger.info(f"Indexed document: {doc_id}")
                except Exception as e:
                    logger.error(f"Failed to index document {doc_id}: {e}")
            
            logger.info(f"Indexed {len(documents_by_id)} documents in Elasticsearch")
            
        except Exception as e:
            logger.error(f"Error indexing documents in Elasticsearch: {e}")
    
    def _add_upstash(self, chunks: List[Dict], client=None):
        """Add to Upstash Vector"""
        if client is None:
            client = self.client
            
        vectors = []
        for chunk in chunks:
            metadata = {
                "title": chunk.get("title", ""),
                "category": chunk.get("category", ""),
                "source_url": chunk.get("source_url", ""),
                "source_name": chunk.get("source_name", ""),
                "chunk_index": chunk.get("chunk_index", 0),
                "total_chunks": chunk.get("total_chunks", 1),
                "text": chunk["text"]
            }
            vectors.append({
                "id": chunk["chunk_id"],
                "vector": chunk["embedding"],
                "metadata": metadata
            })
        
        client.upsert(vectors=vectors)
        logger.info(f"Added {len(chunks)} chunks to Upstash")
    
    def _add_qdrant(self, chunks: List[Dict], batch_size: int, client=None):
        """Add to QDrant"""
        if client is None:
            client = self.client
            
        points = []
        for i, chunk in enumerate(chunks):
            payload = {
                "title": chunk.get("title", ""),
                "category": chunk.get("category", ""),
                "source_url": chunk.get("source_url", ""),
                "source_name": chunk.get("source_name", ""),
                "chunk_index": chunk.get("chunk_index", 0),
                "total_chunks": chunk.get("total_chunks", 1),
                "text": chunk["text"],
                "chunk_id": chunk["chunk_id"]  # Store original chunk_id in payload
            }
            # Use hash of chunk_id as integer ID for QDrant
            point_id = hash(chunk["chunk_id"]) % (2**63 - 1)  # Ensure positive integer
            points.append(models.PointStruct(
                id=point_id,
                vector=chunk["embedding"],
                payload=payload
            ))
        
        client.upsert(collection_name=self.collection_name, points=points)
        logger.info(f"Added {len(chunks)} chunks to QDrant")
    
    def _add_chromadb(self, chunks: List[Dict], batch_size: int):
        """Add to ChromaDB (existing logic)"""
        # Process in batches
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            
            # Prepare data
            ids = [chunk["chunk_id"] for chunk in batch]
            embeddings = [chunk["embedding"] for chunk in batch]
            documents = [chunk["text"] for chunk in batch]
            
            # Prepare metadata
            metadatas = []
            for chunk in batch:
                metadata = {
                    "title": str(chunk.get("title", "")),
                    "category": str(chunk.get("category", "")),
                    "source_url": str(chunk.get("source_url", "")),
                    "source_name": str(chunk.get("source_name", "")),
                    "chunk_index": int(chunk.get("chunk_index", 0)),
                    "total_chunks": int(chunk.get("total_chunks", 1)),
                }
                
                # Add optional fields if available
                if chunk.get("author"):
                    metadata["author"] = str(chunk["author"])
                if chunk.get("publication_date"):
                    metadata["publication_date"] = str(chunk["publication_date"])
                if chunk.get("keywords"):
                    metadata["keywords"] = str(chunk["keywords"])
                
                metadatas.append(metadata)
            
            # Add to collection
            try:
                self.collection.add(
                    ids=ids,
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas,
                )
                logger.info(f"Added batch {i // batch_size + 1} ({len(batch)} chunks)")
            except Exception as e:
                logger.error(f"Error adding batch: {e}")
        
        logger.info(f"Total documents in collection: {self.collection.count()}")
    
    def index_document(self, doc_id: str, document: Dict):
        """Index document in Elasticsearch"""
        if self.es_client:
            try:
                self.es_client.index(index=self.collection_name, id=doc_id, document=document)
                logger.info(f"Indexed document: {doc_id}")
            except Exception as e:
                logger.error(f"Failed to index document {doc_id}: {e}")
    
    def search_documents(self, query: str, n_results: int = 5) -> List[Dict]:
        """Search documents in Elasticsearch"""
        if not self.es_client:
            return []
        
        try:
            response = self.es_client.search(
                index=self.collection_name,
                query={"match": {"content": query}},
                size=n_results
            )
            results = []
            for hit in response["hits"]["hits"]:
                results.append({
                    "id": hit["_id"],
                    "text": hit["_source"].get("content", ""),
                    "metadata": hit["_source"],
                    "score": hit["_score"]
                })
            logger.info(f"Elasticsearch search returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Elasticsearch search failed: {e}")
            return []
    
    def query(
        self,
        query_text: str,
        n_results: int = 5,
        filter: Optional[Dict] = None,
    ) -> List[Dict]:
        """
        Query vector store for similar documents
        
        Args:
            query_text: Query string
            n_results: Number of results to return
            filter: Metadata filter
        
        Returns:
            List of similar documents with metadata
        """
        try:
            # Generate query embedding
            query_embedding = self.embedding_model.encode(query_text).tolist()
            
            if self.backend == "upstash":
                return self._query_upstash(query_embedding, n_results, filter)
            elif self.backend == "qdrant":
                return self._query_qdrant(query_embedding, n_results, filter)
            elif self.backend == "chromadb":
                return self._query_chromadb(query_embedding, n_results, filter)
            else:
                logger.error(f"Unsupported backend for query: {self.backend}")
                return []
            
        except Exception as e:
            logger.error(f"Error querying vector store: {e}")
            return []
    
    def _query_upstash(self, query_embedding: List[float], n_results: int, filter: Optional[Dict]) -> List[Dict]:
        """Query Upstash Vector"""
        # Upstash query with metadata filter
        filter_dict = {}
        if filter:
            for k, v in filter.items():
                filter_dict[f"metadata.{k}"] = v
        
        results = self.client.query(
            vector=query_embedding,
            top_k=n_results,
            filter=filter_dict,
            include_metadata=True,
            include_data=True
        )
        
        formatted_results = []
        for hit in results:
            formatted_results.append({
                "id": hit.id,
                "text": hit.metadata.get("text", ""),
                "metadata": hit.metadata,
                "distance": hit.score,
            })
        
        logger.info(f"Upstash query returned {len(formatted_results)} results")
        return formatted_results
    
    def _query_qdrant(self, query_embedding: List[float], n_results: int, filter: Optional[Dict]) -> List[Dict]:
        """Query QDrant"""
        scroll_filter = None
        if filter:
            conditions = []
            for k, v in filter.items():
                conditions.append(models.FieldCondition(key=k, match=models.MatchValue(value=v)))
            scroll_filter = models.Filter(must=conditions)
        
        results = self.client.search(
            collection_name=self.collection_name,
            query_vector=query_embedding,
            limit=n_results,
            query_filter=scroll_filter,
            with_payload=True
        )
        
        formatted_results = []
        for hit in results:
            formatted_results.append({
                "id": hit.payload.get("chunk_id", str(hit.id)),  # Use original chunk_id from payload
                "text": hit.payload.get("text", ""),
                "metadata": hit.payload,
                "distance": hit.score,
            })
        
        logger.info(f"QDrant query returned {len(formatted_results)} results")
        return formatted_results
    
    def _query_chromadb(self, query_embedding: List[float], n_results: int, filter: Optional[Dict]) -> List[Dict]:
        """Query ChromaDB (existing logic)"""
        # Query collection
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=n_results,
            where=filter,
        )
        
        # Format results
        formatted_results = []
        for i in range(len(results["ids"][0])):
            formatted_results.append({
                "id": results["ids"][0][i],
                "text": results["documents"][0][i],
                "metadata": results["metadatas"][0][i],
                "distance": results["distances"][0][i] if "distances" in results else None,
            })
        
        logger.info(f"ChromaDB query returned {len(formatted_results)} results")
        return formatted_results
    
    def delete_collection(self):
        """Delete the entire collection"""
        self.client.delete_collection(self.collection_name)
        logger.info(f"Deleted collection: {self.collection_name}")
    
    def get_stats(self) -> Dict:
        """Get collection statistics"""
        stats = {
            "backend": self.backend,
            "collection_name": self.collection_name,
            "cloud_backends": list(self.backends.keys()),
            "elasticsearch_enabled": self.es_client is not None,
            "total_chunks": 0,
            "elasticsearch_docs": 0
        }
        
        # Get stats from primary backend
        if self.backend == "chromadb":
            try:
                stats["total_chunks"] = self.collection.count()
                stats["persist_directory"] = self.persist_directory
                
                # Get sample to analyze categories
                sample = self.collection.get(limit=1000)
                categories = {}
                
                if sample["metadatas"]:
                    for meta in sample["metadatas"]:
                        cat = meta.get("category", "Unknown")
                        categories[cat] = categories.get(cat, 0) + 1
                
                stats["sample_categories"] = categories
            except Exception as e:
                logger.error(f"Error getting ChromaDB stats: {e}")
                stats["total_chunks"] = 0
                
        elif self.backend == "upstash":
            # Upstash doesn't have count, use cloud backend count if available
            if "upstash" in self.backends:
                stats["total_chunks"] = 0  # We don't have a way to count
            else:
                stats["total_chunks"] = 0
                
        elif self.backend == "qdrant":
            try:
                if "qdrant" in self.backends:
                    stats["total_chunks"] = self.backends["qdrant"].count(self.collection_name).count
                else:
                    stats["total_chunks"] = self.client.count(self.collection_name).count
            except Exception as e:
                logger.error(f"Error getting QDrant stats: {e}")
                stats["total_chunks"] = 0
        
        # Get Elasticsearch stats
        if self.es_client:
            try:
                es_stats = self.es_client.count(index=self.collection_name)
                stats["elasticsearch_docs"] = es_stats["count"]
            except Exception as e:
                logger.error(f"Error getting Elasticsearch stats: {e}")
                stats["elasticsearch_docs"] = 0
        
        return stats
