"""
NiruSpider v2.0 - Kenyan Civic Data Crawler
============================================

Comprehensive Scrapy-based crawler for:
- Kenya Law Reports (kenyalaw.org)
- Parliament Hansard (parliament.go.ke)
- County Assembly websites

Features:
- Clause-level chunking for legal documents
- Rich metadata extraction (bill_stage, MP info, dates, etc.)
- LLM-generated plain English summaries
- Vector DB ready output

Usage:
    scrapy crawl kenya_law -o output.jsonl
    scrapy crawl parliament_hansard -o hansard.jsonl
    scrapy crawl county_assembly -a county=nairobi -o nairobi.jsonl
"""

import scrapy
from scrapy.http import Response
from typing import Dict, List, Optional, Iterator
from datetime import datetime
import re
from dataclasses import dataclass, asdict
import hashlib
import logging


# ============================================================================
# DATA MODELS
# ============================================================================

@dataclass
class CivicDocument:
    """Structured document with all required metadata"""
    
    # Core content
    doc_id: str                          # Unique hash
    text: str                            # Full text or chunk
    chunk_index: int                     # Position in document (0 for full doc)
    total_chunks: int                    # Total chunks in document
    
    # Document metadata
    doc_type: str                        # "act", "bill", "hansard", "judgment", "county_law"
    title: str                           # Document title
    source_url: str                      # Original URL
    date_published: str                  # ISO format: 2024-06-25
    date_scraped: str                    # ISO format
    
    # Legal metadata
    bill_stage: Optional[str] = None     # "Introduced", "Committee", "Third Reading", "Assented"
    act_number: Optional[str] = None     # e.g., "Act No. 7 of 2023"
    section_number: Optional[str] = None # e.g., "3(b)"
    article_number: Optional[int] = None # e.g., 201
    clause_text: Optional[str] = None    # Verbatim statutory text
    date_enacted: Optional[str] = None   # When became law
    date_passed: Optional[str] = None    # When Parliament passed
    
    # Parliamentary metadata
    speaking_mp: Optional[str] = None    # MP name
    constituency: Optional[str] = None   # MP constituency
    committee: Optional[str] = None      # Parliamentary committee
    session_date: Optional[str] = None   # Session date
    hansard_page: Optional[int] = None   # Page number
    
    # County metadata
    county_name: Optional[str] = None    # e.g., "Nairobi"
    ward: Optional[str] = None           # Ward name
    
    # Data/statistics
    has_tables: bool = False             # Contains data tables
    tables: Optional[List[Dict]] = None  # Extracted tables
    statistics: Optional[Dict] = None    # Key statistics
    voting_record: Optional[Dict] = None # Vote tallies
    
    # Enhancement fields
    summary_plain_english: Optional[str] = None  # LLM-generated summary
    metadata_tags: List[str] = None      # ["explainer", "summary", etc.]
    
    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return {k: v for k, v in asdict(self).items() if v is not None}


# ============================================================================
# KENYA LAW REPORTS SPIDER
# ============================================================================

