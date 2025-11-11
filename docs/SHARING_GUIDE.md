# Social Media Sharing Guide

## Overview

Module 5 (NiruShare) provides intelligent formatting and sharing of AmaniQuery responses to social media platforms.

## Supported Platforms

### 1. X (Twitter)
- **Character Limit:** 280 per tweet
- **Thread Support:** Yes (automatic for long answers)
- **Hashtags:** Up to 3 optimized hashtags
- **Best For:** Quick insights, breaking news, threads

### 2. LinkedIn
- **Character Limit:** 3000
- **Optimal Length:** ~1300 characters
- **Format:** Professional with key takeaways
- **Best For:** Legal analysis, professional insights, detailed research

### 3. Facebook
- **Character Limit:** None (but optimized for ~500 chars)
- **Format:** Engaging with call-to-action
- **Best For:** Accessible explanations, community engagement

## API Endpoints

### `POST /share/format`
Format a response for a specific platform.

**Request:**
```json
{
  "answer": "The Kenyan Constitution protects freedom of expression under Article 33...",
  "sources": [
    {
      "title": "Constitution of Kenya 2010",
      "url": "https://example.com",
      "category": "Kenyan Law"
    }
  ],
  "platform": "twitter",
  "query": "What does the Constitution say about free speech?",
  "include_hashtags": true
}
```

**Response:**
```json
{
  "platform": "twitter",
  "content": ["Tweet 1...", "Tweet 2...", "Tweet 3..."],
  "character_count": null,
  "hashtags": ["#KenyanLaw", "#Kenya", "#Constitution"],
  "metadata": {
    "format": "thread",
    "tweet_count": 3
  }
}
```

### `POST /share/preview`
Preview formatted posts for all platforms at once.

**Request:**
```json
{
  "answer": "Recent parliamentary debates...",
  "sources": [...],
  "query": "Recent Parliament debates?"
}
```

**Response:**
```json
{
  "twitter": {...},
  "linkedin": {...},
  "facebook": {...}
}
```

### `POST /share/generate-link`
Generate a platform-specific share link.

**Request:**
```json
{
  "platform": "twitter",
  "content": "Your formatted tweet",
  "url": "https://amaniquery.ke/query/123"
}
```

**Response:**
```json
{
  "platform": "twitter",
  "share_url": "https://twitter.com/intent/tweet?text=...",
  "instructions": "Click to open Twitter with pre-filled text..."
}
```

### `GET /share/platforms`
Get list of supported platforms and their limits.

## Usage Examples

### Example 1: Twitter Thread

```python
import requests

API_BASE = "http://localhost:8000"

# Get answer from AmaniQuery
query_result = requests.post(f"{API_BASE}/query", json={
    "query": "What are Kenya's data protection laws?",
    "top_k": 5
}).json()

# Format for Twitter
twitter_post = requests.post(f"{API_BASE}/share/format", json={
    "answer": query_result["answer"],
    "sources": query_result["sources"],
    "platform": "twitter",
    "query": "What are Kenya's data protection laws?"
}).json()

# Print thread
if twitter_post["metadata"]["format"] == "thread":
    print(f"Created thread with {twitter_post['metadata']['tweet_count']} tweets:\n")
    for i, tweet in enumerate(twitter_post["content"], 1):
        print(f"Tweet {i}:")
        print(tweet)
        print(f"({len(tweet)} characters)\n")
```

### Example 2: LinkedIn Professional Post

```python
# Format for LinkedIn
linkedin_post = requests.post(f"{API_BASE}/share/format", json={
    "answer": query_result["answer"],
    "sources": query_result["sources"],
    "platform": "linkedin",
    "query": "What are Kenya's data protection laws?",
    "include_hashtags": True
}).json()

print("LinkedIn Post:")
print("=" * 80)
print(linkedin_post["content"])
print("=" * 80)
print(f"Character count: {linkedin_post['character_count']}")
print(f"Hashtags: {', '.join(linkedin_post['hashtags'])}")
```

### Example 3: Multi-Platform Preview

