"""
Speech-to-Text and Text-to-Speech Handlers
"""
from typing import Optional, Dict
from loguru import logger


class STTHandler:
    """Speech-to-Text handler interface"""
    
    def __init__(self, provider: str, config: Dict):
        """
        Initialize STT handler
        
        Args:
            provider: STT provider (openai, assemblyai, kimi)
            config: Provider-specific configuration
        """
        self.provider = provider
        self.config = config
        logger.info(f"STT handler initialized with provider: {provider}")


class TTSHandler:
    """Text-to-Speech handler interface"""
    
    def __init__(self, provider: str, config: Dict):
        """
        Initialize TTS handler
        
        Args:
            provider: TTS provider (openai, silero, kimi)
            config: Provider-specific configuration
        """
        self.provider = provider
        self.config = config
        logger.info(f"TTS handler initialized with provider: {provider}")


def create_stt_handler(provider: str, config: Dict) -> STTHandler:
    """Factory function to create STT handler"""
    return STTHandler(provider, config)


def create_tts_handler(provider: str, config: Dict) -> TTSHandler:
    """Factory function to create TTS handler"""
    return TTSHandler(provider, config)

