# Contributing to AmaniQuery

![Join the AmaniQuery community](imgs/contribution.png)

Thank you for your interest in contributing to AmaniQuery! This guide will help you get started contributing to our mission of democratizing access to Kenyan legal information.

**Quick Links:**
- [📖 Documentation Index](./docs/DOCUMENTATION_INDEX.md)
- [🏗️ Architecture Overview](./docs/ARCHITECTURE_OVERVIEW.md)
- [📋 Code Documentation Guide](./CODE_DOCUMENTATION_GUIDE.md)
- [🚀 Quick Start](./QUICKSTART.md)

---

## 🌟 About AmaniQuery

AmaniQuery is an AI-powered legal intelligence platform that makes Kenyan legal, parliamentary, and news information accessible through natural language queries. Our unique capabilities include:

- ⚖️ **Constitutional Alignment Analysis** - Compares bills against Kenya's 2010 Constitution
- 📊 **Public Sentiment Gauge** - Tracks sentiment from news coverage
- 📱 **InfoSMS Gateway** - SMS queries for feature phone accessibility (Kenya focus)
- 🎥 **Parliament Video Indexer** - Searchable YouTube transcripts with timestamps

### Tech Stack

**Backend (413 Python files)**
- FastAPI, LangGraph, Scrapy
- ChromaDB/Upstash (vectors), PostgreSQL (metadata)
- OpenAI/Claude/Gemini LLMs
- Celery + APScheduler for crawling

**Frontend (186 files)**
- Next.js 16, React 19, TypeScript
- Radix UI, TailwindCSS v4

**Infrastructure**
- Docker, Kubernetes, Render, HuggingFace Spaces

---

## 🚀 Getting Started

### Prerequisites

- **Python 3.8+** (3.10+ recommended)
- **Node.js 18+** and npm
- **Git**
- **16GB+ RAM** (for embeddings and LLMs)
- **100GB+ disk space** (for data storage)
- **API Keys**: OpenAI/Claude/Gemini, Deepgram (optional), Africa's Talking (optional)

### Development Environment Setup

#### 1. Fork & Clone

```bash
# Fork the repository on GitHub first

git clone https://github.com/your-username/amaniquery.git
cd amaniquery
git remote add upstream https://github.com/Benaah/amaniquery.git
```

#### 2. Automated Setup (Recommended)

```bash
# Run the automated setup script
python setup.py

# This will:
# ✓ Create virtual environment
# ✓ Install all Python dependencies
# ✓ Create required directories (data/raw, data/processed, etc.)
# ✓ Generate .env file from template
# ✓ Download embedding model
# ✓ Verify installation
```

#### 3. Manual Setup (Alternative)

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate     # Windows

# Install dependencies
pip install -r requirements.txt

# Setup directories
mkdir -p data/raw data/processed data/embeddings

# Create environment file
cp .env.example .env
```

#### 4. Configure Environment

Edit `.env` file with your API keys:

```env
# LLM Configuration (Choose one)
LLM_PROVIDER=openai  # or: moonshot, anthropic, google
OPENAI_API_KEY=sk-...
# OR
MOONSHOT_API_KEY=your_key_here
# OR
ANTHROPIC_API_KEY=sk-ant-...
# OR
GOOGLE_API_KEY=your_gemini_key

# Database Configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/amaniquery
CHROMA_DB_PATH=./data/embeddings
REDIS_URL=redis://localhost:6379

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
CORS_ORIGINS=http://localhost:3000

# Optional: SMS Integration (Kenya)
AT_USERNAME=your_africastalking_username
AT_API_KEY=your_africastalking_key

# Optional: Voice Features
DEEPGRAM_API_KEY=your_deepgram_key
ELEVENLABS_API_KEY=your_elevenlabs_key
```

#### 5. Frontend Setup

```bash
cd frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Frontend will be available at http://localhost:3000
```

#### 6. Verify Installation

```bash
# Test Python imports
python -c "from Module4_NiruAPI.api import app; print('✓ Backend OK')"

# Test vector DB
python -c "import chromadb; print('✓ ChromaDB OK')"