```python
# Preview all platforms at once
preview = requests.post(f"{API_BASE}/share/preview", json={
    "answer": query_result["answer"],
    "sources": query_result["sources"],
    "query": "What are Kenya's data protection laws?"
}).json()

print("TWITTER:", preview["twitter"]["metadata"].get("tweet_count", 1), "tweets")
print("LINKEDIN:", preview["linkedin"]["character_count"], "chars")
print("FACEBOOK:", preview["facebook"]["metadata"]["word_count"], "words")
```

## Smart Features

### 1. Automatic Thread Creation
Long answers are automatically split into Twitter threads:
- First tweet: Question + intro
- Middle tweets: Key points (numbered)
- Last tweet: Sources + hashtags

### 2. Hashtag Generation
Platform-appropriate hashtags based on:
- Content category (Parliament, Law, News)
- Keywords (AI, Technology, Policy)
- Always includes #Kenya

### 3. Smart Truncation
Text is truncated at:
- Sentence boundaries (when possible)
- Word boundaries (fallback)
- Never cuts mid-word

### 4. Source Attribution
All posts include proper source citations:
- Twitter: URLs in last tweet
- LinkedIn: Full reference section
- Facebook: Learn more section

## Best Practices

### Twitter/X
✅ Keep first tweet engaging
✅ Use threads for detailed answers
✅ Include 2-3 relevant hashtags
✅ Always cite sources in last tweet

❌ Don't exceed 280 chars per tweet
❌ Don't use too many hashtags
❌ Don't forget to thread long content

### LinkedIn
✅ Use professional tone
✅ Include key takeaways section
✅ Full source citations
✅ Use 5-10 relevant hashtags

❌ Don't exceed 3000 characters
❌ Don't use casual language
❌ Don't skip source attribution

### Facebook
✅ Engaging opening
✅ Include call-to-action
✅ Use emojis appropriately
✅ Keep it accessible

❌ Don't be too formal
❌ Don't use too many hashtags
❌ Don't make it too long

## Workflow

1. **Query AmaniQuery** → Get answer with sources
2. **Preview All Platforms** → See how it looks everywhere
3. **Choose Platform** → Format for specific platform
4. **Generate Share Link** → Get shareable URL
5. **Post** → Share to your audience!

## Advanced: Custom Formatting

You can also format manually using the service:

```python
from Module5_NiruShare import ShareService

service = ShareService()

# Format for specific platform
formatted = service.format_for_platform(
    answer="Your answer",
    sources=[...],
    platform="twitter",
    query="Your question",
    include_hashtags=True
)

# Get statistics
stats = service.get_platform_stats(formatted)
print(f"Tweet count: {stats['tweet_count']}")
print(f"Total characters: {stats['total_characters']}")
```

## Error Handling

The API returns clear errors:

```python
# Invalid platform
response = requests.post(f"{API_BASE}/share/format", json={
    "answer": "...",
    "sources": [],
    "platform": "instagram"  # Not supported
})
# Returns: 400 Bad Request - "Unsupported platform: instagram"

# Missing required field
response = requests.post(f"{API_BASE}/share/format", json={
    "sources": [],
    "platform": "twitter"
    # Missing "answer"
})
# Returns: 422 Validation Error
```

## Integration Tips

### Frontend Integration
```javascript
// JavaScript example
async function shareToTwitter(answer, sources, query) {
  const response = await fetch('http://localhost:8000/share/format', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      answer,
      sources,
      platform: 'twitter',
      query,
      include_hashtags: true
    })
  });
  
  const formatted = await response.json();
  
  // Display thread
  formatted.content.forEach((tweet, i) => {
    console.log(`Tweet ${i + 1}: ${tweet}`);
  });
}
```

### Webhook Integration
Set up webhooks to auto-share new insights:
```python
# After processing new data
result = rag_pipeline.query("Latest parliamentary news")

# Auto-format for all platforms
preview = share_service.preview_all_platforms(
    result["answer"],
    result["sources"],
    "Latest parliamentary news"
)

# Post to your social accounts (use respective APIs)
# twitter_api.post_thread(preview["twitter"]["content"])
# linkedin_api.post(preview["linkedin"]["content"])
```

## See Also

- [Main README](../README.md)
- [API Documentation](../Module4_NiruAPI/README.md)
- [Example Usage](../examples/example_sharing.py)
