# Kenya Law New Spider Documentation

## Overview

The **Kenya Law New Spider** (`kenya_law_new_spider`) is a comprehensive web scraper designed to crawl the new Kenya Law website at **https://new.kenyalaw.org**. This spider replaces the old Kenya Law spider and provides complete coverage of all legal resources available on the new platform.

## Coverage

### 1. Constitution
- **Constitution of Kenya 2010** - Complete text with article-level chunking
- URL: `https://new.kenyalaw.org/akn/ke/act/2010/constitution`

### 2. Legislation
The spider crawls all types of legislation:
- **Acts in Force** (500+ chapters)
- **Recent Legislation**
- **Subsidiary Legislation**
- **Uncommenced Legislation**
- **Repealed Legislation**
- **County Legislation**

Features:
- Section-level chunking for detailed analysis
- Automatic extraction of Act numbers and years
- Full text preservation
- Pagination support for large lists

### 3. Case Law (Judgments)
Comprehensive coverage of over **300,000+ judicial decisions** from:

#### Superior Courts
- Supreme Court (KESC)
- Court of Appeal (KECA)
- High Court (KEHC)
- Employment & Labour Relations Court (KEELRC)
- Environment and Land Court (KEELC)
- Industrial Court (KEIC)

#### Subordinate Courts
- Magistrate's Court (KEMC)
- Kadhis Court (KEKC)
- Small Claims Court (SCC)

#### Tribunals
- Civil and Human Rights Tribunals
- Commercial Tribunals
- Environment and Land Tribunals
- Intellectual Property Tribunals

#### International Courts
- African Court on Human and Peoples' Rights (AfCHPR)

### 4. Kenya Gazette
- **8,000+ gazette notices** from 1899 to 2025
- Year-by-year coverage
- Individual gazette document extraction

### 5. Treaties
- International treaties and conventions
- Bilateral and multilateral agreements

### 6. Publications
- Legal research publications
- Parliamentary reports
- Law reform publications

### 7. Cause Lists
- Court schedules
- Case listings

### 8. Blog Articles
- Legal commentary and analysis
- Updates and announcements

## Features

### Intelligent Parsing
- **Content Type Detection**: Automatically identifies document types (acts, judgments, gazettes, etc.)
- **Metadata Extraction**: Extracts dates, citations, court names, act numbers, section numbers
- **Chunking**: Intelligent splitting of long documents by sections/articles for better analysis

### Pagination Support
- Automatically follows pagination links
- Configurable page limits to control crawl scope
- Tracks pages crawled to prevent infinite loops

### Robust Error Handling
- Retry logic for failed requests
- HTTP caching to reduce server load
- AutoThrottle to respect server capacity
- Polite crawling with delays

### Data Quality
- De-duplication using MD5 hashing
- Content validation (minimum length checks)
- Structured metadata tagging
- ISO date formatting

## Usage

### Run Individual Spider

```bash
# From Module1_NiruSpider directory
python crawl_spider.py kenya_law_new_spider
```

### Run Test (Limited Pages)

```bash
python test_kenya_law_new.py
```

### Run All Spiders (Including Kenya Law New)

```bash
python crawl_all.py
```

### Custom Configuration

You can pass custom parameters:

```python
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings
from niruspider.spiders.kenya_law_new_spider import KenyaLawNewSpider

settings = get_project_settings()
process = CrawlerProcess(settings)

# Limit to 1000 pages
process.crawl(KenyaLawNewSpider, max_pages=1000)

process.start()
```

## Configuration

### Custom Settings (in spider)

```python
custom_settings = {
    "DOWNLOAD_DELAY": 2,  # Wait 2 seconds between requests
    "CONCURRENT_REQUESTS": 4,  # Max 4 concurrent requests
    "CONCURRENT_REQUESTS_PER_DOMAIN": 2,  # Max 2 per domain
    "ROBOTSTXT_OBEY": True,  # Respect robots.txt
    "RETRY_TIMES": 3,  # Retry failed requests 3 times
    "DOWNLOAD_TIMEOUT": 60,  # 60 second timeout
    "AUTOTHROTTLE_ENABLED": True,  # Auto-adjust crawl speed
    "HTTPCACHE_ENABLED": True,  # Cache responses
    "DEPTH_LIMIT": 10,  # Max depth from start URLs
}
```

### Global Settings (settings.py)

The spider inherits settings from `Module1_NiruSpider/settings.py`:
- LLM integration for summaries
- Vector database storage
- Pipeline configuration

## Output Data Structure

Each crawled document produces a `DocumentItem` with:

