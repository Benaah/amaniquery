"""
Process all raw data from Module1
"""
import sys
from pathlib import Path
from loguru import logger
from tqdm import tqdm

# Add parent to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from Module2_NiruParser.pipeline import ProcessingPipeline
from Module2_NiruParser.config import Config


def main():
    """Process all raw data files"""
    print("=" * 60)
    print("🔄 Starting Data Processing Pipeline")
    print("=" * 60)
    
    # Initialize pipeline
    config = Config()
    pipeline = ProcessingPipeline(config)
    
    # Configure logging
    logger.add(
        config.PROJECT_ROOT / "logs" / "processing.log",
        rotation="100 MB",
        level=config.LOG_LEVEL,
    )
    
    # Find all raw data files
    raw_data_path = config.RAW_DATA_PATH
    
    if not raw_data_path.exists():
        logger.error(f"Raw data path does not exist: {raw_data_path}")
        print(f"❌ Error: Raw data directory not found")
        print(f"   Please run Module 1 (NiruSpider) first")
        return
    
    # Find all JSONL files from crawlers
    jsonl_files = list(raw_data_path.rglob("*.jsonl"))
    
    if not jsonl_files:
        logger.warning("No JSONL files found in raw data directory")
        print(f"⚠️  No data files found in {raw_data_path}")
        print(f"   Please run Module 1 (NiruSpider) first")
        return
    
    print(f"\n📂 Found {len(jsonl_files)} data files to process\n")
    
    # Process each file
    total_chunks = 0
    
    for jsonl_file in tqdm(jsonl_files, desc="Processing files"):
        logger.info(f"Processing file: {jsonl_file.name}")
        print(f"\n📄 Processing: {jsonl_file.name}")
        
        # Load raw documents
        raw_docs = pipeline.load_raw_documents(jsonl_file)
        
        if not raw_docs:
            logger.warning(f"No documents found in {jsonl_file.name}")
            continue
        
        print(f"   Loaded {len(raw_docs)} documents")
        
        # Process documents
        all_chunks = []
        for doc in tqdm(raw_docs, desc="  Documents", leave=False):
            chunks = pipeline.process_document(doc)
            all_chunks.extend(chunks)
        
        if all_chunks:
            # Determine output filename
            category = all_chunks[0].get("category", "unknown")
            output_file = config.get_output_path(
                category,
                jsonl_file.stem + "_processed.jsonl"
            )
            
            # Save processed chunks
            pipeline.save_chunks(all_chunks, output_file)
            
            total_chunks += len(all_chunks)
            print(f"   ✅ Created {len(all_chunks)} chunks")
        else:
            print(f"   ⚠️  No chunks created")
    
    print("\n" + "=" * 60)
    print(f"✅ Processing Complete!")
    print(f"📊 Total chunks created: {total_chunks}")
    print(f"📁 Processed data saved to: {config.PROCESSED_DATA_PATH}")
    print("=" * 60)


if __name__ == "__main__":
    main()
