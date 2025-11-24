
# voice_graph_robust.py
import os
import asyncio
import json
from typing import TypedDict, Optional, Dict, Any
from pathlib import Path
from loguru import logger

from langgraph.graph import StateGraph, END
from langchain_core.messages import HumanMessage

# Import offline manifest
try:
    from Module6_NiruVoice.offline_manifest import OFFLINE_RESPONSES
except ImportError:
    try:
        from offline_manifest import OFFLINE_RESPONSES
    except ImportError:
        OFFLINE_RESPONSES = {}
        logger.error("Could not import OFFLINE_RESPONSES")

# Redis Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", 6379))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", None)

# Initialize Redis Client
try:
    import redis.asyncio as redis
    redis_client = redis.Redis(
        host=REDIS_HOST, 
        port=REDIS_PORT, 
        password=REDIS_PASSWORD,
        db=0, 
        decode_responses=True,
        socket_timeout=0.5  # Fast fail for offline check
    )
except ImportError:
    logger.warning("redis-py not installed. Using mock redis.")
    class MockRedis:
        async def ping(self): return True
    redis_client = MockRedis()

# Initialize LiteLLM
try:
    import litellm
    # Configure LiteLLM (optional: set callbacks, etc.)
    litellm.suppress_debug_info = True
except ImportError:
    logger.warning("litellm not installed. LLM calls will fail or use fallback.")
    litellm = None

# Initialize ElevenLabs
try:
    from elevenlabs.client import AsyncElevenLabs
    elevenlabs_client = AsyncElevenLabs(api_key=os.getenv("ELEVENLABS_API_KEY"))
except ImportError:
    logger.warning("elevenlabs not installed. TTS will fail or use fallback.")
    elevenlabs_client = None

# Audio Cache Configuration
AUDIO_CACHE_DIR = Path(os.getenv("AUDIO_CACHE_DIR", "public/audio"))

# Mock edge_whisper for now (Replace with actual implementation or API client)
class EdgeWhisper:
    async def invoke(self, audio_bytes: bytes) -> Dict[str, str]:
        # TODO: Implement actual Whisper call (OpenAI, Azure, or local)
        # For now, return a placeholder if no actual implementation is provided
        await asyncio.sleep(0.1)
        return {"text": "This is a placeholder transcript."}

edge_whisper = EdgeWhisper()

def load_local_audio(filename: str) -> Optional[bytes]:
    """Load audio bytes from local cache with error handling."""
    try:
        file_path = AUDIO_CACHE_DIR / filename
        if file_path.exists():
            return file_path.read_bytes()
        logger.warning(f"Audio file not found: {file_path}")
        return None
    except Exception as e:
        logger.error(f"Error loading local audio {filename}: {e}")
        return None

def detect_keywords_from_audio(audio_bytes: bytes) -> list:
    """
    Fallback keyword detection from raw audio.
    In a real deployment, integrate with a lightweight keyword spotter (e.g., Porcupine).
    """
    # Placeholder
    return []

class VoiceState(TypedDict, total=False):
    audio_bytes: bytes
    transcript: str
    intent: str
    answer: str
    final_audio: Optional[bytes]
    offline_mode: bool
    error: str
    tts_failed: bool

graph = StateGraph(VoiceState)

# ── 1. Offline Pre-Check (First Node – Instant) ─────────────────────
@graph.add_node("offline_check")
async def offline_check(state):
    try:
        # Fast ping to check connectivity
        if redis_client:
            await asyncio.wait_for(redis_client.ping(), timeout=0.2)
        return {"offline_mode": False}
    except Exception as e:
        logger.warning(f"Offline check failed: {e}. Entering offline mode.")
        return {"offline_mode": True, "go_to": "offline_fallback"}

# ── 2. Offline Fallback (Keyword + Exact Match) ─────────────────────
@graph.add_node("offline_fallback")
async def offline_fallback(state):
    transcript = state.get("transcript", "").lower().strip()
    
    # Exact match
    if transcript in OFFLINE_RESPONSES:
        response = OFFLINE_RESPONSES[transcript]
        return {
            "answer": response["text"],
            "final_audio": load_local_audio(response["audio"]),
            "offline_mode": True
        }
    
    # Fuzzy keyword match (top 20 triggers)
    keywords = {
        "housing levy": "housing_levy_2025.mp3",
        "shif": "shif_explainer.mp3",
        "doctors strike": "doctors_strike_update.mp3",
        "kanjo parking": "parking_fees_nairobi.mp3"
    }
    
    for kw, audio_file in keywords.items():
        if kw in transcript:
            return {
                "answer": "Hii ndio update ya hivi sasa...", # Should ideally come from manifest too
                "final_audio": load_local_audio(audio_file),
                "offline_mode": True
            }
    
    # Ultimate fallback
    return {
        "answer": "Kwa sasa hakuna mtandao. Lakini Finance Bill 2024 iliangushwa, housing levy iko 1.5%, na SHIF ni 2.75%. Tafadhali jaribu baadaye.",
        "final_audio": load_local_audio("no_internet_generic.mp3"),
        "offline_mode": True
    }

