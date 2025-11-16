"""
Real-time Streaming Pipeline

Provides streaming processing for queries and generated data.
"""

from .stream_processor import StreamProcessor
from .stream_buffer import StreamBuffer

__all__ = ["StreamProcessor", "StreamBuffer"]

