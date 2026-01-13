#!/usr/bin/env python3
"""
Test RAG Pipeline
"""
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from Module4_NiruAPI.rag_pipeline import RAGPipeline

def test_rag():
    print("Testing RAG Pipeline...")

    try:
        # Initialize pipeline
        pipeline = RAGPipeline()
        print("[OK] Pipeline initialized")

        # Test query
        query = "What is the Kenyan Constitution?"
        print(f"Query: {query}")

        result = pipeline.query(query)
        print(f"Answer: {repr(result['answer'])}")
        print(f"Answer length: {len(result['answer'])}")
        print(f"Retrieved chunks: {result['retrieved_chunks']}")
        print(f"Model used: {result['model_used']}")
        print(f"Query time: {result['query_time']:.2f}s")

        if result['sources']:
            print(f"Sources: {len(result['sources'])}")
            for i, src in enumerate(result['sources'][:2]):  # Show first 2
                print(f"  [{i+1}] {src['title']} ({src['category']})")

    except Exception as e:
        print(f"[ERROR] Error: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_rag()