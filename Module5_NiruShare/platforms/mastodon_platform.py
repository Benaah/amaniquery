"""
Mastodon platform plugin
"""
from typing import List, Dict, Optional, Union
from urllib.parse import quote

from .base_platform import BasePlatform, PlatformMetadata
from ..formatters.base_formatter import BaseFormatter


class MastodonFormatter(BaseFormatter):
    """Formatter for Mastodon posts (toots)"""
    
    CHAR_LIMIT = 500  # Mastodon character limit
    
    def __init__(self):
        super().__init__(char_limit=self.CHAR_LIMIT)
    
    def format_post(
        self,
        answer: str,
        sources: List[Dict],
        query: Optional[str] = None,
        include_hashtags: bool = True,
    ) -> Dict:
        """Format for Mastodon"""
        self._validate_input(answer, sources)
        
        toot_parts = []
        
        if query:
            query_text = str(query).strip()
            toot_parts.append(f"{query_text}\n\n")
        
        # Main content
        available_space = self.CHAR_LIMIT - len("".join(toot_parts))
        main_content = self._truncate_smart(answer, available_space - 50)  # Reserve space
        toot_parts.append(main_content)
        
        # Sources (brief)
        if sources:
            source = sources[0]
            if isinstance(source, dict):
                url = str(source.get('url', '')).strip()
                if url:
                    toot_parts.append(f"\n\n{url}")
        
        # Hashtags
        hashtags = self._generate_hashtags(answer, sources, max_tags=5) if include_hashtags else []
        if hashtags:
            hashtag_text = " " + " ".join(hashtags)
            if len("".join(toot_parts)) + len(hashtag_text) <= self.CHAR_LIMIT:
                toot_parts.append(hashtag_text)
        
        toot = "".join(toot_parts)
        
        # Ensure it fits
        if len(toot) > self.CHAR_LIMIT:
            toot = self._truncate_smart(toot, self.CHAR_LIMIT)
        
        return {
            "platform": "mastodon",
            "content": toot.strip(),
            "character_count": len(toot.strip()),
            "hashtags": hashtags,
        }


class MastodonPlatform(BasePlatform):
    """Mastodon platform handler"""
    
    def __init__(self):
        self.formatter = MastodonFormatter()
        super().__init__()
    
    def get_metadata(self) -> PlatformMetadata:
        """Return Mastodon platform metadata"""
        return PlatformMetadata(
            name="mastodon",
            display_name="Mastodon",
            char_limit=500,
            supports_threads=True,  # Threads via replies
            supports_images=True,
            supports_video=True,
            posting_supported=False,  # Requires Mastodon API
            requires_auth=True,
            features=["hashtags", "mentions", "links", "images", "threads"],
        )
    
    def format_post(
        self,
        answer: str,
        sources: List[Dict],
        query: Optional[str] = None,
        include_hashtags: bool = True,
        style: Optional[str] = None,
    ) -> Dict:
        """Format response for Mastodon"""
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
        """Generate Mastodon share link"""
        # Mastodon doesn't have a universal share URL
        # Return a generic share URL (would need instance URL)
        text = content[0] if isinstance(content, list) else str(content)
        encoded_text = quote(text)
        
        # Generic format (would need instance URL in production)
        if url:
            encoded_url = quote(url)
            return f"https://mastodon.social/share?text={encoded_text}&url={encoded_url}"
        return f"https://mastodon.social/share?text={encoded_text}"

