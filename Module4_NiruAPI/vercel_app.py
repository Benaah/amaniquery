"""
Vercel-compatible entry point for FastAPI application
"""
from Module4_NiruAPI.api import app
from fastapi.middleware.cors import CORSMiddleware
import os

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

# Export the app for Vercel
app = app