"""
Kenya Law Spider - Crawls kenyalaw.org for Constitution and Acts
Enhanced with robust extraction and error handling
"""
import scrapy
from datetime import datetime
from ..items import DocumentItem
from ..extractors import ArticleExtractor


class KenyaLawSpider(scrapy.Spider):
    name = "kenya_law"
    allowed_domains = ["kenyalaw.org"]
    
    def __init__(self, *args, **kwargs):
        super(KenyaLawSpider, self).__init__(*args, **kwargs)
        self.article_extractor = ArticleExtractor()
        self.max_pages = 100  # Limit pages to crawl
    
    # Start URLs
    start_urls = [
        "http://kenyalaw.org/kl/index.php?id=398",  # Constitution
        "http://kenyalaw.org/kl/index.php?id=569",  # Acts
    ]
    
    custom_settings = {
        "DOWNLOAD_DELAY": 2.5,  # Polite delay between requests
        "RANDOMIZE_DOWNLOAD_DELAY": True,  # Randomize delay to avoid patterns
        "CONCURRENT_REQUESTS": 4,  # Allow more concurrent requests for efficiency
        "CONCURRENT_REQUESTS_PER_DOMAIN": 2,  # Limit per domain
        "ROBOTSTXT_OBEY": True,  # Respect robots.txt
        "USER_AGENT": "AmaniQuery/1.0 (Legal Research Bot; contact@amaniquery.org)",
        "RETRY_ENABLED": True,
        "RETRY_TIMES": 5,  # More retries for reliability
        "RETRY_HTTP_CODES": [500, 502, 503, 504, 408, 429, 403],
        "DOWNLOAD_TIMEOUT": 60,  # Longer timeout for slow responses
        "AUTOTHROTTLE_ENABLED": True,
        "AUTOTHROTTLE_START_DELAY": 1,
        "AUTOTHROTTLE_MAX_DELAY": 120,  # Allow longer delays if needed
        "AUTOTHROTTLE_TARGET_CONCURRENCY": 2.0,
        "AUTOTHROTTLE_DEBUG": False,  # Disable debug logs
        "HTTPCACHE_ENABLED": True,  # Enable HTTP caching
        "HTTPCACHE_EXPIRATION_SECS": 3600,  # Cache for 1 hour
        "HTTPCACHE_DIR": "httpcache",  # Cache directory
        "DUPEFILTER_CLASS": "scrapy.dupefilters.RFPDupeFilter",  # Standard dupe filter
    }
    
    def parse(self, response):
        """Parse index pages to find document links"""
        try:
            self.logger.info(f"Parsing: {response.url}")
            
            # Find all document links
            # Kenya Law uses specific patterns for acts
            doc_links = response.css('a[href*="actview"]::attr(href)').getall()
            
            for link in doc_links:
                yield response.follow(link, callback=self.parse_document)
            
            # Also look for generic links to legal documents
            for link in response.css('a::attr(href)').getall():
                if any(keyword in link.lower() for keyword in ['act', 'law', 'constitution']):
                    yield response.follow(link, callback=self.parse_document)
        except Exception as e:
            self.logger.error(f"Error parsing {response.url}: {e}")
    
    def parse_document(self, response):
        """Parse individual legal document using enhanced extractor"""
        try:
            self.logger.info(f"Parsing document: {response.url}")
            
            # Check if this is a PDF link
            if response.url.endswith('.pdf'):
                yield DocumentItem(
                    url=response.url,
                    title="Legal Document",
                    content="",
                    content_type="pdf",
                    category="Kenyan Law",
                    source_name="Kenya Law",
                    publication_date=None,
                    raw_html="",
                )
                return
            
            # Use enhanced article extractor
            extracted = self.article_extractor.extract(response.text, url=response.url)
            
            # Use extracted content, fallback to basic extraction
            content = extracted.get("text", "")
            if not content or len(content) < 50:
                # Fallback to basic extraction
                content_selectors = [
                    '#content-core',
                    '.document-content',
                    'div.content',
                    'article',
                    'main',
                ]
                
                for selector in content_selectors:
                    content_parts = response.css(f'{selector}::text').getall()
                    if content_parts:
                        content = '\n'.join([t.strip() for t in content_parts if t.strip()])
                        break
                
                if not content:
                    content = '\n'.join([t.strip() for t in response.css('p::text').getall() if t.strip()])
            
            # Use extracted title if available
            title = extracted.get("title", "") or response.css('h1::text, h2::text, title::text').get()
            if title:
                title = title.strip()
            else:
                title = "Untitled Document"
            
            # Extract publication date if available
            publication_date = extracted.get("date", "")
            
            yield DocumentItem(
                url=response.url,
                title=title,
                content=content,
                content_type="html",
                category="Kenyan Law",
                source_name="Kenya Law",
                author=extracted.get("author", ""),
                publication_date=publication_date,
                summary=extracted.get("description", ""),
                raw_html=response.text,
                status_code=response.status,
            )
        except Exception as e:
            self.logger.error(f"Error parsing document {response.url}: {e}")
