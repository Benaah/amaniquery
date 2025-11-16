# Retention Guide

## Overview

The dynamic retention system provides continual learning, memory management, and adaptive retrieval for maintaining and improving model performance over time.

## Components

### Continual Learning

Fine-tunes the hybrid encoder on generated data.

```python
from Module7_NiruHybrid.retention.continual_learner import ContinualLearner

learner = ContinualLearner(
    hybrid_encoder=encoder,
    text_diffusion=text_diffusion,
    learning_rate=1e-5,
    update_frequency=100
)

# Add generated sample
learner.add_generated_sample(
    text="Generated text",
    embeddings=embeddings
)

# Trigger update (or automatic at update_frequency)
learner.update_model()
```

### Memory Management

Selective pattern retention with importance scoring.

```python
from Module7_NiruHybrid.retention.memory_manager import MemoryManager

memory = MemoryManager(
    buffer_size=10000,
    importance_threshold=0.7,
    eviction_policy="lru"  # or "lfu", "importance"
)

# Add pattern
memory.add_pattern(
    pattern_id="pattern_1",
    embeddings=embeddings,
    metadata={"query": "Query text"}
)

# Get top patterns
top_patterns = memory.get_top_patterns(top_k=10)

# Retain important patterns
retained = memory.retain_important_patterns()
```

### Adaptive Retrieval

Context-aware retrieval with multi-stage filtering.

```python
from Module7_NiruHybrid.retention.adaptive_retriever import AdaptiveRetriever

retriever = AdaptiveRetriever(
    hybrid_encoder=encoder,
    vector_store=vector_store,
    coarse_top_k=50,
    fine_top_k=5
)

# Retrieve with adaptive thresholds
results = retriever.retrieve(
    query_text="Your query",
    use_hybrid=True,
    adaptive=True
)
```

## Configuration

Configure retention in `config.py`:

```python
from Module7_NiruHybrid.config import RetentionConfig

retention_config = RetentionConfig(
    continual_learning_enabled=True,
    update_frequency=100,
    learning_rate=1e-5,
    memory_buffer_size=10000,
    importance_threshold=0.7,
    eviction_policy="lru",
    retention_ratio=0.1,
    adaptive_retrieval_enabled=True,
    coarse_top_k=50,
    fine_top_k=5,
    similarity_threshold=0.5
)
```

## Usage Patterns

### Continual Learning Workflow

1. Generate synthetic data using diffusion models
2. Add to continual learner buffer
3. Automatic update when buffer reaches threshold
4. Model weights updated with gradient accumulation

### Memory Management Workflow

1. Patterns added with importance scores
2. Patterns accessed and scored over time
3. Periodic retention: keep top N% by importance
4. Eviction of less important patterns when buffer full

### Adaptive Retrieval Workflow

1. Query encoded with hybrid encoder
2. Coarse retrieval: fast approximate search
3. Fine retrieval: similarity filtering with adaptive threshold
4. Context from recent queries adjusts threshold

## API Integration

### Trigger Retention Update

```bash
curl -X POST http://localhost:8000/retention/update
```

### Generate and Retain

```python
# Generate synthetic documents
docs = hybrid_rag.generate_synthetic_documents(
    query="Context",
    num_docs=10
)

# Automatic retention update after generation
# Or trigger manually:
hybrid_rag.trigger_retention_update()
```

## Best Practices

1. **Update Frequency**: Balance between learning and stability
2. **Memory Size**: Set based on available resources
3. **Importance Threshold**: Tune based on pattern quality
4. **Eviction Policy**: Choose based on access patterns
5. **Checkpointing**: Save model states regularly

## Monitoring

Track retention statistics:

```python
stats = hybrid_rag.get_stats()
print(stats["continual_learner"])
print(stats["memory_manager"])
print(stats["adaptive_retriever"])
```

## Troubleshooting

- **Low retention**: Increase importance threshold or buffer size
- **Slow updates**: Reduce update frequency or batch size
- **Memory issues**: Reduce buffer size or retention ratio
- **Poor retrieval**: Adjust similarity thresholds or top_k values

