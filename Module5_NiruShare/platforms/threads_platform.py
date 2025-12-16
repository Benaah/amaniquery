from typing import List, Dict, Optional, Any
from .base_platform import BasePlatform, PlatformMetadata
from ..formatters.threads_formatter import ThreadsFormatter

class ThreadsPlatform(BasePlatform):
    def __init__(self):
        self.formatter = ThreadsFormatter()

    def get_metadata(self) -> PlatformMetadata:
        return PlatformMetadata(
            id="threads",
            name="Threads",
            max_characters=500,
            supported_media=["image", "video"],
            requires_auth=False  # For basic sharing via intents
        )

    def format_content(self, request_data: Any) -> List[str]:
        return self.formatter.format_post(
            answer=request_data.answer,
            sources=request_data.sources,
            query=request_data.query
        )

    def generate_share_link(self, content: str, url: Optional[str] = None) -> str:
        # Threads intent URL scheme
        # https://threads.net/intent/post?text=Hello%20World
        import urllib.parse
        
        base_url = "https://threads.net/intent/post"
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
            "error": "Direct posting to Threads API is not yet configured."
        }
