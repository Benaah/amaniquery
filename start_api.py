#!/usr/bin/env python3
"""
AmaniQuery API, Voice Agent, and Scheduler Startup Script

This script starts the AmaniQuery API, Voice Agent, and Crawler Scheduler concurrently
"""

import os
import sys
import platform
import threading
import atexit
from pathlib import Path
from loguru import logger
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Global scheduler reference for cleanup
_scheduler_instance = None


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


def start_scheduler():
    """Start the crawler scheduler service"""
    global _scheduler_instance
    
    try:
        logger.info("📅 Initializing Crawler Scheduler...")
        from Module1_NiruSpider.scheduler.scheduler_service import SchedulerService
        
        # Create scheduler instance
        _scheduler_instance = SchedulerService()
        
        # Register cleanup on exit
        def cleanup_scheduler():
            if _scheduler_instance:
                logger.info("🛑 Stopping scheduler...")
                _scheduler_instance.stop()
        
        atexit.register(cleanup_scheduler)
        
        # Start the scheduler (this runs in the background)
        _scheduler_instance.start()
        
        logger.info("✔ Crawler scheduler started successfully")
        logger.info("   Crawlers will run automatically on schedule")
        
        return True
        
    except ImportError as e:
        logger.warning(f"⚠️  Scheduler dependencies not available: {e}")
        logger.warning("   Install APScheduler: pip install apscheduler")
        return False
    except Exception as e:
        logger.error(f"✗ Failed to start scheduler: {e}")
        import traceback
        logger.debug(traceback.format_exc())
        return False


def get_scheduler_status():
    """Get the current scheduler status"""
    global _scheduler_instance
    if _scheduler_instance:
        return _scheduler_instance.get_status()
    return {"running": False, "message": "Scheduler not initialized"}


def start_api():
    """Start the FastAPI server"""
    try:
        import uvicorn
    except ImportError:
        logger.error("✗ uvicorn not found. Please install it with: pip install uvicorn")
        return False

    # Get configuration
    # Check API_PORT first, then PORT (for Render compatibility), then default to 8000
    host = os.getenv("API_HOST", "0.0.0.0")
    port_env = os.getenv("API_PORT") or os.getenv("PORT")
    port = int(port_env) if port_env else 8000
    
    # Log port source for debugging
    if os.getenv("PORT"):
        logger.info(f"🔌 Using PORT from environment: {port}")
    elif os.getenv("API_PORT"):
        logger.info(f"🔌 Using API_PORT from environment: {port}")
    else:
        logger.info(f"🔌 Using default port: {port}")

    # Disable reload on production platforms (Render) and Windows to avoid issues
    is_render = os.getenv("RENDER") is not None
    is_windows = platform.system() == "Windows"
    
    if is_render:
        # Always disable reload on Render for reliable port binding
        reload_enabled = False
        logger.info("🔧 Running on Render - reload disabled for reliable port binding")
    elif is_windows:
        reload_enabled = os.getenv("API_RELOAD", "False").lower() == "true"
        if reload_enabled:
            logger.warning("⚠️  Reload enabled on Windows may cause import issues")
            logger.warning("   Consider setting API_RELOAD=False")
    else:
        reload_enabled = os.getenv("API_RELOAD", "True").lower() == "true"

    # Check auth module configuration
    auth_enabled = os.getenv("ENABLE_AUTH", "false").lower() == "true"
    
    logger.info(f"📍 API Server: http://{host}:{port}")
    logger.info(f"📚 API Docs: http://{host}:{port}/docs")
    logger.info(f"🔧 Provider: {os.getenv('LLM_PROVIDER', 'moonshot')}")
    logger.info(f"🔄 Reload: {'Enabled' if reload_enabled else 'Disabled'}")
    logger.info(f"🔐 Auth Module: {'Enabled' if auth_enabled else 'Disabled'}")
    
    if auth_enabled:
        logger.info("   Run 'python migrate_auth_db.py' if auth tables don't exist")

    try:
        # Exclude setup.py and other non-source files from reload watch
        reload_excludes = [
            "setup.py",
            "*.pyc",
            "__pycache__",
            "*.log",
            ".env",
            "venv/**",
            "node_modules/**",
        ] if reload_enabled else None
        
        logger.info(f"🚀 Starting uvicorn server on {host}:{port}")
        uvicorn.run(
            "Module4_NiruAPI.api:app",
            host=host,
            port=port,
            reload=reload_enabled,
            reload_excludes=reload_excludes,
            log_level="info",
            access_log=True,
        )
    except KeyboardInterrupt:
        logger.info("\n👋 API server stopped")
        return True
    except Exception as e:
        logger.error(f"✗ Failed to start API server: {e}")
        return False