class KenyaLawSpider(scrapy.Spider):
    """
    Crawls Kenya Law Reports (kenyalaw.org) for:
    - Constitution of Kenya 2010
    - Acts of Parliament
    - Bills
    - Legal Notices
    - Court Judgments
    """
    
    name = 'kenya_law'
    allowed_domains = ['kenyalaw.org']
    start_urls = [
        'http://kenyalaw.org/kl/index.php?id=398',  # Constitution
        'http://kenyalaw.org/kl/index.php?id=399',  # Acts
        'http://kenyalaw.org/kl/index.php?id=400',  # Bills
    ]
    
    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'CONCURRENT_REQUESTS': 2,
        'DOWNLOAD_DELAY': 2,
        'USER_AGENT': 'AmaniQuery/2.0 (Educational Research Bot; contact@amaniquery.org)'
    }
    
    def parse(self, response: Response) -> Iterator[scrapy.Request]:
        """Parse index pages and follow document links"""
        
        # Extract all document links
        doc_links = response.css('a[href*="fileadmin"]::attr(href)').getall()
        
        for link in doc_links:
            full_url = response.urljoin(link)
            
            # Determine document type from URL patterns
            doc_type = self._determine_doc_type(full_url)
            
            yield scrapy.Request(
                url=full_url,
                callback=self.parse_document,
                meta={'doc_type': doc_type, 'source_url': full_url}
            )
    
    def parse_document(self, response: Response) -> Iterator[CivicDocument]:
        """Parse individual legal document and extract metadata"""
        
        doc_type = response.meta['doc_type']
        source_url = response.meta['source_url']
        
        # Extract title
        title = self._extract_title(response)
        
        # Extract full text
        full_text = self._extract_text(response)
        
        # Extract metadata based on doc type
        if doc_type == 'constitution':
            yield from self._parse_constitution(response, title, full_text, source_url)
        
        elif doc_type in ['act', 'bill']:
            yield from self._parse_act_or_bill(response, title, full_text, source_url, doc_type)
        
        elif doc_type == 'judgment':
            yield from self._parse_judgment(response, title, full_text, source_url)
    
    def _parse_constitution(
        self, 
        response: Response, 
        title: str, 
        full_text: str, 
        source_url: str
    ) -> Iterator[CivicDocument]:
        """Parse Constitution and chunk by Article"""
        
        # Split by Articles
        article_pattern = r'Article\s+(\d+)[.\s]+(.*?)(?=Article\s+\d+|$)'
        articles = re.finditer(article_pattern, full_text, re.DOTALL)
        
        chunks = list(articles)
        total_chunks = len(chunks)
        
        for idx, article_match in enumerate(chunks):
            article_num = int(article_match.group(1))
            article_text = article_match.group(2).strip()
            
            # Extract article title (first line)
            lines = article_text.split('\n')
            article_title = lines[0].strip() if lines else ''
            article_content = '\n'.join(lines[1:]).strip()
            
            doc_id = hashlib.md5(
                f"constitution_article_{article_num}".encode()
            ).hexdigest()
            
            yield CivicDocument(
                doc_id=doc_id,
                text=f"Article {article_num} - {article_title}\n\n{article_content}",
                chunk_index=idx,
                total_chunks=total_chunks,
                doc_type='constitution',
                title=f"Constitution of Kenya, 2010 - Article {article_num}",
                source_url=source_url,
                date_published='2010-08-27',
                date_scraped=datetime.now().isoformat(),
                article_number=article_num,
                clause_text=article_content,
                date_enacted='2010-08-27',
                metadata_tags=['constitution', 'foundational'],
                summary_plain_english=None  # Will be filled by LLM pipeline
            )
    
    def _parse_act_or_bill(
        self,
        response: Response,
        title: str,
        full_text: str,
        source_url: str,
        doc_type: str
    ) -> Iterator[CivicDocument]:
        """Parse Acts/Bills and chunk by Section"""
        
        # Extract Act number and year
        act_match = re.search(r'Act\s+No[.\s]+(\d+)\s+of\s+(\d{4})', title)
        act_number = act_match.group(0) if act_match else None
        year = act_match.group(2) if act_match else None
        
        # Extract bill stage (for bills)
        bill_stage = None
        if doc_type == 'bill':
            bill_stage = self._extract_bill_stage(response, full_text)
        
        # Extract date passed/enacted
        date_passed = self._extract_date_passed(response, full_text)
        date_enacted = date_passed if doc_type == 'act' else None
        
        # Split by Sections
        section_pattern = r'(?:Section|SECTION)\s+(\d+(?:[A-Z]|\(\w+\))?)[.\s]+(.*?)(?=(?:Section|SECTION)\s+\d+|$)'
        sections = re.finditer(section_pattern, full_text, re.DOTALL | re.IGNORECASE)
        
        chunks = list(sections)
        total_chunks = len(chunks)
        
        for idx, section_match in enumerate(chunks):
            section_num = section_match.group(1)
            section_text = section_match.group(2).strip()
            
            doc_id = hashlib.md5(
                f"{title}_section_{section_num}".encode()
            ).hexdigest()
            
            yield CivicDocument(
                doc_id=doc_id,
                text=f"Section {section_num}\n\n{section_text}",
                chunk_index=idx,
                total_chunks=total_chunks,
                doc_type=doc_type,
                title=f"{title} - Section {section_num}",
                source_url=source_url,
                date_published=year if year else None,
                date_scraped=datetime.now().isoformat(),
                act_number=act_number,
                section_number=section_num,
                clause_text=section_text,
                date_enacted=date_enacted,
                date_passed=date_passed,
                bill_stage=bill_stage,
                metadata_tags=[doc_type, 'legislation'],
                summary_plain_english=None
            )
    
    def _parse_judgment(
        self,
        response: Response,
        title: str,
        full_text: str,
        source_url: str
    ) -> Iterator[CivicDocument]:
        """Parse court judgments"""
        
        # Extract case citation
        citation_match = re.search(r'\[(\d{4})\]\s+\w+\s+\d+', title)
        citation = citation_match.group(0) if citation_match else None
        
        # Extract date
        date_match = re.search(r'(\d{1,2})(?:st|nd|rd|th)?\s+(\w+),?\s+(\d{4})', full_text)
        date_published = self._parse_date(date_match.group(0)) if date_match else None
        
        doc_id = hashlib.md5(title.encode()).hexdigest()
        
        yield CivicDocument(
            doc_id=doc_id,
            text=full_text,
            chunk_index=0,
            total_chunks=1,
            doc_type='judgment',
            title=title,
            source_url=source_url,
            date_published=date_published,
            date_scraped=datetime.now().isoformat(),
            act_number=citation,
            metadata_tags=['judgment', 'case_law'],
            summary_plain_english=None
        )
    
    # Helper methods
    
    def _determine_doc_type(self, url: str) -> str:
        """Determine document type from URL"""
        if 'constitution' in url.lower():
            return 'constitution'
        elif 'acts' in url.lower():
            return 'act'
        elif 'bills'in url.lower():
            return 'bill'
        elif 'judgment' in url.lower() or 'cases' in url.lower():
            return 'judgment'
        return 'unknown'
    
    def _extract_title(self, response: Response) -> str:
        """Extract document title"""
        # Try multiple selectors
        title = (
            response.css('h1::text').get() or
            response.css('title::text').get() or
            response.css('.document-title::text').get() or
            'Untitled Document'
        )
        return title.strip()
    
    def _extract_text(self, response: Response) -> str:
        """Extract main text content"""
        # Prefer article/main content, fallback to body
        text = (
            ' '.join(response.css('article ::text').getall()) or
            ' '.join(response.css('main ::text').getall()) or
            ' '.join(response.css('body ::text').getall())
        )
        
        # Clean whitespace
        text = re.sub(r'\s+', ' ', text).strip()
        return text
    
    def _extract_bill_stage(self, response: Response, text: str) -> Optional[str]:
        """Extract bill stage from document"""
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
    
    def _extract_date_passed(self, response: Response, text: str) -> Optional[str]:
        """Extract date when bill was passed"""
        date_patterns = [
            r'passed\s+on\s+(\d{1,2}\w{0,2}\s+\w+,?\s+\d{4})',
            r'enacted\s+on\s+(\d{1,2}\w{0,2}\s+\w+,?\s+\d{4})',
            r'(\d{4}-\d{2}-\d{2})'
        ]
        
        for pattern in date_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                return self._parse_date(match.group(1))
        
        return None
    
    def _parse_date(self, date_str: str) -> Optional[str]:
        """Parse various date formats to ISO"""
        from dateutil import parser
        try:
            dt = parser.parse(date_str)
            return dt.date().isoformat()
        except:
            return None


