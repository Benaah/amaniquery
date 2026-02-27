from typing import List, Dict, Optional, Any
from .base_platform import BasePlatform, PlatformMetadata
from ..formatters.threads_formatter import ThreadsFormatter

class ThreadsPlatform(BasePlatform):
    def __init__(self):
        self.formatter = ThreadsFormatter()

    def get_metadata(self) -> PlatformMetadata:
        return PlatformMetadata(
            name="Threads",
            display_name="Threads",
            char_limit=500,
            supports_images=True,
            supports_video=True,
            requires_auth=False  # For basic sharing via intents
        )

    def format_post(
        self,
        answer: str,
        sources: List[Dict],
        query: Optional[str] = None,
        include_hashtags: bool = True,
        style: Optional[str] = None,
    ) -> Dict:
        return self.formatter.format_post(
            answer=answer,
            sources=sources,
            query=query
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
