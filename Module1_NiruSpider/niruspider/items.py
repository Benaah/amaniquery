"""
NiruSpider - Scrapy-based data items
"""
import scrapy


class DocumentItem(scrapy.Item):
    """Base item for all crawled documents"""
    
    # Core fields
    url = scrapy.Field()
    title = scrapy.Field()
    content = scrapy.Field()
    content_type = scrapy.Field()  # html, pdf, text
    
    # Metadata
    category = scrapy.Field()  # Kenyan Law, Parliament, Kenyan News, Global Trend
    source_name = scrapy.Field()
    author = scrapy.Field()
    publication_date = scrapy.Field()
    crawl_date = scrapy.Field()
    
    # Technical
    raw_html = scrapy.Field()
    pdf_path = scrapy.Field()
    status_code = scrapy.Field()
    
    # Additional metadata
    keywords = scrapy.Field()
    summary = scrapy.Field()
    language = scrapy.Field()


class RSSItem(scrapy.Item):
    """Item for RSS feed entries"""
    
    url = scrapy.Field()
    title = scrapy.Field()
    summary = scrapy.Field()
    published = scrapy.Field()
    author = scrapy.Field()
    category = scrapy.Field()
    source_name = scrapy.Field()
    feed_url = scrapy.Field()
    
    # To be populated after fetching full article
    full_content = scrapy.Field()
    crawl_date = scrapy.Field()
