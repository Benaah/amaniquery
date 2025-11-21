#!/usr/bin/env python3
"""
Database Reset Script for AmaniQuery
Drops all tables and recreates them with fresh migrations
"""
import os
import sys
from pathlib import Path
from sqlalchemy import text, inspect

# Add the project root to the Python path
sys.path.insert(0, str(Path(__file__).parent))

from dotenv import load_dotenv
from Module3_NiruDB.chat_models import create_database_engine, Base as ChatBase
from Module8_NiruAuth.models.auth_models import Base as AuthBase
from loguru import logger

def drop_all_tables(engine):
    """Drop all tables from the database"""
    logger.warning("⚠️  Dropping all tables from database...")
    try:
        # Get all table names from both bases
        with engine.connect() as conn:
            inspector = inspect(conn)
            all_tables = inspector.get_table_names()
            
            if all_tables:
                logger.info(f"Dropping {len(all_tables)} tables...")
                # Drop all tables with CASCADE to handle foreign key dependencies
                for table_name in all_tables:
                    try:
                        conn.execute(text(f'DROP TABLE IF EXISTS "{table_name}" CASCADE'))
                        logger.debug(f"Dropped table: {table_name}")
                    except Exception as e:
                        logger.warning(f"Error dropping table {table_name}: {e}")
                
                conn.commit()
                logger.info("✅ All tables dropped successfully!")
            else:
                logger.info("No tables to drop")
    except Exception as e:
        logger.error(f"❌ Error dropping tables: {e}")
        import traceback
        logger.error(traceback.format_exc())
        raise

def verify_tables(engine):
    """Verify that all required tables exist"""
    with engine.connect() as conn:
        inspector = inspect(conn)
        tables = inspector.get_table_names()
        
        required_tables = [
            # Chat tables
            "chat_sessions", "chat_messages", "user_feedback",
            # Auth tables
            "users", "roles", "user_roles", "integrations", "integration_roles",
            "api_keys", "oauth_clients", "oauth_tokens", "user_sessions",
            "permissions", "usage_logs", "rate_limits",
            # Blog tables
            "blog_posts", "blog_categories", "blog_tags",
            "blog_post_categories", "blog_post_tags"
        ]
        
        missing_tables = []
        for table in required_tables:
            if table in tables:
                logger.info(f"✅ Table '{table}' exists")
            else:
                logger.warning(f"⚠️  Table '{table}' not found")
                missing_tables.append(table)
        
        if missing_tables:
            logger.error(f"❌ Missing tables: {', '.join(missing_tables)}")
            return False
        
        logger.info("✅ All required tables verified!")
        return True

def run_chat_migrations(engine):
    """Run chat database migrations"""
    from Module3_NiruDB.chat_models import create_tables
    
    logger.info("Creating chat tables...")
    create_tables(engine)
    logger.info("✅ Chat tables created successfully!")
    
    # Add missing columns
    from sqlalchemy import inspect as sql_inspect
    
    def column_exists(conn, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table"""
        inspector = sql_inspect(conn)
        columns = [col['name'] for col in inspector.get_columns(table_name)]
        return column_name in columns
    
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

def run_auth_migrations(engine):
    """Run authentication database migrations"""
    from Module8_NiruAuth.models.blog_models import (
        BlogPost, BlogCategory, BlogTag,
        BlogPostCategory, BlogPostTag
    )
    
    logger.info("Creating authentication tables...")
    AuthBase.metadata.create_all(engine)
    logger.info("✅ Authentication tables created successfully!")
    
    # Create blog tables (they use the same Base)
    logger.info("Creating blog tables...")
    AuthBase.metadata.create_all(engine)
    logger.info("✅ Blog tables created successfully!")
    
    # Add missing columns
    from sqlalchemy import inspect as sql_inspect
    
    def column_exists(conn, table_name: str, column_name: str) -> bool:
        """Check if a column exists in a table"""
        try:
            inspector = sql_inspect(conn)
            columns = [col['name'] for col in inspector.get_columns(table_name)]
            return column_name in columns
        except:
            return False
    
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
    
    # Initialize default roles
    logger.info("Initializing default roles...")
    from Module8_NiruAuth.authorization.role_manager import RoleManager
    from sqlalchemy.orm import sessionmaker
    
    Session = sessionmaker(bind=engine)
    db = Session()
    try:
        RoleManager.get_or_create_default_roles(db)
        logger.info("✅ Default roles initialized!")
    finally:
        db.close()

def reset_database():
    """Reset database by dropping all tables and recreating them"""
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
        
        # Step 1: Drop all tables
        logger.warning("=" * 60)
        logger.warning("⚠️  WARNING: This will DELETE ALL DATA in the database!")
        logger.warning("=" * 60)
        drop_all_tables(engine)
        
        # Step 2: Create auth tables first (users table must exist before chat_sessions)
        logger.info("=" * 60)
        logger.info("Creating authentication tables...")
        logger.info("=" * 60)
        run_auth_migrations(engine)
        
        # Step 3: Create chat tables (can now reference users table)
        logger.info("=" * 60)
        logger.info("Creating chat tables...")
        logger.info("=" * 60)
        run_chat_migrations(engine)
        
        # Step 4: Verify all tables exist
        logger.info("=" * 60)
        logger.info("Verifying all tables...")
        logger.info("=" * 60)
        if not verify_tables(engine):
            logger.error("❌ Table verification failed!")
            sys.exit(1)
        
        # Step 5: Test connection
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            logger.info("✅ Database connection test successful!")
        
        logger.info("=" * 60)
        logger.info("🎉 Database reset completed successfully!")
        logger.info("=" * 60)
        
    except Exception as e:
        logger.error(f"❌ Database reset failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        sys.exit(1)

if __name__ == "__main__":
    logger.info("🚀 Starting AmaniQuery database reset...")
    reset_database()
    logger.info("✅ Database reset completed!")