### Core Fields
- `doc_id`: Unique MD5 hash
- `url`: Source URL
- `title`: Document title
- `content`: Full text or chunked content
- `content_type`: "html", "pdf", "text"
- `chunk_index`: Position in document (0 for full doc)
- `total_chunks`: Total chunks in document

### Legal Metadata
- `doc_type`: "act", "judgment", "constitution", "gazette", etc.
- `category`: Category classification
- `source_name`: "Kenya Law"
- `publication_date`: ISO format date
- `act_number`: Act citation (if applicable)
- `section_number`: Section reference (if applicable)
- `article_number`: Article number (for Constitution)

### Additional Fields
- `metadata_tags`: List of tags for categorization
- `crawl_date`: When the document was crawled
- `raw_html`: Sample HTML for verification

## Architecture

### URL Routing
The `parse()` method routes to specialized parsers based on URL patterns:

| URL Pattern | Handler | Purpose |
|------------|---------|---------|
| `/akn/ke/act/2010/constitution` | `parse_constitution()` | Constitution with article chunking |
| `/legislation/` | `parse_legislation_list()` | Legislation listings |
| `/akn/ke/act/` | `parse_act()` | Individual Acts with section chunking |
| `/judgments/` | `parse_judgments_list()` | Court judgment listings |
| `/gazettes/` | `parse_gazette_list()` | Gazette listings |
| `/articles/` | `parse_articles_list()` | Blog articles |
| `/causelists/` | `parse_causelists()` | Court schedules |
| `/taxonomy/` | `parse_taxonomy()` | Collections and publications |

### Specialized Parsers

1. **Constitution Parser**: Extracts articles with numbering
2. **Legislation Parser**: Handles acts with section-level detail
3. **Judgment Parser**: Extracts court info, citations, dates
4. **Gazette Parser**: Year-based navigation and document extraction
5. **Generic Parser**: Fallback for other content types

## Performance

### Expected Crawl Times
- **Test run (50 pages)**: ~2-3 minutes
- **Legislation only (~500 acts)**: ~30-60 minutes
- **Full crawl (all resources)**: 8-24 hours (depending on server and settings)

### Resource Usage
- Memory: ~200-500 MB
- Network: Respects rate limits and robots.txt
- Storage: Varies by content (estimated 1-5 GB for full crawl)

## Best Practices

1. **Start with Test**: Always run `test_kenya_law_new.py` first to verify functionality
2. **Monitor Logs**: Check `niruspider.log` for errors and progress
3. **Use Caching**: HTTP cache prevents re-downloading unchanged content
4. **Respect Limits**: Don't disable rate limiting or robots.txt
5. **Incremental Crawls**: Run targeted crawls for specific sections when updating data

## Troubleshooting

### Common Issues

**Spider doesn't start:**
```bash
# Ensure you're in the correct directory
cd Module1_NiruSpider
python crawl_spider.py kenya_law_new_spider
```

**Too many retries:**
- Check internet connection
- Verify website is accessible: https://new.kenyalaw.org
- Increase `DOWNLOAD_TIMEOUT` in settings

**No data extracted:**
- Check if website structure has changed
- Review CSS selectors in parser methods
- Verify `ITEM_PIPELINES` is enabled

**Memory issues:**
- Reduce `CONCURRENT_REQUESTS`
- Increase `DOWNLOAD_DELAY`
- Use `max_pages` parameter to limit scope

## Future Enhancements

- [ ] PDF extraction for downloadable documents
- [ ] Advanced search integration
- [ ] Real-time monitoring for new content
- [ ] Differential updates (only crawl changed content)
- [ ] Multi-language support
- [ ] Enhanced metadata extraction using ML
- [ ] Integration with constitutional comparison tools

## Comparison: Old vs New Spider

| Feature | Old Spider | New Spider |
|---------|-----------|-----------|
| Website | kenyalaw.org | new.kenyalaw.org |
| Constitution | Basic | Article-level chunking |
| Legislation | Limited | Complete (500+ acts) |
| Case Law | Partial | Comprehensive (300K+ judgments) |
| Gazette | No | Yes (8K+ gazettes) |
| Pagination | Limited | Full support |
| Chunking | No | Section/Article level |
| Metadata | Basic | Rich (citations, dates, courts) |

## Support

For issues or questions:
1. Check the logs: `Module1_NiruSpider/niruspider.log`
2. Review settings in `settings.py`
3. Test with limited pages first
4. Verify website accessibility

## License

Part of AmaniQuery project - RAG-Powered Legal Intelligence Platform
