"""
Module6_NiruVoice - Voice Module for AmaniQuery

Provides text-to-speech using Microsoft VibeVoice and integrates with RAG pipeline.
This is a simplified module that uses HTTP endpoints instead of LiveKit WebSockets.
"""

from Module6_NiruVoice.vibevoice_tts import (
    VibeVoiceTTS,
    get_tts,
    synthesize,
)
from Module6_NiruVoice.rag_integration import VoiceRAGIntegration

__all__ = [
    "VibeVoiceTTS",
    "get_tts",
    "synthesize",
    "VoiceRAGIntegration",
]

__version__ = "2.0.0"  # Major version bump for refactor
