"""
Parliament Spider - Crawls parliament.go.ke for Hansards and Bills
Enhanced with robust extraction and error handling
"""
import scrapy
from datetime import datetime
import re
from ..items import DocumentItem
from ..extractors import ArticleExtractor


class ParliamentSpider(scrapy.Spider):
    name = "parliament"
    allowed_domains = ["parliament.go.ke"]
    
    def __init__(self, *args, **kwargs):
        super(ParliamentSpider, self).__init__(*args, **kwargs)
        self.article_extractor = ArticleExtractor()
        self.max_pages = 50  # Limit pages to crawl
    
    start_urls = [
        "https://www.parliament.go.ke/the-national-assembly/house-business/hansard",
        "https://www.parliament.go.ke/the-national-assembly/house-business/bills",
        "https://www.parliament.go.ke/documents-publications",
    ]
    
    custom_settings = {
        "DOWNLOAD_DELAY": 2.5,
        "RETRY_TIMES": 3,
        "RETRY_HTTP_CODES": [500, 502, 503, 504, 408, 429],
        "DOWNLOAD_TIMEOUT": 60,
    }
    
    def parse(self, response):
        """Parse listing pages"""
        self.logger.info(f"Parsing: {response.url}")
        
        # Look for PDF links (most parliamentary documents are PDFs)
        pdf_links = response.css('a[href$=".pdf"]::attr(href)').getall()
        
        for link in pdf_links:
            # Extract title from link text or nearby text
            link_element = response.css(f'a[href="{link}"]')
            title = link_element.css('::text').get() or link_element.xpath('./text()').get()
            
            if not title:
                # Try to get title from parent element
                title = link_element.xpath('..//text()').get()
            
            if not title:
                # Use filename as title
                title = link.split('/')[-1].replace('.pdf', '').replace('-', ' ').title()
            
            yield response.follow(
                link,
                callback=self.parse_pdf,
                meta={'title': title.strip()}
            )
        
        # Look for article/document links
        doc_links = response.css('article a::attr(href), .document a::attr(href)').getall()
        for link in doc_links:
            if not link.endswith('.pdf'):
                yield response.follow(link, callback=self.parse_document)
        
        # Pagination
        next_page = response.css('a.next::attr(href), a[rel="next"]::attr(href)').get()
        if next_page:
            yield response.follow(next_page, callback=self.parse)
    
    def parse_pdf(self, response):
        """Handle PDF documents"""
        title = response.meta.get('title', 'Untitled Parliamentary Document')
        
        # Try to extract date from URL or title
        date_match = re.search(r'(\d{4}[-/]\d{2}[-/]\d{2})', response.url)
        pub_date = date_match.group(1) if date_match else None
        
        yield DocumentItem(
            url=response.url,
            title=title,
            content="",
            content_type="pdf",
            category="Parliament",
            source_name="Parliament of Kenya",
            publication_date=pub_date,
            raw_html="",
        )
    
    def parse_document(self, response):
        """Parse HTML documents using enhanced extractor"""
        try:
            # Use enhanced article extractor
            extracted = self.article_extractor.extract(response.text, url=response.url)
            
            # Use extracted content, fallback to basic extraction
            content = extracted.get("text", "")
            if not content or len(content) < 50:
                # Fallback
                content_parts = response.css('article::text, .content::text, main::text').getall()
                if not content_parts:
                    content_parts = response.css('p::text').getall()
                content = '\n'.join([t.strip() for t in content_parts if t.strip()])
            
            # Use extracted title
            title = extracted.get("title", "") or (
                response.css('h1::text').get() or
                response.css('title::text').get() or
                "Untitled Document"
            )
            title = title.strip()
            
            # Use extracted date or try to extract from page
            pub_date = extracted.get("date", "")
            if not pub_date:
                date_text = response.css('.date::text, time::text, .published::text').get()
                if date_text:
                    date_match = re.search(r'(\d{4}[-/]\d{2}[-/]\d{2})', date_text)
                    pub_date = date_match.group(1) if date_match else None
            
            yield DocumentItem(
                url=response.url,
                title=title,
                content=content,
                content_type="html",
                category="Parliament",
                source_name="Parliament of Kenya",
                author=extracted.get("author", ""),
                publication_date=pub_date,
                summary=extracted.get("description", ""),
                raw_html=response.text,
                status_code=response.status,
            )
        except Exception as e:
            self.logger.error(f"Error parsing document {response.url}: {e}")
