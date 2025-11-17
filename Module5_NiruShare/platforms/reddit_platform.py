"""
Reddit platform plugin
"""
from typing import List, Dict, Optional, Union
from urllib.parse import quote

from .base_platform import BasePlatform, PlatformMetadata
from ..formatters.base_formatter import BaseFormatter


class RedditFormatter(BaseFormatter):
    """Formatter for Reddit posts"""
    
    CHAR_LIMIT = 40000  # Reddit post limit
    
    def __init__(self):
        super().__init__(char_limit=self.CHAR_LIMIT)
    
    def format_post(
        self,
        answer: str,
        sources: List[Dict],
        query: Optional[str] = None,
        include_hashtags: bool = False,  # Reddit doesn't use hashtags
    ) -> Dict:
        """Format for Reddit"""
        self._validate_input(answer, sources)
        
        post_parts = []
        
        if query:
            post_parts.append(f"**Question:** {query}\n\n")
        
        post_parts.append("**Answer:**\n\n")
        post_parts.append(answer)
        
        # Sources with Reddit formatting
        if sources:
            post_parts.append("\n\n**Sources:**\n\n")
            for i, source in enumerate(sources[:5], 1):
                if isinstance(source, dict):
                    title = str(source.get('title', '')).strip()
                    url = str(source.get('url', '')).strip()
                    if url:
                        post_parts.append(f"{i}. [{title}]({url})\n\n")
                    else:
                        post_parts.append(f"{i}. {title}\n\n")
        
        post = "".join(post_parts)
        
        return {
            "platform": "reddit",
            "content": post.strip(),
            "character_count": len(post.strip()),
            "hashtags": [],
        }


class RedditPlatform(BasePlatform):
    """Reddit platform handler"""
    
    def __init__(self):
        self.formatter = RedditFormatter()
        super().__init__()
    
    def get_metadata(self) -> PlatformMetadata:
        """Return Reddit platform metadata"""
        return PlatformMetadata(
            name="reddit",
            display_name="Reddit",
            char_limit=40000,
            supports_threads=True,  # Comments
            supports_images=True,
            supports_video=True,
            posting_supported=False,  # Requires Reddit API
            requires_auth=True,
            features=["markdown", "links", "images", "comments"],
        )
    
    def format_post(
        self,
        answer: str,
        sources: List[Dict],
        query: Optional[str] = None,
        include_hashtags: bool = False,
        style: Optional[str] = None,
    ) -> Dict:
        """Format response for Reddit"""
        result = self.formatter.format_post(
            answer=answer,
            sources=sources,
            query=query,
            include_hashtags=include_hashtags,
        )
        if style:
            result["style"] = style
        return result
    
    def generate_share_link(
        self,
        content: Union[str, List[str]],
        url: Optional[str] = None,
    ) -> str:
        """Generate Reddit share link"""
        if url:
            encoded_url = quote(url)
            return f"https://www.reddit.com/submit?url={encoded_url}"
        return "https://www.reddit.com/submit"

