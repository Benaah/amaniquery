"""
Module6_NiruVoice - LiveKit Voice Agent for AmaniQuery

This module provides a professional voice agent using LiveKit Agents framework
that integrates with AmaniQuery's RAG pipeline to answer voice queries about
Kenyan legal, parliamentary, and news intelligence.
"""

__version__ = "1.0.0"

from Module6_NiruVoice.voice_agent import AmaniQueryVoiceAgent
from Module6_NiruVoice.agent_config import VoiceAgentConfig

__all__ = ["AmaniQueryVoiceAgent", "VoiceAgentConfig"]

