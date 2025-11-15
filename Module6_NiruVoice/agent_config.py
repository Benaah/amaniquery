"""
Configuration management for LiveKit Voice Agent
"""
import os
from typing import Optional
from dataclasses import dataclass
from dotenv import load_dotenv
from loguru import logger

load_dotenv()


@dataclass
class VoiceAgentConfig:
    """Configuration for the voice agent"""
    
    # LiveKit credentials
    livekit_url: str
    livekit_api_key: str
    
    # STT/TTS providers
    stt_provider: str = "openai"  # openai, assemblyai
    tts_provider: str = "openai"  # openai, silero
    language: str = "en"  # en, sw
    
    # Agent behavior
    max_response_length: int = 500  # Maximum words in response
    enable_follow_ups: bool = True
    conversation_timeout: int = 300  # seconds
    
    # RAG pipeline settings
    rag_top_k: int = 5
    rag_temperature: float = 0.7
    rag_max_tokens: int = 1500
    
    @classmethod
    def from_env(cls) -> "VoiceAgentConfig":
        """Load configuration from environment variables"""
        
        # Required LiveKit credentials
        livekit_url = os.getenv("LIVEKIT_URL")
        livekit_api_key = os.getenv("LIVEKIT_API_KEY")
        
        if not livekit_url:
            raise ValueError("LIVEKIT_URL environment variable is required")
        if not livekit_api_key:
            raise ValueError("LIVEKIT_API_KEY environment variable is required")
        
        # Optional STT/TTS settings
        stt_provider = os.getenv("VOICE_STT_PROVIDER", "openai").lower()
        tts_provider = os.getenv("VOICE_TTS_PROVIDER", "openai").lower()
        language = os.getenv("VOICE_LANGUAGE", "en").lower()
        
        # Validate providers
        if stt_provider not in ["openai", "assemblyai"]:
            logger.warning(f"Unknown STT provider: {stt_provider}, defaulting to openai")
            stt_provider = "openai"
        
        if tts_provider not in ["openai", "silero"]:
            logger.warning(f"Unknown TTS provider: {tts_provider}, defaulting to openai")
            tts_provider = "openai"
        
        if language not in ["en", "sw"]:
            logger.warning(f"Unknown language: {language}, defaulting to en")
            language = "en"
        
        # Agent behavior settings
        max_response_length = int(os.getenv("VOICE_MAX_RESPONSE_LENGTH", "500"))
        enable_follow_ups = os.getenv("VOICE_ENABLE_FOLLOW_UPS", "true").lower() == "true"
        conversation_timeout = int(os.getenv("VOICE_CONVERSATION_TIMEOUT", "300"))
        
        # RAG settings
        rag_top_k = int(os.getenv("VOICE_RAG_TOP_K", "5"))
        rag_temperature = float(os.getenv("VOICE_RAG_TEMPERATURE", "0.7"))
        rag_max_tokens = int(os.getenv("VOICE_RAG_MAX_TOKENS", "1500"))
        
        logger.info(f"Voice agent config loaded: STT={stt_provider}, TTS={tts_provider}, Lang={language}")
        
        return cls(
            livekit_url=livekit_url,
            livekit_api_key=livekit_api_key,
            stt_provider=stt_provider,
            tts_provider=tts_provider,
            language=language,
            max_response_length=max_response_length,
            enable_follow_ups=enable_follow_ups,
            conversation_timeout=conversation_timeout,
            rag_top_k=rag_top_k,
            rag_temperature=rag_temperature,
            rag_max_tokens=rag_max_tokens,
        )
    
    def get_stt_config(self) -> dict:
        """Get STT provider configuration"""
        config = {
            "provider": self.stt_provider,
            "language": self.language,
        }
        
        if self.stt_provider == "openai":
            config["model"] = "whisper-1"
        elif self.stt_provider == "assemblyai":
            config["language_code"] = "en" if self.language == "en" else "sw"
        
        return config
    
    def get_tts_config(self) -> dict:
        """Get TTS provider configuration"""
        config = {
            "provider": self.tts_provider,
            "language": self.language,
        }
        
        if self.tts_provider == "openai":
            config["voice"] = "alloy"  # Professional, clear voice
            config["model"] = "tts-1"
        elif self.tts_provider == "silero":
            config["speaker"] = "en_0" if self.language == "en" else "sw_0"
        
        return config

