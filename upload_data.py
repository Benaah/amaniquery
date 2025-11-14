#!/usr/bin/env python3
"""
Script to upload processed data from JSONL files to PostgreSQL database
and configure cloud database settings from environment variables.
"""

import os
import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional
from datetime import datetime
import psycopg2
from psycopg2.extras import execute_values
import numpy as np

# Load environment variables from .env file
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv not available, rely on system environment variables

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DatabaseUploader:
    """Handles uploading processed data to PostgreSQL database."""

    def __init__(self, db_config: Dict[str, Any]):
        """Initialize database connection.

        Args:
            db_config: Database configuration dictionary
        """
        self.db_config = db_config
        self.connection = None

    def connect(self):
        """Establish database connection."""
        try:
            self.connection = psycopg2.connect(**self.db_config)
            self.connection.autocommit = False  # Use transactions
            logger.info("Successfully connected to PostgreSQL database")
        except Exception as e:
            logger.error(f"Failed to connect to database: {e}")
            raise

    def disconnect(self):
        """Close database connection."""
        if self.connection:
            self.connection.close()
            logger.info("Database connection closed")

    def create_tables_if_not_exist(self):
        """Create necessary tables if they don't exist."""
        create_raw_table = """
        CREATE TABLE IF NOT EXISTS raw_documents (
            id SERIAL PRIMARY KEY,
            url TEXT,
            title TEXT,
            content TEXT,
            content_type TEXT,
            category TEXT,
            source_name TEXT,
            publication_date DATE,
            crawl_date TIMESTAMP,
            raw_html TEXT,
            status_code INTEGER,
            language TEXT,
            pdf_path TEXT,
            metadata_json JSONB,
            processed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """

        create_processed_table = """
        CREATE TABLE IF NOT EXISTS processed_chunks (
            id SERIAL PRIMARY KEY,
            text TEXT NOT NULL,
            chunk_id TEXT UNIQUE NOT NULL,
            chunk_index INTEGER,
            total_chunks INTEGER,
            url TEXT,
            title TEXT,
            category TEXT,
            source_name TEXT,
            author TEXT,
            publication_date DATE,
            crawl_date TIMESTAMP,
            processed_at TIMESTAMP,
            keywords TEXT[],
            char_count INTEGER,
            word_count INTEGER,
            embedding TEXT,
            metadata_json JSONB
        );
        """

        try:
            with self.connection.cursor() as cursor:
                cursor.execute(create_raw_table)
                cursor.execute(create_processed_table)
                self.connection.commit()
                logger.info("Tables created or already exist")
        except Exception as e:
            logger.error(f"Failed to create tables: {e}")
            self.connection.rollback()
            raise

    def upload_processed_chunks(self, chunks_data: List[Dict[str, Any]]) -> int:
        """Upload processed chunks to database.

        Args:
            chunks_data: List of chunk dictionaries

        Returns:
            Number of chunks uploaded
        """
        if not chunks_data:
            logger.warning("No chunks data to upload")
            return 0

        # Prepare data for bulk insert
        values = []
        for chunk in chunks_data:
            # Convert embedding list to JSON string for storage
            embedding = chunk.get('embedding', [])
            if isinstance(embedding, list):
                embedding_json = json.dumps(embedding)
            else:
                embedding_json = json.dumps([])

            # Parse dates
            publication_date = None
            if chunk.get('publication_date'):
                try:
                    publication_date = datetime.fromisoformat(chunk['publication_date'].replace('Z', '+00:00'))
                except:
                    publication_date = None

            crawl_date = None
            if chunk.get('crawl_date'):
                try:
                    crawl_date = datetime.fromisoformat(chunk['crawl_date'].replace('Z', '+00:00'))
                except:
                    crawl_date = None

            # Create metadata_json from remaining fields
            metadata = {k: v for k, v in chunk.items() if k not in [
                'text', 'chunk_id', 'chunk_index', 'total_chunks', 'url', 'title',
                'category', 'source_name', 'author', 'publication_date', 'crawl_date',
                'embedding'
            ]}

            values.append((
                chunk.get('chunk_id', ''),
                None,  # doc_id (not available in processed data)
                chunk.get('url', ''),  # source_url
                chunk.get('title', ''),
                chunk.get('category', ''),
                chunk.get('source_name', ''),
                chunk.get('author'),
                publication_date,
                crawl_date,
                'text',  # content_type
                chunk.get('text', ''),
                chunk.get('chunk_index', 0),
                chunk.get('total_chunks', 1),
                embedding_json,
                json.dumps(metadata),
                datetime.now()  # created_at
            ))

        insert_query = """
        INSERT INTO processed_chunks (
            chunk_id, doc_id, source_url, title, category, source_name, author,
            publication_date, crawl_date, content_type, text, chunk_index,
            total_chunks, embedding, metadata_json, created_at
        ) VALUES %s
        ON CONFLICT (chunk_id) DO UPDATE SET
            doc_id = EXCLUDED.doc_id,
            source_url = EXCLUDED.source_url,
            title = EXCLUDED.title,
            category = EXCLUDED.category,
            source_name = EXCLUDED.source_name,
            author = EXCLUDED.author,
            publication_date = EXCLUDED.publication_date,
            crawl_date = EXCLUDED.crawl_date,
            content_type = EXCLUDED.content_type,
            text = EXCLUDED.text,
            chunk_index = EXCLUDED.chunk_index,
            total_chunks = EXCLUDED.total_chunks,
            embedding = EXCLUDED.embedding,
            metadata_json = EXCLUDED.metadata_json
        """

        try:
            with self.connection.cursor() as cursor:
                execute_values(cursor, insert_query, values)
                self.connection.commit()
                logger.info(f"Successfully uploaded {len(values)} processed chunks")
                return len(values)
        except Exception as e:
            logger.error(f"Failed to upload processed chunks: {e}")
            self.connection.rollback()
            raise

    def upload_raw_documents(self, raw_data: List[Dict[str, Any]]) -> int:
        """Upload raw documents to database.

        Args:
            raw_data: List of raw document dictionaries

        Returns:
            Number of documents uploaded
        """
        if not raw_data:
            logger.warning("No raw documents data to upload")
            return 0

        values = []
        for doc in raw_data:
            # For raw documents, the content is HTML and we have metadata
            content = doc.get('content', '')
            url = doc.get('url', '')
            status_code = doc.get('status_code', 200)
            language = doc.get('language', 'en')

            # Parse crawl_date if available
            crawl_date = None
            if doc.get('crawl_date'):
                try:
                    crawl_date = datetime.fromisoformat(doc['crawl_date'].replace('Z', '+00:00'))
                except:
                    crawl_date = None

            # Create metadata_json from remaining fields
            metadata = {k: v for k, v in doc.items() if k not in [
                'content', 'url', 'status_code', 'language', 'crawl_date'
            ]}

            values.append((
                url,  # source_url
                None,  # title
                'Unknown',  # category
                'Parliament of Kenya',  # source_name
                None,  # author
                None,  # publication_date
                crawl_date,  # crawl_date
                'html',  # content_type
                content,  # raw_content
                content,  # raw_html
                None,  # pdf_path
                json.dumps(metadata),  # metadata_json
                False,  # processed
                datetime.now(),  # created_at
                datetime.now()  # updated_at
            ))

        insert_query = """
        INSERT INTO raw_documents (
            source_url, title, category, source_name, author,
            publication_date, crawl_date, content_type, raw_content, raw_html,
            pdf_path, metadata_json, processed, created_at, updated_at
        ) VALUES %s
        """

        try:
            with self.connection.cursor() as cursor:
                execute_values(cursor, insert_query, values)
                self.connection.commit()
                logger.info(f"Successfully uploaded {len(values)} raw documents")
                return len(values)
        except Exception as e:
            logger.error(f"Failed to upload raw documents: {e}")
            self.connection.rollback()
            raise

