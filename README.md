# AmaniQuery 🇰🇪

A Retrieval-Augmented Generation (RAG) system for Kenyan legal, parliamentary, and news intelligence with **three unique "wow" features**: Constitutional Alignment Analysis, Public Sentiment Gauge, InfoSMS Gateway, and Parliament Video Indexer.

## 🌟 Unique Features (Hackathon Differentiators)

### 1. 📊 Public Sentiment Gauge
**Track public sentiment on trending topics from news coverage**

- Sentiment analysis on all news articles (positive/negative/neutral)
- Real-time aggregation by topic with percentage breakdowns
- Visual sentiment distribution for policies, bills, and events
- Example: "Finance Bill: 70% negative, 20% neutral, 10% positive"

```bash
GET /sentiment?topic=Finance%20Bill&days=30
```

### 2. 📱 InfoSMS Gateway (Kabambe Accessibility)
**SMS-based queries for feature phone users**

- 160-character intelligent responses via SMS
- English and Swahili language support
- Africa's Talking integration for Kenya
- Automatic query type detection (legal/parliament/news)
- Works on feature phones without internet

```bash
User SMS: "Finance Bill"
AmaniQuery: "Finance Bill 2025 raises revenue through digital service tax..."
```

### 3. 🎥 Parliament Video Indexer
**Searchable YouTube transcripts with timestamp citations**

- Automatic transcript extraction from Parliament YouTube channels
- Timestamp-based citations (jump to exact moment)
- 60-second chunks with contextual overlap
- Vector search for semantic matching
- Direct YouTube links with `&t=XXs` parameters

```bash
Query: "budget allocation for education"
Response: "At 15:42 in the Finance Committee session..."
Link: https://youtube.com/watch?v=abc123&t=942s
```

### 4. ⚖️ Constitutional Alignment Analysis
**Compare Bills and Acts against the Constitution**

- Dual-retrieval RAG system (Bill + Constitution chunks separately)
- Granular legal metadata extraction (articles, clauses)
- Structured comparative analysis with citations
- Quick-check endpoint for specific constitutional topics

## 🏛️ Architecture

AmaniQuery is built as a 7-module pipeline:

1. **NiruSpider** - Web crawler for data ingestion
2. **NiruParser** - ETL pipeline with embedding generation
3. **NiruDB** - Vector database with metadata storage
4. **NiruAPI** - RAG-powered query interface with multi-model support
5. **NiruShare** - Social media sharing service
6. **NiruVoice** - Voice agent for real-time conversations
7. **NiruHybrid** - Enhanced RAG with hybrid encoder and adaptive retrieval

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
│   ├── metadata_manager.py
│   └── chat_manager.py
├── Module4_NiruAPI/             # RAG API
│   ├── api.py
│   ├── rag_pipeline.py
│   ├── alignment_pipeline.py
│   ├── sms_pipeline.py
│   └── models/
├── Module5_NiruShare/           # Social media sharing
│   ├── formatters/
│   │   ├── twitter_formatter.py
│   │   ├── linkedin_formatter.py
│   │   └── facebook_formatter.py
│   ├── service.py
│   └── api.py
├── Module6_NiruVoice/           # Voice agent
│   ├── voice_agent.py
│   └── rag_integration.py
├── Module7_NiruHybrid/          # Enhanced RAG with hybrid encoder
│   ├── hybrid_encoder.py
│   ├── integration/
│   │   ├── rag_integration.py
│   │   └── vector_store_adapter.py
│   ├── retention/
│   │   ├── adaptive_retriever.py
│   │   ├── memory_manager.py
│   │   └── continual_learner.py
│   └── streaming/
│       └── stream_processor.py
├── frontend/                    # Next.js frontend
│   └── src/
│       └── components/
│           └── chat.tsx
├── data/                        # Data storage
│   ├── raw/
│   ├── processed/
│   └── embeddings/
├── config/
│   └── sources.yaml
├── start_api.py                 # Unified startup script
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

