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
    
    # Start URLs - Enhanced with sitemaps and more entry points
    start_urls = [
        "http://kenyalaw.org/kl/index.php?id=398",  # Constitution
        "http://kenyalaw.org/kl/index.php?id=569",  # Acts
        "http://kenyalaw.org/kl/index.php?id=4266",  # Court decisions
        "http://kenyalaw.org/kl/index.php?id=572",  # Gazette notices
        "http://kenyalaw.org/kl/index.php?id=1837",  # Legal opinions
        # Sitemaps for better coverage
        "http://kenyalaw.org/sitemap.xml",
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
```
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
    
    # Start URLs - Enhanced with sitemaps and more entry points
    start_urls = [
        "http://kenyalaw.org/kl/index.php?id=398",  # Constitution
        "http://kenyalaw.org/kl/index.php?id=569",  # Acts
        "http://kenyalaw.org/kl/index.php?id=4266",  # Court decisions
        "http://kenyalaw.org/kl/index.php?id=572",  # Gazette notices
        "http://kenyalaw.org/kl/index.php?id=1837",  # Legal opinions
        # Sitemaps for better coverage
        "http://kenyalaw.org/sitemap.xml",
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
        """Parse individual legal document with clause-level chunking and rich metadata"""
        try:
            self.logger.info(f"Parsing document: {response.url}")
            
            # Check if this is a PDF link
            if response.url.endswith('.pdf'):
                yield DocumentItem(
                    url=response.url,
                    title="Legal Document PDF",
                    content="",
                    content_type="pdf",
                   category="Kenyan Law",
                    source_name="Kenya Law",
                    pdf_path=response.url,
                    crawl_date=datetime.now().isoformat(),
                )
                return
            
            # Use enhanced article extractor
            extracted = self.article_extractor.extract(response.text, url=response.url)
            
            # Extract content with fallback
            content = extracted.get("text", "")
            if not content or len(content) < 50:
                content_selectors = ['#content-core', '.document-content', 'div.content', 'article', 'main']
                for selector in content_selectors:
                    content_parts = response.css(f'{selector}::text').getall()
                    if content_parts:
                        content = '\n'.join([t.strip() for t in content_parts if t.strip()])
                        break
                if not content:
                    content = '\n'.join([t.strip() for t in response.css('p::text').getall() if t.strip()])
            
            # Extract title
            title = extracted.get("title", "") or response.css('h1::text, h2::text, title::text').get()
            title = title.strip() if title else "Untitled Document"
            
            # Determine document type
            doc_type = self._determine_doc_type(title, response.url)
            
            # Extract metadata based on doc type
            if doc_type == 'constitution':
                yield from self._parse_constitution(response, title, content)
            elif doc_type in ['act', 'bill']:
                yield from self._parse_act_or_bill(response, title, content, doc_type)
            else:
                # Generic document
                import hashlib
                doc_id = hashlib.md5(response.url.encode()).hexdigest()
                
                yield DocumentItem(
                    doc_id=doc_id,
                    url=response.url,
                    title=title,
                    content=content,
                    content_type="html",
                    chunk_index=0,
                    total_chunks=1,
                    doc_type=doc_type,
                    category="Kenyan Law",
                    source_name="Kenya Law",
                    author=extracted.get("author", ""),
                    publication_date=extracted.get("date", ""),
                    crawl_date=datetime.now().isoformat(),
                    metadata_tags=["legal", doc_type],
                    raw_html=response.text,
                    status_code=response.status,
                )
        except Exception as e:
            self.logger.error(f"Error parsing document {response.url}: {e}")
    
    def _determine_doc_type(self, title: str, url: str) -> str:
        """Determine document type from title/URL"""
        title_lower = title.lower()
        url_lower = url.lower()
        
        if 'constitution' in title_lower or 'constitution' in url_lower:
            return 'constitution'
        elif 'bill' in title_lower or 'bill' in url_lower:
            return 'bill'
        elif 'act' in title_lower or 'actview' in url_lower:
            return 'act'
        elif 'judgment' in title_lower or 'case' in title_lower:
            return 'judgment'
        return 'legal_document'
    
    def _parse_constitution(self, response, title, full_text):
        """Parse Constitution and chunk by Article"""
        import re
        import hashlib
        
        # Split by Articles
        article_pattern = r'Article\s+(\d+)[.\s]+(.*?)(?=Article\s+\d+|$)'
        articles = list(re.finditer(article_pattern, full_text, re.DOTALL))
        total_chunks = len(articles) if articles else 1
        
        if not articles:
            # No articles found, yield full document
            doc_id = hashlib.md5(f"constitution_full_{response.url}".encode()).hexdigest()
            yield DocumentItem(
                doc_id=doc_id,
                url=response.url,
                title=title,
                content=full_text,
                content_type="html",
                chunk_index=0,
                total_chunks=1,
                doc_type='constitution',
                category="Kenyan Law",
                source_name="Kenya Law",
                publication_date='2010-08-27',
                date_enacted='2010-08-27',
                crawl_date=datetime.now().isoformat(),
                metadata_tags=['constitution', 'foundational'],
                raw_html=response.text,
            )
            return
        
        # Yield each article as separate chunk
        for idx, article_match in enumerate(articles):
            article_num = int(article_match.group(1))
            article_text = article_match.group(2).strip()
            
            # Extract article title (first line)
            lines = article_text.split('\n')
            article_title = lines[0].strip() if lines else ''
            article_content = '\n'.join(lines[1:]).strip()
            
            doc_id = hashlib.md5(f"constitution_article_{article_num}".encode()).hexdigest()
            
            yield DocumentItem(
                doc_id=doc_id,
                url=response.url,
                title=f"Constitution of Kenya, 2010 - Article {article_num}",
                content=f"Article {article_num} - {article_title}\n\n{article_content}",
                content_type="html",
                chunk_index=idx,
                total_chunks=total_chunks,
                doc_type='constitution',
                category="Kenyan Law",
                source_name="Kenya Law",
                publication_date='2010-08-27',
                date_enacted='2010-08-27',
                crawl_date=datetime.now().isoformat(),
                article_number=article_num,
                clause_text=article_content,
                metadata_tags=['constitution', 'article'],
                raw_html=response.text,
            )
    
    def _parse_act_or_bill(self, response, title, full_text, doc_type):
        """Parse Acts/Bills and chunk by Section"""
        import re
        import hashlib
        
        # Extract Act number and year
        act_match = re.search(r'Act\s+No[.\s]+(\d+)\s+of\s+(\d{4})', title)
        act_number = act_match.group(0) if act_match else None
        year = act_match.group(2) if act_match else None
        
        # Extract bill stage (for bills)
        bill_stage = self._extract_bill_stage(full_text) if doc_type == 'bill' else None
        
        # Extract dates
        date_passed = self._extract_date_passed(full_text)
        date_enacted = date_passed if doc_type == 'act' else None
        
        # Split by Sections
        section_pattern = r'(?:Section|SECTION)\s+(\d+(?:[A-Z]|\(\w+\))?)[.\s]+(.*?)(?=(?:Section|SECTION)\s+\d+|$)'
        sections = list(re.finditer(section_pattern, full_text, re.DOTALL | re.IGNORECASE))
        total_chunks = len(sections) if sections else 1
        
        if not sections:
            # No sections found, yield full document
            doc_id = hashlib.md5(f"{title}_{response.url}".encode()).hexdigest()
            yield DocumentItem(
                doc_id=doc_id,
                url=response.url,
                title=title,
                content=full_text,
                content_type="html",
                chunk_index=0,
                total_chunks=1,
                doc_type=doc_type,
                category="Kenyan Law",
                source_name="Kenya Law",
                publication_date=year,
                date_enacted=date_enacted,
                date_passed=date_passed,
                crawl_date=datetime.now().isoformat(),
                act_number=act_number,
                bill_stage=bill_stage,
                metadata_tags=[doc_type, 'legislation'],
                raw_html=response.text,
            )
            return
        
        # Yield each section as separate chunk
        for idx, section_match in enumerate(sections):
            section_num = section_match.group(1)
            section_text = section_match.group(2).strip()
            
            doc_id = hashlib.md5(f"{title}_section_{section_num}".encode()).hexdigest()
            
            yield DocumentItem(
                doc_id=doc_id,
                url=response.url,
                title=f"{title} - Section {section_num}",
                content=f"Section {section_num}\n\n{section_text}",
                content_type="html",
                chunk_index=idx,
                total_chunks=total_chunks,
                doc_type=doc_type,
                category="Kenyan Law",
                source_name="Kenya Law",
                publication_date=year,
                date_enacted=date_enacted,
                date_passed=date_passed,
                crawl_date=datetime.now().isoformat(),
                act_number=act_number,
                section_number=section_num,
                clause_text=section_text,
                bill_stage=bill_stage,
                metadata_tags=[doc_type, 'section'],
                raw_html=response.text,
            )
    
    def _extract_bill_stage(self, text: str) -> str:
        """Extract bill stage from document text"""
        import re
        stages = {
            'first reading': 'Introduced',
            'second reading': 'Committee',
            'third reading': 'Third Reading',
            'presidential assent': 'Assented',
            'assented': 'Assented'
        }
        
        text_lower = text.lower()
        for keyword, stage in stages.items():
            if keyword in text_lower:
                return stage
        return 'Introduced'  # Default
    
    def _extract_date_passed(self, text: str) -> str:
        """Extract date when bill was passed"""
        import re
        from dateutil import parser
        
        date_patterns = [
            r'passed\s+on\s+(\d{1,2}\w{0,2}\s+\w+,?\s+\d{4})',
            r'enacted\s+on\s+(\d{1,2}\w{0,2}\s+\w+,?\s+\d{4})',
            r'(\d{4}-\d{2}-\d{2})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    dt = parser.parse(match.group(1))
                    return dt.date().isoformat()
                except:
                    pass
        return None
```
