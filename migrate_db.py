#!/usr/bin/env python3
"""
Database Migration Script for AmaniQuery
Creates all necessary database tables for the chat system
"""
import os
import sys
from pathlib import Path
from sqlalchemy import text, inspect

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from Module3_NiruDB.chat_models import create_database_engine, create_tables
from loguru import logger

def column_exists(conn, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table"""
    inspector = inspect(conn)
    columns = [col['name'] for col in inspector.get_columns(table_name)]
    return column_name in columns

def add_missing_columns(engine):
    """Add missing columns to existing tables"""
    with engine.connect() as conn:
        # Check and add attachments column to chat_messages
        if not column_exists(conn, 'chat_messages', 'attachments'):
            logger.info("Adding 'attachments' column to chat_messages table...")
            conn.execute(text("""
                ALTER TABLE chat_messages 
                ADD COLUMN attachments JSON
            """))
            conn.commit()
            logger.info("✅ Added 'attachments' column to chat_messages")
        else:
            logger.info("✅ 'attachments' column already exists in chat_messages")

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
        
        # Create tables if they don't exist
        create_tables(engine)
        logger.info("✅ Database tables created/verified successfully!")

        # Add any missing columns to existing tables
        add_missing_columns(engine)

        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection test successful!")

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    logger.info("🚀 Starting AmaniQuery database migrations...")
    run_migrations()
    logger.info("🎉 Migrations completed successfully!")