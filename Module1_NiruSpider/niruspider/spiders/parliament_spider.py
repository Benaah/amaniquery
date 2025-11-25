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
        "https://www.parliament.go.ke/the-national-assembly/business/budget-documents",  # Updated for 2025-2026
        "https://www.parliament.go.ke/the-national-assembly/committees",  # Committee reports
        "https://www.parliament.go.ke/the-senate/house-business/bills",  # Senate bills
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
        
        # Special handling for budget documents page
        if "budget-documents" in response.url:
            yield from self.parse_budget_documents(response)
            return
        
        # Look for PDF links (most parliamentary documents are PDFs)
        pdf_links = response.css('a[href$=".pdf"]::attr(href)').getall()
        
        # Also look for links that might point to PDFs (download links, file links)
        pdf_links.extend(response.css('a[href*=".pdf"]::attr(href)').getall())
        pdf_links.extend(response.css('a[href*="/sites/default/files/"]::attr(href)').getall())
        
        # Remove duplicates while preserving order
        seen = set()
        unique_pdf_links = []
        for link in pdf_links:
            if link and link not in seen:
                seen.add(link)
                unique_pdf_links.append(link)
        
        for link in unique_pdf_links:
            # Make absolute URL if relative
            if link.startswith('/'):
                link = response.urljoin(link)
            elif not link.startswith('http'):
                link = response.urljoin(link)
            
            # Extract title from link text or nearby text
            try:
                link_element = response.css(f'a[href*="{link.split("/")[-1]}"]').get()
                if not link_element:
                    # Try exact match
                    link_element = response.css(f'a[href="{link}"]').get()
            except Exception:
                link_element = None
            
            title = None
            if link_element:
                # Extract text from the link element
                from scrapy.selector import Selector
                sel = Selector(text=link_element)
                title = sel.css('::text').get()
                
                if not title:
                    # Try to get title from nearby text
                    title = response.css(f'a[href*="{link.split("/")[-1]}"]::text').get()
            
            if not title:
                # Use filename as title
                filename = link.split('/')[-1]
                if filename.endswith('.pdf'):
                    filename = filename.replace('.pdf', '')
                title = filename.replace('-', ' ').replace('_', ' ').title()
            
            yield response.follow(
                link,
                callback=self.parse_pdf,
                meta={'title': title.strip() if title else 'Parliamentary Document'}
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
    
    def parse_budget_documents(self, response):
        """Special parser for budget documents page"""
        self.logger.info(f"Parsing budget documents page: {response.url}")
        
        # Look for all PDF links on the page
        pdf_links = response.css('a[href$=".pdf"]::attr(href)').getall()
        pdf_links.extend(response.css('a[href*=".pdf"]::attr(href)').getall())
        
        # Also look for file download links
        file_links = response.css('a[href*="/sites/default/files/"]::attr(href)').getall()
        pdf_links.extend(file_links)
        
        # Remove duplicates
        seen = set()
        unique_links = []
        for link in pdf_links:
            if link and link not in seen:
                seen.add(link)
                unique_links.append(link)
        
        self.logger.info(f"Found {len(unique_links)} PDF links on budget documents page")
        
        for link in unique_links:
            # Make absolute URL
            if link.startswith('/'):
                link = response.urljoin(link)
            elif not link.startswith('http'):
                link = response.urljoin(link)
            
            # Extract title - try multiple strategies
            title = None
            
            # Strategy 1: Link text
            link_selector = f'a[href*="{link.split("/")[-1]}"]'
            link_element = response.css(link_selector).first()
            
            if link_element:
                title = link_element.css('::text').get()
                if not title:
                    # Try parent or preceding text
                    title = link_element.xpath('../text()').get() or link_element.xpath('preceding-sibling::text()[1]').get()
            
            # Strategy 2: Look for text near the link (within same container)
            if not title and link_element:
                parent = link_element.xpath('..')
                if parent:
                    title = parent.css('::text').get()
            
            # Strategy 3: Extract from filename
            if not title:
                filename = link.split('/')[-1]
                if filename.endswith('.pdf'):
                    filename = filename.replace('.pdf', '')
                # Clean up filename to create readable title
                title = filename.replace('-', ' ').replace('_', ' ').replace('%20', ' ')
                # Capitalize properly
                title = ' '.join(word.capitalize() for word in title.split())
            
            # Add budget document context to title
            if title and 'budget' not in title.lower() and 'finance' not in title.lower():
                if '2025' in link or '2026' in link:
                    title = f"{title} (Budget 2025-2026)"
            
            yield response.follow(
                link,
                callback=self.parse_pdf,
                meta={
                    'title': title.strip() if title else 'Budget Document',
                    'is_budget_doc': True
                }
            )
    
    def parse_pdf(self, response):
        """Handle PDF documents"""
        title = response.meta.get('title', 'Untitled Parliamentary Document')
        is_budget_doc = response.meta.get('is_budget_doc', False)
        
        # Try to extract date from URL or title
        date_match = re.search(r'(\d{4}[-/]\d{2}[-/]\d{2})', response.url)
        pub_date = date_match.group(1) if date_match else None
        
        # Extract year from URL or title for budget documents
        if is_budget_doc and not pub_date:
            year_match = re.search(r'(202[4-9])', response.url + ' ' + title)
            if year_match:
                pub_date = year_match.group(1) + "-01-01"  # Default to start of year
        
        # Enhance category for budget documents
        category = "Parliament"
        if is_budget_doc or 'budget' in title.lower() or 'finance' in title.lower():
            category = "Parliament - Budget Documents"
        
        yield DocumentItem(
            url=response.url,
            title=title,
            content="",
            content_type="pdf",
            category=category,
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
