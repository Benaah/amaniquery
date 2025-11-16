"""
Streaming-optimized attention computation for real-time processing
"""
import torch
import torch.nn as nn
from typing import Optional, Tuple, List
import math
from .quantized_attention import QuantizedMultiHeadAttention


class StreamingAttention(nn.Module):
    """Streaming attention with sliding window and chunked processing"""
    
    def __init__(
        self,
        embed_dim: int,
        num_heads: int,
        chunk_size: int = 128,
        overlap_size: int = 32,
        dropout: float = 0.1,
        quantize: bool = True
    ):
        super().__init__()
        self.chunk_size = chunk_size
        self.overlap_size = overlap_size
        self.embed_dim = embed_dim
        self.num_heads = num_heads
        
        # Use quantized attention
        self.attention = QuantizedMultiHeadAttention(
            embed_dim=embed_dim,
            num_heads=num_heads,
            dropout=dropout,
            quantize_weights=quantize
        )
    
    def forward(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        use_streaming: bool = True,
        key_padding_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Forward pass with optional streaming
        
        Args:
            query: [batch_size, seq_len, embed_dim]
            key: [batch_size, seq_len, embed_dim]
            value: [batch_size, seq_len, embed_dim]
            use_streaming: Whether to use chunked processing
            key_padding_mask: Optional padding mask
        
        Returns:
            output: [batch_size, seq_len, embed_dim]
        """
        batch_size, seq_len, _ = query.shape
        
        if not use_streaming or seq_len <= self.chunk_size:
            # Standard attention for short sequences
            output, _ = self.attention(
                query, key, value,
                key_padding_mask=key_padding_mask
            )
            return output
        
        # Streaming attention with sliding window
        return self._streaming_attention(
            query, key, value, key_padding_mask
        )
    
    def _streaming_attention(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        key_padding_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """Process attention in chunks with overlap"""
        batch_size, seq_len, embed_dim = query.shape
        outputs = []
        
        # Process in chunks
        start = 0
        while start < seq_len:
            end = min(start + self.chunk_size, seq_len)
            
            # Extract chunk
            q_chunk = query[:, start:end, :]
            k_chunk = key[:, start:end, :]
            v_chunk = value[:, start:end, :]
            
            # Include overlap from previous chunk for context
            if start > 0:
                overlap_start = max(0, start - self.overlap_size)
                k_context = key[:, overlap_start:end, :]
                v_context = value[:, overlap_start:end, :]
            else:
                k_context = k_chunk
                v_context = v_chunk
            
            # Extract mask chunk if provided
            mask_chunk = None
            if key_padding_mask is not None:
                if start > 0:
                    overlap_start = max(0, start - self.overlap_size)
                    mask_chunk = key_padding_mask[:, overlap_start:end]
                else:
                    mask_chunk = key_padding_mask[:, start:end]
            
            # Compute attention for chunk
            chunk_output, _ = self.attention(
                q_chunk, k_context, v_context,
                key_padding_mask=mask_chunk
            )
            
            # Only keep non-overlapping part (except for first chunk)
            if start > 0:
                # Remove overlap from output
                keep_start = self.overlap_size
                chunk_output = chunk_output[:, keep_start:, :]
            
            outputs.append(chunk_output)
            start = end
        
        # Concatenate all chunks
        output = torch.cat(outputs, dim=1)
        return output


class SlidingWindowAttention(nn.Module):
    """Sliding window attention for efficient long-sequence processing"""
    
    def __init__(
        self,
        embed_dim: int,
        num_heads: int,
        window_size: int = 128,
        dropout: float = 0.1,
        quantize: bool = True
    ):
        super().__init__()
        self.window_size = window_size
        self.attention = QuantizedMultiHeadAttention(
            embed_dim=embed_dim,
            num_heads=num_heads,
            dropout=dropout,
            quantize_weights=quantize
        )
    
    def forward(
        self,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        key_padding_mask: Optional[torch.Tensor] = None
    ) -> torch.Tensor:
        """
        Sliding window attention
        
        Each position only attends to positions within window_size
        """
        batch_size, seq_len, embed_dim = query.shape
        
        if seq_len <= self.window_size:
            # Standard attention for short sequences
            output, _ = self.attention(query, key, value, key_padding_mask=key_padding_mask)
            return output
        
        outputs = []
        
        for i in range(seq_len):
            # Determine window boundaries
            window_start = max(0, i - self.window_size // 2)
            window_end = min(seq_len, i + self.window_size // 2 + 1)
            
            # Extract window
            q_i = query[:, i:i+1, :]  # [batch_size, 1, embed_dim]
            k_window = key[:, window_start:window_end, :]
            v_window = value[:, window_start:window_end, :]
            
            # Extract mask window
            mask_window = None
            if key_padding_mask is not None:
                mask_window = key_padding_mask[:, window_start:window_end]
            
            # Compute attention
            output_i, _ = self.attention(
                q_i, k_window, v_window,
                key_padding_mask=mask_window
            )
            outputs.append(output_i)
        
        output = torch.cat(outputs, dim=1)
        return output