# Test LLM connection
python -c "from openai import OpenAI; client = OpenAI(); print('✓ OpenAI OK')"
```

---

## 📁 Project Structure

```
AmaniQuery/
├── .agent/                      # AI agent configuration
├── docs/                        # 📖 Documentation
│   ├── DOCUMENTATION_INDEX.md      # Navigation hub
│   └── ARCHITECTURE_OVERVIEW.md    # Technical architecture
├── Module1_NiruSpider/          # 🕷️ Web crawler (Scrapy)
│   ├── niruspider/
│   │   ├── spiders/                # 10 specialized spiders
│   │   ├── pipelines/              # Deduplication, quality scoring
│   │   └── settings.py             # Spider configuration
│   └── crawl_all.py                # Run all spiders
├── Module2_NiruParser/          # 🔄 ETL & embeddings
│   ├── extractors/                 # HTML/PDF extraction
│   ├── cleaners/                   # Text preprocessing
│   ├── chunkers/                   # Document chunking
│   └── embedders/                  # Vector generation
├── Module3_NiruDB/              # 💾 Vector & metadata storage
│   ├── vector_store.py             # ChromaDB interface
│   ├── metadata_manager.py         # PostgreSQL queries
│   └── chat_manager.py             # Session handling
├── Module4_NiruAPI/             # 🚀 FastAPI REST interface
│   ├── api.py                      # Main application
│   ├── routers/                    # Route handlers
│   ├── agents/                     # LangGraph agents
│   └── rag/                        # RAG pipeline
├── Module5_NiruShare/           # 📱 Social media sharing
├── Module6_NiruVoice/           # 🎤 Voice interface (STT/TTS)
├── Module7_NiruHybrid/          # 🧠 Enhanced RAG (hybrid encoder)
├── Module8_NiruAuth/            # 🔐 Authentication system
├── Module9_NiruSense/           # 🇰🇪 Kenyan NLP models
├── frontend/                    # 💻 Next.js frontend
│   ├── app/                      # App router
│   ├── src/components/           # React components
│   └── src/lib/                  # Frontend utilities
├── data/                        # 📂 Data storage
│   ├── raw/                      # Crawled content
│   ├── processed/                # Chunks & embeddings
│   └── embeddings/               # Vector databases
├── config/                      # ⚙️ Configuration
├── examples/                    # 💡 Example usage
├── scripts/                     # 🛠️ Utility scripts
├── setup.py                     # 🚀 Setup script
├── start_api.py                 # ▶️ Unified startup
├── requirements.txt             # Python dependencies
├── CODE_DOCUMENTATION_GUIDE.md  # 📋 Code documentation
├── CONTRIBUTING.md              # 🤝 This file
├── LICENSE                      # 📄 MIT License
├── llms.txt                     # 🤖 AI-friendly docs
└── README.md                    # 📖 Main project README
```

---

## 💻 Development Workflow

### Branch Naming

Use descriptive branch names:
- `feature/add-swahili-tts` - New features
- `bugfix/fix-sentiment-analysis` - Bug fixes
- `docs/update-api-docs` - Documentation
- `refactor/auth-module` - Refactoring
- `test/add-unit-tests` - Testing

### Making Changes

1. **Create Feature Branch**
```bash
git checkout main
git pull upstream main
git checkout -b feature/your-feature-name
```

2. **Make Your Changes**
- Write clean, documented code
- Add type hints
- Follow existing patterns
- See [CODE_DOCUMENTATION_GUIDE.md](./CODE_DOCUMENTATION_GUIDE.md)

3. **Test Your Changes**
```bash
# Run relevant tests
pytest tests/test_your_module.py -v

# Run full test suite
pytest

# Test manually if needed
python -m Module4_NiruAPI.api  # Start API
# Test endpoints with curl or Postman
```

4. **Update Documentation**
```bash
# Update module README if you modified a module
# Update API docs if you changed endpoints
# Update main docs if you added features
```

5. **Commit Your Changes**
```bash
# Stage files
git add .

# Commit with descriptive message
git commit -m "feat: add Swahili TTS support

- Implements VibeVoice for Swahili text-to-speech
- Updates Module6_NiruVoice with language detection
- Adds tests and documentation

