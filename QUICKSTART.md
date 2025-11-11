# Quick Start Guide

## Prerequisites

- Python 3.8 or higher
- 4GB+ RAM (for embedding model)
- Internet connection (for crawling and LLM API)
- Moonshot AI API key (or OpenAI/Anthropic as alternatives)

## Installation

### 1. Clone/Download Project

```bash
cd AmaniQuery
```

### 2. Run Setup

```bash
python setup.py
```

This will:
- Create a virtual environment
- Install all dependencies
- Create necessary directories
- Generate .env file

### 3. Activate Virtual Environment

**Windows (PowerShell):**
```powershell
venv\Scripts\activate
```

**Linux/Mac:**
```bash
source venv/bin/activate
```

### 4. Configure Environment

Edit `.env` file and add your Moonshot AI API key:

```env
MOONSHOT_API_KEY=your-moonshot-api-key-here
MOONSHOT_BASE_URL=https://api.moonshot.cn/v1
```

**Get your Moonshot AI API key from:** https://platform.moonshot.cn/

## Running the Pipeline

### Step 1: Crawl Data (Module 1)

```bash
python -m Module1_NiruSpider.crawl_all
```

This will:
- Crawl Kenya Law website
- Fetch Parliamentary documents
- Parse Kenyan news RSS feeds
- Collect global tech/policy news

**Time:** 30 minutes - 2 hours (depending on sources)

**Output:** Raw data in `data/raw/`

### Step 2: Process Data (Module 2)

```bash
python -m Module2_NiruParser.process_all
```

This will:
- Extract text from HTML/PDF
- Clean and normalize text
- Chunk into 800-character segments
- Generate embeddings
- Enrich with metadata

**Time:** 10-30 minutes (depending on data volume)

**Output:** Processed chunks in `data/processed/`

### Step 3: Populate Database (Module 3)

```bash
python -m Module3_NiruDB.populate_db
```

This will:
- Load processed chunks
- Store in ChromaDB vector database
- Index for fast retrieval

**Time:** 5-15 minutes

**Output:** Vector database in `data/chroma_db/`

### Step 4: Start API Server (Module 4)

```bash
python -m Module4_NiruAPI.api
```

This will:
- Start FastAPI server on http://localhost:8000
- Initialize RAG pipeline
- Serve API endpoints

**Access:**
- API: http://localhost:8000
- Interactive Docs: http://localhost:8000/docs

## Testing the API

### Using the Browser

Visit http://localhost:8000/docs and use the interactive Swagger UI.

### Query AmaniQuery

```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d "{\"query\": \"What does the Kenyan Constitution say about freedom of speech?\"}"
```

### Share to Social Media

```bash
# Preview on all platforms
curl -X POST http://localhost:8000/share/preview \
  -H "Content-Type: application/json" \
  -d "{\"answer\": \"Your answer\", \"sources\": [], \"query\": \"Your question\"}"

# Format for Twitter
curl -X POST http://localhost:8000/share/format \
  -H "Content-Type: application/json" \
  -d "{\"answer\": \"Your answer\", \"sources\": [], \"platform\": \"twitter\"}"
```

### Using Python

```python
import requests

# Query AmaniQuery
response = requests.post(
    "http://localhost:8000/query",
    json={
        "query": "Recent parliamentary debates on finance",
        "top_k": 5,
        "category": "Parliament"
    }
)

result = response.json()
print(result["answer"])

# Share to Twitter
share_response = requests.post(
    "http://localhost:8000/share/format",
    json={
        "answer": result["answer"],
        "sources": result["sources"],
        "platform": "twitter",
        "query": "Recent parliamentary debates on finance"
    }
)

formatted = share_response.json()
print("\nTwitter Thread:")
for i, tweet in enumerate(formatted["content"], 1):
    print(f"\nTweet {i}:")
    print(tweet)
```

## Scheduled Crawling

To keep data up-to-date, schedule Module 1 to run periodically:

### Windows Task Scheduler

1. Open Task Scheduler
2. Create Basic Task
3. Set trigger (e.g., daily at 6 AM)
4. Action: Start a program
   - Program: `C:\Users\YourUser\OneDrive\Desktop\AmaniQuery\venv\Scripts\python.exe`
   - Arguments: `-m Module1_NiruSpider.crawl_all`
   - Start in: `C:\Users\YourUser\OneDrive\Desktop\AmaniQuery`

### Linux/Mac Cron

```bash
# Edit crontab
crontab -e

# Add daily crawl at 6 AM
0 6 * * * cd /path/to/AmaniQuery && venv/bin/python -m Module1_NiruSpider.crawl_all
```

## Troubleshooting

### "Import scrapy could not be resolved"

This is just a linting warning. The code will work when you install dependencies.

### "MOONSHOT_API_KEY not set"

Edit `.env` file and add your Moonshot AI API key. Get it from https://platform.moonshot.cn/

**Alternative:** You can also use OpenAI or Anthropic by changing `LLM_PROVIDER` in `.env`

### "No data files found"

Run Module 1 first to crawl data.

### "ChromaDB connection error"

Make sure `data/chroma_db/` directory exists and has write permissions.

### Slow crawling

Adjust `DOWNLOAD_DELAY` in `Module1_NiruSpider/niruspider/settings.py` (lower = faster but less polite).

## Data Management

### Reset Everything

```bash
# Delete all data
rm -rf data/raw/* data/processed/* data/chroma_db/*

# Re-run pipeline
python -m Module1_NiruSpider.crawl_all
python -m Module2_NiruParser.process_all
python -m Module3_NiruDB.populate_db
```

### Update Data Only

```bash
# Crawl new data
python -m Module1_NiruSpider.crawl_all

# Process new data
python -m Module2_NiruParser.process_all

# Add to database
python -m Module3_NiruDB.populate_db
```

## Performance Optimization

### For Faster Processing

Edit `.env`:
```env
MAX_WORKERS=8
BATCH_SIZE=100
EMBEDDING_BATCH_SIZE=64
```

### For Lower Memory Usage

```env
MAX_WORKERS=2
BATCH_SIZE=25
EMBEDDING_BATCH_SIZE=16
CHUNK_SIZE=600
```

## Support

For issues or questions:
1. Check the module-specific README files
2. Review the logs in `logs/` directory
3. Check the FastAPI docs at http://localhost:8000/docs

---

**Happy querying! 🇰🇪**