def main():
    """Start API, Voice Agent, and Scheduler"""
    print("=" * 60)
    print("🚀 Starting AmaniQuery Services")
    print("=" * 60)
    
    # Check if scheduler should be started
    enable_scheduler = os.getenv("ENABLE_SCHEDULER", "true").lower() == "true"
    scheduler_backend = os.getenv("SCHEDULER_BACKEND", "apscheduler")
    
    # Log scheduler configuration status
    print("\n📅 Crawler Scheduler Configuration:")
    print(f"   Enabled: {enable_scheduler}")
    print(f"   Backend: {scheduler_backend}")
    if enable_scheduler:
        print("   Crawlers will run automatically on schedule")
        print("   - News sources: Every 6 hours")
        print("   - Legal sources: Daily at 2 AM UTC")
        print("   - Parliament: Daily at 3 AM UTC")
        print("   - Vector store update: Daily at 5 AM UTC")
    
    # Check if voice agent should be started
    # Auto-disable voice agent on Render (unless explicitly enabled) to avoid CLI issues
    is_render = os.getenv("RENDER") is not None
    if is_render:
        # On Render, default to disabled unless explicitly set to true
        enable_voice = os.getenv("ENABLE_VOICE_AGENT", "false").lower() == "true"
        if not os.getenv("ENABLE_VOICE_AGENT"):
            print("\nℹ️  Running on Render - voice agent disabled by default")
            print("   Set ENABLE_VOICE_AGENT=true in environment to enable")
    else:
        # On other platforms, default to enabled
        enable_voice = os.getenv("ENABLE_VOICE_AGENT", "true").lower() == "true"
    livekit_url = os.getenv("LIVEKIT_URL", "").strip()
    livekit_api_key = os.getenv("LIVEKIT_API_KEY", "").strip()
    livekit_api_secret = os.getenv("LIVEKIT_API_SECRET", "").strip()
    
    # Check auth module configuration
    auth_enabled = os.getenv("ENABLE_AUTH", "false").lower() == "true"
    database_url = os.getenv("DATABASE_URL", "").strip()
    
    # Log voice agent configuration status
    print("\n🎤 Voice Agent Configuration:")
    print(f"   Enabled: {enable_voice}")
    print(f"   LIVEKIT_URL: {'✔ Set' if livekit_url else '✗ Not set'}")
    print(f"   LIVEKIT_API_KEY: {'✔ Set' if livekit_api_key else '✗ Not set'}")
    print(f"   LIVEKIT_API_SECRET: {'✔ Set' if livekit_api_secret else '✗ Not set'}")
    
    # Log auth module configuration status
    print("\n🔐 Authentication Module Configuration:")
    print(f"   Enabled: {auth_enabled}")
    print(f"   DATABASE_URL: {'✔ Set' if database_url else '✗ Not set'}")
    if auth_enabled and not database_url:
        print("   ⚠️  Warning: DATABASE_URL required for auth module")
    if auth_enabled:
        print("   💡 Tip: Run 'python migrate_auth_db.py' to create auth tables")
    
    # Start the scheduler if enabled
    if enable_scheduler:
        print("\n📅 Starting Crawler Scheduler...")
        scheduler_started = start_scheduler()
        if scheduler_started:
            print("✔ Scheduler is running in background")
        else:
            print("⚠️  Scheduler failed to start - crawlers won't run automatically")
            print("   You can still trigger crawlers manually via the admin API")
    else:
        print("\nℹ️  Scheduler disabled (set ENABLE_SCHEDULER=true to enable)")
    
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

    # Start NiruSense Orchestrator (Background Service)
    enable_nirusense = os.getenv("ENABLE_NIRUSENSE", "false").lower() == "true"
    if enable_nirusense:
        print("\n🧠 Starting NiruSense Orchestrator...")
        try:
            from Module9_NiruSense.nirusense_service import start_nirusense_thread
            
            # Start NiruSense in a separate thread
            nirusense_thread = threading.Thread(
                target=start_nirusense_thread,
                daemon=True,
                name="NiruSenseOrchestrator"
            )
            nirusense_thread.start()
            logger.info("✔ NiruSense orchestrator thread started")
            
            # Check if it's running
            import time
            time.sleep(1.0)
            if nirusense_thread.is_alive():
                logger.info("✔ NiruSense orchestrator is running")
            else:
                logger.error("✗ NiruSense thread died immediately - check logs")
                
        except ImportError as e:
            logger.error(f"✗ Failed to import NiruSense: {e}")
        except Exception as e:
            logger.error(f"✗ Failed to start NiruSense: {e}")
    else:
        logger.info("ℹ️  NiruSense disabled (set ENABLE_NIRUSENSE=true to enable)")

    
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