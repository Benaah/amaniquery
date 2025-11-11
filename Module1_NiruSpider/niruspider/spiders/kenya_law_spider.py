"""
Kenya Law Spider - Crawls kenyalaw.org for Constitution and Acts
"""
import scrapy
from datetime import datetime
from ..items import DocumentItem


class KenyaLawSpider(scrapy.Spider):
    name = "kenya_law"
    allowed_domains = ["kenyalaw.org"]
    
    # Start URLs
    start_urls = [
        "http://kenyalaw.org/kl/index.php?id=398",  # Constitution
        "http://kenyalaw.org/kl/index.php?id=569",  # Acts
    ]
    
    custom_settings = {
        "DOWNLOAD_DELAY": 3.0,  # Be extra polite with government sites
    }
    
    def parse(self, response):
        """Parse index pages to find document links"""
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
    
    def parse_document(self, response):
        """Parse individual legal document"""
        self.logger.info(f"Parsing document: {response.url}")
        
        # Extract title
        title = response.css('h1::text, h2::text, title::text').get()
        if title:
            title = title.strip()
        else:
            title = "Untitled Document"
        
        # Extract main content
        # Kenya Law typically puts content in specific divs
        content_selectors = [
            '#content-core',
            '.document-content',
            'div.content',
            'article',
            'main',
        ]
        
        content = None
        for selector in content_selectors:
            content = response.css(f'{selector}::text').getall()
            if content:
                break
        
        # Fallback: get all paragraph text
        if not content:
            content = response.css('p::text').getall()
        
        # Join content
        full_content = '\n'.join([t.strip() for t in content if t.strip()])
        
        # Check if this is a PDF link
        if response.url.endswith('.pdf'):
            yield DocumentItem(
                url=response.url,
                title=title,
                content="",
                content_type="pdf",
                category="Kenyan Law",
                source_name="Kenya Law",
                publication_date=None,
                raw_html=response.text,
            )
        else:
            yield DocumentItem(
                url=response.url,
                title=title,
                content=full_content,
                content_type="html",
                category="Kenyan Law",
                source_name="Kenya Law",
                publication_date=None,
                raw_html=response.text,
                status_code=response.status,
            )
