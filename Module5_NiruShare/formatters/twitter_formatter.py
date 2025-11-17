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
        # Validate input
        self._validate_input(answer, sources)
        
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
        # Reserve space for source link (more natural)
        source_link = ""
        if sources and isinstance(sources[0], dict):
            url = sources[0].get('url', '')
            if url:
                # More natural link format
                source_link = f"\n\n{url}"
        
        # Calculate available space more accurately
        base_space = self.SINGLE_TWEET_LIMIT
        base_space -= len(hashtag_text)
        base_space -= len(source_link)
        
        # Add query if provided 
        prefix = ""
        if query:
            query_text = str(query).strip()
            prefix = f"{query_text}\n\n"
            base_space -= len(prefix)
        
        # Ensure we have positive space
        available_space = max(50, base_space)  # Minimum 50 chars for content
        
        # Truncate answer
        truncated_answer = self._truncate_smart(answer, available_space)
        
        # Build tweet efficiently
        parts = []
        if prefix:
            parts.append(prefix)
        parts.append(truncated_answer)
        if source_link:
            parts.append(source_link)
        if hashtag_text:
            parts.append(hashtag_text)
        
        return "".join(parts).strip()
    
    def _format_thread(
        self,
        answer: str,
        sources: List[Dict],
        hashtags: List[str],
        query: Optional[str] = None
    ) -> List[str]:
        """Format as Twitter thread"""
        tweets = []
        
        # First tweet: Query + intro (more natural)
        if query:
            query_text = str(query).strip()
            intro = f"{query_text}\n\nA thread:"
        else:
            intro = "Here's what I found:\n\n"
        
        # Ensure intro fits
        if len(intro) > self.SINGLE_TWEET_LIMIT:
            intro = intro[:self.SINGLE_TWEET_LIMIT - 3] + "..."
        tweets.append(intro)
        
        # Split answer into tweet-sized chunks
        key_points = self._extract_key_points(answer, max_points=5)
        
        if not key_points:
            # Fallback: split answer into chunks
            chunk_size = self.SINGLE_TWEET_LIMIT - 30  # Reserve space for numbering
            words = answer.split()
            current_chunk = []
            current_length = 0
            
            for word in words:
                word_len = len(word) + 1  # +1 for space
                if current_length + word_len > chunk_size and current_chunk:
                    key_points.append(" ".join(current_chunk))
                    current_chunk = [word]
                    current_length = len(word)
                else:
                    current_chunk.append(word)
                    current_length += word_len
            
            if current_chunk:
                key_points.append(" ".join(current_chunk))
        
        # Format each point as a tweet
        total_points = len(key_points)
        for i, point in enumerate(key_points, 1):
            # Reserve space for numbering (e.g., "1/5 ")
            numbering = f"{i}/{total_points} "
            available = self.SINGLE_TWEET_LIMIT - len(numbering)
            
            tweet_content = self._truncate_smart(point, available, suffix="")
            tweet = f"{numbering}{tweet_content}".strip()
            
            # Ensure it fits
            if len(tweet) > self.SINGLE_TWEET_LIMIT:
                tweet = tweet[:self.SINGLE_TWEET_LIMIT - 3] + "..."
            
            tweets.append(tweet)
        
        # Last tweet: Sources and hashtags (more natural)
        sources_parts = []
        sources_parts.append("Sources:")
        
        for i, source in enumerate(sources[:2], 1):
            if not isinstance(source, dict):
                continue
            
            title = str(source.get('title', 'Untitled')).strip()
            url = str(source.get('url', '')).strip()
            
            # Truncate title if needed
            if len(title) > 40:
                title = title[:37] + "..."
            
            if url:
                # More natural format
                sources_parts.append(f"{i}. {title} - {url}")
            else:
                sources_parts.append(f"{i}. {title}")
        
        sources_text = "\n".join(sources_parts)
        
        hashtag_text = " ".join(hashtags[:5]) if hashtags else ""
        
        # Combine sources and hashtags
        if hashtag_text:
            last_tweet = f"{sources_text}\n\n{hashtag_text}".strip()
        else:
            last_tweet = sources_text.strip()
        
        # Check if it fits
        if len(last_tweet) <= self.SINGLE_TWEET_LIMIT:
            tweets.append(last_tweet)
        else:
            # Split sources and hashtags if needed
            if len(sources_text) <= self.SINGLE_TWEET_LIMIT:
                tweets.append(sources_text)
            else:
                # Truncate sources
                truncated_sources = sources_text[:self.SINGLE_TWEET_LIMIT - 3] + "..."
                tweets.append(truncated_sources)
            
            if hashtag_text and len(hashtag_text) <= self.SINGLE_TWEET_LIMIT:
                tweets.append(hashtag_text)
        
        return tweets
    
    def format_quote_tweet(self, answer: str, original_tweet_url: str) -> str:
        """Format as quote tweet"""
        available = self.TWEET_WITH_LINK_LIMIT - len(original_tweet_url) - 10
        
        truncated = self._truncate_smart(answer, available)
        return f"{truncated}\n\n💬 {original_tweet_url}"
