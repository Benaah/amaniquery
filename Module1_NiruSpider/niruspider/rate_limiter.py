"""
Rate Limiter for Per-Domain Request Throttling
Uses Redis for distributed rate limiting
"""
import os
import time
from typing import Optional
from urllib.parse import urlparse
from loguru import logger

try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not available, rate limiting will be disabled")


class RateLimiter:
    """
    Per-domain rate limiter using Redis
    Implements token bucket algorithm for rate limiting
    """
    
    def __init__(self, redis_url: Optional[str] = None, default_rate: float = 2.0):
        """
        Initialize rate limiter
        
        Args:
            redis_url: Redis connection URL (defaults to REDIS_URL env var)
            default_rate: Default requests per second per domain
        """
        self.redis_client = None
        self.default_rate = default_rate
        self.domain_rates = {}  # Per-domain custom rates
        
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available, rate limiting disabled")
            return
        
        if redis_url is None:
            redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        
        try:
            # Parse Redis URL
            if redis_url.startswith("redis://") or redis_url.startswith("rediss://"):
                self.redis_client = redis.from_url(redis_url, decode_responses=True)
            else:
                # Fallback to localhost
                self.redis_client = redis.Redis(
                    host="localhost",
                    port=6379,
                    db=0,
                    decode_responses=True
                )
            
            # Test connection
            self.redis_client.ping()
            logger.info("Rate limiter initialized with Redis")
        except Exception as e:
            logger.error(f"Failed to connect to Redis: {e}")
            logger.warning("Rate limiting disabled, falling back to in-memory limiter")
            self.redis_client = None
            self._in_memory_limits = {}  # Fallback in-memory storage
    
    def set_domain_rate(self, domain: str, rate: float):
        """
        Set custom rate for a domain
        
        Args:
            domain: Domain name
            rate: Requests per second
        """
        self.domain_rates[domain] = rate
        logger.debug(f"Set rate for {domain}: {rate} req/s")
    
    def wait_if_needed(self, url: str) -> bool:
        """
        Check if request should be throttled and wait if needed
        
        Args:
            url: Request URL
        
        Returns:
            True if request should proceed, False if should be skipped
        """
        domain = self._extract_domain(url)
        if not domain:
            return True  # Allow if can't extract domain
        
        rate = self.domain_rates.get(domain, self.default_rate)
        min_interval = 1.0 / rate  # Minimum seconds between requests
        
        if self.redis_client:
            return self._check_redis(domain, min_interval)
        else:
            return self._check_in_memory(domain, min_interval)
    
    def _check_redis(self, domain: str, min_interval: float) -> bool:
        """Check rate limit using Redis"""
        try:
            key = f"rate_limit:{domain}"
            now = time.time()
            
            # Get last request time
            last_time_str = self.redis_client.get(key)
            
            if last_time_str:
                last_time = float(last_time_str)
                elapsed = now - last_time
                
                if elapsed < min_interval:
                    # Need to wait
                    wait_time = min_interval - elapsed
                    logger.debug(f"Rate limiting {domain}: waiting {wait_time:.2f}s")
                    time.sleep(wait_time)
            
            # Update last request time
            self.redis_client.set(key, str(time.time()), ex=3600)  # Expire after 1 hour
            return True
            
        except Exception as e:
            logger.error(f"Redis rate limit check error: {e}")
            # Fallback to in-memory
            return self._check_in_memory(domain, min_interval)
    
    def _check_in_memory(self, domain: str, min_interval: float) -> bool:
        """Check rate limit using in-memory storage (fallback)"""
        if not hasattr(self, '_in_memory_limits'):
            self._in_memory_limits = {}
        
        now = time.time()
        last_time = self._in_memory_limits.get(domain, 0)
        elapsed = now - last_time
        
        if elapsed < min_interval:
            wait_time = min_interval - elapsed
            logger.debug(f"Rate limiting {domain}: waiting {wait_time:.2f}s")
            time.sleep(wait_time)
        
        self._in_memory_limits[domain] = time.time()
        return True
    
    def _extract_domain(self, url: str) -> Optional[str]:
        """Extract domain from URL"""
        try:
            parsed = urlparse(url)
            domain = parsed.netloc.lower()
            # Remove port if present
            if ':' in domain:
                domain = domain.split(':')[0]
            return domain
        except Exception:
            return None
    
    def get_stats(self) -> dict:
        """Get rate limiting statistics"""
        if not self.redis_client:
            return {"status": "disabled", "reason": "Redis not available"}
        
        try:
            # Get all rate limit keys
            keys = self.redis_client.keys("rate_limit:*")
            stats = {
                "status": "active",
                "domains_tracked": len(keys),
                "default_rate": self.default_rate,
                "custom_rates": self.domain_rates,
            }
            return stats
        except Exception as e:
            logger.error(f"Error getting rate limit stats: {e}")
            return {"status": "error", "error": str(e)}


class PoliteDelayMiddleware:
    """
    Scrapy middleware for rate limiting
    Integrates with RateLimiter
    """
    
    def __init__(self, rate_limiter: Optional[RateLimiter] = None):
        self.rate_limiter = rate_limiter or RateLimiter()
    
    @classmethod
    def from_crawler(cls, crawler):
        """Create middleware from crawler settings"""
        redis_url = crawler.settings.get("REDIS_URL")
        default_rate = crawler.settings.getfloat("DEFAULT_RATE_LIMIT", 2.0)
        rate_limiter = RateLimiter(redis_url=redis_url, default_rate=default_rate)
        return cls(rate_limiter=rate_limiter)
    
    def process_request(self, request, spider):
        """Process request and apply rate limiting"""
        if self.rate_limiter and self.rate_limiter.redis_client:
            self.rate_limiter.wait_if_needed(request.url)
        return None

