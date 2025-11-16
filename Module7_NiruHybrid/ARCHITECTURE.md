# Architecture Documentation

## System Overview

The Hybrid Convolutional-Transformer Pipeline integrates multiple components to enhance the existing RAG architecture with:

1. Hybrid encoding for improved embeddings
2. Diffusion models for synthetic data generation
3. Dynamic retention for continual learning
4. Quantized attention for efficiency
5. Real-time streaming support

## Component Architecture

### 1. Hybrid Encoder

**File**: `hybrid_encoder.py`

The hybrid encoder combines:
- **Convolutional Blocks**: 1D convolutions with multiple kernel sizes (3, 5, 7) for multi-scale local pattern extraction
- **Transformer Blocks**: Multi-head attention with quantization and feed-forward networks for global context
- **Fusion Mechanism**: Combines conv and transformer features via concatenation + projection, weighted sum, or attention

**Architecture Flow**:
```
Input Text → Token Embedding → Positional Encoding
    ↓
[Convolutional Block] → Local Features
    ↓
[Transformer Block] → Global Features
    ↓
[Fusion Layer] → Combined Features
    ↓
Output Projection → Final Embeddings
```

### 2. Diffusion Models

**Files**: `diffusion/text_diffusion.py`, `diffusion/embedding_diffusion.py`

Two diffusion models:
- **Text-to-Text**: Denoising diffusion for synthetic document generation
- **Text-to-Embedding**: Direct embedding generation via diffusion

**Process**:
1. Forward diffusion: Add noise to data
2. Reverse diffusion: Denoise to generate samples
3. Conditioning: Use query context to guide generation

### 3. Dynamic Retention System

**Files**: `retention/continual_learner.py`, `retention/memory_manager.py`, `retention/adaptive_retriever.py`

Three components:
- **Continual Learning**: Fine-tune encoder on generated data with gradient accumulation
- **Memory Management**: Importance-based pattern retention with eviction policies (LRU, LFU, importance)
- **Adaptive Retrieval**: Multi-stage retrieval (coarse + fine) with context-aware thresholds

### 4. Quantization

**Files**: `quantization/quantized_attention.py`, `quantization/attention_streaming.py`

- **INT8 Weights**: Attention and feed-forward weights quantized to 8-bit
- **FP16 Activations**: Attention activations in half precision
- **Streaming Attention**: Chunked processing with sliding windows for long sequences

### 5. Streaming Pipeline

**Files**: `streaming/stream_buffer.py`, `streaming/stream_processor.py`

- **Stream Buffer**: Manages incoming queries and generated data with timeout and batch processing
- **Stream Processor**: Processes streams in real-time with async support

## Data Flow

### Query Processing Flow

```
User Query
    ↓
Hybrid Encoder (if enabled)
    ↓
Adaptive Retriever
    ├─→ Coarse Retrieval (top 50)
    └─→ Fine Retrieval (top 5, filtered by similarity)
    ↓
Context Preparation
    ↓
LLM Generation
    ↓
Response
```

### Diffusion Generation Flow

```
Query Context
    ↓
Diffusion Model
    ├─→ Text-to-Text: Generate synthetic documents
    └─→ Text-to-Embedding: Generate synthetic embeddings
    ↓
Quality Filtering
    ↓
Vector Store (if enabled)
    ↓
Continual Learning Update
```

### Retention Update Flow

```
Generated Data Buffer
    ↓
Continual Learner
    ├─→ Gradient Accumulation
    ├─→ Model Update
    └─→ Checkpoint Save
    ↓
Memory Manager
    ├─→ Importance Scoring
    ├─→ Pattern Retention
    └─→ Eviction (if needed)
```

## Integration Points

### With Existing RAG Pipeline

The `HybridRAGPipeline` wraps the existing `RAGPipeline`:
- Enhances embedding generation with hybrid encoder
- Adds adaptive retrieval before LLM generation
- Integrates diffusion-generated documents into retrieval

### With Vector Store

The `HybridVectorStoreAdapter`:
- Adapts existing vector store to use hybrid embeddings
- Maintains compatibility with original encoder (fallback)
- Supports indexing diffusion-generated documents

## Performance Optimizations

1. **Quantization**: Reduces memory usage by ~50% with minimal accuracy loss
2. **Streaming**: Chunked processing enables real-time handling of long sequences
3. **Adaptive Retrieval**: Multi-stage filtering reduces computation
4. **Batch Processing**: Buffers enable efficient batch operations

## Configuration

All components are configurable via `config.py`:
- Encoder architecture (layers, dimensions, fusion method)
- Quantization settings (bit widths, calibration)
- Diffusion parameters (steps, schedules, guidance)
- Retention settings (update frequency, memory size)
- Streaming settings (buffer size, timeout, batch size)

## Scalability

The architecture supports:
- **Horizontal scaling**: Stateless components can be distributed
- **GPU acceleration**: PyTorch-based components support CUDA
- **Async processing**: Streaming components support async/await
- **Checkpointing**: Model states can be saved/loaded for recovery

