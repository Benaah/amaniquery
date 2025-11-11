# Module 4: NiruAPI - RAG-Powered Query Interface

This module provides a FastAPI-based REST API for querying the AmaniQuery knowledge base using Retrieval-Augmented Generation (RAG).

## Features

- **RAG Pipeline**: Combines vector search with LLM generation
- **Source Citations**: Always includes source references
- **REST API**: Easy integration with any client
- **Multiple LLM Support**: OpenAI, Anthropic, or local models
- **Filtering**: Query by category, source, date range

## Components

### API Server (`api.py`)
- FastAPI application
- Query endpoints
- Health checks
- CORS support

### RAG Pipeline (`rag_pipeline.py`)
- Retrieval from vector database
- Context preparation
- LLM prompt engineering
- Response generation with citations

## API Endpoints

### `POST /query`
Main query endpoint

**Request:**
```json
{
  "query": "What are the recent parliamentary debates on finance?",
  "top_k": 5,
  "category": "Parliament",
  "include_sources": true
}
```

**Response:**
```json
{
  "answer": "Recent parliamentary debates have focused on...",
  "sources": [
    {
      "title": "Finance Bill 2025 Debate",
      "url": "https://parliament.go.ke/...",
      "relevance_score": 0.92
    }
  ],
  "query_time": 1.24
}
```

### `GET /health`
Health check endpoint

### `GET /stats`
Database statistics

## Usage

### Start Server
```bash
python -m Module4_NiruAPI.api
# or
uvicorn Module4_NiruAPI.api:app --reload
```

### Query from Python
```python
import requests

response = requests.post(
    "http://localhost:8000/query",
    json={"query": "What is the Kenyan Constitution on freedom of speech?"}
)
print(response.json()["answer"])
```

### Query from cURL
```bash
curl -X POST http://localhost:8000/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Recent news on AI policy in Kenya"}'
```

## Configuration

Set in `.env`:
- `LLM_PROVIDER`: openai, anthropic, or local
- `OPENAI_API_KEY`: Your OpenAI API key
- `DEFAULT_MODEL`: Model to use (gpt-3.5-turbo, gpt-4, etc.)
- `API_PORT`: Port to run on (default: 8000)