# ============================================================================
# PARLIAMENT HANSARD SPIDER
# ============================================================================

class ParliamentHansardSpider(scrapy.Spider):
    """
    Crawls Parliament of Kenya Hansard records
    Extracts: MP speeches, voting records, committee reports
    """
    
    name = 'parliament_hansard'
    allowed_domains = ['parliament.go.ke']
    start_urls = [
        'http://www.parliament.go.ke/the-national-assembly/house-business/hansard'
    ]
    
    custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'CONCURRENT_REQUESTS': 1,
        'DOWNLOAD_DELAY': 3,
        'USER_AGENT': 'AmaniQuery/2.0 (Educational Research Bot; contact@amaniquery.org)'
    }
    
    def parse(self, response: Response) -> Iterator[scrapy.Request]:
        """Parse Hansard index and follow session links"""
        
        # Find all Hansard session links
        session_links = response.css('a[href*="hansard"]::attr(href)').getall()
        
        for link in session_links:
            full_url = response.urljoin(link)
            yield scrapy.Request(
                url=full_url,
                callback=self.parse_hansard_session
            )
    
    def parse_hansard_session(self, response: Response) -> Iterator[CivicDocument]:
        """Parse individual Hansard session"""
        
        # Extract session date from title or URL
        session_date = self._extract_session_date(response)
        
        # Extract title (e.g., "Finance Bill 2024 Second Reading")
        title = response.css('h1::text').get() or 'Hansard Session'
        
        # Extract all speeches/contributions
        speeches = self._extract_speeches(response)
        
        total_chunks = len(speeches)
        
        for idx, speech in enumerate(speeches):
            doc_id = hashlib.md5(
                f"{session_date}_{speech['mp']}_{idx}".encode()
            ).hexdigest()
            
            yield CivicDocument(
                doc_id=doc_id,
                text=speech['text'],
                chunk_index=idx,
                total_chunks=total_chunks,
                doc_type='hansard',
                title=f"Hansard - {title} - {speech['mp']}",
                source_url=response.url,
                date_published=session_date,
                date_scraped=datetime.now().isoformat(),
                speaking_mp=speech['mp'],
                constituency=speech.get('constituency'),
                committee=self._extract_committee(title),
                session_date=session_date,
                hansard_page=speech.get('page'),
                voting_record=speech.get('voting_record'),
                metadata_tags=['hansard', 'parliamentary_debate'],
                summary_plain_english=None
            )
    
    def _extract_session_date(self, response: Response) -> str:
        """Extract session date"""
        # Try to find date in title or meta
        date_str = (
            response.css('meta[name="date"]::attr(content)').get() or
            response.css('.session-date::text').get()
        )
        
        if date_str:
            return self._parse_date(date_str)
        
        # Fallback: extract from URL
        url_date_match = re.search(r'(\d{4})-(\d{2})-(\d{2})', response.url)
        if url_date_match:
            return f"{url_date_match.group(1)}-{url_date_match.group(2)}-{url_date_match.group(3)}"
        
        return datetime.now().date().isoformat()
    
    def _extract_speeches(self, response: Response) -> List[Dict]:
        """Extract individual MP speeches from Hansard"""
        speeches = []
        
        # Pattern: "Hon. [Name] ([Constituency]):"
        speech_blocks = response.css('.speech, .contribution, p')
        
        for block in speech_blocks:
            text = block.css('::text').get()
            if not text:
                continue
            
            # Check if starts with MP name
            mp_match = re.match(
                r'(?:Hon\.|Mr\.|Ms\.|Dr\.)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)+)\s*\(([^)]+)\):',
                text
            )
            
            if mp_match:
                mp_name = mp_match.group(1)
                constituency = mp_match.group(2)
                speech_text = text[mp_match.end():].strip()
                
                speeches.append({
                    'mp': mp_name,
                    'constituency': constituency,
                    'text': speech_text,
                    'page': None  # Extract if available
                })
        
        return speeches
    
    def _extract_committee(self, title: str) -> Optional[str]:
        """Extract committee name from title"""
        committees = [
            'Finance Committee',
            'Budget Committee',
            'Public Accounts Committee',
            'Health Committee',
            'Education Committee'
        ]
        
        for committee in committees:
            if committee.lower() in title.lower():
                return committee
        
        return None
    
    def _parse_date(self, date_str: str) -> str:
        """Parse date to ISO format"""
        from dateutil import parser
        try:
            dt = parser.parse(date_str)
            return dt.date().isoformat()
        except:
            return datetime.now().date().isoformat()


