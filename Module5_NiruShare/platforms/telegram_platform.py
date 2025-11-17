"""
Telegram platform plugin
"""
from typing import List, Dict, Optional, Union
from urllib.parse import quote

from .base_platform import BasePlatform, PlatformMetadata
from ..formatters.base_formatter import BaseFormatter


class TelegramFormatter(BaseFormatter):
    """Formatter for Telegram messages"""
    
    CHAR_LIMIT = 4096  # Telegram message limit
    
    def __init__(self):
        super().__init__(char_limit=self.CHAR_LIMIT)
    
    def format_post(
        self,
        answer: str,
        sources: List[Dict],
        query: Optional[str] = None,
        include_hashtags: bool = True,
    ) -> Dict:
        """Format for Telegram"""
        self._validate_input(answer, sources)
        
        message_parts = []
        
        if query:
            message_parts.append(f"*{query}*\n\n")
        
        message_parts.append(answer)
        
        # Sources
        if sources:
            message_parts.append("\n\n*Sources:*")
            for i, source in enumerate(sources[:5], 1):
                if isinstance(source, dict):
                    title = str(source.get('title', '')).strip()
                    url = str(source.get('url', '')).strip()
                    if url:
                        message_parts.append(f"\n{i}. [{title}]({url})")
                    else:
                        message_parts.append(f"\n{i}. {title}")
        
        # Hashtags
        hashtags = self._generate_hashtags(answer, sources, max_tags=10) if include_hashtags else []
        if hashtags:
            message_parts.append("\n\n" + " ".join(hashtags))
        
        message = "".join(message_parts)
        
        return {
            "platform": "telegram",
            "content": message.strip(),
            "character_count": len(message.strip()),
            "hashtags": hashtags,
        }


class TelegramPlatform(BasePlatform):
    """Telegram platform handler"""
    
    def __init__(self):
        self.formatter = TelegramFormatter()
        super().__init__()
    
    def get_metadata(self) -> PlatformMetadata:
        """Return Telegram platform metadata"""
        return PlatformMetadata(
            name="telegram",
            display_name="Telegram",
            char_limit=4096,
            supports_threads=False,
            supports_images=True,
            supports_video=True,
            posting_supported=False,  # Requires Telegram Bot API
            requires_auth=True,
            features=["markdown", "links", "images", "videos", "channels"],
        )
    
    def format_post(
        self,
        answer: str,
        sources: List[Dict],
        query: Optional[str] = None,
        include_hashtags: bool = True,
        style: Optional[str] = None,
    ) -> Dict:
        """Format response for Telegram"""
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
        """Generate Telegram share link"""
        if url:
            encoded_url = quote(url)
            text = content[0] if isinstance(content, list) else str(content)
            encoded_text = quote(text[:100])  # Limit text length
            return f"https://t.me/share/url?url={encoded_url}&text={encoded_text}"
        return "https://t.me/share/url"

