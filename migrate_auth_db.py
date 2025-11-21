#!/usr/bin/env python3
"""
Database Migration Script for Authentication System
Creates all necessary database tables for the auth system
"""
import os
import sys
from pathlib import Path
from sqlalchemy import text, inspect

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from Module3_NiruDB.chat_models import create_database_engine
from Module8_NiruAuth.models.auth_models import Base
from Module8_NiruAuth.models.blog_models import (
    BlogPost, BlogCategory, BlogTag,
    BlogPostCategory, BlogPostTag
)
from loguru import logger

def column_exists(conn, table_name: str, column_name: str) -> bool:
    """Check if a column exists in a table"""
    try:
        inspector = inspect(conn)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    except:
        return False

def add_missing_columns(engine):
    """Add missing columns to existing tables"""
    from sqlalchemy import text
    
    with engine.begin() as conn:
        # Add profile_image_url column to users table if it doesn't exist
        if not column_exists(conn, "users", "profile_image_url"):
            logger.info("Adding 'profile_image_url' column to users table...")
            try:
                conn.execute(text("""
                    ALTER TABLE users 
                    ADD COLUMN profile_image_url VARCHAR
                """))
                logger.info("✅ 'profile_image_url' column added to users table")
            except Exception as e:
                logger.error(f"❌ Failed to add 'profile_image_url' column: {e}")
                raise
        else:
            logger.info("✅ 'profile_image_url' column already exists in users table")

def table_exists(conn, table_name: str) -> bool:
    """Check if a table exists"""
    try:
        inspector = inspect(conn)
        return table_name in inspector.get_table_names()
    except:
        return False

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
        # Create engine
        engine = create_database_engine(database_url)
        
        # Create all auth tables
        logger.info("Creating authentication tables...")
        Base.metadata.create_all(engine)
        logger.info("✅ Authentication tables created/verified successfully!")
        
        # Create blog tables (they use the same Base)
        logger.info("Creating blog tables...")
        Base.metadata.create_all(engine)
        logger.info("✅ Blog tables created/verified successfully!")
        
        # Verify tables were created
        with engine.connect() as conn:
            inspector = inspect(conn)
            tables = inspector.get_table_names()
            
            required_tables = [
                "users", "roles", "user_roles", "integrations", "integration_roles",
                "api_keys", "oauth_clients", "oauth_tokens", "user_sessions",
                "permissions", "usage_logs", "rate_limits",
                "blog_posts", "blog_categories", "blog_tags",
                "blog_post_categories", "blog_post_tags"
            ]
            
            for table in required_tables:
                if table in tables:
                    logger.info(f"✅ Table '{table}' exists")
                else:
                    logger.warning(f"⚠️  Table '{table}' not found")
        
        # Add any missing columns to existing tables
        add_missing_columns(engine)
        
        # Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection test successful!")
        
        # Initialize default roles
        logger.info("Initializing default roles...")
        from Module8_NiruAuth.authorization.role_manager import RoleManager
        db_session = engine.connect()
        try:
            from sqlalchemy.orm import sessionmaker
            Session = sessionmaker(bind=engine)
            db = Session()
            try:
                RoleManager.get_or_create_default_roles(db)
                logger.info("✅ Default roles initialized!")
            finally:
                db.close()
        finally:
            db_session.close()

    except Exception as e:
        logger.error(f"❌ Migration failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    logger.info("🚀 Starting AmaniQuery authentication database migrations...")
    run_migrations()
    logger.info("🎉 Migrations completed successfully!")

