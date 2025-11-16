# Quantization Guide

## Overview

Quantization reduces model size and memory usage by using lower precision (INT8) for weights while maintaining FP16 for activations, enabling efficient real-time processing.

## Architecture

### Quantized Attention

- **Weights**: INT8 quantization (8-bit)
- **Activations**: FP16 precision (16-bit)
- **Mixed Precision**: Optimal balance of accuracy and efficiency

### Components

1. **QuantizedLinear**: Linear layers with INT8 weights
2. **QuantizedMultiHeadAttention**: Attention with quantized weights
3. **QuantizedFeedForward**: Feed-forward with quantized weights
4. **StreamingAttention**: Chunked processing for long sequences

## Usage

### Basic Quantization

```python
from Module7_NiruHybrid.quantization.quantized_attention import QuantizedMultiHeadAttention

attention = QuantizedMultiHeadAttention(
    embed_dim=384,
    num_heads=12,
    quantize_weights=True,
    attention_bits=8
)
```

### Streaming Attention

```python
from Module7_NiruHybrid.quantization.attention_streaming import StreamingAttention

streaming_attention = StreamingAttention(
    embed_dim=384,
    num_heads=12,
    chunk_size=128,
    overlap_size=32,
    quantize=True
)
```

### Hybrid Encoder with Quantization

```python
from Module7_NiruHybrid.hybrid_encoder import HybridEncoder
from Module7_NiruHybrid.config import default_config

# Quantization enabled by default in config
encoder = HybridEncoder(
    embed_dim=384,
    quantize=True,  # Enable quantization
    config=default_config
)
```

## Configuration

Configure quantization in `config.py`:

```python
from Module7_NiruHybrid.config import QuantizationConfig

quant_config = QuantizationConfig(
    attention_weight_bits=8,  # INT8
    attention_activation_bits=16,  # FP16
    use_bitsandbytes=True,  # Use bitsandbytes library
    ff_weight_bits=8,
    ff_activation_bits=16,
    calibration_samples=1000,
    streaming_chunk_size=128
)
```

## Calibration

For optimal quantization, calibrate on representative data:

```python
# Calibration dataset
calibration_data = ["Sample text 1", "Sample text 2", ...]

# Calibration process (automatic in hybrid encoder)
encoder.calibrate(calibration_data)
```

## Performance

### Memory Reduction

- **Weights**: ~4x reduction (FP32 → INT8)
- **Overall**: ~50% memory reduction
- **Speed**: 2-3x faster inference (on supported hardware)

### Accuracy Impact

- **Minimal**: <1% accuracy loss typically
- **Calibration**: Improves accuracy
- **Mixed Precision**: Maintains activation precision

## Hardware Support

### bitsandbytes

Automatic INT8 quantization with bitsandbytes:

```python
# Requires CUDA
import bitsandbytes as bnb

# Automatic quantization in QuantizedLinear
```

### CPU Fallback

Manual quantization for CPU:

```python
# Falls back to manual quantization
# Slightly slower but works on CPU
```

## Best Practices

1. **Calibration**: Always calibrate on representative data
2. **Mixed Precision**: Use FP16 for activations, INT8 for weights
3. **Streaming**: Use chunked processing for long sequences
4. **Monitoring**: Track accuracy after quantization
5. **Hardware**: Use GPU for best performance

## Troubleshooting

### Low Accuracy

- Increase calibration samples
- Use FP16 for critical layers
- Check calibration data quality

### Memory Issues

- Reduce batch size
- Use streaming attention
- Enable gradient checkpointing

### Performance Issues

- Ensure GPU support (CUDA)
- Use bitsandbytes when available
- Optimize chunk sizes

## Advanced Usage

### Custom Quantization

```python
from Module7_NiruHybrid.quantization.quantized_attention import QuantizedLinear

# Custom quantized layer
custom_layer = QuantizedLinear(
    in_features=768,
    out_features=384,
    bits=8,
    use_bitsandbytes=True
)
```

### Streaming for Long Sequences

```python
# Automatic streaming for sequences > chunk_size
output = encoder.forward(
    embeddings=long_sequence_embeddings,
    use_streaming=True  # Automatic for long sequences
)
```

