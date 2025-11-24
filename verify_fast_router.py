import os
import sys
import asyncio
from dotenv import load_dotenv

# Add project root to path
sys.path.insert(0, os.getcwd())

from Module4_NiruAPI.agents.ak_rag_graph import create_ak_rag_graph, execute_pipeline
from Module4_NiruAPI.rag_pipeline import RAGPipeline
from Module3_NiruDB.vector_store import VectorStore
from Module4_NiruAPI.agents.retrieval_strategies import UnifiedRetriever

# Load env
load_dotenv()

async def verify_router():
    print("🚀 Verifying Fast Intent Router...")
    
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
    fast_llm_callable = None
    try:
        if gemini_key:
            import google.generativeai as genai
            genai.configure(api_key=gemini_key)
            flash_model = genai.GenerativeModel('gemini-1.5-flash')
            def gemini_wrapper(prompt, **kwargs):
                try:
                    return flash_model.generate_content(prompt).text
                except Exception as e:
                    print(f"❌ Gemini Wrapper Error: {e}")
                    raise e
            fast_llm_callable = gemini_wrapper
            print("✅ Initialized Gemini 1.5 Flash wrapper")
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
            fast_llm_callable = openrouter_wrapper
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
    print("\nCreating graph with fast_llm_client...")
    graph = create_ak_rag_graph(
        llm_client=MockLLM(),
        vector_db_client=MockVectorDB(),
        fast_llm_client=fast_llm_callable
    )
    
    # Test Query
    query = "Naskia kuna tax mpya kwa bodaboda?"
    print(f"\nTesting Query: '{query}'")
    
    result = execute_pipeline(graph, query)
    
    print("\n📊 Results:")
    print(f"Query Type: {result['metadata']['query_type']}")
    print(f"Confidence: {result['metadata']['confidence']}")
    print(f"Reasoning: {result['response'].get('routing_reasoning', 'N/A')}")
    print(f"Pipeline Error: {result['metadata'].get('error')}")
    
    # Check if we got a real classification or fallback
    if result['metadata']['confidence'] == 0.5:
        print("❌ Router failed (Fallback used)")
    else:
        print("✅ Router worked")

    print(f"Language: {result['metadata'].get('has_sheng')}")
    print(f"Total Time: {result['metadata']['total_time_seconds']:.2f}s")
    
    if result['metadata']['total_time_seconds'] < 2.0:
        print("\n✅ Speed Test PASSED (< 2s)")
    else:
        print("\n⚠️ Speed Test WARNING (> 2s)")

if __name__ == "__main__":
    asyncio.run(verify_router())
