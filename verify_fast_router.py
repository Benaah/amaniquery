import os
import sys
import asyncio
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.getcwd())

from Module4_NiruAPI.agents.amaniq_v1 import create_amaniq_v1_graph, execute_pipeline
from Module4_NiruAPI.rag_pipeline import RAGPipeline
from Module3_NiruDB.vector_store import VectorStore
from Module4_NiruAPI.agents.retrieval_strategies import UnifiedRetriever

# Load env
load_dotenv()

async def verify_router():
    print("🚀 Verifying Fast Intent Router (Amaniq v1)...")
    
    # Check keys
    gemini_key = os.getenv("GEMINI_API_KEY")
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    
    if gemini_key:
        print(f"✅ GEMINI_API_KEY found (Priority 1)")
    elif openrouter_key:
        print(f"✅ OPENROUTER_API_KEY found (Priority 2)")
    else:
        print("❌ No fast LLM keys found!")
        return

    # Initialize Fast LLM
    fast_llm_client = None
    try:
        if gemini_key:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            # Using 2.0 Flash Experimental for best speed
            flash_model = genai.GenerativeModel('gemini-2.0-flash-exp')
            # Pass the model object directly (it has generate_content method)
            fast_llm_client = flash_model
            print("✅ Initialized Gemini 2.0 Flash (Experimental)")
        elif openrouter_key:
            from openai import OpenAI
            or_client = OpenAI(
                api_key=openrouter_key,
                base_url="https://openrouter.ai/api/v1"
            )
            def openrouter_wrapper(prompt, **kwargs):
                return or_client.chat.completions.create(
                    model="meta-llama/llama-3-70b-instruct",
                    messages=[{"role": "user", "content": prompt}]
                ).choices[0].message.content
            fast_llm_client = openrouter_wrapper
            print("✅ Initialized OpenRouter wrapper")
    except Exception as e:
        print(f"❌ Failed to init fast LLM: {e}")
        return

    # Mock other components
    class MockLLM:
        def chat(self, *args, **kwargs): return "Mock response"
        def generate(self, *args, **kwargs): return "Mock response"
        def __call__(self, *args, **kwargs): return "Mock response"

    class MockVectorDB:
        def retrieve(self, *args, **kwargs): return []

    # Create graph with fast LLM
    print("\nCreating Amaniq v1 graph with fast_llm_client...")
    graph = create_amaniq_v1_graph(
        llm_client=MockLLM(),
        vector_db_client=MockVectorDB(),
        fast_llm_client=fast_llm_client
    )
    
    # Test Query 1: Wanjiku/Sheng
    query1 = "Naskia kuna tax mpya kwa bodaboda?"
    print(f"\nTesting Query 1: '{query1}'")
    
    result1 = execute_pipeline(graph, query1)
    
    print("\n📊 Results 1:")
    print(f"Query Type: {result1['metadata']['query_type']}")
    print(f"Confidence: {result1['metadata']['confidence']}")
    print(f"Pipeline Error: {result1['metadata'].get('error')}")
    print(f"Web Search Used: {result1['metadata'].get('web_search_used')}")
    
    if result1['metadata']['confidence'] > 0.6:
        print("✅ Router worked")
    else:
        print("❌ Router failed (Low confidence/Fallback)")

    # Test Query 2: Mwanahabari (Should trigger search/research intent)
    query2 = "What are the latest amendments to the Finance Bill 2024?"
    print(f"\nTesting Query 2: '{query2}'")
    
    result2 = execute_pipeline(graph, query2)
    
    print("\n📊 Results 2:")
    print(f"Query Type: {result2['metadata']['query_type']}")
    print(f"Confidence: {result2['metadata']['confidence']}")
    print(f"Web Search Used: {result2['metadata'].get('web_search_used')}")
    
    if result2['metadata']['query_type'] == 'mwanahabari':
        print("✅ Correctly classified as mwanahabari")
    else:
        print(f"⚠️ Classified as {result2['metadata']['query_type']}")

    print(f"\nTotal Time (Q1): {result1['metadata']['total_time_seconds']:.2f}s")
    
    if result1['metadata']['total_time_seconds'] < 2.0:
        print("\n✅ Speed Test PASSED (< 2s)")
    else:
        print("\n⚠️ Speed Test WARNING (> 2s)")

if __name__ == "__main__":
    asyncio.run(verify_router())
