"""
Populate vector database from processed data
"""
import sys
import json
from pathlib import Path
from loguru import logger
from tqdm import tqdm

sys.path.insert(0, str(Path(__file__).parent.parent))

from Module3_NiruDB.vector_store import VectorStore


def main():
    """Load processed data into vector database"""
    print("=" * 60)
    print("💾 Populating Vector Database")
    print("=" * 60)
    
    # Initialize vector store
    vector_store = VectorStore()
    
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
    
    for jsonl_file in tqdm(jsonl_files, desc="Loading files"):
        print(f"\n📄 Loading: {jsonl_file.name}")
        
        # Load chunks
        chunks = []
        with open(jsonl_file, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    chunks.append(json.loads(line))
        
        if chunks:
            print(f"   Adding {len(chunks)} chunks to database...")
            vector_store.add_documents(chunks)
            total_chunks += len(chunks)
    
    # Show stats
    stats = vector_store.get_stats()
    
    print("\n" + "=" * 60)
    print(f"✅ Database Populated!")
    print(f"📊 Total chunks: {stats['total_chunks']}")
    print(f"📁 Database location: {stats['persist_directory']}")
    
    if stats.get("sample_categories"):
        print(f"\n📚 Categories:")
        for cat, count in stats["sample_categories"].items():
            print(f"   - {cat}: {count}+ documents")
    
    print("=" * 60)


if __name__ == "__main__":
    main()
