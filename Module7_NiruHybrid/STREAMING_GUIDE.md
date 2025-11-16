# Streaming Guide

## Overview

The streaming pipeline enables real-time processing of queries and generated data with optimized buffer management and async support.

## Components

### StreamBuffer

Manages buffered data with timeout and batch processing.

```python
from Module7_NiruHybrid.streaming.stream_buffer import StreamBuffer

buffer = StreamBuffer(
    buffer_size=1000,
    timeout=0.1,
    batch_size=32
)

# Add items
buffer.add(item_id="query_1", data={"text": "Query text"})

# Get batch
batch = buffer.get_batch(max_items=32)
```

### StreamProcessor

Processes streaming queries and generated data.

```python
from Module7_NiruHybrid.streaming.stream_processor import StreamProcessor

processor = StreamProcessor(
    hybrid_encoder=encoder,
    batch_size=32
)

# Process single query
result = processor.process_query(
    query_id="q1",
    query_text="Your query"
)

# Process batch
queries = [{"id": "q1", "text": "Query 1"}]
results = processor.process_query_batch(queries)
```

## Async Streaming

### AsyncStreamBuffer

```python
from Module7_NiruHybrid.streaming.stream_buffer import AsyncStreamBuffer

async_buffer = AsyncStreamBuffer(
    buffer_size=1000,
    timeout=0.1
)

# Add item
await async_buffer.add(item_id="q1", data={"text": "Query"})

# Get batch
batch = await async_buffer.get_batch(max_items=32)
```

### AsyncStreamProcessor

```python
from Module7_NiruHybrid.streaming.stream_processor import AsyncStreamProcessor

async_processor = AsyncStreamProcessor(hybrid_encoder=encoder)

# Process query stream
async def query_stream():
    async for query in input_stream:
        yield query

async for result in async_processor.process_query_stream(query_stream()):
    print(result)
```

## Configuration

Configure streaming in `config.py`:

```python
from Module7_NiruHybrid.config import StreamingConfig

streaming_config = StreamingConfig(
    buffer_size=1000,
    buffer_timeout=0.1,
    batch_size=32,
    max_concurrent_streams=10,
    processing_timeout=30.0
)
```

## API Usage

### Streaming Query Endpoint

```bash
curl -X POST http://localhost:8000/stream/query \
  -H "Content-Type: application/json" \
  -d '{"query": "Your question", "top_k": 5}'
```

Response is Server-Sent Events (SSE) stream.

### Python Client

```python
import requests

response = requests.post(
    "http://localhost:8000/stream/query",
    json={"query": "Your question"},
    stream=True
)

for line in response.iter_lines():
    if line:
        print(line.decode('utf-8'))
```

## Best Practices

1. **Buffer Sizing**: Set buffer size based on expected throughput
2. **Timeout Tuning**: Adjust timeout based on latency requirements
3. **Batch Processing**: Use batch processing for efficiency
4. **Error Handling**: Implement retry logic for failed streams
5. **Monitoring**: Track buffer statistics for optimization

## Performance Tips

- Use async processing for high-throughput scenarios
- Tune batch size based on available memory
- Monitor buffer drop rates to adjust sizing
- Use streaming attention for long sequences