Closes #123"
```

**Commit Message Format (Conventional Commits):**
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `refactor:` Code refactoring
- `test:` Tests
- `chore:` Maintenance

### Before Submitting

```bash
# 1. Pull latest changes
git pull upstream main

# 2. Resolve conflicts (if any)
git status
# Fix conflicts in files

# 3. Run tests again
pytest

# 4. Check linting
black ModuleX_Name/
flake8 ModuleX_Name/

# 5. Update requirements if needed
pip freeze > requirements.txt
```

### Create Pull Request

1. Push your branch:
```bash
git push origin feature/your-feature-name
```

2. Create PR on GitHub with template:
```markdown
Title: [feat/fix/docs] Descriptive title

Description:
- What does this PR do?
- Why is it needed?
- How to test?

Testing:
- [ ] Unit tests added
- [ ] Manual testing done
- [ ] All tests pass

Screenshots/Logs:
[If applicable]

Closes #issue-number
```

3. PR Requirements:
- ✅ Passes all tests
- ✅ Code reviewed by 1+ maintainer
- ✅ Documentation updated
- ✅ No merge conflicts
- ✅ Follows code style guide

---

## 🎨 Code Style Guidelines

### Python

- **Formatter**: Black (line length: 88)
- **Linter**: flake8
- **Type Hints**: Required for all functions
- **Docstrings**: Google style for public APIs
- **Imports**: Standard lib, 3rd party, local (with blank lines)

```python
# ✅ Good
import os
from pathlib import Path
from typing import List, Optional

import httpx
from fastapi import FastAPI

from Module2_NiruParser import ProcessingPipeline

def process_documents(
    file_paths: List[Path], 
    chunk_size: int = 500
) -> List[dict]:
    """Process documents and return chunks with metadata.
    
    Args:
        file_paths: List of file paths to process
        chunk_size: Size of text chunks in characters
        
    Returns:
        List of chunks with metadata
    """
    # Implementation
    pass
```

### TypeScript/JavaScript

- **Formatter**: Prettier
- **Linter**: ESLint
- **Use TypeScript strict mode
- Prefer functional components
- Use hooks appropriately

```typescript
// ✅ Good
interface SearchResult {
  id: string;
  title: string;
  content: string;
  relevance: number;
}

export const SearchComponent: React.FC = () => {
  const [query, setQuery] = useState<string>("");
  const [results, setResults] = useState<SearchResult[]>([]);
  
  const handleSearch = useCallback(async () => {
    const res = await fetch("/api/search", {
      method: "POST",
      body: JSON.stringify({ query }),
    });
    const data = await res.json();
    setResults(data.results);
  }, [query]);
  
  return (
    <div>
      <input value={query} onChange={e => setQuery(e.target.value)} />
      <button onClick={handleSearch}>Search</button>
    </div>
  );
};
```

### Documentation

See [CODE_DOCUMENTATION_GUIDE.md](./CODE_DOCUMENTATION_GUIDE.md) for:
- Docstring templates
- Comment guidelines
- API documentation standards
- Module README templates

---

## 🧪 Testing

### Test Structure

```
tests/
├── unit/              # Unit tests for functions/classes
├── integration/       # Integration tests for modules
├── api/              # API endpoint tests
└── e2e/              # End-to-end tests (Playwright)
```

### Running Tests

```bash
# All tests
pytest -v

# Specific module
pytest tests/unit/test_module1/ -v

# With coverage
pytest --cov=Module1_NiruSpider --cov-report=html

# API tests only
pytest tests/api/test_search.py -v

# E2E tests (Playwright)
cd frontend && npm run test:e2e
```

### Writing Tests

```python
# tests/unit/test_parser.py
def test_text_chunking():
    """Test that text is chunked correctly with overlap."""
    from Module2_NiruParser.chunkers import RecursiveChunker
    
    chunker = RecursiveChunker(chunk_size=100, overlap=20)
    text = "This is a test. " * 20
    chunks = chunker.chunk(text)
    
    assert len(chunks) > 1
    assert all(len(chunk) <= 100 for chunk in chunks)
    # Check overlap
    assert chunks[0][-20:] in chunks[1][:20]