# ============================================================================
# COUNTY ASSEMBLY SPIDER
# ============================================================================

class CountyAssemblySpider(scrapy.Spider):
    """
    Crawls County Assembly websites
    Supports: Nairobi, Mombasa, Kisumu, etc.
    """
    
    name = 'county_assembly'
    
   custom_settings = {
        'ROBOTSTXT_OBEY': True,
        'CONCURRENT_REQUESTS': 2,
        'DOWNLOAD_DELAY': 2
    }
    
    # County-specific URLs
    COUNTY_URLS = {
        'nairobi': 'https://www.nairobiassembly.go.ke',
        'mombasa': 'https://www.mombasacountyassembly.go.ke',
        'kisumu': 'https://www.kisumucounty.go.ke/assembly'
    }
    
    def __init__(self, county='nairobi', *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.county = county.lower()
        self.start_urls = [self.COUNTY_URLS.get(self.county, self.COUNTY_URLS['nairobi'])]
        self.allowed_domains = [self.start_urls[0].replace('https://', '').replace('http://', '')]
    
    def parse(self, response: Response) -> Iterator[scrapy.Request]:
        """Parse county assembly index"""
        
        # Find legislation/bills links
        doc_links = response.css('a[href*="bill"], a[href*="act"], a[href*="resolution"]::attr(href)').getall()
        
        for link in doc_links:
            full_url = response.urljoin(link)
            yield scrapy.Request(
                url=full_url,
                callback=self.parse_county_document,
                meta={'county': self.county}
            )
    
    def parse_county_document(self, response: Response) -> Iterator[CivicDocument]:
        """Parse county legislation"""
        
        title = self._extract_title(response)
        full_text = self._extract_text(response)
        county = response.meta['county']
        
        doc_id = hashlib.md5(f"{county}_{title}".encode()).hexdigest()
        
        yield CivicDocument(
            doc_id=doc_id,
            text=full_text,
            chunk_index=0,
            total_chunks=1,
            doc_type='county_law',
            title=title,
            source_url=response.url,
            date_published=self._extract_date(response),
            date_scraped=datetime.now().isoformat(),
            county_name=county.title(),
            metadata_tags=['county', 'devolution'],
            summary_plain_english=None
        )
    
    def _extract_title(self, response: Response) -> str:
        return (response.css('h1::text').get() or 'County Document').strip()
    
    def _extract_text(self, response: Response) -> str:
        text = ' '.join(response.css('article ::text, main ::text').getall())
        return re.sub(r'\s+', ' ', text).strip()
    
    def _extract_date(self, response: Response) -> Optional[str]:
        date_str = response.css('meta[name="date"]::attr(content)').get()
        if date_str:
            from dateutil import parser
            try:
                return parser.parse(date_str).date().isoformat()
            except:
                pass
        return None


# ============================================================================
# LLM SUMMARY PIPELINE
# ============================================================================

class LLMSummaryPipeline:
    """
    Scrapy pipeline that adds plain English summaries using LLM
    """
    
    def __init__(self):
        self.llm_client = None  # Initialize your LLM client here
    
    def process_item(self, item: CivicDocument, spider):
        """Add LLM-generated summary to each document"""
        
        if item.summary_plain_english is None and len(item.text) > 50:
            # Generate summary
            summary_prompt = f"""
Summarize this Kenyan legal/parliamentary text in plain English for ordinary citizens:

{item.text[:1000]}...

Provide a 2-3 sentence summary focusing on practical impact.
"""
            
            try:
                # Call your LLM (Gemini, GPT, etc.)
                summary = self._call_llm(summary_prompt)
                item.summary_plain_english = summary
            except Exception as e:
                logging.error(f"LLM summary failed: {e}")
                item.summary_plain_english = None
        
        return item
    
    def _call_llm(self, prompt: str) -> str:
        """Call LLM API - implement with your provider"""
        # Example with Gemini:
        # response = gemini_client.generate_content(prompt)
        # return response.text
        
        # Placeholder
        return "Summary generation not configured"


# ============================================================================
# USAGE EXAMPLES
# ============================================================================

if __name__ == "__main__":
    print("""
NiruSpider v2.0 Usage Examples:
================================

1. Crawl Kenya Law (Acts, Bills, Constitution):
   scrapy crawl kenya_law -o kenya_law_output.jsonl

2. Crawl Parliament Hansard:
   scrapy crawl parliament_hansard -o hansard_output.jsonl

3. Crawl Nairobi County Assembly:
   scrapy crawl county_assembly -a county=nairobi -o nairobi_county.jsonl

4. Crawl Mombasa County Assembly:
   scrapy crawl county_assembly -a county=mombasa-o mombasa_county.jsonl

5. Enable LLM summaries in settings.py:
   ITEM_PIPELINES = {
       'niruspider.pipelines.LLMSummaryPipeline': 300,
   }

Output Format:
Each JSONL line contains a CivicDocument with all metadata fields populated.
Ready for ingestion into Weaviate/Qdrant with full filtering capabilities.
""")
