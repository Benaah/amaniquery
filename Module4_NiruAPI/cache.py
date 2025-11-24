"""
Redis Cache Utility for API Endpoints
Implements "Kenyan" caching strategies: Exact/Normalized Query Cache, Smart TTL, Stampede Protection, Two-Level Cache.
"""
import os
import json
import hashlib
import re
import time
import asyncio
from typing import Optional, Any, Callable, Dict, Union, List
from functools import wraps
from collections import OrderedDict
from loguru import logger
import numpy as np

# Try importing standard redis first (preferred for local), then upstash
try:
    import redis
    STANDARD_REDIS_AVAILABLE = True
except ImportError:
    STANDARD_REDIS_AVAILABLE = False

try:
    from upstash_redis import Redis as UpstashRedis
    UPSTASH_AVAILABLE = True
except ImportError:
    UPSTASH_AVAILABLE = False

# Smart TTL Strategy (Kenyan Reality)
TTL_MAP = {
    "wanjiku": 3600 * 24,      # 24 hrs (citizens repeat a lot)
    "mwanahabari": 3600 * 4,   # 4 hrs (news moves fast)
    "wakili": 3600 * 24 * 90,  # 90 days (laws rarely change)
    "widget": 3600 * 24 * 365, # 1 year (calculator never changes)
    "trending": 300,           # 5 min during protests
    "default": 3600 * 12       # 12 hours default
}

class LRUCache:
    """Simple Local LRU Cache"""
    def __init__(self, capacity: int = 5000):
        self.cache = OrderedDict()
        self.capacity = capacity

    def get(self, key: str) -> Optional[Any]:
        if key not in self.cache:
            return None
        self.cache.move_to_end(key)
        return self.cache[key]

    def set(self, key: str, value: Any):
        if key in self.cache:
            self.cache.move_to_end(key)
        self.cache[key] = value
        if len(self.cache) > self.capacity:
            self.cache.popitem(last=False)
            
    def delete(self, key: str):
        if key in self.cache:
            del self.cache[key]
            
    def clear(self):
        self.cache.clear()

class SemanticCache:
    """In-Memory Semantic Cache using Cosine Similarity"""
    def __init__(self, capacity: int = 100, threshold: float = 0.92):
        self.capacity = capacity
        self.threshold = threshold
        # Store as list of tuples: (embedding_vector, result_dict, timestamp)
        self.entries = [] 

    def get_similar(self, query_embedding: List[float]) -> Optional[Dict]:
        if not self.entries:
            return None
            
        # Convert to numpy for fast calculation if not already
        query_vec = np.array(query_embedding)
        norm_query = np.linalg.norm(query_vec)
        if norm_query == 0:
            return None
            
        best_score = -1
        best_result = None
        
        for cached_emb, result, _ in self.entries:
            cached_vec = np.array(cached_emb)
            norm_cached = np.linalg.norm(cached_vec)
            if norm_cached == 0:
                continue
                
            score = np.dot(query_vec, cached_vec) / (norm_query * norm_cached)
            
            if score > best_score:
                best_score = score
                best_result = result
        
        if best_score >= self.threshold:
            logger.info(f"🧠 Semantic Cache Hit! Score: {best_score:.4f}")
            return best_result
            
        return None

    def set(self, embedding: List[float], result: Dict):
        # Evict if full (Simple FIFO for now, or remove oldest)
        if len(self.entries) >= self.capacity:
            self.entries.pop(0)
            
        self.entries.append((embedding, result, time.time()))

