# AmaniQuery 🇰🇪

A Retrieval-Augmented Generation (RAG) system for Kenyan legal, parliamentary, and news intelligence with **Constitutional Alignment Analysis** and social media sharing capabilities.

## 🏛️ Architecture

AmaniQuery is built as a 5-module pipeline:

1. **NiruSpider** - Web crawler for data ingestion
2. **NiruParser** - ETL pipeline with embedding generation
3. **NiruDB** - Vector database with metadata storage
4. **NiruAPI** - RAG-powered query interface (Moonshot AI)
5. **NiruShare** - Social media sharing service

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
├── Module5_NiruShare/           # Social media sharing
│   ├── formatters/
│   │   ├── twitter_formatter.py
│   │   ├── linkedin_formatter.py
│   │   └── facebook_formatter.py
│   ├── service.py
│   └── api.py
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

# Module 4 & 5: Start API server (includes sharing endpoints)
python -m Module4_NiruAPI.api
```

### 4. Query and Share

```python
import requests

# Query AmaniQuery
response = requests.post("http://localhost:8000/query", json={
    "query": "What does the Constitution say about freedom of expression?"
})
result = response.json()

# Share to Twitter
share = requests.post("http://localhost:8000/share/format", json={
    "answer": result["answer"],
    "sources": result["sources"],
    "platform": "twitter",
    "query": "Constitutional rights"
})
print(share.json()["content"])
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

### Global News & International Affairs
- **Sources**:
  - Geopolitics: Reuters, BBC, Al Jazeera, Foreign Policy
  - International Organizations: UN, WHO, World Bank, IMF, African Union
  - Technology: Reuters Tech, TechCrunch, MIT Tech Review
  - Policy: The Economist, Brookings, CFR
  - Climate & Development: UN Climate, UNDP
- **Strategy**: Daily RSS feed parsing
- **Focus**: Africa-relevant global news, international policy, institutional announcements

## 🚀 Features

- ✅ Automated web crawling from Kenyan sources
- ✅ Intelligent text processing & chunking
- ✅ Vector embeddings for semantic search
- ✅ RAG-powered Q&A with Moonshot AI
- ✅ **Constitutional Alignment Analysis** (dual-retrieval comparative analysis)
- ✅ Source citation & verification
- ✅ Social media sharing (Twitter/X, LinkedIn, Facebook)
- ✅ REST API with interactive documentation

## 🧠 RAG Pipeline

1. **Chunking**: 500-1000 characters with 100-char overlap
2. **Embedding Model**: all-MiniLM-L6-v2
3. **Vector DB**: ChromaDB / FAISS
4. **LLM**: Moonshot AI (default), OpenAI, Anthropic, or Local models

## 🏛️ Constitutional Alignment Module (Core Feature)

AmaniQuery's **unique value proposition**: Dual-retrieval RAG for constitutional compliance analysis.

**How it works:**
1. Analyzes query to identify Bill and constitutional concepts
2. Retrieves Bill chunks (filtered by `category='Bill'`)
3. Retrieves Constitution chunks (filtered by `category='Constitution'`)
4. Generates structured comparative analysis with citations

**Example:**
```python
response = requests.post("http://localhost:8000/alignment-check", json={
    "query": "How does the Finance Bill housing levy align with the constitution?"
})

# Returns structured analysis:
# 1. The Bill's Proposal (with citations)
# 2. Relevant Constitutional Provisions
# 3. Alignment Analysis (objective comparison)
# 4. Key Considerations
```

**API Endpoints:**
- `POST /alignment-check` - Full constitutional alignment analysis
- `POST /alignment-quick-check` - Quick bill vs concept check

See [Constitutional Alignment Guide](docs/CONSTITUTIONAL_ALIGNMENT.md) for details.

## 📱 Social Media Sharing

Module 5 provides intelligent formatting for:

- **Twitter/X**: Auto-threading for long content (280 char limit)
- **LinkedIn**: Professional posts with key takeaways (3000 char)
- **Facebook**: Engaging posts with call-to-action

**API Endpoints:**
- `POST /share/format` - Format for specific platform
- `POST /share/preview` - Preview all platforms
- `POST /share/generate-link` - Get shareable link
- `GET /share/platforms` - List supported platforms

See [Sharing Guide](docs/SHARING_GUIDE.md) for details.

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

## 📚 Documentation

- [Quick Start Guide](QUICKSTART.md) - Step-by-step setup
- [Constitutional Alignment](docs/CONSTITUTIONAL_ALIGNMENT.md) - **Core feature guide**
- [Moonshot AI Setup](docs/MOONSHOT_SETUP.md) - LLM configuration
- [Social Media Sharing](docs/SHARING_GUIDE.md) - Sharing guide
- [API Documentation](http://localhost:8000/docs) - Interactive docs

## 💡 Use Cases

- 📚 Legal research & constitutional queries
- ⚖️ **Constitutional alignment analysis** (Bills vs Constitution)
- 🏛️ Parliamentary proceedings analysis
- 📰 News aggregation & summarization
- 🌍 Policy & global trend tracking
- 📱 Social media content creation
- 🎓 Educational resource for Kenyan civics
- 💼 Legislative due diligence

## �📝 License

MIT License - See LICENSE file

## 🤝 Contributing

This is a hackathon project. Contributions welcome!

---

**Built with ❤️ for Kenya**
