#!/usr/bin/env python3
"""
AmaniQuery API Startup Script

This script provides a clean way to start the AmaniQuery API
without multiprocessing issues that can occur on Windows.
"""

import os
import sys
import platform
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Start the AmaniQuery API"""
    print("=" * 60)
    print("🚀 Starting AmaniQuery API (via startup script)")
    print("=" * 60)

    # Import uvicorn
    try:
        import uvicorn
    except ImportError:
        print("❌ uvicorn not found. Please install it with: pip install uvicorn")
        return 1

    # Get configuration
    host = os.getenv("API_HOST", "0.0.0.0")
    port = int(os.getenv("API_PORT", "8000"))

    # On Windows, disable reload by default to avoid multiprocessing issues
    is_windows = platform.system() == "Windows"
    if is_windows:
        reload_enabled = os.getenv("API_RELOAD", "False").lower() == "true"
        if reload_enabled:
            print("⚠️  Warning: Reload enabled on Windows may cause import issues")
            print("   Consider setting API_RELOAD=False")
    else:
        reload_enabled = os.getenv("API_RELOAD", "True").lower() == "true"

    print(f"📍 Server: http://{host}:{port}")
    print(f"📚 Docs: http://{host}:{port}/docs")
    print(f"🔧 Provider: {os.getenv('LLM_PROVIDER', 'moonshot')}")
    print(f"🔄 Reload: {'Enabled' if reload_enabled else 'Disabled'}")
    print("=" * 60)

    try:
        uvicorn.run(
            "Module4_NiruAPI.api:app",
            host=host,
            port=port,
            reload=reload_enabled,
        )
    except KeyboardInterrupt:
        print("\n👋 API server stopped")
        return 0
    except Exception as e:
        print(f"❌ Failed to start API server: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())