# Module9_NiruSense: Kenyan Context-Aware NLP Processing Pipeline

Production-ready asynchronous NLP processing pipeline for AmaniQuery, specialized in Kenyan languages and contexts.

## Overview

NiruSense processes raw text documents through 9 specialized agents to extract rich metadata and generate searchable embeddings. Built for Kenyan social media, news, and web content with specific support for:

- **Sheng/Kenyan Slang** understanding and normalization
- **Swahili-English code-mixing** handling
- **Kenyan-specific entities** (politicians, counties, organizations)
- **15+ topic categories** relevant to Kenyan content
- **Tribalism and bias detection** for sensitive content filtering

## Architecture

```
Raw Document → Redis Stream → Orchestrator → 9 Agents → PostgreSQL + Qdrant
```

### The 9 Agents

1. **LanguageIdentifier**: Detects English, Swahili, or Sheng
2. **SlangDecoder**: Normalizes Sheng to standard English/Swahili
3. **TopicClassifier**: 15+ Kenyan-specific topics
4. **EntityExtractor**: Kenyan politicians, locations, organizations  
5. **SentimentAnalyzer**: Context-aware sentiment
6. **EmotionDetector**: Fine-grained emotion detection
7. **BiasDetector**: Tribalism, hate speech, political bias
8. **Summarizer**: Concise summarization
9. **QualityScorer**: Content quality scoring

## Quick Start

### Prerequisites

- Python 3.10+
- Redis (local or remote)
- PostgreSQL (Neon.tech recommended)
- Qdrant Cloud account
- MinIO/S3 for document storage

### Installation

```bash
# Clone and navigate
cd AmaniQuery/Module9_NiruSense

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r processing/requirements.txt

# Copy environment template
cp .env.example .env

# Edit .env with your credentials
nano .env
```

### Configuration

Edit `.env` to configure:

```env
# Required: Update these with your actual credentials
DATABASE_URL=postgresql://your-user:password@neon-host/db?sslmode=require
QDRANT_URL=https://your-instance.aws.cloud.qdrant.io:6333
QDRANT_API_KEY=your-api-key

# Redis (if remote)
REDIS_HOST=your-redis-host
REDIS_PORT=6379

# MinIO (if using remote S3)
MINIO_ENDPOINT=s3.amazonaws.com
MINIO_ACCESS_KEY=your-access-key
MINIO_SECRET_KEY=your-secret-key
```

### Running Locally

```bash
# Start the orchestrator
python -m processing.orchestrator

# In another terminal, start the health API
python app.py
```

Check health: `curl http://localhost:8000/health`

### Docker Deployment

```bash
# Build image
docker build -t nirusense:latest .

# Run container
docker run -p 8000:8000 --env-file .env nirusense:latest
```

### HuggingFace Spaces Deployment

1. Create a new Space on HuggingFace
2. Push this directory to the Space repository
3. Configure secrets in Space settings:
   - `DATABASE_URL`
   - `QDRANT_URL`
   - `QDRANT_API_KEY`
   - Other sensitive variables from `.env.example`

## API Endpoints

### Health Checks

- `GET /health` - Overall system health
- `GET /health/redis` - Redis connection status
- `GET /health/postgres` - PostgreSQL connection status
- `GET /health/qdrant` - Qdrant connection status
- `GET /health/agents` - Agent loading status

### Monitoring

- `GET /metrics` - Processing metrics (documents processed, success rate, etc.)
- `GET /status` - System configuration and status

## Database Schema

### PostgreSQL

**documents** table:
- `id` - UUID primary key
- `url` - Unique document URL
- `raw_content` - Original text
- `normalized_content` - Processed text
- `source_domain` - Source (twitter, tiktok, news, etc.)
- `published_at` - Publication timestamp

**analysis_results** table:
- `document_id` - Foreign key to documents
- `agent_id` - Which agent produced this result
- `result_json` - JSONB analysis output
- `model_version` - Model version used
- `execution_time_ms` - Processing time

### Qdrant

**Collection**: `amaniquery_sense`
- **Vector**: 768 dimensions (nomic-embed-text-v1.5)
- **Payload**: document metadata, topics, sentiment, entities, etc.

## Models Used

| Purpose | Model | Size |
|---------|-------|------|
| Embeddings | `nomic-ai/nomic-embed-text-v1.5` | 137M |
| Language ID | `papluca/xlm-roberta-base-language-detection` | 278M |
| Slang/Sheng | `google/flan-t5-base` | 250M |
| Topics/Bias | `MoritzLaurer/mDeBERTa-v3-base-mnli-xnli` | 279M |
| NER | `Davlan/xlm-roberta-base-ner-hrl` | 278M |
| Sentiment | `lxyuan/distilbert-base-multilingual-cased-sentiments-student` | 135M |
| Emotion | `j-hartmann/emotion-english-distilroberta-base` | 82M |
| Summarizer | `google/mt5-small` | 300M |

**Total Model Size**: ~1.7GB (downloads on first run) 

## Performance Targets

Per the TDD specifications:

- **Latency**: < 5 seconds per document
- **Throughput**: 10,000 documents/day on free tier
- **Sheng Accuracy**: > 85% correct identification
- **Sentiment F1**: > 0.80 on code-mixed text
- **Entity Recall**: > 0.90 for Kenyan political figures

## Troubleshooting

### Models Not Loading

```bash
# Pre-download models
python -c "from sentence_transformers import SentenceTransformer; SentenceTransformer('nomic-ai/nomic-embed-text-v1.5')"
```

### Redis Connection Issues

Check Redis is running:
```bash
redis-cli ping  # Should return "PONG"
```

### PostgreSQL Connection Issues

Test connection:
```bash
psql $DATABASE_URL -c "SELECT 1"
```

### Out of Memory

Reduce parallel processing:
```env
ENABLE_PARALLEL_AGENTS=false
BATCH_SIZE=1
```

## Development

### Running Tests

```bash
# Unit tests
pytest tests/test_agents.py -v

# Integration tests
pytest tests/test_pipeline.py -v

# End-to-end test
python tests/test_e2e.py
```

### Adding New Agents

1. Create agent class in `processing/agents/`
2. Inherit from `BaseAgent`
3. Implement `process(text, metadata)` method
4. Register in `orchestrator.py`
5. Update `config.py` with model settings

## License

Part of the AmaniQuery project - see root LICENSE file

## Support

For issues, questions, or contributions:
- Open an issue in the main AmaniQuery repository
- Contact: Eng. Onyango Benard

---

**Version**: 1.0.0  
**Status**: Production Ready  
**Last Updated**: November 2025
