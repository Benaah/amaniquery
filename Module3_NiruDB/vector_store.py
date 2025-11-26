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
        
        # Always ensure ChromaDB is available as local fallback
        try:
            chroma_persist_dir = persist_directory or str(Path(__file__).parent.parent / "data" / "chroma_db")
            self.chromadb_client = chromadb.PersistentClient(
                path=chroma_persist_dir,
                settings=Settings(
                    anonymized_telemetry=False,
                    allow_reset=True,
                )
            )
            self.chromadb_collection = self.chromadb_client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "AmaniQuery local ChromaDB fallback"}
            )
            logger.info("ChromaDB initialized as local fallback")
        except Exception as e:
            logger.warning(f"Failed to initialize ChromaDB fallback: {e}")
            self.chromadb_client = None
            self.chromadb_collection = None
        
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
                
                # OPTIMIZATION: Dynamic Quantization for CPU
                if device == 'cpu':
                    try:
                        import torch
                        logger.info("🚀 Applying Dynamic Quantization to Embedding Model for CPU speedup...")
                        self._embedding_model = torch.quantization.quantize_dynamic(
                            self._embedding_model, 
                            {torch.nn.Linear}, 
                            dtype=torch.qint8
                        )
                        logger.info("✅ Model Quantized Successfully")
                    except Exception as q_e:
                        logger.warning(f"Quantization failed: {q_e}")

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
        """Initialize with fallback: ChromaDB -> QDrant -> Upstash"""
        backends = ["chromadb", "qdrant", "upstash"]
        
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
    
    def _add_upstash(self, chunks: List[Dict], client=None, namespace: str = None):
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
            if namespace:
                metadata["namespace"] = namespace
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
    
    def add_documents(self, chunks: List[Dict], batch_size: int = 100, namespace: str = None):
        """Add documents to vector store (public method)
        
        Args:
            chunks: List of chunk dictionaries with 'text', 'embedding', and metadata
            batch_size: Batch size for processing (default: 100)
            namespace: Optional namespace for collection separation
        """
        if not chunks:
            logger.warning("No chunks provided to add_documents")
            return

        # Modify collection name based on namespace for supported backends
        original_collection = self.collection_name
        if namespace:
            if self.backend in ["qdrant", "chromadb"]:
                self.collection_name = f"{original_collection}_{namespace}"
                # Ensure namespaced collection exists for QDrant
                if self.backend == "qdrant":
                    try:
                        self.client.get_collection(self.collection_name)
                    except:
                        self.client.create_collection(
                            collection_name=self.collection_name,
                            vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
                        )
                        logger.info(f"Created QDrant collection: {self.collection_name}")
            elif self.backend == "upstash":
                # Namespace will be used as metadata filter during upsert/query
                pass
            elif self.es_client:
                # ElasticSearch index name changed by namespace
                self.collection_name = f"{original_collection}_{namespace}"
        
        try:
            if self.backend == "upstash":
                self._add_upstash(chunks, namespace=namespace)
            elif self.backend == "qdrant":
                self._add_qdrant(chunks, batch_size)
            elif self.backend == "chromadb":
                self._add_chromadb(chunks, batch_size)
            else:
                logger.error(f"Unsupported backend for add_documents: {self.backend}")
                raise ValueError(f"Unsupported backend: {self.backend}")
        except Exception as e:
            logger.error(f"Failed to add documents to primary backend {self.backend}: {e}")
            # If primary backend fails and ChromaDB is available, try ChromaDB as fallback
            if self.is_chromadb_available() and self.backend != "chromadb":
                logger.warning(f"Primary backend {self.backend} failed, falling back to ChromaDB")
                try:
                    # Temporarily switch to ChromaDB for this operation
                    original_backend = self.backend
                    original_client = self.client
                    original_collection = getattr(self, "collection", None)
                    
                    self.backend = "chromadb"
                    self.client = self.chromadb_client
                    
                    # Handle namespace for ChromaDB
                    if namespace:
                        self.collection_name = f"{original_collection}_{namespace}"
                        self.collection = self.chromadb_client.get_or_create_collection(
                            name=self.collection_name,
                            metadata={"description": f"AmaniQuery ChromaDB collection: {self.collection_name}"}
                        )
                    else:
                        self.collection = self.chromadb_collection
                        self.collection_name = original_collection
                    
                    self._add_chromadb(chunks, batch_size)
                    
                    # Restore original backend
                    self.backend = original_backend
                    self.client = original_client
                    self.collection = original_collection
                    self.collection_name = original_collection
                    
                    logger.info(f"ChromaDB fallback successfully added {len(chunks)} documents")
                except Exception as fallback_error:
                    logger.error(f"ChromaDB fallback also failed: {fallback_error}")
                    raise fallback_error
            else:
                raise e

        # Restore original collection name
        self.collection_name = original_collection
    
    def index_document(self, doc_id: str, document: Dict, namespace: str = None):
        """Index document in Elasticsearch"""
        if self.es_client:
            try:
                # Create a copy of the document to avoid modifying the original
                es_document = document.copy()
                
                # Parse publication_date if it exists
                if "publication_date" in es_document and es_document["publication_date"]:
                    parsed_date = self._parse_publication_date(es_document["publication_date"])
                    if parsed_date:
                        es_document["publication_date"] = parsed_date
                
                index_name = self.collection_name
                if namespace:
                    index_name = f"{index_name}_{namespace}"
                # Ensure index existence for namespace-based index
                if not self.es_client.indices.exists(index=index_name):
                    # Create index with proper mapping for date fields
                    mapping = {
                        "mappings": {
                            "properties": {
                                "publication_date": {
                                    "type": "date",
                                    "format": "yyyy-MM-dd||yyyy-MM-dd'T'HH:mm:ss||epoch_millis||strict_date_optional_time"
                                },
                                "content": {"type": "text"},
                                "title": {"type": "text"},
                                "source_name": {"type": "keyword"},
                                "category": {"type": "keyword"},
                                "author": {"type": "text"},
                                "source_url": {"type": "keyword"}
                            }
                        }
                    }
                    self.es_client.indices.create(index=index_name, body=mapping)
                    logger.info(f"Created Elasticsearch index: {index_name}")
                self.es_client.index(index=index_name, id=doc_id, document=es_document)
                logger.info(f"Indexed document: {doc_id} in index: {index_name}")
            except Exception as e:
                logger.error(f"Failed to index document {doc_id}: {e}")
    
    def _parse_publication_date(self, date_str: str) -> Optional[str]:
        """
        Parse publication date from various formats to ISO format
        
        Args:
            date_str: Date string in various formats
            
        Returns:
            ISO formatted date string or None if parsing fails
        """
        if not date_str or not isinstance(date_str, str):
            return None
            
        date_str = date_str.strip()
        if not date_str:
            return None
            
        try:
            from datetime import datetime
            import re
            
            # Try ISO format first (already correct)
            try:
                # Check if it's already ISO format
                if re.match(r'^\d{4}-\d{2}-\d{2}', date_str):
                    datetime.fromisoformat(date_str.replace('Z', '+00:00').split('T')[0])
                    return date_str.split('T')[0]  # Return just the date part
            except:
                pass
            
            # Handle "DD Month YYYY" format (e.g., "26 August 2023", "28 July")
            month_map = {
                'january': 1, 'february': 2, 'march': 3, 'april': 4, 'may': 5, 'june': 6,
                'july': 7, 'august': 8, 'september': 9, 'october': 10, 'november': 11, 'december': 12,
                'jan': 1, 'feb': 2, 'mar': 3, 'apr': 4, 'may': 5, 'jun': 6,
                'jul': 7, 'aug': 8, 'sep': 9, 'oct': 10, 'nov': 11, 'dec': 12
            }
            
            # Match patterns like "26 August 2023" or "28 July"
            match = re.match(r'^(\d{1,2})\s+(\w+)\s*(\d{4})?$', date_str.lower())
            if match:
                day = int(match.group(1))
                month_name = match.group(2)
                year = int(match.group(3)) if match.group(3) else datetime.now().year
                
                if month_name in month_map:
                    month = month_map[month_name]
                    # Validate date
                    try:
                        date_obj = datetime(year, month, day)
                        return date_obj.strftime('%Y-%m-%d')
                    except ValueError:
                        # Invalid date (e.g., Feb 30)
                        logger.warning(f"Invalid date: {day}/{month}/{year} from '{date_str}'")
                        return None
            
            # Handle "Month DD, YYYY" format (e.g., "August 26, 2023")
            match = re.match(r'^(\w+)\s+(\d{1,2}),?\s*(\d{4})$', date_str.lower())
            if match:
                month_name = match.group(1)
                day = int(match.group(2))
                year = int(match.group(3))
                
                if month_name in month_map:
                    month = month_map[month_name]
                    try:
                        date_obj = datetime(year, month, day)
                        return date_obj.strftime('%Y-%m-%d')
                    except ValueError:
                        logger.warning(f"Invalid date: {day}/{month}/{year} from '{date_str}'")
                        return None
            
            # Handle "DD/MM/YYYY" or "DD-MM-YYYY" format
            match = re.match(r'^(\d{1,2})[/-](\d{1,2})[/-](\d{4})$', date_str)
            if match:
                day = int(match.group(1))
                month = int(match.group(2))
                year = int(match.group(3))
                try:
                    date_obj = datetime(year, month, day)
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    logger.warning(f"Invalid date: {day}/{month}/{year} from '{date_str}'")
                    return None
            
            # Handle "YYYY-MM-DD" format (already ISO)
            match = re.match(r'^(\d{4})-(\d{2})-(\d{2})$', date_str)
            if match:
                year = int(match.group(1))
                month = int(match.group(2))
                day = int(match.group(3))
                try:
                    date_obj = datetime(year, month, day)
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError:
                    logger.warning(f"Invalid date: {day}/{month}/{year} from '{date_str}'")
                    return None
            
            # If all parsing fails, log warning and return None
            logger.warning(f"Could not parse publication date: '{date_str}'")
            return None
            
        except Exception as e:
            logger.warning(f"Error parsing publication date '{date_str}': {e}")
            return None
    
    def search_documents(self, query: str, n_results: int = 5, namespace: str = None) -> List[Dict]:
        """Search documents in Elasticsearch"""
        if not self.es_client:
            return []
        try:
            index_name = self.collection_name
            if namespace:
                index_name = f"{index_name}_{namespace}"
            response = self.es_client.search(index=index_name, query={"match": {"content": query}}, size=n_results)
            results = []
            for hit in response["hits"]["hits"]:
                results.append({"id": hit["_id"], "text": hit["_source"].get("content", ""), "metadata": hit["_source"], "score": hit["_score"]})
            logger.info(f"Elasticsearch search returned {len(results)} results from index: {index_name}")
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
            
    def query(self, query_text: str, n_results: int = 5, filter: Optional[Dict] = None, namespace: str = None) -> List[Dict]:
        """Query vector store for similar documents with fallback support"""
        try:
            # 1. Encode query
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

            # 2. Define backends to try in order
            # Primary -> ChromaDB -> QDrant -> Upstash
            backends_to_try = [self.backend]
            fallbacks = ["chromadb", "qdrant", "upstash"]
            for fb in fallbacks:
                if fb != self.backend and fb not in backends_to_try:
                    backends_to_try.append(fb)
            
            logger.info(f"Querying with fallback chain: {backends_to_try}")

            # 3. Try backends in order
            for backend in backends_to_try:
                try:
                    results = []
                    
                    # Check availability before trying
                    if backend == "chromadb" and not self.is_chromadb_available():
                        continue
                    if backend == "qdrant" and "qdrant" not in self.backends and self.backend != "qdrant":
                        continue
                    if backend == "upstash" and "upstash" not in self.backends and self.backend != "upstash":
                        continue

                    # Execute query based on backend
                    if backend == self.backend:
                        # Use current configuration
                        results = self._execute_query(self.backend, query_embedding, n_results, filter, namespace)
                    else:
                        # Context switch for fallback
                        logger.info(f"Falling back to {backend}...")
                        
                        # Save current state
                        original_backend = self.backend
                        original_client = self.client
                        original_collection = getattr(self, "collection", None)
                        original_collection_name = self.collection_name
                        
                        try:
                            # Setup fallback state
                            self.backend = backend
                            
                            if backend == "chromadb":
                                self.client = self.chromadb_client
                                if namespace:
                                    self.collection_name = f"{original_collection_name}_{namespace}"
                                    self.collection = self.chromadb_client.get_or_create_collection(
                                        name=self.collection_name,
                                        metadata={"description": f"AmaniQuery ChromaDB collection: {self.collection_name}"}
                                    )
                                else:
                                    self.collection = self.chromadb_collection
                                    self.collection_name = original_collection_name
                                    
                            elif backend == "qdrant":
                                self.client = self.backends["qdrant"]
                                # QDrant handles collection name in _execute_query logic (via self.collection_name)
                                if namespace:
                                    self.collection_name = f"{original_collection_name}_{namespace}"
                                    # Ensure collection exists
                                    try:
                                        self.client.get_collection(self.collection_name)
                                    except:
                                        pass # Might fail if not exists, query will return empty
                                else:
                                    self.collection_name = original_collection_name

                            elif backend == "upstash":
                                self.client = self.backends["upstash"]
                                # Upstash uses metadata filter, collection name doesn't change on client
                                self.collection_name = original_collection_name

                            # Execute query
                            results = self._execute_query(backend, query_embedding, n_results, filter, namespace)
                            
                        finally:
                            # Restore state
                            self.backend = original_backend
                            self.client = original_client
                            if original_collection:
                                self.collection = original_collection
                            self.collection_name = original_collection_name
                    
                    if results:
                        logger.info(f"Query successful using {backend}, found {len(results)} results")
                        return results
                    
                except Exception as e:
                    logger.warning(f"Query failed with {backend}: {e}")
                    continue
            
            logger.warning("All backends in fallback chain failed or returned no results")
            return []

        except Exception as e:
            logger.error(f"Error querying vector store: {e}")
            return []

    def _execute_query(self, backend: str, query_embedding: List[float], n_results: int, filter: Optional[Dict], namespace: str) -> List[Dict]:
        """Helper to execute query on specific backend"""
        # Handle namespace setup for current backend (if not already handled in context switch)
        # Note: For primary backend, namespace setup logic was inside query(), moving it here or duplicating?
        # The context switch logic above handles namespace for fallbacks.
        # For primary backend, we need to handle it here if it wasn't done.
        
        # But wait, self.collection_name is modified in place in the original code.
        # Let's handle it safely.
        
        original_collection_name = self.collection_name
        
        try:
            if namespace:
                if backend in ["qdrant", "chromadb"]:
                    # For primary backend, we might need to update collection name if not already updated
                    if self.collection_name == original_collection_name: # Simple check
                         self.collection_name = f"{original_collection_name}_{namespace}"
                         
                    # For QDrant primary, ensure collection exists
                    if backend == "qdrant" and backend == self.backend: # Only if it's the primary/active one
                         try:
                             self.client.get_collection(self.collection_name)
                         except:
                             from qdrant_client.http import models
                             self.client.create_collection(
                                 collection_name=self.collection_name,
                                 vectors_config=models.VectorParams(size=384, distance=models.Distance.COSINE)
                             )
                elif backend == "es":
                     self.collection_name = f"{original_collection_name}_{namespace}"

            if backend == "upstash":
                return self._query_upstash(query_embedding, n_results, filter, namespace)
            elif backend == "qdrant":
                return self._query_qdrant(query_embedding, n_results, filter)
            elif backend == "chromadb":
                return self._query_chromadb(query_embedding, n_results, filter)
            else:
                return []
        finally:
            # Restore collection name if it was changed
            self.collection_name = original_collection_name

    def get_document(self, doc_id: str) -> Optional[Dict]:
        """
        Get a specific document by ID
        
        Args:
            doc_id: Document ID
            
        Returns:
            Document dictionary or None if not found
        """
        try:
            if self.backend == "chromadb":
                result = self.collection.get(ids=[doc_id])
                if result and result["ids"]:
                    metadata = result["metadatas"][0]
                    return {
                        "id": result["ids"][0],
                        "content": result["documents"][0],
                        "metadata": metadata
                    }
            elif self.backend == "qdrant":
                # Handle both integer and string IDs for Qdrant
                try:
                    # Try as is first (could be UUID string or int)
                    points = self.client.retrieve(
                        collection_name=self.collection_name,
                        ids=[doc_id]
                    )
                except:
                    # If that fails, it might be a hashed ID issue or format issue
                    # For now return None if direct retrieval fails
                    points = []
                
                if points:
                    point = points[0]
                    payload = point.payload
                    return {
                        "id": str(point.id),
                        "content": payload.get("text", ""),
                        "metadata": payload
                    }
            elif self.backend == "upstash":
                # Upstash fetch
                result = self.client.fetch(ids=[doc_id], include_metadata=True)
                if result:
                    vector = result[0]
                    if vector:
                        metadata = vector.metadata
                        return {
                            "id": vector.id,
                            "content": metadata.get("text", ""),
                            "metadata": metadata
                        }
            
            # Try Elasticsearch if available and not found in vector store
            if self.es_client:
                try:
                    res = self.es_client.get(index=self.collection_name, id=doc_id)
                    if res and res["found"]:
                        source = res["_source"]
                        return {
                            "id": res["_id"],
                            "content": source.get("text", ""),
                            "metadata": source
                        }
                except:
                    pass
                    
            return None
            
        except Exception as e:
            logger.error(f"Error getting document {doc_id}: {e}")
            return None

    
    def _query_upstash(self, query_embedding: List[float], n_results: int, filter: Optional[Dict], namespace: str = None) -> List[Dict]:
        """Query Upstash Vector"""
        filter_dict = {}
        if filter:
            for k, v in filter.items():
                filter_dict[f"metadata.{k}"] = str(v)
        if namespace:
            filter_dict["metadata.namespace"] = namespace
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

    def is_chromadb_available(self) -> bool:
        """Check if ChromaDB fallback is available"""
        return self.chromadb_client is not None and self.chromadb_collection is not None


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
    
    def query(self, query_embeddings=None, n_results=5, where=None):
        """Query QDrant collection"""
        if not query_embeddings:
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
        
        # Assume query_embeddings is a list, take the first one
        query_embedding = query_embeddings[0]
        
        scroll_filter = None
        if where:
            conditions = []
            for k, v in where.items():
                conditions.append(models.FieldCondition(key=k, match=models.MatchValue(value=str(v))))
            scroll_filter = models.Filter(must=conditions)
        
        query_result = self.client.query_points(
            collection_name=self.collection_name, 
            query=query_embedding, 
            limit=n_results, 
            query_filter=scroll_filter, 
            with_payload=True
        )
        
        ids = []
        documents = []
        metadatas = []
        distances = []
        
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
            ids.append(metadata.get("chunk_id", str(point_id) if point_id else ""))
            documents.append(metadata.get("text", ""))
            metadatas.append(metadata)
            distances.append(score)
        
        return {"ids": [ids], "documents": [documents], "metadatas": [metadatas], "distances": [distances]}


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
    
    def query(self, query_embeddings=None, n_results=5, where=None):
        """Query Upstash index"""
        if not query_embeddings:
            return {"ids": [[]], "documents": [[]], "metadatas": [[]], "distances": [[]]}
        
        # Assume query_embeddings is a list, take the first one
        query_embedding = query_embeddings[0]
        
        filter_dict = {}
        # Add collection filter
        filter_dict["metadata.collection"] = self.collection_name
        
        if where:
            for k, v in where.items():
                filter_dict[f"metadata.{k}"] = str(v)
                
        results = self.client.query(
            vector=query_embedding, 
            top_k=n_results, 
            filter=filter_dict, 
            include_metadata=True, 
            include_data=True
        )
        
        ids = []
        documents = []
        metadatas = []
        distances = []
        
        for hit in results:
            metadata = {k: str(v) if not isinstance(v, str) else v for k, v in hit.metadata.items()}
            ids.append(hit.id)
            documents.append(metadata.get("text", ""))
            metadatas.append(metadata)
            distances.append(hit.score)
            
        return {"ids": [ids], "documents": [documents], "metadatas": [metadatas], "distances": [distances]}
