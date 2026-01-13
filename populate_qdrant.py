"""
Populate QDrant vector database from processed data
Standalone script to fix population issues.
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

sys.path.insert(0, str(Path(__file__).parent))

from Module3_NiruDB.vector_store import VectorStore
from Module4_NiruAPI.config_manager import ConfigManager
from Module3_NiruDB.populate_db import determine_namespace

def main():
    """Load processed data into QDrant"""
    print("=" * 60)
    print("[START] Populating QDrant Database")
    print("=" * 60)

    # Initialize config manager
    try:
        config_manager = ConfigManager()
        print("[OK] ConfigManager initialized")
    except Exception as e:
        print(f"[WARN] ConfigManager not available ({e}), using environment variables")
        config_manager = None

    # Initialize QDrant Vector Store
    try:
        print("[INIT] Initializing QDrant Vector Store...")
        # Force backend to qdrant
        vector_store = VectorStore(
            backend="qdrant",
            collection_name="amaniquery_docs",
            config_manager=config_manager
        )
        print("[OK] QDrant Vector Store initialized")
    except Exception as e:
        print(f"[ERROR] Failed to initialize QDrant: {e}")
        return

    # Find processed data
    processed_path = Path(__file__).parent / "data" / "processed"

    if not processed_path.exists():
        print(f"[ERROR] Error: Processed data directory not found at {processed_path}")
        return

    # Find all processed JSONL files
    jsonl_files = list(processed_path.rglob("*_processed.jsonl"))

    if not jsonl_files:
        print(f"[WARN] No processed data files found in {processed_path}")
        return

    print(f"\n[INFO] Found {len(jsonl_files)} processed files\n")

    total_chunks = 0
    total_files = 0
    
    for jsonl_file in tqdm(jsonl_files, desc="Processing files"):
        print(f"\n[FILE] Processing: {jsonl_file.name}")

        # Load chunks
        chunks = []
        try:
            with open(jsonl_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        chunks.append(json.loads(line))
        except Exception as e:
            print(f"   [ERROR] Error reading file {jsonl_file.name}: {e}")
            continue

        if chunks:
            print(f"   Adding {len(chunks)} chunks to QDrant...")

            # Group the chunks by proper namespace
            namespace_map = {}
            for chunk in chunks:
                category = chunk.get("category", "Unknown")
                publication_date = chunk.get("publication_date", "")
                ns = determine_namespace(category, publication_date)
                if ns not in namespace_map:
                    namespace_map[ns] = []
                namespace_map[ns].append(chunk)

            # Add documents per namespace
            for namespace, ns_chunks in namespace_map.items():
                try:
                    print(f"     -> Adding to namespace '{namespace}' ({len(ns_chunks)} chunks)...")
                    vector_store.add_documents(ns_chunks, namespace=namespace)
                    print(f"     [OK] Added to namespace '{namespace}'")
                except Exception as e:
                    print(f"     [ERROR] Failed to add to namespace '{namespace}': {e}")

            total_chunks += len(chunks)
            total_files += 1

    print("\n" + "=" * 60)
    print(f"[OK] QDrant Population Complete!")
    print(f"[INFO] Total files processed: {total_files}")
    print(f"[INFO] Total chunks added: {total_chunks}")
    print("=" * 60)

if __name__ == "__main__":
    main()
