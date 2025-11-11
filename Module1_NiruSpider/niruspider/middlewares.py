"""
NiruSpider - Custom Middlewares
"""
import random
import time
from scrapy import signals


class PoliteDelayMiddleware:
    """
    Add extra politeness - random delays to avoid patterns
    """
    
    def __init__(self, delay_range=(1.0, 3.0)):
        self.delay_range = delay_range
    
    @classmethod
    def from_crawler(cls, crawler):
        # Get delay settings
        base_delay = crawler.settings.getfloat("DOWNLOAD_DELAY", 2.0)
        delay_range = (base_delay * 0.5, base_delay * 1.5)
        
        middleware = cls(delay_range)
        crawler.signals.connect(middleware.spider_opened, signal=signals.spider_opened)
        return middleware
    
    def spider_opened(self, spider):
        spider.logger.info(f"PoliteDelayMiddleware: Random delays between {self.delay_range[0]:.1f}s and {self.delay_range[1]:.1f}s")
    
    def process_request(self, request, spider):
        # Add random delay
        delay = random.uniform(*self.delay_range)
        time.sleep(delay)
        return None