def load_jsonl_file(file_path: Path) -> List[Dict[str, Any]]:
    """Load data from a JSONL file.

    Args:
        file_path: Path to the JSONL file

    Returns:
        List of dictionaries from the file
    """
    data = []
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                if line:
                    try:
                        data.append(json.loads(line))
                    except json.JSONDecodeError as e:
                        logger.warning(f"Skipping invalid JSON at line {line_num} in {file_path}: {e}")
                        continue
        logger.info(f"Loaded {len(data)} records from {file_path}")
    except Exception as e:
        logger.error(f"Failed to load {file_path}: {e}")
        raise
    return data

def get_database_config_from_env() -> Dict[str, Any]:
    """Get database configuration from environment variables.

    Returns:
        Database configuration dictionary
    """
    # Try to parse DATABASE_URL first
    database_url = os.getenv('DATABASE_URL')
    if database_url:
        try:
            # Parse postgresql://user:password@host:port/database?params
            import re
            # Remove query parameters first
            url_without_params = database_url.split('?')[0]
            match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', url_without_params)
            if match:
                user, password, host, port, database = match.groups()
                return {
                    'host': host,
                    'port': int(port),
                    'database': database,
                    'user': user,
                    'password': password,
                }
        except Exception as e:
            logger.warning(f"Failed to parse DATABASE_URL: {e}")

    # Fall back to individual environment variables
    config = {
        'host': os.getenv('DB_HOST') or os.getenv('PGHOST', 'localhost'),
        'port': int(os.getenv('DB_PORT') or os.getenv('PGPORT', '5432')),
        'database': os.getenv('DB_NAME') or os.getenv('PGDATABASE', 'amaniquery'),
        'user': os.getenv('DB_USER') or os.getenv('PGUSER', 'postgres'),
        'password': os.getenv('DB_PASSWORD') or os.getenv('PGPASSWORD', ''),
    }

    # Validate required fields
    required = ['database', 'user', 'password']
    missing = [k for k in required if not config.get(k)]
    if missing:
        raise ValueError(f"Missing required environment variables: {missing}")

    return config

