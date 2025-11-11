# AmaniQuery 🇰🇪

A Retrieval-Augmented Generation (RAG) system for Kenyan legal, parliamentary, and news intelligence.

## 🏛️ Architecture

AmaniQuery is built as a 4-module pipeline:

1. **NiruSpider** - Web crawler for data ingestion
2. **NiruParser** - ETL pipeline with embedding generation
3. **NiruDB** - Vector database with metadata storage
4. **NiruAPI** - RAG-powered query interface

## 📂 Project Structure

```
AmaniQuery/
├── Module1_NiruSpider/          # Data crawling & ingestion
│   ├── spiders/
│   │   ├── kenya_law_spider.py
│   │   ├── parliament_spider.py
│   │   ├── news_rss_spider.py
│   │   └── global_trends_spider.py
│   ├── scrapy.cfg
│   └── settings.py
├── Module2_NiruParser/          # ETL & embedding pipeline
│   ├── extractors/
│   ├── cleaners/
│   ├── chunkers/
│   └── embedders/
├── Module3_NiruDB/              # Vector database
│   ├── vector_store.py
│   └── metadata_manager.py
├── Module4_NiruAPI/             # RAG API
│   ├── api.py
│   ├── rag_pipeline.py
│   └── models/
├── data/                        # Data storage
│   ├── raw/
│   ├── processed/
│   └── embeddings/
├── config/
│   └── sources.yaml
├── requirements.txt
├── .env.example
└── README.md
```

## 🚀 Quick Start

### 1. Installation

```bash
# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt
```

### 2. Configuration

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your settings
```

### 3. Run Modules

```bash
# Module 1: Crawl data
python -m Module1_NiruSpider.crawl_all

# Module 2: Process & embed data
python -m Module2_NiruParser.process_pipeline

# Module 3: Initialize database (automatic)

# Module 4: Start API server
python -m Module4_NiruAPI.api
```

## 🎯 Data Sources

### Kenyan Laws & Constitution
- **Source**: http://kenyalaw.org/
- **Strategy**: One-time crawl + periodic updates
- **Content**: Acts of Parliament, Constitution

### Parliament
- **Source**: https://www.parliament.go.ke/
- **Strategy**: Weekly crawl
- **Content**: Hansards, Bills, Publications

### Kenyan News (High-Frequency)
- **Sources**: 
  - nation.africa/rss
  - standardmedia.co.ke/rss
  - the-star.co.ke/rss
  - businessdailyafrica.com/rss
- **Strategy**: Daily RSS feed parsing

### Global Trends
- **Sources**:
  - Reuters (Technology/World)
  - TechCrunch
  - Al Jazeera (Politics)
- **Strategy**: Daily RSS feed parsing

## 🧠 RAG Pipeline

1. **Chunking**: 500-1000 characters with 100-char overlap
2. **Embedding Model**: all-MiniLM-L6-v2
3. **Vector DB**: ChromaDB / FAISS
4. **LLM**: Configurable (OpenAI, Anthropic, Local)

## 📊 Metadata Structure

Each chunk stores:
- `source_url`: Original article/document URL
- `title`: Document title
- `publication_date`: ISO format date
- `category`: ["Kenyan Law", "Parliament", "Kenyan News", "Global Trend"]
- `chunk_id`: Unique identifier (e.g., article-xyz_chunk_3)
- `author`: When available
- `summary`: Auto-generated snippet

## 🔧 Configuration

Edit `config/sources.yaml` to:
- Add/remove data sources
- Adjust crawl schedules
- Configure chunk sizes
- Set embedding parameters

## 📅 Automated Scheduling

Use Windows Task Scheduler or cron (Linux):

```bash
# Daily news crawl at 6 AM
# Weekly parliament crawl on Mondays
# Monthly law database update
```

See `scripts/scheduler_setup.md` for details.

## 🛡️ Ethical Crawling

- Respects `robots.txt`
- 2-3 second delays between requests
- User-agent identification
- Rate limiting on RSS feeds

## 📝 License

MIT License - See LICENSE file

## 🤝 Contributing

This is a hackathon project. Contributions welcome!

---

**Built with ❤️ for Kenya**
