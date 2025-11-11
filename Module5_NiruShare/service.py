"""
Social Media Sharing Service
"""
from typing import Dict, List, Optional
from urllib.parse import quote
import json

from .formatters import (
    TwitterFormatter,
    LinkedInFormatter,
    FacebookFormatter,
)


class ShareService:
    """Service for social media sharing"""
    
    def __init__(self):
        self.formatters = {
            "twitter": TwitterFormatter(),
            "linkedin": LinkedInFormatter(),
            "facebook": FacebookFormatter(),
        }
    
    def format_for_platform(
        self,
        answer: str,
        sources: List[Dict],
        platform: str,
        query: Optional[str] = None,
        include_hashtags: bool = True,
    ) -> Dict:
        """
        Format response for specific platform
        
        Args:
            answer: The RAG answer
            sources: List of source dictionaries
            platform: Platform name (twitter, linkedin, facebook)
            query: Original query
            include_hashtags: Whether to include hashtags
        
        Returns:
            Formatted post with metadata
        """
        platform = platform.lower()
        
        if platform not in self.formatters:
            raise ValueError(f"Unsupported platform: {platform}. Supported: {list(self.formatters.keys())}")
        
        formatter = self.formatters[platform]
        return formatter.format_post(answer, sources, query, include_hashtags)
    
    def generate_share_link(
        self,
        platform: str,
        formatted_content: str,
        url: Optional[str] = None,
    ) -> str:
        """
        Generate platform-specific share link
        
        Args:
            platform: Platform name
            formatted_content: Pre-formatted content
            url: Optional URL to share
        
        Returns:
            Share URL
        """
        platform = platform.lower()
        
        if platform == "twitter":
            return self._generate_twitter_link(formatted_content, url)
        elif platform == "linkedin":
            return self._generate_linkedin_link(formatted_content, url)
        elif platform == "facebook":
            return self._generate_facebook_link(formatted_content, url)
        else:
            raise ValueError(f"Unsupported platform: {platform}")
    
    def _generate_twitter_link(self, text: str, url: Optional[str] = None) -> str:
        """Generate Twitter share link"""
        # Handle thread case
        if isinstance(text, list):
            text = text[0]  # Use first tweet
        
        encoded_text = quote(text)
        
        if url:
            encoded_url = quote(url)
            return f"https://twitter.com/intent/tweet?text={encoded_text}&url={encoded_url}"
        else:
            return f"https://twitter.com/intent/tweet?text={encoded_text}"
    
    def _generate_linkedin_link(self, text: str, url: Optional[str] = None) -> str:
        """Generate LinkedIn share link"""
        # LinkedIn doesn't support pre-filled text via URL
        # Return share dialog URL
        if url:
            encoded_url = quote(url)
            return f"https://www.linkedin.com/sharing/share-offsite/?url={encoded_url}"
        else:
            # Return general sharing URL
            return "https://www.linkedin.com/feed/"
    
    def _generate_facebook_link(self, text: str, url: Optional[str] = None) -> str:
        """Generate Facebook share link"""
        if url:
            encoded_url = quote(url)
            return f"https://www.facebook.com/sharer/sharer.php?u={encoded_url}"
        else:
            # Return general sharing URL
            return "https://www.facebook.com/sharer/sharer.php"
    
    def preview_all_platforms(
        self,
        answer: str,
        sources: List[Dict],
        query: Optional[str] = None,
    ) -> Dict[str, Dict]:
        """
        Preview formatted posts for all platforms
        
        Returns:
            Dictionary with platform names as keys and formatted posts as values
        """
        previews = {}
        
        for platform in self.formatters.keys():
            try:
                previews[platform] = self.format_for_platform(
                    answer, sources, platform, query
                )
            except Exception as e:
                previews[platform] = {"error": str(e)}
        
        return previews
    
    def get_platform_stats(self, formatted_post: Dict) -> Dict:
        """Get statistics for formatted post"""
        platform = formatted_post.get("platform")
        content = formatted_post.get("content")
        
        if isinstance(content, list):
            # Thread
            total_chars = sum(len(tweet) for tweet in content)
            return {
                "platform": platform,
                "type": "thread",
                "tweet_count": len(content),
                "total_characters": total_chars,
                "avg_chars_per_tweet": total_chars // len(content),
            }
        else:
            # Single post
            return {
                "platform": platform,
                "type": "single",
                "character_count": len(content),
                "word_count": len(content.split()),
                "hashtag_count": len(formatted_post.get("hashtags", [])),
            }
