"""
NiruSpider Settings
"""
import os
from pathlib import Path

BOT_NAME = "niruspider"

SPIDER_MODULES = ["niruspider.spiders"]
NEWSPIDER_MODULE = "niruspider.spiders"

# Crawl responsibly
ROBOTSTXT_OBEY = True
USER_AGENT = "AmaniQuery/1.0 (+https://github.com/amaniquery; contact@amaniquery.ke)"

# Performance settings
CONCURRENT_REQUESTS = 8
CONCURRENT_REQUESTS_PER_DOMAIN = 4
DOWNLOAD_DELAY = 2.5  # Be polite - 2.5 seconds between requests
RANDOMIZE_DOWNLOAD_DELAY = True

# AutoThrottle (dynamic delay adjustment)
AUTOTHROTTLE_ENABLED = True
AUTOTHROTTLE_START_DELAY = 2
AUTOTHROTTLE_MAX_DELAY = 10
AUTOTHROTTLE_TARGET_CONCURRENCY = 4.0

# Caching (for development)
HTTPCACHE_ENABLED = True
HTTPCACHE_EXPIRATION_SECS = 86400  # 24 hours
HTTPCACHE_DIR = "httpcache"

# Retry settings
RETRY_TIMES = 3
RETRY_HTTP_CODES = [500, 502, 503, 504, 408, 429]

# Download timeout
DOWNLOAD_TIMEOUT = 30

# Enable pipelines
ITEM_PIPELINES = {
    "niruspider.pipelines.DataValidationPipeline": 100,
    "niruspider.pipelines.VectorStorePipeline": 150, 
    "niruspider.pipelines.PDFDownloadPipeline": 200,
    "niruspider.pipelines.FileStoragePipeline": 300,
}

# Output directory
PROJECT_ROOT = Path(__file__).parent.parent.parent
RAW_DATA_PATH = PROJECT_ROOT / "data" / "raw"
RAW_DATA_PATH.mkdir(parents=True, exist_ok=True)

# Logging
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s [%(name)s] %(levelname)s: %(message)s"
LOG_DATEFORMAT = "%Y-%m-%d %H:%M:%S"

# PDF handling
FILES_STORE = str(RAW_DATA_PATH / "pdfs")
MEDIA_ALLOW_REDIRECTS = True

# Request headers
DEFAULT_REQUEST_HEADERS = {
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}

# Middlewares
DOWNLOADER_MIDDLEWARES = {
    "niruspider.middlewares.PoliteDelayMiddleware": 543,
}

# Feed exports
FEEDS = {
    str(RAW_DATA_PATH / "%(name)s_%(time)s.jsonl"): {
        "format": "jsonlines",
        "encoding": "utf8",
        "store_empty": False,
        "overwrite": False,
    }
}
