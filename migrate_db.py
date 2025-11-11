#!/usr/bin/env python3
"""
Database Migration Script for AmaniQuery
Creates all necessary database tables for the chat system
"""
import os
import sys
from pathlib import Path

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from Module3_NiruDB.chat_models import create_database_engine, create_tables
from loguru import logger

def run_migrations():
    """Run database migrations"""
    load_dotenv()

    # Get database URL from environment
    database_url = os.getenv("DATABASE_URL")
    if not database_url:
        logger.error("DATABASE_URL not found in environment variables")
        sys.exit(1)

    logger.info(f"Connecting to database: {database_url.split('@')[1] if '@' in database_url else 'local'}")

    try:
        # Create engine and tables
        engine = create_database_engine(database_url)
        create_tables(engine)

        logger.info("✅ Database tables created successfully!")

        # Test connection
        with engine.connect() as conn:
            result = conn.execute("SELECT 1")
            logger.info("✅ Database connection test successful!")

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    logger.info("🚀 Starting AmaniQuery database migrations...")
    run_migrations()
    logger.info("🎉 Migrations completed successfully!")