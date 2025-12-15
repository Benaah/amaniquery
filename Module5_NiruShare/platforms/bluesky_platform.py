from typing import List, Dict, Optional, Any
from .base_platform import BasePlatform, PlatformMetadata
from ..formatters.bluesky_formatter import BlueskyFormatter

class BlueskyPlatform(BasePlatform):
    def __init__(self):
        self.formatter = BlueskyFormatter()

    def get_metadata(self) -> PlatformMetadata:
        return PlatformMetadata(
            id="bluesky",
            name="Bluesky",
            max_characters=300,
            supported_media=["image"],
            requires_auth=False 
        )

    def format_content(self, request_data: Any) -> List[str]:
        return self.formatter.format_post(
            answer=request_data.answer,
            sources=request_data.sources,
            query=request_data.query
        )

    def generate_share_link(self, content: str, url: Optional[str] = None) -> str:
        # Bluesky intent URL scheme
        # https://bsky.app/intent/compose?text=Hello%20world
        import urllib.parse
        
        base_url = "https://bsky.app/intent/compose"
        text_param = content
        if url:
             text_param += f"\n\n{url}"
             
        params = {
            "text": text_param
        }
        return f"{base_url}?{urllib.parse.urlencode(params)}"

    def post_content(self, content: str, media_urls: List[str] = None, auth_token: str = None) -> Dict:
         return {
            "success": False,
            "error": "Direct posting to Bluesky API is not yet configured."
        }
