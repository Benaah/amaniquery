"""
Redis Cache Utility for API Endpoints
"""
import os
import json
from typing import Optional, Any, Callable
from functools import wraps
from loguru import logger

try:
    from upstash_redis import Redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("upstash-redis not available, caching disabled")


class CacheManager:
    """Manages Redis caching for API responses"""
    
    def __init__(self, config_manager=None):
        self.redis_client = None
        self.config_manager = config_manager
        self._init_redis()
    
    def _init_redis(self):
        """Initialize Redis client"""
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available, caching disabled")
            return
        
        try:
            redis_url = os.getenv("UPSTASH_REDIS_URL")
            redis_token = os.getenv("UPSTASH_REDIS_TOKEN")
            
            # Try to get from config manager if env vars not set
            if (not redis_url or (redis_url and redis_url.strip().startswith("error"))) and self.config_manager:
                redis_url = self.config_manager.get_config("UPSTASH_REDIS_URL")
            if (not redis_token or (redis_token and redis_token.strip().startswith("error"))) and self.config_manager:
                redis_token = self.config_manager.get_config("UPSTASH_REDIS_TOKEN")
            
            if redis_url and redis_token:
                self.redis_client = Redis(url=redis_url, token=redis_token)
                # Test connection
                self.redis_client.ping()
                logger.info("Redis cache initialized successfully")
            else:
                logger.warning("Redis credentials not configured, caching disabled")
        except Exception as e:
            logger.warning(f"Failed to initialize Redis cache: {e}, caching disabled")
            self.redis_client = None
    
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache"""
        if not self.redis_client:
            return None
        
        try:
            cached = self.redis_client.get(key)
            if cached:
                return json.loads(cached)
            return None
        except Exception as e:
            logger.warning(f"Redis cache get error for key {key}: {e}")
            return None
    
    def set(self, key: str, value: Any, ttl: int = 60) -> bool:
        """Set value in cache with TTL (time-to-live in seconds)"""
        if not self.redis_client:
            return False
        
        try:
            serialized = json.dumps(value)
            self.redis_client.setex(key, ttl, serialized)
            return True
        except Exception as e:
            logger.warning(f"Redis cache set error for key {key}: {e}")
            return False
    
    def delete(self, key: str) -> bool:
        """Delete key from cache"""
        if not self.redis_client:
            return False
        
        try:
            self.redis_client.delete(key)
            return True
        except Exception as e:
            logger.warning(f"Redis cache delete error for key {key}: {e}")
            return False
    
    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern"""
        if not self.redis_client:
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            logger.warning(f"Redis cache delete pattern error for {pattern}: {e}")
            return 0
    
    def invalidate_crawler_cache(self):
        """Invalidate all crawler-related cache"""
        self.delete("cache:admin:crawlers")
        self.delete_pattern("cache:admin:crawlers:*")
    
    def invalidate_stats_cache(self):
        """Invalidate stats-related cache"""
        self.delete("cache:stats")
        self.delete("cache:health")
        self.delete("cache:admin:databases")
        self.delete("cache:admin:database-storage")


# Global cache manager instance
_cache_manager: Optional[CacheManager] = None


def get_cache_manager(config_manager=None) -> CacheManager:
    """Get or create cache manager instance"""
    global _cache_manager
    if _cache_manager is None:
        _cache_manager = CacheManager(config_manager)
    return _cache_manager


def cached(key_prefix: str, ttl: int = 60):
    """
    Decorator to cache function results
    
    Args:
        key_prefix: Prefix for cache key
        ttl: Time-to-live in seconds
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache_manager = get_cache_manager()
            
            # Generate cache key from function name and arguments
            cache_key = f"cache:{key_prefix}"
            if kwargs:
                # Include relevant kwargs in key (exclude request objects)
                key_parts = [f"{k}:{v}" for k, v in sorted(kwargs.items()) 
                           if k not in ['request', 'admin'] and not isinstance(v, object)]
                if key_parts:
                    cache_key += ":" + ":".join(key_parts)
            
            # Try to get from cache
            cached_result = cache_manager.get(cache_key)
            if cached_result is not None:
                logger.debug(f"Cache hit for {cache_key}")
                return cached_result
            
            # Cache miss, execute function
            logger.debug(f"Cache miss for {cache_key}")
            result = await func(*args, **kwargs)
            
            # Store in cache
            cache_manager.set(cache_key, result, ttl)
            
            return result
        
        return wrapper
    return decorator

