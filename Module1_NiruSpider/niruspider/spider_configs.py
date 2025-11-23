"""
Spider-specific configuration settings
Allows per-spider optimization of concurrency, delays, and retry logic
"""

# Spider-specific settings override
SPIDER_CONFIGS = {
    "news_rss": {
        "CONCURRENT_REQUESTS": 100,  # RSS feeds can handle more
        "CONCURRENT_REQUESTS_PER_DOMAIN": 20,
        "DOWNLOAD_DELAY": 0.3,
        "RETRY_TIMES": 3,  # RSS feeds are usually reliable
        "DOWNLOAD_TIMEOUT": 30,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 20.0,
    },
    "global_trends": {
        "CONCURRENT_REQUESTS": 80,  # International sources
        "CONCURRENT_REQUESTS_PER_DOMAIN": 15,
        "DOWNLOAD_DELAY": 0.5,
        "RETRY_TIMES": 4,
        "DOWNLOAD_TIMEOUT": 45,  # International sources may be slower
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 15.0,
    },
    "parliament": {
        "CONCURRENT_REQUESTS": 16,  # Government site - be polite
        "CONCURRENT_REQUESTS_PER_DOMAIN": 4,
        "DOWNLOAD_DELAY": 2.0,  # More conservative for official site
        "RETRY_TIMES": 7,  # Government sites can be flaky
        "DOWNLOAD_TIMEOUT": 60,
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 4.0,
    },
    "kenya_law": {
        "CONCURRENT_REQUESTS": 16,  # Government site - be polite
        "CONCURRENT_REQUESTS_PER_DOMAIN": 4,
        "DOWNLOAD_DELAY": 2.5,
        "RETRY_TIMES": 8,  # Kenya Law can be very slow/flaky
        "DOWNLOAD_TIMEOUT": 90,  # Very slow sometimes
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 3.0,
    },
    "constitution": {
        "CONCURRENT_REQUESTS": 12,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 3,
        "DOWNLOAD_DELAY": 2.5,
        "RETRY_TIMES": 6,
        "DOWNLOAD_TIMEOUT": 60,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 3.0,
    },
    "parliament_videos": {
        "CONCURRENT_REQUESTS": 8,
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,
        "DOWNLOAD_DELAY": 3.0,  # YouTube - be very polite
        "RETRY_TIMES": 5,
        "DOWNLOAD_TIMEOUT": 60,
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 2.0,
    },
}


def get_spider_config(spider_name):
    """
    Get configuration for a specific spider
    
    Args:
        spider_name: Name of the spider
        
    Returns:
        dict: Configuration dictionary or empty dict if not found
    """
    return SPIDER_CONFIGS.get(spider_name, {})


def apply_spider_config(spider):
    """
    Apply spider-specific configuration to a spider instance
    
    Args:
        spider: Spider instance to configure
    """
    config = get_spider_config(spider.name)
    
    if not config:
        return
    
    # Apply custom settings from config
    if not hasattr(spider, 'custom_settings'):
        spider.custom_settings = {}
    
    spider.custom_settings.update(config)
    spider.logger.info(f"Applied custom config for {spider.name}: {config}")
