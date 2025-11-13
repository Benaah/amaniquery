"""
Populate vector database from processed data
"""
import sys
import json
from pathlib import Path
from loguru import logger
from tqdm import tqdm
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

sys.path.insert(0, str(Path(__file__).parent.parent))

from Module3_NiruDB.vector_store import VectorStore
from Module4_NiruAPI.config_manager import ConfigManager


def main():
    """Load processed data into vector databases and Elasticsearch"""
    print("=" * 60)
    print("💾 Populating Databases")
    print("=" * 60)

    # Initialize config manager (optional - fallback to env vars)
    config_manager = None
    try:
        config_manager = ConfigManager()
        print("✅ ConfigManager initialized")
    except Exception as e:
        print(f"⚠️  ConfigManager not available ({e}), using environment variables")
        config_manager = None

    # Initialize vector stores for different backends
    vector_stores = []

    # Try to initialize Upstash Vector Store
    try:
        print("🔄 Initializing Upstash Vector Store...")
        upstash_store = VectorStore(
            backend="upstash",
            collection_name="amaniquery_docs",
            config_manager=config_manager
        )
        vector_stores.append(("Upstash", upstash_store))
        print("✅ Upstash Vector Store initialized")
    except Exception as e:
        print(f"❌ Failed to initialize Upstash: {e}")

    # Try to initialize QDrant Vector Store
    try:
        print("🔄 Initializing QDrant Vector Store...")
        qdrant_store = VectorStore(
            backend="qdrant",
            collection_name="amaniquery_docs",
            config_manager=config_manager
        )
        vector_stores.append(("QDrant", qdrant_store))
        print("✅ QDrant Vector Store initialized")
    except Exception as e:
        print(f"❌ Failed to initialize QDrant: {e}")

    # Initialize ChromaDB as fallback
    try:
        print("🔄 Initializing ChromaDB Vector Store...")
        chromadb_store = VectorStore(
            backend="chromadb",
            collection_name="amaniquery_docs",
            config_manager=config_manager
        )
        vector_stores.append(("ChromaDB", chromadb_store))
        print("✅ ChromaDB Vector Store initialized")
    except Exception as e:
        print(f"❌ Failed to initialize ChromaDB: {e}")

    if not vector_stores:
        print("❌ Error: No vector stores could be initialized")
        print("   Please check your configuration and API keys")
        return

    print(f"\n📊 Initialized {len(vector_stores)} vector stores:")
    for name, store in vector_stores:
        print(f"   - {name}")

    # Find processed data
    processed_path = Path(__file__).parent.parent / "data" / "processed"

    if not processed_path.exists():
        print(f"❌ Error: Processed data directory not found")
        print(f"   Please run Module 2 (NiruParser) first")
        return

    # Find all processed JSONL files
    jsonl_files = list(processed_path.rglob("*_processed.jsonl"))

    if not jsonl_files:
        print(f"⚠️  No processed data files found")
        print(f"   Please run Module 2 (NiruParser) first")
        return

    print(f"\n📂 Found {len(jsonl_files)} processed files\n")

    total_chunks = 0
    total_files = 0

    for jsonl_file in tqdm(jsonl_files, desc="Processing files"):
        print(f"\n📄 Processing: {jsonl_file.name}")

        # Load chunks
        chunks = []
        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    chunks.append(json.loads(line))

        if chunks:
            print(f"   Adding {len(chunks)} chunks to databases...")

            # Add to each vector store
            for store_name, vector_store in vector_stores:
                try:
                    print(f"     → Adding to {store_name}...")
                    vector_store.add_documents(chunks)
                    print(f"     ✅ Added to {store_name}")
                except Exception as e:
                    print(f"     ❌ Failed to add to {store_name}: {e}")

            total_chunks += len(chunks)
            total_files += 1

    # Show stats for each vector store
    print("\n" + "=" * 60)
    print(f"✅ Database Population Complete!")
    print(f"📊 Total files processed: {total_files}")
    print(f"📊 Total chunks added: {total_chunks}")
    print(f"📊 Vector stores updated: {len(vector_stores)}")

    print(f"\n📈 Database Statistics:")
    for store_name, vector_store in vector_stores:
        try:
            stats = vector_store.get_stats()
            print(f"\n🔹 {store_name}:")
            print(f"   Backend: {stats.get('backend', 'unknown')}")
            print(f"   Collection: {stats.get('collection_name', 'unknown')}")
            print(f"   Total chunks: {stats.get('total_chunks', 'unknown')}")

            if stats.get('elasticsearch_enabled'):
                es_docs = stats.get('elasticsearch_docs', 0)
                print(f"   Elasticsearch docs: {es_docs}")

            if stats.get('persist_directory'):
                print(f"   Storage location: {stats['persist_directory']}")

            if stats.get('sample_categories'):
                print(f"   Categories: {', '.join(stats['sample_categories'].keys())}")

        except Exception as e:
            print(f"   ❌ Could not get stats: {e}")

    print("\n" + "=" * 60)
    print("🎉 All databases updated successfully!")
    print("   Data is now available in:")
    print("   - Vector databases (for semantic search)")
    print("   - Elasticsearch (for full-text search)")
    print("=" * 60)


if __name__ == "__main__":
    main()