def setup_cloud_configs(uploader: DatabaseUploader):
    """Set up cloud database configurations from environment variables."""
    cloud_configs = {}

    # Upstash Redis
    if os.getenv('UPSTASH_REDIS_URL'):
        cloud_configs['upstash'] = {
            'url': os.getenv('UPSTASH_REDIS_URL'),
            'token': os.getenv('UPSTASH_REDIS_TOKEN', ''),
        }

    # QDrant
    if os.getenv('QDRANT_URL'):
        cloud_configs['qdrant'] = {
            'url': os.getenv('QDRANT_URL'),
            'api_key': os.getenv('QDRANT_API_KEY', ''),
            'collection_name': os.getenv('QDRANT_COLLECTION', 'amani_query'),
        }

    # Elasticsearch
    if os.getenv('ELASTICSEARCH_URL'):
        cloud_configs['elasticsearch'] = {
            'url': os.getenv('ELASTICSEARCH_URL'),
            'username': os.getenv('ELASTICSEARCH_USERNAME', ''),
            'password': os.getenv('ELASTICSEARCH_PASSWORD', ''),
            'index_name': os.getenv('ELASTICSEARCH_INDEX', 'amani_query'),
        }

    # Azure resources would go here if needed
    # if os.getenv('AZURE_STORAGE_CONNECTION_STRING'):
    #     cloud_configs['azure_storage'] = {...}

    # Save configurations using the config manager
    try:
        from config_manager import ConfigManager
        config_manager = ConfigManager()
        for service, config in cloud_configs.items():
            config_manager.set_config(f"{service}_config", config)
        logger.info(f"Configured {len(cloud_configs)} cloud services")
    except ImportError:
        logger.warning("ConfigManager not available, skipping cloud config setup")
    except Exception as e:
        logger.error(f"Failed to set up cloud configs: {e}")

def main():
    """Main function to upload data to database."""
    # Get database configuration
    try:
        db_config = get_database_config_from_env()
    except ValueError as e:
        logger.error(f"Database configuration error: {e}")
        return

    # Initialize uploader
    uploader = DatabaseUploader(db_config)

    try:
        # Connect to database
        uploader.connect()

        # Create tables if needed
        uploader.create_tables_if_not_exist()

        # Set up cloud configurations
        setup_cloud_configs(uploader)

        # Define data directories
        data_dir = Path("data")
        processed_dir = data_dir / "embeddings" / "processed"
        raw_dir = data_dir / "raw"

        total_processed = 0
        total_raw = 0

        # Upload processed data
        if processed_dir.exists():
            logger.info(f"Processing processed data from {processed_dir}")
            for jsonl_file in processed_dir.glob("*.jsonl"):
                logger.info(f"Loading {jsonl_file}")
                chunks_data = load_jsonl_file(jsonl_file)
                if chunks_data:
                    uploaded = uploader.upload_processed_chunks(chunks_data)
                    total_processed += uploaded
        else:
            logger.warning(f"Processed data directory not found: {processed_dir}")

        # Upload raw data (optional)
        if raw_dir.exists():
            logger.info(f"Processing raw data from {raw_dir}")
            for jsonl_file in raw_dir.glob("*.jsonl"):
                logger.info(f"Loading {jsonl_file}")
                raw_data = load_jsonl_file(jsonl_file)
                if raw_data:
                    uploaded = uploader.upload_raw_documents(raw_data)
                    total_raw += uploaded
        else:
            logger.warning(f"Raw data directory not found: {raw_dir}")

        logger.info(f"Upload complete: {total_processed} processed chunks, {total_raw} raw documents")

    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise
    finally:
        uploader.disconnect()

if __name__ == "__main__":
    main()