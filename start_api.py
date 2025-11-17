#!/usr/bin/env python3
"""
AmaniQuery API and Voice Agent Startup Script

This script starts both the AmaniQuery API and Voice Agent concurrently
"""

import os
import sys
import platform
import threading
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def register_livekit_plugins():
    """Register LiveKit plugins on the main thread (required before starting agent)"""
    try:
        logger.info("🔌 Registering LiveKit plugins...")
        # Import plugins on main thread to register them
        from livekit.plugins import openai, silero
        logger.info("✔ LiveKit plugins registered (openai, silero)")
        return True
    except ImportError as e:
        logger.warning(f"⚠️  Could not register some LiveKit plugins: {e}")
        logger.warning("   Some features may not be available")
        return False
    except Exception as e:
        logger.error(f"✗ Failed to register LiveKit plugins: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return False


def start_voice_agent():
    """Start the LiveKit voice agent in a separate thread with isolated event loop"""
    import asyncio
    import time
    
    loop = None
    try:
        logger.info("🎤 Initializing Voice Agent...")
        from livekit.agents import cli, WorkerOptions
        from Module6_NiruVoice.voice_agent import entrypoint
        
        logger.info("✔ Voice agent imports successful")
        
        # Create a new event loop for this thread (isolated from main thread)
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        
        logger.info("🎤 Starting Voice Agent worker...")
        logger.info("   This will connect to LiveKit and wait for voice sessions")
        
        # Run the agent in the isolated event loop
        cli.run_app(WorkerOptions(entrypoint_fnc=entrypoint))
    except ImportError as e:
        logger.error(f"✗ Voice agent dependencies not available: {e}")
        logger.error("   Install with: pip install -r Module6_NiruVoice/requirements.txt")
        import traceback
        logger.error(traceback.format_exc())
    except KeyboardInterrupt:
        logger.info("Voice agent interrupted")
    except Exception as e:
        logger.error(f"✗ Failed to start voice agent: {e}")
        import traceback
        logger.error(traceback.format_exc())
    finally:
        # Properly close the event loop to prevent ResourceWarning
        if loop is not None and not loop.is_closed():
            try:
                # Cancel all pending tasks
                pending = asyncio.all_tasks(loop)
                for task in pending:
                    task.cancel()
                # Run until all tasks are cancelled
                if pending:
                    loop.run_until_complete(asyncio.gather(*pending, return_exceptions=True))
            except Exception:
                pass
            finally:
                loop.close()
                logger.debug("Voice agent event loop closed")


def start_api():
    """Start the FastAPI server"""
    try:
        import uvicorn
    except ImportError:
        logger.error("✗ uvicorn not found. Please install it with: pip install uvicorn")
        return False

    # Get configuration
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))

    # On Windows, disable reload by default to avoid multiprocessing issues
    is_windows = platform.system() == "Windows"
    if is_windows:
        reload_enabled = os.getenv("API_RELOAD", "False").lower() == "true"
        if reload_enabled:
            logger.warning("⚠️  Reload enabled on Windows may cause import issues")
            logger.warning("   Consider setting API_RELOAD=False")
    else:
        reload_enabled = os.getenv("API_RELOAD", "True").lower() == "true"

    logger.info(f"📍 API Server: http://{host}:{port}")
    logger.info(f"📚 API Docs: http://{host}:{port}/docs")
    logger.info(f"🔧 Provider: {os.getenv('LLM_PROVIDER', 'moonshot')}")
    logger.info(f"🔄 Reload: {'Enabled' if reload_enabled else 'Disabled'}")

    try:
        uvicorn.run(
            "Module4_NiruAPI.api:app",
            host=host,
            port=port,
            reload=reload_enabled,
        )
    except KeyboardInterrupt:
        logger.info("\n👋 API server stopped")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to start API server: {e}")
        return False


def main():
    """Start both API and Voice Agent"""
    print("=" * 60)
    print("🚀 Starting AmaniQuery Services")
    print("=" * 60)
    
    # Check if voice agent should be started
    enable_voice = os.getenv("ENABLE_VOICE_AGENT", "true").lower() == "true"
    livekit_url = os.getenv("LIVEKIT_URL", "").strip()
    livekit_api_key = os.getenv("LIVEKIT_API_KEY", "").strip()
    livekit_api_secret = os.getenv("LIVEKIT_API_SECRET", "").strip()
    
    # Log voice agent configuration status
    print("\n🎤 Voice Agent Configuration:")
    print(f"   Enabled: {enable_voice}")
    print(f"   LIVEKIT_URL: {'✔ Set' if livekit_url else '✗ Not set'}")
    print(f"   LIVEKIT_API_KEY: {'✔ Set' if livekit_api_key else '✗ Not set'}")
    print(f"   LIVEKIT_API_SECRET: {'✔ Set' if livekit_api_secret else '✗ Not set'}")
    
    if enable_voice and livekit_url and livekit_api_key and livekit_api_secret:
        # Register plugins on main thread BEFORE starting agent thread
        # This is required by LiveKit - plugins must be registered on main thread
        if not register_livekit_plugins():
            logger.warning("⚠️  Plugin registration had issues, but continuing...")
        
        # Start voice agent in a separate thread
        print("\n🎤 Starting Voice Agent thread...")
        voice_thread = threading.Thread(
            target=start_voice_agent,
            daemon=True,
            name="VoiceAgent"
        )
        voice_thread.start()
        logger.info("✔ Voice agent thread started")
        
        # Give the thread a moment to initialize and check if it's still alive
        import time
        time.sleep(1.0)
        if voice_thread.is_alive():
            logger.info("✔ Voice agent thread is running")
        else:
            logger.error("✗ Voice agent thread died immediately - check logs above for errors")
    else:
        if enable_voice:
            logger.warning("⚠️  Voice agent disabled: Missing required LiveKit credentials")
            logger.warning("   Set these environment variables to enable the voice agent:")
            if not livekit_url:
                logger.warning("   - LIVEKIT_URL (e.g., wss://your-livekit-server.com)")
            if not livekit_api_key:
                logger.warning("   - LIVEKIT_API_KEY (your LiveKit API key)")
            if not livekit_api_secret:
                logger.warning("   - LIVEKIT_API_SECRET (your LiveKit API secret - get from Settings > Keys)")
                logger.warning("     Note: The secret is only shown once when creating a key in LiveKit Cloud")
        else:
            logger.info("ℹ️  Voice agent disabled (set ENABLE_VOICE_AGENT=true to enable)")
    
    print("=" * 60)
    
    # Start API (blocking)
    try:
        start_api()
    except KeyboardInterrupt:
        logger.info("\n👋 Shutting down services...")
        return 0
    except Exception as e:
        logger.error(f"✗ Failed to start services: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())