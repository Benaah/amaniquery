# Quick Start: Kenya Law New Spider

## Run the Spider

### Option 1: Test Run (Recommended First)
Test with limited pages to verify everything works:
```bash
cd Module1_NiruSpider
python test_kenya_law_new.py
```

### Option 2: Full Crawl
Crawl the entire Kenya Law website:
```bash
cd Module1_NiruSpider
python crawl_spider.py kenya_law_new_spider
```

### Option 3: Crawl All Sources
Run all spiders including Kenya Law New:
```bash
cd Module1_NiruSpider
python crawl_all.py
```

## What Gets Scraped

✅ **Constitution of Kenya 2010** - All 264 articles  
✅ **Acts in Force** - 500+ chapters with full text  
✅ **Court Judgments** - 300,000+ decisions from all courts  
✅ **Kenya Gazette** - 8,000+ gazettes (1899-2025)  
✅ **Treaties & Publications**  
✅ **Cause Lists & Legal Blog**  

## Output

Data is saved to:
- **Raw data**: `../data/raw/`
- **Processed**: Goes through LLM pipeline for summarization
- **Vector DB**: Stored in Qdrant for RAG queries

## Monitor Progress

```bash
# Watch the log file
tail -f niruspider.log  # Linux/Mac
Get-Content niruspider.log -Wait  # Windows PowerShell
```

## Key Features

🔍 **Smart Parsing**: Automatically detects document types  
📄 **Chunking**: Splits long docs by sections/articles  
🔄 **Pagination**: Follows all pages automatically  
⚡ **Caching**: Avoids re-downloading unchanged content  
🛡️ **Polite Crawling**: Respects robots.txt and rate limits  

## Need Help?

See full documentation: `KENYA_LAW_NEW_README.md`
