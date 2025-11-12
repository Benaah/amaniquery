"""
Vercel-compatible entry point for FastAPI application
"""
import sys
import os
from pathlib import Path

# Add the parent directory to the path so we can import modules
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from Module4_NiruAPI.api import app
    from fastapi.middleware.cors import CORSMiddleware

    # Vercel-specific CORS configuration
    cors_origins = os.getenv("CORS_ORIGINS", "https://amaniquery.vercel.app,https://api-amaniquery.vercel.app")
    origins = [origin.strip() for origin in cors_origins.split(",")]

    # Update CORS middleware for Vercel
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

except ImportError as e:
    # Fallback: create a minimal FastAPI app if imports fail
    from fastapi import FastAPI
    from fastapi.middleware.cors import CORSMiddleware

    app = FastAPI(title="AmaniQuery API", description="Fallback API")

    cors_origins = os.getenv("CORS_ORIGINS", "https://amaniquery.vercel.app,https://api-amaniquery.vercel.app")
    origins = [origin.strip() for origin in cors_origins.split(",")]

    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.get("/")
    async def root():
        return {"message": "AmaniQuery API", "status": "fallback_mode", "error": str(e)}

    @app.get("/health")
    async def health():
        return {"status": "fallback", "error": str(e)}