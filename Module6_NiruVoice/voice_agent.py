"""
Main LiveKit Voice Agent Implementation
"""
import os
import sys
from pathlib import Path
from typing import Optional
from loguru import logger

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from livekit import agents, rtc
from livekit.agents import (
    JobContext,
    WorkerOptions,
    cli,
    AutoSubscribe,
    llm,
    voice_assistant,
)
from livekit.plugins import openai, silero

from Module6_NiruVoice.agent_config import VoiceAgentConfig
from Module6_NiruVoice.rag_integration import VoiceRAGIntegration
from Module6_NiruVoice.session_manager import VoiceSessionManager
from Module6_NiruVoice.stt_tts_handlers import create_stt_handler, create_tts_handler

# Import RAG pipeline components
from Module4_NiruAPI.rag_pipeline import RAGPipeline
from Module3_NiruDB.vector_store import VectorStore
from Module4_NiruAPI.config_manager import ConfigManager


class AmaniQueryVoiceAgent:
    """Professional voice agent for AmaniQuery using LiveKit"""
    
    def __init__(self, config: Optional[VoiceAgentConfig] = None):
        """
        Initialize voice agent
        
        Args:
            config: Voice agent configuration (loads from env if None)
        """
        self.config = config or VoiceAgentConfig.from_env()
        
        # Initialize RAG integration
        try:
            # Try to get existing RAG pipeline from environment or create new
            vector_store = None
            config_manager = None
            
            try:
                config_manager = ConfigManager()
            except Exception as e:
                logger.warning(f"ConfigManager not available: {e}")
            
            self.rag_integration = VoiceRAGIntegration(
                rag_pipeline=None,  # Will create new
                vector_store=vector_store,
                config_manager=config_manager,
                top_k=self.config.rag_top_k,
                temperature=self.config.rag_temperature,
                max_tokens=self.config.rag_max_tokens,
            )
            logger.info("RAG integration initialized")
        except Exception as e:
            logger.error(f"Failed to initialize RAG integration: {e}")
            raise
        
        # Initialize session manager
        self.session_manager = VoiceSessionManager(
            default_timeout=self.config.conversation_timeout
        )
        
        # Initialize STT/TTS handlers
        stt_config = self.config.get_stt_config()
        tts_config = self.config.get_tts_config()
        
        self.stt_handler = create_stt_handler(self.config.stt_provider, stt_config)
        self.tts_handler = create_tts_handler(self.config.tts_provider, tts_config)
        
        logger.info("AmaniQuery voice agent initialized")
    
    async def entrypoint(self, ctx: JobContext):
        """
        Main entry point for LiveKit agent
        
        This is called when a new voice session starts
        """
        logger.info(f"New voice session started: {ctx.room.name}")
        
        await ctx.connect(auto_subscribe=AutoSubscribe.AUDIO_ONLY)
        
        # Get or create session
        session_id = ctx.room.name or ctx.room.sid
        voice_session = self.session_manager.get_or_create_session(session_id)
        
        # Create STT based on provider
        if self.config.stt_provider == "openai":
            stt = openai.STT()
        else:
            # Default to OpenAI if provider not supported
            logger.warning(f"STT provider {self.config.stt_provider} not fully supported, using OpenAI")
            stt = openai.STT()
        
        # Create TTS based on provider
        if self.config.tts_provider == "openai":
            tts = openai.TTS(voice=self.tts_handler.config.get("voice", "alloy"))
        elif self.config.tts_provider == "silero":
            tts = silero.TTS()
        else:
            # Default to OpenAI
            logger.warning(f"TTS provider {self.config.tts_provider} not fully supported, using OpenAI")
            tts = openai.TTS()
        
        # Create custom LLM that uses RAG pipeline
        rag_llm = RAGLLM(self.rag_integration, self.session_manager, session_id)
        
        # Create agent session using VoiceAssistant
        assistant = voice_assistant.VoiceAssistant(
            vad=silero.VAD.load(),
            stt=stt,
            llm=rag_llm,
            tts=tts,
            chat_ctx=llm.ChatContext().append(
                role="system",
                text=self._get_system_prompt(),
            ),
        )
        
        # Cleanup on disconnect
        @ctx.room.on("disconnected")
        def on_disconnected():
            logger.info(f"Voice session disconnected: {session_id}")
            # Session will be cleaned up by timeout
        
        # Start the assistant
        assistant.start(ctx.room)
        
        # Wait for the session to complete
        await assistant.aclose()
    
    def _get_system_prompt(self) -> str:
        """Get system prompt for the voice agent"""
        return """You are AmaniQuery, a professional AI voice assistant specialized in Kenyan legal, parliamentary, and news intelligence.

Your role is to provide accurate, well-sourced answers based on the provided context. Always:
1. Be professional and concise in your responses
2. Provide detailed information when relevant
3. Cite sources naturally in speech (e.g., "According to the Kenyan Constitution...")
4. Keep responses focused and under 2-3 minutes when spoken
5. Use clear, authoritative language suitable for legal and policy queries
6. Structure responses: brief summary, key details, and source mentions

You have access to a comprehensive knowledge base of:
- Kenyan Constitution and legal documents
- Parliamentary proceedings and debates
- News articles and current affairs
- Global trends relevant to Kenya

Always provide accurate, factual information and cite your sources naturally."""


