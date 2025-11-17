"""
Instagram platform plugin
"""
from typing import List, Dict, Optional, Union
from urllib.parse import quote

from .base_platform import BasePlatform, PlatformMetadata
from ..formatters.base_formatter import BaseFormatter


class InstagramFormatter(BaseFormatter):
    """Formatter for Instagram captions"""
    
    CHAR_LIMIT = 2200  # Instagram caption limit
    
    def __init__(self):
        super().__init__(char_limit=self.CHAR_LIMIT)
    
    def format_post(
        self,
        answer: str,
        sources: List[Dict],
        query: Optional[str] = None,
        include_hashtags: bool = True,
    ) -> Dict:
        """Format for Instagram"""
        self._validate_input(answer, sources)
        
        # Instagram prefers natural, engaging captions
        caption_parts = []
        
        if query:
            caption_parts.append(f"{query}\n\n")
        
        # Main content
        main_content = self._truncate_smart(answer, 1500)
        caption_parts.append(main_content)
        
        # Sources
        if sources:
            caption_parts.append("\n\nSources:")
            for i, source in enumerate(sources[:3], 1):
                if isinstance(source, dict):
                    title = str(source.get('title', '')).strip()
                    url = str(source.get('url', '')).strip()
                    if title:
                        if url:
                            caption_parts.append(f"{i}. {title} - {url}")
                        else:
                            caption_parts.append(f"{i}. {title}")
        
        # Hashtags (important for Instagram)
        hashtags = self._generate_hashtags(answer, sources, max_tags=15) if include_hashtags else []
        if hashtags:
            caption_parts.append("\n\n" + " ".join(hashtags))
        
        caption = "".join(caption_parts)
        
        return {
            "platform": "instagram",
            "content": caption.strip(),
            "character_count": len(caption.strip()),
            "hashtags": hashtags,
        }


class InstagramPlatform(BasePlatform):
    """Instagram platform handler"""
    
    def __init__(self):
        self.formatter = InstagramFormatter()
        super().__init__()
    
    def get_metadata(self) -> PlatformMetadata:
        """Return Instagram platform metadata"""
        return PlatformMetadata(
            name="instagram",
            display_name="Instagram",
            char_limit=2200,
            supports_threads=False,
            supports_images=True,
            supports_video=True,
            posting_supported=False,  # Requires Instagram Graph API
            requires_auth=True,
            features=["hashtags", "mentions", "images", "stories", "reels"],
        )
    
    def format_post(
        self,
        answer: str,
        sources: List[Dict],
        query: Optional[str] = None,
        include_hashtags: bool = True,
        style: Optional[str] = None,
    ) -> Dict:
        """Format response for Instagram"""
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
        """Generate Instagram share link"""
        # Instagram doesn't support direct text sharing via URL
        # Return Instagram app URL
        if url:
            return f"https://www.instagram.com/"
        return "https://www.instagram.com/"

