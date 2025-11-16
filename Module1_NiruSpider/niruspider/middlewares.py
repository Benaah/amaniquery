"""
NiruSpider - Custom Middlewares
"""
import random
import time
from scrapy import signals
from loguru import logger


class PoliteDelayMiddleware:
    """
    Add extra politeness - random delays to avoid patterns
    Enhanced with per-domain rate limiting via Redis
    """
    
    def __init__(self, delay_range=(1.0, 3.0), rate_limiter=None):
        self.delay_range = delay_range
        self.rate_limiter = rate_limiter
    
    @classmethod
    def from_crawler(cls, crawler):
        # Get delay settings
        base_delay = crawler.settings.getfloat("DOWNLOAD_DELAY", 2.0)
        delay_range = (base_delay * 0.5, base_delay * 1.5)
        
        # Try to initialize rate limiter
        rate_limiter = None
        try:
            from ..rate_limiter import RateLimiter
            redis_url = crawler.settings.get("REDIS_URL")
            default_rate = crawler.settings.getfloat("DEFAULT_RATE_LIMIT", 2.0)
            rate_limiter = RateLimiter(redis_url=redis_url, default_rate=default_rate)
        except Exception as e:
            logger.debug(f"Rate limiter not available: {e}")
        
        middleware = cls(delay_range, rate_limiter=rate_limiter)
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        return middleware
    
    def spider_opened(self, spider):
        if self.rate_limiter and self.rate_limiter.redis_client:
            spider.logger.info("PoliteDelayMiddleware: Using Redis-based rate limiting")
        else:
            spider.logger.info(f"PoliteDelayMiddleware: Random delays between {self.delay_range[0]:.1f}s and {self.delay_range[1]:.1f}s")
    
    def process_request(self, request, spider):
        # Use rate limiter if available
        if self.rate_limiter and self.rate_limiter.redis_client:
            self.rate_limiter.wait_if_needed(request.url)
        else:
            # Fallback to random delay
            delay = random.uniform(*self.delay_range)
            time.sleep(delay)
        return None
