"""
Twitter/X formatter
"""
from typing import List, Dict, Optional
from .base_formatter import BaseFormatter


class TwitterFormatter(BaseFormatter):
    """Format responses for X (Twitter)"""
    
    # Twitter character limits
    SINGLE_TWEET_LIMIT = 280
    TWEET_WITH_LINK_LIMIT = 257  # Reserve space for URL
    
    def __init__(self):
        super().__init__(char_limit=self.SINGLE_TWEET_LIMIT)
    
    def format_post(
        self,
        answer: str,
        sources: List[Dict],
        query: Optional[str] = None,
        include_hashtags: bool = True,
    ) -> Dict:
        """
        Format response for Twitter/X
        
        Returns thread if answer is too long for single tweet
        """
        # Generate hashtags
        hashtags = self._generate_hashtags(answer, sources) if include_hashtags else []
        hashtag_text = " " + " ".join(hashtags[:3]) if hashtags else ""
        
        # Try single tweet first
        single_tweet = self._format_single_tweet(answer, sources, hashtag_text, query)
        
        if len(single_tweet) <= self.SINGLE_TWEET_LIMIT:
            return {
                "platform": "twitter",
                "format": "single",
                "content": single_tweet,
                "character_count": len(single_tweet),
                "hashtags": hashtags[:3],
            }
        
        # Create thread
        thread = self._format_thread(answer, sources, hashtags, query)
        
        return {
            "platform": "twitter",
            "format": "thread",
            "content": thread,
            "tweet_count": len(thread),
            "hashtags": hashtags,
        }
    
    def _format_single_tweet(
        self,
        answer: str,
        sources: List[Dict],
        hashtag_text: str,
        query: Optional[str] = None
    ) -> str:
        """Format as single tweet"""
        # Reserve space for hashtags and source link
        source_link = ""
        if sources:
            source_link = f"\n\n🔗 {sources[0].get('url', '')[:23]}"
        
        available_space = self.SINGLE_TWEET_LIMIT - len(hashtag_text) - len(source_link)
        
        # Add query if provided
        prefix = ""
        if query:
            prefix = f"Q: {query}\n\nA: "
            available_space -= len(prefix)
        
        # Truncate answer
        truncated_answer = self._truncate_smart(answer, available_space)
        
        return f"{prefix}{truncated_answer}{source_link}{hashtag_text}".strip()
    
    def _format_thread(
        self,
        answer: str,
        sources: List[Dict],
        hashtags: List[str],
        query: Optional[str] = None
    ) -> List[str]:
        """Format as Twitter thread"""
        tweets = []
        
        # First tweet: Query + intro
        if query:
            intro = f"❓ {query}\n\n🧵 Thread 👇"
            tweets.append(intro)
        else:
            intro = "🧵 Here's what I found:\n\n👇"
            tweets.append(intro)
        
        # Split answer into tweet-sized chunks
        key_points = self._extract_key_points(answer, max_points=5)
        
        for i, point in enumerate(key_points, 1):
            # Reserve space for numbering
            numbering = f"{i}/{len(key_points)} "
            available = self.SINGLE_TWEET_LIMIT - len(numbering) - 20  # margin
            
            tweet_content = self._truncate_smart(point, available)
            tweets.append(f"{numbering}{tweet_content}")
        
        # Last tweet: Sources and hashtags
        sources_text = "📚 Sources:\n"
        for i, source in enumerate(sources[:2], 1):
            title = source.get('title', 'Untitled')[:40]
            url = source.get('url', '')[:23]
            sources_text += f"{i}. {title}... {url}\n"
        
        hashtag_text = " ".join(hashtags[:5])
        last_tweet = f"{sources_text}\n{hashtag_text}".strip()
        
        if len(last_tweet) <= self.SINGLE_TWEET_LIMIT:
            tweets.append(last_tweet)
        else:
            # Split sources and hashtags if needed
            tweets.append(sources_text.strip())
            if hashtag_text:
                tweets.append(hashtag_text)
        
        return tweets
    
    def format_quote_tweet(self, answer: str, original_tweet_url: str) -> str:
        """Format as quote tweet"""
        available = self.TWEET_WITH_LINK_LIMIT - len(original_tweet_url) - 10
        
        truncated = self._truncate_smart(answer, available)
        return f"{truncated}\n\n💬 {original_tweet_url}"