class CacheManager:
    """Manages Redis caching with advanced strategies"""
    
    def __init__(self, config_manager=None):
        self.redis_client = None
        self.local_cache = LRUCache(capacity=5000)
        self.semantic_cache = SemanticCache(capacity=50) # Keep small for speed
        self.config_manager = config_manager
        self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis client (Local or Upstash)"""
        # 1. Try Local/Standard Redis first (via REDIS_URL)
        redis_url = os.getenv("REDIS_URL")
        if redis_url and STANDARD_REDIS_AVAILABLE:
            try:
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
                self.redis_client.ping()
                logger.info(f"🚀 Local Redis cache initialized: {redis_url}")
                return
            except Exception as e:
                logger.warning(f"Failed to connect to local Redis: {e}")

        # 2. Fallback to Upstash Redis
        if UPSTASH_AVAILABLE:
            try:
                upstash_url = os.getenv("UPSTASH_REDIS_URL")
                upstash_token = os.getenv("UPSTASH_REDIS_TOKEN")
                
                if (not upstash_url or upstash_url.startswith("error")) and self.config_manager:
                    upstash_url = self.config_manager.get_config("UPSTASH_REDIS_URL")
                if (not upstash_token or upstash_token.startswith("error")) and self.config_manager:
                    upstash_token = self.config_manager.get_config("UPSTASH_REDIS_TOKEN")
                
                if upstash_url and upstash_token:
                    self.redis_client = UpstashRedis(url=upstash_url, token=upstash_token)
                    # Upstash client doesn't always support ping in the same way, but let's try basic op
                    # self.redis_client.ping() 
                    logger.info("☁️ Upstash Redis cache initialized")
                    return
            except Exception as e:
                logger.warning(f"Failed to initialize Upstash Redis: {e}")
        
        logger.warning("⚠️ No Redis available. Caching disabled.")
        self.redis_client = None

    def normalize_query(self, query: str) -> str:
        """Normalized + Sheng-Proof Cache Key Generation"""
        if not query:
            return ""
        q = query.lower()
        # Sheng replacements
        q = re.sub(r'kanjo', 'nairobi county', q)
        q = re.sub(r'doa|pesa|dough', 'money', q)
        q = re.sub(r'mhesh|hon|mweshimiwa', 'mp', q)
        q = re.sub(r'shamba boy|bibi ya shamba', 'citizen', q)
        # Remove special chars and extra spaces
        q = re.sub(r'[\W_]+', ' ', q).strip()
        return q

    def generate_keys(self, query: str) -> Dict[str, str]:
        """Generate both Exact and Normalized keys"""
        # Exact Key
        query_hash = hashlib.sha256(query.lower().strip().encode()).hexdigest()
        exact_key = f"q:{query_hash}"
        
        # Normalized Key
        norm_query = self.normalize_query(query)
        norm_hash = hashlib.sha256(norm_query.encode()).hexdigest()
        norm_key = f"norm:{norm_hash}"
        
        return {"exact": exact_key, "normalized": norm_key}

    def get_smart_ttl(self, key_type: str = "default") -> int:
        """Get TTL based on content type"""
        return TTL_MAP.get(key_type, TTL_MAP["default"])

    async def get(self, key: str) -> Optional[Any]:
        """Two-Level Get: Local -> Redis"""
        # 1. Check Local Cache
        local_val = self.local_cache.get(key)
        if local_val:
            return local_val
        
        if not self.redis_client:
            return None
        
        # 2. Check Redis
        try:
            # Handle async/sync difference between standard redis and upstash-redis if needed
            # Standard redis (sync) vs Upstash (http/sync usually, but check lib)
            # Assuming sync for simplicity as per standard python clients
            cached = self.redis_client.get(key)
            if cached:
                data = json.loads(cached)
                # Populate local cache
                self.local_cache.set(key, data)
                return data
        except Exception as e:
            logger.warning(f"Redis get error: {e}")
        
        return None

    async def set(self, key: str, value: Any, ttl: int = None) -> bool:
        """Set value in Redis and Local Cache"""
        if ttl is None:
            ttl = self.get_smart_ttl("default")
            
        # Set local
        self.local_cache.set(key, value)
        
        if not self.redis_client:
            return False
            
        try:
            serialized = json.dumps(value)
            # Standard redis uses setex(name, time, value)
            # Upstash uses set(name, value, ex=time) or setex
            if hasattr(self.redis_client, 'setex'):
                 self.redis_client.setex(key, ttl, serialized)
            else:
                 self.redis_client.set(key, serialized, ex=ttl)
            return True
        except Exception as e:
            logger.warning(f"Redis set error: {e}")
            return False

    async def get_or_compute(self, query: str, compute_func: Callable, ttl_type: str = "default", embedding: List[float] = None) -> Any:
        """
        Get from cache or compute with Stampede Protection and Semantic Caching
        """
        keys = self.generate_keys(query)
        exact_key = keys["exact"]
        norm_key = keys["normalized"]
        
        # 1. Try Exact Match
        cached = await self.get(exact_key)
        if cached:
            logger.info(f"🎯 Cache Hit (Exact): {query[:30]}...")
            return cached
            
        # 2. Try Normalized Match
        cached = await self.get(norm_key)
        if cached:
            logger.info(f"🎯 Cache Hit (Normalized): {query[:30]}...")
            return cached

        # 3. Try Semantic Match (if embedding provided)
        if embedding is not None:
            semantic_cached = self.semantic_cache.get_similar(embedding)
            if semantic_cached:
                return semantic_cached

        # 4. Cache Miss - Stampede Protection
        if not self.redis_client:
            result = await compute_func()
            # Update semantic cache locally
            if embedding is not None:
                self.semantic_cache.set(embedding, result)
            return result

        stampede_key = f"computing:{exact_key}"
        try:
            # Try to acquire lock
            # nx=True means set only if not exists
            # Standard redis: set(name, value, ex=None, px=None, nx=False, xx=False)
            # Upstash: set(name, value, ex=None, nx=False)
            is_computing = self.redis_client.set(stampede_key, "1", ex=10, nx=True)
            
            if not is_computing:
                # Someone else is computing, wait and retry
                logger.info(f"⏳ Waiting for computation: {query[:30]}...")
                await asyncio.sleep(0.2) # Wait 200ms
                # Retry get
                cached = await self.get(exact_key)
                if cached:
                    return cached
                # If still not found after wait, just compute it ourselves (fallback)
            
            # Compute
            result = await compute_func()
            
            # Cache result (both exact and normalized)
            ttl = self.get_smart_ttl(ttl_type)
            await self.set(exact_key, result, ttl)
            await self.set(norm_key, result, ttl)
            
            # Update semantic cache locally
            if embedding is not None:
                self.semantic_cache.set(embedding, result)
            
            # Release lock
            self.redis_client.delete(stampede_key)
            
            return result
            
        except Exception as e:
            logger.error(f"Cache stampede error: {e}")
            return await compute_func()

    def delete(self, key: str) -> bool:
        self.local_cache.delete(key)
        if not self.redis_client:
            return False
        try:
            self.redis_client.delete(key)
            return True
        except Exception:
            return False

    def delete_pattern(self, pattern: str) -> int:
        self.local_cache.clear() # Clear local cache on pattern delete to be safe
        if not self.redis_client:
            return 0
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception:
            return 0

    def invalidate_crawler_cache(self):
        self.delete("cache:admin:crawlers")
        self.delete_pattern("cache:admin:crawlers:*")
    
    def invalidate_stats_cache(self):
        self.delete("cache:stats")
        self.delete("cache:health")
        self.delete("cache:admin:databases")
        self.delete("cache:admin:database-storage")

# Global cache manager instance
_cache_manager: Optional[CacheManager] = None

def get_cache_manager(config_manager=None) -> CacheManager:
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager(config_manager)
    return _cache_manager

def cached(key_prefix: str, ttl: int = 60):
    """Decorator to cache function results"""
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()
            
            cache_key = f"cache:{key_prefix}"
            if kwargs:
                key_parts = [f"{k}:{v}" for k, v in sorted(kwargs.items()) 
                           if k not in ['request', 'admin'] and not isinstance(v, object)]
                if key_parts:
                    cache_key += ":" + ":".join(key_parts)
            
            # Use the new async get
            cached_result = await cache_manager.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            result = await func(*args, **kwargs)
            await cache_manager.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator
