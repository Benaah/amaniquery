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
    
    def get_livekit_config(self) -> Dict:
        """Get LiveKit-compatible STT configuration"""
        if self.provider == "openai":
            return {
                "provider": "openai",
                "model": self.config.get("model", "whisper-1"),
                "language": self.config.get("language", "en"),
            }
        elif self.provider == "assemblyai":
            return {
                "provider": "assemblyai",
                "language_code": self.config.get("language_code", "en"),
            }
        elif self.provider == "kimi":
            return {
                "provider": "kimi",
                "model_path": self.config.get("model_path", "moonshotai/Kimi-Audio-7B-Instruct"),
                "device": self.config.get("device", "cuda"),
                "language": self.config.get("language", "en"),
            }
        else:
            raise ValueError(f"Unsupported STT provider: {self.provider}")


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
    
    def get_livekit_config(self) -> Dict:
        """Get LiveKit-compatible TTS configuration"""
        if self.provider == "openai":
            return {
                "provider": "openai",
                "voice": self.config.get("voice", "alloy"),
                "model": self.config.get("model", "tts-1"),
            }
        elif self.provider == "silero":
            return {
                "provider": "silero",
                "speaker": self.config.get("speaker", "en_0"),
            }
        elif self.provider == "kimi":
            return {
                "provider": "kimi",
                "model_path": self.config.get("model_path", "moonshotai/Kimi-Audio-7B-Instruct"),
                "device": self.config.get("device", "cuda"),
                "voice": self.config.get("voice", "default"),
            }
        else:
            raise ValueError(f"Unsupported TTS provider: {self.provider}")


def create_stt_handler(provider: str, config: Dict) -> STTHandler:
    """Factory function to create STT handler"""
    return STTHandler(provider, config)


def create_tts_handler(provider: str, config: Dict) -> TTSHandler:
    """Factory function to create TTS handler"""
    return TTSHandler(provider, config)