```

**Test Coverage Goal:** > 80% for critical modules

---

## 🐛 Debugging

### Common Issues

1. **Import errors**
```bash
# Add project root to Python path
export PYTHONPATH="${PWD}:${PYTHONPATH}"
```

2. **Database connection errors**
```bash
# Check PostgreSQL is running
sudo systemctl status postgresql

# Check connection string in .env
DATABASE_URL=postgresql://user:pass@localhost:5432/amaniquery
```

3. **Vector DB issues**
```bash
# Reset ChromaDB (if corrupted)
rm -rf data/embeddings/chroma_db
python -m Module3_NiruDB.populate_db
```

4. **Crawling errors**
```bash
# Check spider logs
python -m Module1_NiruSpider.crawl --logfile logs/spider.log

# Test single URL
python -m Module1_NiruSpider.test_spider --url "https://example.com"
```

5. **LLM errors**
```bash
# Test API key
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

### Debug Mode

```bash
# Enable debug logging
export LOG_LEVEL=DEBUG

# Run with debug
python start_api.py --debug

# Debug specific module
LOG_LEVEL=DEBUG python -m Module4_NiruAPI.api
```

---

## 📞 Getting Help

### Communication Channels

1. **GitHub Issues** - Bug reports, feature requests
2. **GitHub Discussions** - Q&A, ideas, showcase
3. **Email** - contact@amaniquery.ke
4. **Discord** - Join our [Discord server](https://discord.gg/amaniquery) (if available)

### Before Asking for Help

1. Check [TROUBLESHOOTING.md](./docs/TROUBLESHOOTING.md) (if exists)
2. Search existing GitHub issues
3. Check logs in `logs/` directory
4. Try running with `LOG_LEVEL=DEBUG`
5. Provide detailed information:
   - Steps to reproduce
   - Error messages
   - Logs
   - Environment details

---

## 🎯 Areas for Contribution

### Good First Issues

- 🐛 **Bug fixes** in spider parsing logic
- 📝 **Documentation updates** for modules
- ✅ **Test coverage** improvements
- 🎨 **UI/UX enhancements** in frontend
- 🌐 **Internationalization** (Swahili translation)

### Feature Requests

- 🔍 **Advanced search filters** (date, source, court level)
- 📊 **Analytics dashboard** for usage insights
- 🔔 **Alert system** for new legislation
- 📱 **Mobile app** (React Native)
- 🔗 **Third-party integrations** (Slack, Teams)

### Performance Improvements

- ⚡ **API response optimization**
- 📈 **Vector search indexing**
- 🗄️ **Database query optimization**
- 🚀 **Frontend bundle size reduction**

---

## 🏆 Recognition

Contributors are recognized in:
- [README.md](./README.md) contributors section
- Release notes
- Project documentation
- Special contributor badges (for significant contributions)

---

## 📜 Code of Conduct

By participating, you agree to:
- Be respectful and inclusive
- Welcome newcomers
- Focus on constructive criticism
- Respect differing viewpoints
- Prioritize community well-being

### Reporting Issues

If you experience/witness unacceptable behavior:
1. Contact maintainers privately
2. Provide detailed description
3. Include evidence if possible
4. We'll review and take appropriate action

---

## 📚 Additional Resources

- [🔍 Architecture Deep-Dive](./docs/ARCHITECTURE_OVERVIEW.md)
- [📝 Code Documentation Standards](./CODE_DOCUMENTATION_GUIDE.md)
- [🚀 Deployment Guide](./docs/DEPLOYMENT_GUIDE.md)
- [📱 API Reference](./Module4_NiruAPI/)
- [🎨 Frontend README](./frontend/README.md)
- [🐳 Docker Setup](./docs/DOCKER_README.md)

---

## 🏁 Next Steps

1. ⭐ **Star the repository** to show support
2. 🍴 **Fork the project** and explore
3. 🐛 **Find an issue** labeled "good first issue"
4. 💬 **Join discussions** and introduce yourself
5. 🚀 **Make your first contribution**

**Welcome to the AmaniQuery community!** 🇰🇪

---

<div align="center">

**Questions?** Open an issue or discussion on GitHub

[← Back to README](./README.md) | [View Architecture →](./docs/ARCHITECTURE_OVERVIEW.md)

</div>