class RAGLLM(llm.LLM):
    """
    Custom LLM implementation that uses RAG pipeline instead of direct LLM calls
    """
    
    def __init__(
        self,
        rag_integration: VoiceRAGIntegration,
        session_manager: VoiceSessionManager,
        session_id: str,
    ):
        """
        Initialize RAG-based LLM
        
        Args:
            rag_integration: Voice RAG integration instance
            session_manager: Session manager for conversation context
            session_id: Current session ID
        """
        super().__init__()
        self.rag_integration = rag_integration
        self.session_manager = session_manager
        self.session_id = session_id
    
    async def chat(
        self,
        *,
        chat_ctx: llm.ChatContext,
        fnc_ctx: Optional[llm.FunctionContext] = None,
        temperature: Optional[float] = None,
    ) -> "llm.ChatStream":
        """
        Process chat request through RAG pipeline
        
        This is called by the voice agent when user speaks
        """
        # Get the last user message from chat context
        user_messages = [msg for msg in chat_ctx.messages if msg.role == "user"]
        if not user_messages:
            # No user message, return empty response
            return llm.ChatStream()
        
        user_query = user_messages[-1].content
        
        logger.info(f"Processing voice query: {user_query[:50]}...")
        
        # Get conversation context
        conversation_context = self.session_manager.get_conversation_context(
            self.session_id,
            max_turns=3
        )
        
        # Process through RAG
        try:
            result = self.rag_integration.query(
                query_text=user_query,
                conversation_context=conversation_context if conversation_context else None,
            )
            
            response_text = result.get("text", "I apologize, but I couldn't process your query.")
            
            # Add conversation turn to session
            self.session_manager.add_conversation_turn(
                self.session_id,
                user_query,
                response_text
            )
            
            logger.info(f"RAG response generated: {len(response_text)} characters")
            
            # Create chat stream with response
            stream = llm.ChatStream()
            stream.append(role="assistant", content=response_text)
            return stream
            
        except Exception as e:
            logger.error(f"Error processing RAG query: {e}")
            error_response = "I apologize, but I encountered an error processing your query. Please try again."
            
            # Still add to conversation
            self.session_manager.add_conversation_turn(
                self.session_id,
                user_query,
                error_response
            )
            
            stream = llm.ChatStream()
            stream.append(role="assistant", content=error_response)
            return stream


# Global agent instance
_agent_instance: Optional[AmaniQueryVoiceAgent] = None


async def entrypoint(ctx: JobContext):
    """
    Entry point function for LiveKit agent worker
    
    This is called by LiveKit when a new job starts
    """
    global _agent_instance
    
    if _agent_instance is None:
        try:
            _agent_instance = AmaniQueryVoiceAgent()
        except Exception as e:
            logger.error(f"Failed to initialize voice agent: {e}")
            raise
    
    await _agent_instance.entrypoint(ctx)


def main():
    """Main entry point for running the agent"""
    cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))


if __name__ == "__main__":
    main()