# Start API server (includes all modules)
python start_api.py

# Or start API only
python -m Module4_NiruAPI.api
```

**Note**: The `start_api.py` script initializes:
- FastAPI server
- Hybrid RAG pipeline (Module 7)
- Voice agent (Module 6, if configured)
- All API endpoints

### 4. Query and Share

```python
import requests

# Standard query
response = requests.post("http://localhost:8000/query", json={
    "query": "What does the Constitution say about freedom of expression?"
})
result = response.json()

# Streaming query (real-time token-by-token)
response = requests.post("http://localhost:8000/query/stream", json={
    "query": "What does the Constitution say about freedom of expression?",
    "top_k": 5,
    "include_sources": True
}, stream=True)

for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))

# Hybrid RAG query (enhanced retrieval)
response = requests.post("http://localhost:8000/query/hybrid", json={
    "query": "What does the Constitution say about freedom of expression?",
    "top_k": 5,
    "use_hybrid": True
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

### Core Features
- ✅ Automated web crawling from Kenyan sources
- ✅ Intelligent text processing & chunking
- ✅ Vector embeddings for semantic search
- ✅ RAG-powered Q&A with multi-model support (OpenAI, Moonshot, Anthropic, Gemini)
- ✅ **Real-time streaming responses** - Token-by-token generation for faster perceived speed
- ✅ **Multi-model ensemble** - When context is limited, queries all available models and combines responses for accuracy
- ✅ **Hybrid RAG Pipeline** - Enhanced retrieval with hybrid encoder and adaptive retrieval
- ✅ Source citation & verification
- ✅ REST API with interactive documentation

### Unique Differentiators
- ✅ **Public Sentiment Gauge** - Track news sentiment by topic
- ✅ **InfoSMS Gateway** - SMS queries via Africa's Talking (kabambe accessibility)
- ✅ **Parliament Video Indexer** - Searchable YouTube transcripts with timestamps
- ✅ **Constitutional Alignment Analysis** - Dual-retrieval Bill-Constitution comparison
- ✅ **Social media sharing** - Intelligent formatting for Twitter/X, LinkedIn, Facebook
- ✅ **Chat interface** - Modern, responsive UI with copy/edit/resend for failed queries
- ✅ **Voice agent** - Real-time voice conversations via LiveKit

## 🧠 RAG Pipeline

### Standard RAG
1. **Chunking**: 500-1000 characters with 100-char overlap
2. **Embedding Model**: all-MiniLM-L6-v2
3. **Vector DB**: ChromaDB / FAISS / Upstash / Qdrant
4. **LLM**: Moonshot AI (default), OpenAI, Anthropic, Gemini

### Enhanced Features

#### Multi-Model Ensemble
When context is limited or unavailable in vector storage, AmaniQuery automatically:
- Queries all available models (OpenAI, Moonshot, Anthropic, Gemini) in parallel
- Combines responses intelligently to remove redundancy
- Streams the synthesized response for better accuracy

#### Hybrid RAG (Module 7)
- **Hybrid Encoder**: Combines convolutional and transformer architectures for enhanced embeddings
- **Adaptive Retrieval**: Multi-stage retrieval with context-aware thresholds
- **Streaming Support**: Optimized for real-time token-by-token responses
- **Improved Response Format**: Concise, scannable responses with clear structure

#### Response Formatting
- **Concise structure**: Summary → Key Points → Important Details
- **Better readability**: Proper spacing, bullet points, limited section length
- **No redundant disclaimers**: Only cites sources when directly used

## 📊 Feature Details

### Public Sentiment Gauge
Analyze news sentiment on any topic:

```python
# Get sentiment breakdown
GET /sentiment?topic=Finance%20Bill&days=30

# Response
{
  "sentiment_percentages": {
    "positive": 15.0,
    "negative": 70.0,
    "neutral": 15.0
  },
  "average_polarity": -0.35,
  "total_articles": 20
}
```

**Use Cases:**
- Track public reaction to legislation
- Monitor news tone on policies
- Identify controversial topics
- Compare Kenyan vs Global coverage sentiment

### InfoSMS Gateway
Query AmaniQuery via SMS (no internet needed):

```python
# Webhook for incoming SMS
POST /sms-webhook

# Preview SMS response (testing)
GET /sms-query?query=Finance%20Bill&language=en

# Manual SMS send
POST /sms-send?phone_number=+254712345678&message=...
```

**Setup:**
1. Sign up at https://africastalking.com
2. Set environment variables: `AT_USERNAME`, `AT_API_KEY`
3. Configure webhook URL in Africa's Talking dashboard
4. Users send SMS to your shortcode

**Features:**
- 160-character concise responses
- English and Swahili support
- ~KES 0.80 per SMS in Kenya
- Feature phone accessibility (kabambe)

### Parliament Video Indexer
Search Parliament YouTube videos with timestamp citations:

```python
# Search videos
POST /query
{
  "query": "budget allocation for education",
  "category": "Parliamentary Record"
}

# Response includes timestamp URLs
{
  "sources": [{
    "title": "Finance Committee Session",
    "timestamp_url": "https://youtube.com/watch?v=abc&t=942s",
    "timestamp_formatted": "15:42",
    "excerpt": "Budget allocation discussion..."
  }]
}
```

**How it works:**
1. Spider scrapes Parliament YouTube channels
2. youtube-transcript-api extracts transcripts with timestamps
3. 60-second chunks with 10-second overlap
4. Each chunk indexed with `start_time_seconds`
5. Citations include YouTube links with `&t=XXs` parameter

## 🏛️ Constitutional Alignment Module

AmaniQuery's **core legal feature**: Dual-retrieval RAG for constitutional compliance analysis.

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

## � API Endpoints Summary

### Core Query Endpoints
- `POST /query` - General RAG query with filters
- `POST /query/stream` - Streaming RAG query (token-by-token)
- `GET /health` - API health check
- `GET /stats` - Database statistics

### Hybrid RAG Endpoints
- `POST /query/hybrid` - Enhanced RAG with hybrid encoder
- `POST /stream/query` - Real-time streaming with hybrid RAG
- `GET /hybrid/stats` - Hybrid pipeline statistics
- `POST /retention/update` - Trigger retention update

### Chat Endpoints
- `GET /chat/sessions` - List chat sessions
- `POST /chat/sessions` - Create new session
- `GET /chat/sessions/{id}/messages` - Get session messages
- `POST /chat/sessions/{id}/messages` - Add message (with streaming)
- `POST /chat/feedback` - Submit feedback (like/dislike)
- `POST /chat/share` - Generate shareable chat link

### Unique Feature Endpoints
- `GET /sentiment` - Public sentiment analysis by topic
- `POST /sms-webhook` - Africa's Talking SMS webhook
- `POST /sms-send` - Manual SMS sending
- `GET /sms-query` - Preview SMS response
- `POST /alignment-check` - Full constitutional alignment analysis
- `POST /alignment-quick-check` - Quick bill vs concept check

### Social Media Sharing
- `POST /share/format` - Format for specific platform
- `POST /share/preview` - Preview all platforms
- `POST /share/generate-link` - Get shareable link
- `GET /share/platforms` - List supported platforms

### Documentation
- `GET /docs` - Interactive API documentation (Swagger UI)
- `GET /redoc` - Alternative documentation (ReDoc)

## �📱 Social Media Sharing

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
- 💬 **Real-time chat interface** - Interactive Q&A with streaming responses
- 🎤 **Voice queries** - Ask questions via voice (LiveKit integration)
- 🔄 **Multi-model accuracy** - Enhanced responses when context is limited
- 📊 **Hybrid retrieval** - Improved accuracy with adaptive retrieval

## �📝 License

MIT License - See LICENSE file

## 🤝 Contributing

This is a hackathon project. Contributions welcome!

---

**Built with ❤️ for Kenya**