# ── 3. Safe Transcription (Whisper with Fallback) ───────────────────
@graph.add_node("safe_transcribe")
async def safe_transcribe(state):
    try:
        # Attempt transcription with timeout
        result = await asyncio.wait_for(edge_whisper.invoke(state["audio_bytes"]), timeout=2.0)
        return {"transcript": result["text"]}
    except Exception as e:
        logger.error(f"Transcription failed: {e}")
        # Fallback: simple keyword detection from raw audio bytes
        keywords_found = detect_keywords_from_audio(state["audio_bytes"])
        return {
            "transcript": f"[keywords: {', '.join(keywords_found)}]" if keywords_found else "",
            "error": "whisper_failed"
        }

# ── 4. Safe LLM Call with Triple Fallback ─────────────────────────────
@graph.add_node("safe_llm")
async def safe_llm(state):
    # If we have a transcript error or empty transcript, skip LLM or use fallback
    if state.get("error") == "whisper_failed" and not state.get("transcript"):
         return {
            "answer": OFFLINE_RESPONSES.get("default", {"text": "Samahani, sikupata hiyo vizuri."})["text"],
            "offline_mode": True
        }

    try:
        # Try Groq → Together → Local Gemma-2-2B (simulated by litellm router or logic here)
        if litellm:
            # Example: using a router or specific model list
            # model="amani/fast" would be a custom alias in litellm config
            response = await asyncio.wait_for(
                litellm.acompletion(
                    model="gpt-3.5-turbo", # Replace with "amani/fast" or configured model
                    messages=[{"role": "user", "content": state.get("transcript", "")}],
                    fallbacks=["together_ai/togethercomputer/llama-2-70b-chat", "huggingface/google/gemma-2b"] 
                ), 
                timeout=8.0
            )
            return {"answer": response.choices[0].message.content}
        else:
            raise ImportError("litellm not installed")
    except Exception as e:
        logger.error(f"LLM call failed: {e}")
        # Final offline answer
        return {
            "answer": OFFLINE_RESPONSES.get("default", {"text": "Samahani, mfumo haupatikani kwa sasa."})["text"],
            "offline_mode": True
        }

# ── 5. Safe TTS with Browser Fallback ─────────────────────────────────
@graph.add_node("safe_tts")
async def safe_tts(state):
    if state.get("offline_mode") or state.get("final_audio"):
        return state

    try:
        if elevenlabs_client:
            # Generate audio
            audio_generator = await asyncio.wait_for(
                elevenlabs_client.generate(
                    text=state["answer"], 
                    model="eleven_turbo_v2_5",
                    voice="Rachel" # Specify a voice
                ),
                timeout=6.0
            )
            # Consume generator to get bytes
            audio_bytes = b"".join([chunk async for chunk in audio_generator])
            return {"final_audio": audio_bytes}
        else:
            raise ImportError("elevenlabs not installed")
    except Exception as e:
        logger.error(f"TTS failed: {e}")
        # Return text only → frontend uses Web Speech API
        return {
            "final_audio": None,
            "answer": state["answer"], # + " [Soma hii kwa sauti yako]" - let frontend handle UI
            "tts_failed": True
        }

# ── 3. Conditional Edges (The Magic) ─────────────────────────────────
graph.set_entry_point("offline_check")

graph.add_conditional_edges(
    "offline_check",
    lambda s: "offline_fallback" if s.get("offline_mode") else "safe_transcribe"
)

graph.add_edge("offline_fallback", END)
graph.add_edge("safe_transcribe", "safe_llm")
graph.add_edge("safe_llm", "safe_tts")
graph.add_edge("safe_tts", END)

robust_voice_agent = graph.compile(
    checkpointer=None,  # stateless = faster
    interrupt_before=[],
)
