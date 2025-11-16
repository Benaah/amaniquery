# API Reference

## Hybrid RAG Endpoints

### POST /query/hybrid

Hybrid RAG query with enhanced encoder and adaptive retrieval.

**Request Body**:
```json
{
  "query": "What does the Kenyan Constitution say about freedom of speech?",
  "top_k": 5,
  "category": "Constitution",
  "source": null,
  "temperature": 0.7,
  "max_tokens": 1500,
  "include_sources": true
}
```

**Response**:
```json
{
  "answer": "The Kenyan Constitution guarantees freedom of speech...",
  "sources": [
    {
      "title": "Constitution Article 33",
      "url": "...",
      "relevance_score": 0.95
    }
  ],
  "query_time": 0.45,
  "retrieved_chunks": 5,
  "model_used": "moonshot-v1-8k"
}
```

### POST /diffusion/generate

Generate synthetic documents using diffusion models.

**Query Parameters**:
- `query` (optional): Query context for generation
- `num_docs` (default: 10): Number of documents to generate
- `add_to_store` (default: true): Whether to add to vector store

**Request Body**:
```json
{
  "query": "Kenyan legal system",
  "num_docs": 10,
  "add_to_store": true
}
```

**Response**:
```json
{
  "generated_documents": [
    "Generated text document 1...",
    "Generated text document 2..."
  ],
  "count": 10,
  "added_to_store": true
}
```

### POST /retention/update

Trigger retention update (continual learning).

**Request**: No body required

**Response**:
```json
{
  "status": "success",
  "message": "Retention update completed"
}
```

### POST /stream/query

Real-time streaming query endpoint.

**Request Body**: Same as `/query/hybrid`

**Response**: Server-Sent Events (SSE) stream

```
data: Generated text chunk 1

data: Generated text chunk 2

data: [DONE]{"sources": [...], "query_time": 0.45, ...}
```

### GET /hybrid/stats

Get statistics for hybrid RAG pipeline.

**Response**:
```json
{
  "hybrid_queries": 150,
  "diffusion_generations": 50,
  "adaptive_retrievals": 120,
  "use_hybrid": true,
  "use_diffusion": true,
  "use_adaptive_retrieval": true,
  "vector_store_adapter": {
    "hybrid_encodings": 100,
    "fallback_encodings": 50,
    "hybrid_ratio": 0.67
  },
  "memory_manager": {
    "buffer_size": 5000,
    "total_patterns_added": 1000
  }
}
```

## Python API

### HybridRAGPipeline

```python
from Module7_NiruHybrid.integration.rag_integration import HybridRAGPipeline

# Initialize
hybrid_rag = HybridRAGPipeline(
    base_rag_pipeline=rag_pipeline,
    hybrid_encoder=hybrid_encoder,
    use_hybrid=True
)

# Query
result = hybrid_rag.query(
    query="Your question",
    top_k=5,
    use_hybrid=True,
    generate_augmentation=True
)

# Generate synthetic documents
docs = hybrid_rag.generate_synthetic_documents(
    query="Context",
    num_docs=10
)

# Trigger retention update
hybrid_rag.trigger_retention_update()

# Get statistics
stats = hybrid_rag.get_stats()
```

### HybridEncoder

```python
from Module7_NiruHybrid.hybrid_encoder import HybridEncoder

encoder = HybridEncoder(config=default_config.encoder)
embeddings = encoder.encode(text="Sample", return_pooled=True)
```

### AdaptiveRetriever

```python
from Module7_NiruHybrid.retention.adaptive_retriever import AdaptiveRetriever

retriever = AdaptiveRetriever(
    hybrid_encoder=encoder,
    vector_store=vector_store
)
results = retriever.retrieve(query_text="Query")
```

## Error Handling

All endpoints return standard HTTP status codes:
- `200`: Success
- `400`: Bad request (invalid parameters)
- `500`: Internal server error
- `503`: Service unavailable (component not initialized)

Error responses include:
```json
{
  "detail": "Error message"
}
```

