"""
Simple Vercel entrypoint for FastAPI
"""
import os

# Set up environment
os.environ.setdefault("CORS_ORIGINS", "https://amaniquery.vercel.app,https://api-amaniquery.vercel.app")

# Import the main app
from main import app

# Export for Vercel
app = app