"""
Example: Parliament Video Indexer

This example demonstrates how to search Parliament YouTube videos
with timestamp-based citations.
"""
import requests
import json


API_URL = "http://localhost:8000"


def search_parliament_videos(query: str):
    """Search for query in parliament videos"""
    response = requests.post(
        f"{API_URL}/query",
        json={
            "query": query,
            "category": "Parliamentary Record",
            "top_k": 5,
            "include_sources": True
        }
    )
    
    if response.status_code == 200:
        return response.json()
    else:
        print(f"Error: {response.status_code}")
        print(response.text)
        return None


def print_video_results(result):
    """Print search results with video timestamps"""
    if not result:
        return
    
    print("\n" + "=" * 70)
    print(f"🎥 PARLIAMENT VIDEO SEARCH")
    print("=" * 70)
    
    print(f"\n❓ Query: {result.get('query', 'N/A')}")
    print(f"\n💬 ANSWER:")
    print("─" * 70)
    print(result.get('answer', 'No answer'))
    print("─" * 70)
    
    sources = result.get('sources', [])
    
    if not sources:
        print("\n📚 No video sources found")
        return
    
    print(f"\n📹 VIDEO SOURCES ({len(sources)}):")
    print()
    
    for i, source in enumerate(sources, 1):
        # Check if this is a video source
        if source.get('video_id'):
            print(f"{i}. 🎬 {source['title']}")
            print(f"   ⏱️  Timestamp: {source.get('timestamp_formatted', 'N/A')}")
            print(f"   🔗 Watch at: {source.get('timestamp_url', source['url'])}")
            print(f"   📝 Excerpt: {source['excerpt'][:150]}...")
            if source.get('relevance_score'):
                print(f"   📊 Relevance: {source['relevance_score']:.3f}")
        else:
            # Regular source
            print(f"{i}. 📄 {source['title']}")
            print(f"   🔗 {source['url']}")
            print(f"   📝 {source['excerpt'][:150]}...")
        
        print()
    
    print("=" * 70)


def main():
    """Run video search examples"""
    print("\n🎥 PARLIAMENT VIDEO INDEXER - Examples\n")
    print("Search Parliament YouTube videos with timestamp-based citations")
    print("Jump directly to the moment a topic was discussed!\n")
    
    # Example 1: Budget discussion
    print("\n1️⃣  Searching: Budget allocation for education")
    result = search_parliament_videos("budget allocation for education")
    print_video_results(result)
    
    # Example 2: Healthcare policy
    print("\n2️⃣  Searching: Healthcare policy debate")
    result = search_parliament_videos("healthcare policy and universal health coverage")
    print_video_results(result)
    
    # Example 3: Tax legislation
    print("\n3️⃣  Searching: Tax legislation discussion")
    result = search_parliament_videos("tax legislation and revenue collection")
    print_video_results(result)
    
    # Example 4: Climate change
    print("\n4️⃣  Searching: Climate change initiatives")
    result = search_parliament_videos("climate change and environmental protection")
    print_video_results(result)
    
    # Example 5: Speaker mentions
    print("\n5️⃣  Searching: Speaker rulings")
    result = search_parliament_videos("speaker ruling on procedure")
    print_video_results(result)
    
    print("\n" + "=" * 70)
    print("🎥 VIDEO INDEXER FEATURES")
    print("=" * 70)
    print("\n✅ Capabilities:")
    print("  • Searchable YouTube transcripts")
    print("  • Timestamp-based citations (jump to exact moment)")
    print("  • 60-second chunks with context")
    print("  • English and Swahili transcript support")
    print("  • Automatic transcript extraction")
    print("  • Vector search for semantic matching")
    
    print("\n📋 Use Cases:")
    print("  • Fact-check what MPs said on specific topics")
    print("  • Find exact moments in debate videos")
    print("  • Research legislative discussions")
    print("  • Quote MPs with timestamp citations")
    print("  • Monitor parliamentary proceedings")
    
    print("\n🔧 How It Works:")
    print("  1. Spider scrapes Parliament YouTube channels")
    print("  2. Transcript API extracts text with timestamps")
    print("  3. Chunks created (60s segments, 10s overlap)")
    print("  4. Each chunk indexed with start_time_seconds")
    print("  5. Search returns results with &t=XXs YouTube links")
    
    print("\n📊 Example Citation:")
    print("  'According to the Finance Committee discussion'")
    print("  '  at 15:42 in the parliamentary session:'")
    print("  '  https://youtube.com/watch?v=abc123&t=942s'")
    
    print("\n💡 Wow Factor:")
    print("  • First RAG system with YouTube timestamp citations!")
    print("  • Makes hours of video instantly searchable")
    print("  • Accountability through precise citations")
    print("  • Unique to AmaniQuery - no competitors have this")
    
    print("\n" + "=" * 70)
    print("✅ Video indexer examples complete!")
    print("=" * 70)


if __name__ == "__main__":
    main()
