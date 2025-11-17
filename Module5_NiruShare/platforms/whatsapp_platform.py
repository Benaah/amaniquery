"""
WhatsApp platform plugin
"""
from typing import List, Dict, Optional, Union
from urllib.parse import quote

from .base_platform import BasePlatform, PlatformMetadata
from ..formatters.base_formatter import BaseFormatter


class WhatsAppFormatter(BaseFormatter):
    """Formatter for WhatsApp messages"""
    
    CHAR_LIMIT = None  # No strict limit, but keep concise
    
    def __init__(self):
        super().__init__(char_limit=None)
    
    def format_post(
        self,
        answer: str,
        sources: List[Dict],
        query: Optional[str] = None,
        include_hashtags: bool = False,  # WhatsApp doesn't use hashtags
    ) -> Dict:
        """Format for WhatsApp"""
        self._validate_input(answer, sources)
        
        message_parts = []
        
        if query:
            message_parts.append(f"*{query}*\n\n")
        
        # Keep it concise for WhatsApp
        if len(answer) > 1000:
            answer = self._truncate_smart(answer, 1000, suffix="...")
        
        message_parts.append(answer)
        
        # Sources
        if sources:
            message_parts.append("\n\n*Sources:*")
            for i, source in enumerate(sources[:3], 1):
                if isinstance(source, dict):
                    title = str(source.get('title', '')).strip()
                    url = str(source.get('url', '')).strip()
                    if url:
                        message_parts.append(f"\n{i}. {title}\n   {url}")
                    else:
                        message_parts.append(f"\n{i}. {title}")
        
        message = "".join(message_parts)
        
        return {
            "platform": "whatsapp",
            "content": message.strip(),
            "character_count": len(message.strip()),
            "hashtags": [],
        }


class WhatsAppPlatform(BasePlatform):
    """WhatsApp platform handler"""
    
    def __init__(self):
        self.formatter = WhatsAppFormatter()
        super().__init__()
    
    def get_metadata(self) -> PlatformMetadata:
        """Return WhatsApp platform metadata"""
        return PlatformMetadata(
            name="whatsapp",
            display_name="WhatsApp",
            char_limit=None,
            supports_threads=False,
            supports_images=True,
            supports_video=True,
            posting_supported=False,  # Requires WhatsApp Business API
            requires_auth=True,
            features=["links", "images", "videos", "groups"],
        )
    
    def format_post(
        self,
        answer: str,
        sources: List[Dict],
        query: Optional[str] = None,
        include_hashtags: bool = False,
        style: Optional[str] = None,
    ) -> Dict:
        """Format response for WhatsApp"""
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
        """Generate WhatsApp share link"""
        text = content[0] if isinstance(content, list) else str(content)
        encoded_text = quote(text)
        
        if url:
            encoded_url = quote(url)
            return f"https://wa.me/?text={encoded_text}%20{encoded_url}"
        return f"https://wa.me/?text={encoded_text}"

