"""
Twitter/X platform plugin
"""
from typing import List, Dict, Optional, Union
from urllib.parse import quote
import os
import requests
from datetime import datetime

from .base_platform import BasePlatform, PlatformMetadata
from ..formatters.twitter_formatter import TwitterFormatter


class TwitterPlatform(BasePlatform):
    """Twitter/X platform handler"""
    
    def __init__(self):
        self.formatter = TwitterFormatter()
        super().__init__()
    
    def get_metadata(self) -> PlatformMetadata:
        """Return Twitter platform metadata"""
        return PlatformMetadata(
            name="twitter",
            display_name="X (Twitter)",
            char_limit=280,
            supports_threads=True,
            supports_images=True,
            supports_video=False,
            posting_supported=True,
            requires_auth=True,
            features=["threads", "hashtags", "mentions", "links"],
        )
    
    def format_post(
        self,
        answer: str,
        sources: List[Dict],
        query: Optional[str] = None,
        include_hashtags: bool = True,
        style: Optional[str] = None,
    ) -> Dict:
        """Format response for Twitter/X"""
        result = self.formatter.format_post(
            answer=answer,
            sources=sources,
            query=query,
            include_hashtags=include_hashtags,
        )
        # Add style info if provided
        if style:
            result["style"] = style
        return result
    
    def generate_share_link(
        self,
        content: Union[str, List[str]],
        url: Optional[str] = None,
    ) -> str:
        """Generate Twitter share link"""
        # Handle thread case (take first tweet)
        if isinstance(content, list):
            text = content[0] if content else ""
        else:
            text = str(content)
        
        encoded_text = quote(text)
        
        if url:
            encoded_url = quote(url)
            return f"https://twitter.com/intent/tweet?text={encoded_text}&url={encoded_url}"
        else:
            return f"https://twitter.com/intent/tweet?text={encoded_text}"
    
    def _post_impl(
        self,
        content: Union[str, List[str]],
        access_token: str,
        message_id: Optional[str] = None,
    ) -> Dict:
        """Post to Twitter/X using API v2"""
        try:
            # Handle thread case
            if isinstance(content, list):
                # Post thread (simplified - would need proper thread API)
                text = content[0] if content else ""
            else:
                text = str(content)
            
            url = "https://api.twitter.com/2/tweets"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
            data = {"text": text}
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            tweet_id = result["data"]["id"]
            
            return {
                "platform": "twitter",
                "post_id": tweet_id,
                "status": "success",
                "message": "Tweet posted successfully",
                "url": f"https://twitter.com/i/web/status/{tweet_id}",
                "metadata": {
                    "message_id": message_id,
                    "posted_at": datetime.utcnow().isoformat(),
                }
            }
        except requests.exceptions.RequestException as e:
            return {
                "platform": "twitter",
                "status": "error",
                "message": f"Failed to post to Twitter: {str(e)}",
                "metadata": {"message_id": message_id}
            }
    
    def _get_auth_url_impl(self, redirect_uri: Optional[str] = None) -> Dict:
        """Get Twitter OAuth URL"""
        client_id = os.getenv("TWITTER_CLIENT_ID")
        if not client_id:
            return {
                "platform": "twitter",
                "status": "error",
                "message": "Twitter API credentials not configured"
            }
        
        # Twitter OAuth 2.0 PKCE flow would be implemented here
        return {
            "platform": "twitter",
            "status": "needs_auth",
            "message": "Twitter authentication not yet implemented",
            "auth_url": None
        }

