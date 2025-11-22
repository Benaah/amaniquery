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
                import torch
                
                # Ensure model is loaded on CPU to avoid device issues
                # Explicitly set device to avoid meta tensor errors
                device = 'cpu'  # Use CPU for embeddings to avoid GPU/meta device issues
                
                self._embedding_model = SentenceTransformer(
                    self.embedding_model_name,
                    device=device
                )
                
                # Ensure model is properly initialized (not on meta device)
                if hasattr(self._embedding_model, 'to'):
                    # Move to CPU explicitly if needed
                    try:
                        self._embedding_model = self._embedding_model.to(device)
                    except Exception as device_error:
                        # If to() fails, try to_empty() for meta tensors
                        if 'meta' in str(device_error).lower():
                            logger.warning(f"Model on meta device, reinitializing: {device_error}")
                            # Reinitialize model without meta device
                            self._embedding_model = SentenceTransformer(
                                self.embedding_model_name,
                                device=device
                            )
                        else:
                            raise
                
                logger.info(f"Loaded embedding model: {self.embedding_model_name} on {device}")
            except ImportError as e:
                logger.error(f"Failed to import SentenceTransformer: {e}")
                raise
            except Exception as e:
                logger.error(f"Failed to load embedding model: {e}")
                # Try fallback: load without device specification
                try:
                    self._embedding_model = SentenceTransformer(self.embedding_model_name)
                    logger.info(f"Loaded embedding model (fallback): {self.embedding_model_name}")
                except Exception as fallback_error:
                    logger.error(f"Fallback model loading also failed: {fallback_error}")
                    raise
        return self._embedding_model
    
    def _init_with_fallback(self) -> str:
        """Initialize with fallback: QDrant -> ChromaDB -> Upstash"""
        backends = ["qdrant", "chromadb", "upstash"]
        
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
    
    def _get_config_value(self, key: str) -> Optional[str]:
        """Fetch configuration value from encrypted config store"""
        if not self.config_manager:
            return None

        try:
            return self.config_manager.get_config(key)
        except Exception as exc:
            logger.warning(f"Failed to read config '{key}' from ConfigManager: {exc}")
            return None

    def _init_all_cloud_backends(self):
        """Initialize all available cloud backends for multi-cloud storage"""
        cloud_backends = ["upstash", "qdrant"]
        
        for backend in cloud_backends:
            try:
                logger.info(f"Trying to initialize cloud backend: {backend}")
                if backend == "upstash":
                    # Prefer environment variables, then fall back to config manager
                    url = os.getenv("UPSTASH_VECTOR_URL")
                    token = os.getenv("UPSTASH_VECTOR_TOKEN")

                    if (not url or not url.strip()) and self.config_manager:
                        url = self._get_config_value("UPSTASH_VECTOR_URL")
                    if (not token or not token.strip()) and self.config_manager:
                        token = self._get_config_value("UPSTASH_VECTOR_TOKEN")
                    
                    if url and token:
                        self.backends["upstash"] = Index(url=url, token=token)
                        logger.info("Upstash Vector backend initialized")
                    else:
                        logger.warning("Upstash Vector credentials not found")
                        
                elif backend == "qdrant":
                    # Prefer environment variables, then fall back to config manager
                    url = os.getenv("QDRANT_URL")
                    api_key = os.getenv("QDRANT_API_KEY")

                    if (not url or not url.strip()) and self.config_manager:
                        url = self._get_config_value("QDRANT_URL")
                    if (not api_key or not api_key.strip()) and self.config_manager:
                        api_key = self._get_config_value("QDRANT_API_KEY")
                    
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
        es_url = os.getenv("ELASTICSEARCH_URL")
        es_api_key = os.getenv("ELASTICSEARCH_API_KEY")

        # Fall back to encrypted config only when env vars are missing
        if (not es_url or (es_url and es_url.strip().startswith("error"))) and self.config_manager:
            es_url = self._get_config_value("ELASTICSEARCH_URL")
        if (not es_api_key or (es_api_key and es_api_key.strip().startswith("error"))) and self.config_manager:
            es_api_key = self._get_config_value("ELASTICSEARCH_API_KEY")
        
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
        redis_url = os.getenv("UPSTASH_REDIS_URL")
        redis_token = os.getenv("UPSTASH_REDIS_TOKEN")

        if (not redis_url or (redis_url and redis_url.strip().startswith("error"))) and self.config_manager:
            redis_url = self._get_config_value("UPSTASH_REDIS_URL")
        if (not redis_token or (redis_token and redis_token.strip().startswith("error"))) and self.config_manager:
            redis_token = self._get_config_value("UPSTASH_REDIS_TOKEN")
        
        if redis_url and redis_token:
            self.redis_client = Redis(url=redis_url, token=redis_token)
            logger.info("Upstash Redis initialized for caching")
        else:
            self.redis_client = None
            logger.info("Upstash Redis not configured")
    
    def _init_upstash(self):
        """Initialize Upstash Vector"""
        url = os.getenv("UPSTASH_VECTOR_URL")
        token = os.getenv("UPSTASH_VECTOR_TOKEN")

        if (not url or not url.strip()) and self.config_manager:
            url = self._get_config_value("UPSTASH_VECTOR_URL")
        if (not token or not token.strip()) and self.config_manager:
            token = self._get_config_value("UPSTASH_VECTOR_TOKEN")
        
        if not url or not token:
            raise ValueError("Upstash Vector URL and token required")
        
        self.client = Index(url=url, token=token)
    
    def _init_qdrant(self):
        """Initialize QDrant"""
        url = os.getenv("QDRANT_URL")
        api_key = os.getenv("QDRANT_API_KEY")

        if (not url or not url.strip()) and self.config_manager:
            url = self._get_config_value("QDRANT_URL")
        if (not api_key or not api_key.strip()) and self.config_manager:
            api_key = self._get_config_value("QDRANT_API_KEY")
        
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
    
    def get_or_create_collection(self, collection_name: str):
        """Get or create a collection by name (for session-specific collections)"""
        if self.backend == "chromadb":
            return self.client.get_or_create_collection(
                name=collection_name,
                metadata={"description": f"AmaniQuery session collection: {collection_name}"}
            )
        elif self.backend == "qdrant":
            try:
                self.client.get_collection(collection_name)
            except:
                from qdrant_client.http import models
                self.client.create_collection(
                    collection_name=collection_name,
                    vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
                )
            # Return a wrapper that mimics ChromaDB collection interface
            return QDrantCollectionWrapper(self.client, collection_name)
        elif self.backend == "upstash":
            # Upstash uses a single index, so we'll use metadata filtering
            return UpstashCollectionWrapper(self.client, collection_name)
        else:
            raise ValueError(f"Unsupported backend for get_or_create_collection: {self.backend}")
    
    def get_collection(self, collection_name: str):
        """Get an existing collection by name"""
        if self.backend == "chromadb":
            try:
                return self.client.get_collection(collection_name)
            except:
                return None
        elif self.backend == "qdrant":
            try:
                self.client.get_collection(collection_name)
                return QDrantCollectionWrapper(self.client, collection_name)
            except:
                return None
        elif self.backend == "upstash":
            return UpstashCollectionWrapper(self.client, collection_name)
        else:
            return None
    
    def _add_upstash(self, chunks: List[Dict], client=None):
        """Add to Upstash Vector"""
        if client is None:
            client = self.client
            
        vectors = []
        for chunk in chunks:
            metadata = {
                "title": str(chunk.get("title", "")),
                "category": str(chunk.get("category", "")),
                "source_url": str(chunk.get("source_url", "")),
                "source_name": str(chunk.get("source_name", "")),
                "chunk_index": str(chunk.get("chunk_index", 0)),
                "total_chunks": str(chunk.get("total_chunks", 1)),
                "text": str(chunk["text"])
            }
            vectors.append({
                "id": str(chunk["chunk_id"]),
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
                "title": str(chunk.get("title", "")),
                "category": str(chunk.get("category", "")),
                "source_url": str(chunk.get("source_url", "")),
                "source_name": str(chunk.get("source_name", "")),
                "chunk_index": str(chunk.get("chunk_index", 0)),
                "total_chunks": str(chunk.get("total_chunks", 1)),
                "text": str(chunk["text"]),
                "chunk_id": str(chunk["chunk_id"])
            }
            point_id = hash(chunk["chunk_id"]) % (2**63 - 1)
            points.append(models.PointStruct(
                id=point_id,
                vector=chunk["embedding"],
                payload=payload
            ))
        
        client.upsert(collection_name=self.collection_name, points=points)
        logger.info(f"Added {len(chunks)} chunks to QDrant")
    
    def _add_chromadb(self, chunks: List[Dict], batch_size: int):
        """Add to ChromaDB"""
        for i in range(0, len(chunks), batch_size):
            batch = chunks[i:i + batch_size]
            ids = [str(chunk["chunk_id"]) for chunk in batch]
            embeddings = [chunk["embedding"] for chunk in batch]
            documents = [str(chunk["text"]) for chunk in batch]
            metadatas = []
            for chunk in batch:
                metadata = {
                    "title": str(chunk.get("title", "")),
                    "category": str(chunk.get("category", "")),
                    "source_url": str(chunk.get("source_url", "")),
                    "source_name": str(chunk.get("source_name", "")),
                    "chunk_index": str(chunk.get("chunk_index", 0)),
                    "total_chunks": str(chunk.get("total_chunks", 1)),
                }
                if chunk.get("author"):
                    metadata["author"] = str(chunk["author"])
                if chunk.get("publication_date"):
                    metadata["publication_date"] = str(chunk["publication_date"])
                if chunk.get("keywords"):
                    metadata["keywords"] = str(chunk["keywords"])
                metadatas.append(metadata)
            try:
                self.collection.add(ids=ids, embeddings=embeddings, documents=documents, metadatas=metadatas)
                logger.info(f"Added batch {i // batch_size + 1} ({len(batch)} chunks)")
            except Exception as e:
                logger.error(f"Error adding batch: {e}")
        logger.info(f"Total documents in collection: {self.collection.count()}")
    
    def add_documents(self, chunks: List[Dict], batch_size: int = 100):
        """Add documents to vector store (public method)
        
        Args:
            chunks: List of chunk dictionaries with 'text', 'embedding', and metadata
            batch_size: Batch size for processing (default: 100)
        """
        if not chunks:
            logger.warning("No chunks provided to add_documents")
            return
        
        if self.backend == "upstash":
            self._add_upstash(chunks)
        elif self.backend == "qdrant":
            self._add_qdrant(chunks, batch_size)
        elif self.backend == "chromadb":
            self._add_chromadb(chunks, batch_size)
        else:
            logger.error(f"Unsupported backend for add_documents: {self.backend}")
            raise ValueError(f"Unsupported backend: {self.backend}")
    
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
            response = self.es_client.search(index=self.collection_name, query={"match": {"content": query}}, size=n_results)
            results = []
            for hit in response["hits"]["hits"]:
                results.append({"id": hit["_id"], "text": hit["_source"].get("content", ""), "metadata": hit["_source"], "score": hit["_score"]})
            logger.info(f"Elasticsearch search returned {len(results)} results")
            return results
        except Exception as e:
            logger.error(f"Elasticsearch search failed: {e}")
            return []
    
    def get_sample_documents(self, limit: int = 100) -> List[Dict]:
        """
        Get sample documents without vector search (efficient for metadata)
        
        Args:
            limit: Maximum number of documents to return
            
        Returns:
            List of document dictionaries
        """
        try:
            if self.backend == "upstash":
                return self._get_sample_upstash(limit)
            elif self.backend == "qdrant":
                return self._get_sample_qdrant(limit)
            elif self.backend == "chromadb":
                return self._get_sample_chromadb(limit)
            else:
                logger.error(f"Unsupported backend for get_sample_documents: {self.backend}")
                return []
        except Exception as e:
            logger.error(f"Error getting sample documents: {e}")
            return []

    def _get_sample_upstash(self, limit: int) -> List[Dict]:
        """Get sample documents from Upstash"""
        # Upstash doesn't support random access easily without vector, 
        # so we'll use a dummy vector of zeros or range if available
        # For now, falling back to a query with zero vector is still better than encoding text
        try:
            # Create a zero vector of appropriate dimension (384 for all-MiniLM-L6-v2)
            zero_vector = [0.0] * 384
            results = self.client.query(vector=zero_vector, top_k=limit, include_metadata=True, include_data=True)
            
            formatted_results = []
            for hit in results:
                metadata = {k: str(v) if not isinstance(v, str) else v for k, v in hit.metadata.items()}
                formatted_results.append({"id": hit.id, "text": metadata.get("text", ""), "metadata": metadata})
            return formatted_results
        except Exception as e:
            logger.warning(f"Upstash sample fetch failed: {e}")
            return []

    def _get_sample_qdrant(self, limit: int) -> List[Dict]:
        """Get sample documents from QDrant using scroll"""
        try:
            # Use scroll API which is much more efficient than search
            scroll_result, _ = self.client.scroll(
                collection_name=self.collection_name,
                limit=limit,
                with_payload=True,
                with_vectors=False
            )
            
            formatted_results = []
            for hit in scroll_result:
                payload = hit.payload if hasattr(hit, 'payload') else {}
                metadata = {k: str(v) if not isinstance(v, str) else v for k, v in payload.items()}
                point_id = hit.id if hasattr(hit, 'id') else None
                formatted_results.append({"id": metadata.get("chunk_id", str(point_id) if point_id else ""), "text": metadata.get("text", ""), "metadata": metadata})
            
            logger.info(f"QDrant scroll returned {len(formatted_results)} results")
            return formatted_results
        except Exception as e:
            logger.warning(f"QDrant scroll failed: {e}")
            return []

    def _get_sample_chromadb(self, limit: int) -> List[Dict]:
        """Get sample documents from ChromaDB using get"""
        try:
            # Use get API which avoids vector search
            results = self.collection.get(limit=limit, include=["metadatas", "documents"])
            
            formatted_results = []
            if results["ids"]:
                for i in range(len(results["ids"])):
                    metadata = results["metadatas"][i] if results["metadatas"] else {}
                    # Ensure metadata values are strings
                    metadata = {k: str(v) if not isinstance(v, str) else v for k, v in metadata.items()}
                    
                    formatted_results.append({
                        "id": results["ids"][i], 
                        "text": results["documents"][i] if results["documents"] else "", 
                        "metadata": metadata
                    })
            
            logger.info(f"ChromaDB get returned {len(formatted_results)} results")
            return formatted_results
        except Exception as e:
            logger.warning(f"ChromaDB get failed: {e}")
            return []
            
    def query(self, query_text: str, n_results: int = 5, filter: Optional[Dict] = None) -> List[Dict]:
        """Query vector store for similar documents"""
        try:
            try:
                query_embedding = self.embedding_model.encode(query_text).tolist()
            except Exception as encode_error:
                if 'meta' in str(encode_error).lower() or 'device' in str(encode_error).lower():
                    logger.warning(f"Encoding error (device issue): {encode_error}, retrying with CPU")
                    import torch
                    if hasattr(self._embedding_model, 'to'):
                        self._embedding_model = self._embedding_model.to('cpu')
                    query_embedding = self.embedding_model.encode(query_text).tolist()
                else:
                    raise
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
        filter_dict = {}
        if filter:
            for k, v in filter.items():
                filter_dict[f"metadata.{k}"] = str(v)
        results = self.client.query(vector=query_embedding, top_k=n_results, filter=filter_dict, include_metadata=True, include_data=True)
        formatted_results = []
        for hit in results:
            metadata = {k: str(v) if not isinstance(v, str) else v for k, v in hit.metadata.items()}
            formatted_results.append({"id": hit.id, "text": metadata.get("text", ""), "metadata": metadata, "distance": hit.score})
        logger.info(f"Upstash query returned {len(formatted_results)} results")
        return formatted_results
    
    def _query_qdrant(self, query_embedding: List[float], n_results: int, filter: Optional[Dict]) -> List[Dict]:
        """Query QDrant"""
        scroll_filter = None
        if filter:
            conditions = []
            for k, v in filter.items():
                conditions.append(models.FieldCondition(key=k, match=models.MatchValue(value=str(v))))
            scroll_filter = models.Filter(must=conditions)
        query_result = self.client.query_points(collection_name=self.collection_name, query=query_embedding, limit=n_results, query_filter=scroll_filter, with_payload=True)
        formatted_results = []
        if hasattr(query_result, 'points'):
            points = query_result.points
        elif hasattr(query_result, '__iter__'):
            points = query_result
        else:
            points = []
        for hit in points:
            payload = hit.payload if hasattr(hit, 'payload') else {}
            metadata = {k: str(v) if not isinstance(v, str) else v for k, v in payload.items()}
            point_id = hit.id if hasattr(hit, 'id') else None
            score = hit.score if hasattr(hit, 'score') else 0.0
            formatted_results.append({"id": metadata.get("chunk_id", str(point_id) if point_id else ""), "text": metadata.get("text", ""), "metadata": metadata, "distance": score})
        logger.info(f"QDrant query returned {len(formatted_results)} results")
        return formatted_results
    
    def _query_chromadb(self, query_embedding: List[float], n_results: int, filter: Optional[Dict]) -> List[Dict]:
        """Query ChromaDB"""
        where = None
        if filter:
            where = {k: str(v) for k, v in filter.items()}
        results = self.collection.query(query_embeddings=[query_embedding], n_results=n_results, where=where)
        formatted_results = []
        for i in range(len(results["ids"][0])):
            metadata = {k: str(v) if not isinstance(v, str) else v for k, v in results["metadatas"][0][i].items()}
            formatted_results.append({"id": results["ids"][0][i], "text": results["documents"][0][i], "metadata": metadata, "distance": results["distances"][0][i] if "distances" in results else None})
        logger.info(f"ChromaDB query returned {len(formatted_results)} results")
        return formatted_results
    
    def delete_collection(self):
        """Delete the entire collection"""
        self.client.delete_collection(self.collection_name)
        logger.info(f"Deleted collection: {self.collection_name}")
    
    def get_stats(self) -> Dict:
        """Get collection statistics"""
        stats = {"backend": self.backend, "collection_name": self.collection_name, "cloud_backends": list(self.backends.keys()), "elasticsearch_enabled": self.es_client is not None, "total_chunks": 0, "elasticsearch_docs": 0}
        if self.backend == "chromadb":
            try:
                stats["total_chunks"] = self.collection.count()
                stats["persist_directory"] = self.persist_directory
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
            if "upstash" in self.backends:
                stats["total_chunks"] = 0
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
        if self.es_client:
            try:
                es_stats = self.es_client.count(index=self.collection_name)
                stats["elasticsearch_docs"] = es_stats["count"]
            except Exception as e:
                logger.error(f"Error getting Elasticsearch stats: {e}")
                stats["elasticsearch_docs"] = 0
        return stats


class QDrantCollectionWrapper:
    """Wrapper to make QDrant collection work like ChromaDB collection"""
    def __init__(self, client, collection_name: str):
        self.client = client
        self.collection_name = collection_name
    
    def add(self, embeddings=None, documents=None, metadatas=None, ids=None):
        """Add documents to QDrant collection"""
        from qdrant_client.http import models
        points = []
        for i, doc_id in enumerate(ids):
            payload = metadatas[i] if metadatas else {}
            payload["text"] = documents[i] if documents else ""
            point_id = hash(doc_id) % (2**63 - 1)
            points.append(models.PointStruct(
                id=point_id,
                vector=embeddings[i] if embeddings else [],
                payload=payload
            ))
        self.client.upsert(collection_name=self.collection_name, points=points)
    
    def query(self, query_texts=None, n_results=5, where=None):
        """Query QDrant collection"""
        # This is a simplified version - full implementation would need embedding
        return {"documents": [[]], "metadatas": [[]], "distances": [[]]}


class UpstashCollectionWrapper:
    """Wrapper to make Upstash index work like ChromaDB collection"""
    def __init__(self, client, collection_name: str):
        self.client = client
        self.collection_name = collection_name
    
    def add(self, embeddings=None, documents=None, metadatas=None, ids=None):
        """Add documents to Upstash index"""
        vectors = []
        for i, doc_id in enumerate(ids):
            metadata = metadatas[i] if metadatas else {}
            metadata["text"] = documents[i] if documents else ""
            metadata["collection"] = self.collection_name
            vectors.append({
                "id": doc_id,
                "vector": embeddings[i] if embeddings else [],
                "metadata": metadata
            })
        self.client.upsert(vectors=vectors)
    
    def query(self, query_texts=None, n_results=5, where=None):
        """Query Upstash index"""
        # This is a simplified version - full implementation would need embedding
        return {"documents": [[]], "metadatas": [[]], "distances": [[]]}
