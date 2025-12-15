#!/usr/bin/env python3
"""
AmaniQuery API and Scheduler Startup Script

This script starts the AmaniQuery API and Crawler Scheduler concurrently.
Voice functionality is now handled via REST API endpoints (no LiveKit).
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
    is_huggingface = os.getenv("SPACE_ID") is not None
    is_windows = platform.system() == "Windows"
    
    if is_render or is_huggingface:
        # Always disable reload on cloud platforms for reliable port binding
        reload_enabled = False
        logger.info("🔧 Running on cloud platform - reload disabled for reliability")
    elif is_windows:
        reload_enabled = os.getenv("API_RELOAD", "False").lower() == "true"
        if reload_enabled:
            logger.warning("⚠️  Reload enabled on Windows may cause import issues")
            logger.warning("   Consider setting API_RELOAD=False")
    else:
        reload_enabled = os.getenv("API_RELOAD", "True").lower() == "true"

    # Check auth module configuration
    auth_enabled = os.getenv("ENABLE_AUTH", "false").lower() == "true"
    
    # Check voice configuration
    vibevoice_enabled = os.getenv("VIBEVOICE_MODEL_PATH", "") != "" or True  # Always enabled
    
    logger.info(f"📍 API Server: http://{host}:{port}")
    logger.info(f"📚 API Docs: http://{host}:{port}/docs")
    logger.info(f"🔧 Provider: {os.getenv('LLM_PROVIDER', 'moonshot')}")
    logger.info(f"🔄 Reload: {'Enabled' if reload_enabled else 'Disabled'}")
    logger.info(f"🔐 Auth Module: {'Enabled' if auth_enabled else 'Disabled'}")
    logger.info(f"🎤 Voice (VibeVoice): {'Enabled' if vibevoice_enabled else 'Disabled'}")
    
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
    """Start API and Scheduler"""
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
    
    # Check auth module configuration
    auth_enabled = os.getenv("ENABLE_AUTH", "false").lower() == "true"
    database_url = os.getenv("DATABASE_URL", "").strip()
    
    # Log auth module configuration status
    print("\n🔐 Authentication Module Configuration:")
    print(f"   Enabled: {auth_enabled}")
    print(f"   DATABASE_URL: {'✔ Set' if database_url else '✗ Not set'}")
    if auth_enabled and not database_url:
        print("   ⚠️  Warning: DATABASE_URL required for auth module")
    if auth_enabled:
        print("   💡 Tip: Run 'python migrate_auth_db.py' to create auth tables")
    
    # Log voice configuration
    print("\n🎤 Voice Module Configuration:")
    print("   Provider: VibeVoice (microsoft/VibeVoice-Realtime-0.5B)")
    print(f"   Device: {os.getenv('VIBEVOICE_DEVICE', 'auto')}")
    print(f"   Default Voice: {os.getenv('VIBEVOICE_VOICE', 'Wayne')}")
    print("   Endpoints: /api/v1/voice/speak, /api/v1/voice/chat")
    
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