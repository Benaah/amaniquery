"""
Social Media Sharing Service
"""
from typing import Dict, List, Optional
from urllib.parse import quote
import json
import os
import requests
from datetime import datetime

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
            total_chars = sum(len(tweet) for tweet in content if tweet)
            return {
                "platform": platform,
                "type": "thread",
                "tweet_count": len(content),
                "total_characters": total_chars,
                "avg_chars_per_tweet": total_chars // len(content) if content else 0,
            }
        else:
            # Single post
            content_str = content or ""
            return {
                "platform": platform,
                "type": "single",
                "character_count": len(content_str),
                "word_count": len(content_str.split()),
                "hashtag_count": len(formatted_post.get("hashtags", [])),
            }
    
    def post_to_platform(
        self,
        platform: str,
        content: str,
        access_token: str,
        message_id: Optional[str] = None,
    ) -> Dict:
        """
        Post content to a social media platform
        
        Args:
            platform: Platform name (twitter, linkedin, facebook)
            content: Content to post
            access_token: OAuth access token
            message_id: Optional chat message ID for tracking
        
        Returns:
            Post result with ID and metadata
        """
        platform = platform.lower()
        
        if platform == "twitter":
            return self._post_to_twitter(content, access_token, message_id)
        elif platform == "linkedin":
            return self._post_to_linkedin(content, access_token, message_id)
        elif platform == "facebook":
            return self._post_to_facebook(content, access_token, message_id)
        else:
            raise ValueError(f"Unsupported platform: {platform}")
    
    def _post_to_twitter(self, content: str, access_token: str, message_id: Optional[str] = None) -> Dict:
        """Post to Twitter/X using API v2"""
        try:
            # Twitter API v2 endpoint
            url = "https://api.twitter.com/2/tweets"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
            }
            data = {"text": content}
            
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
    
    def _post_to_linkedin(self, content: str, access_token: str, message_id: Optional[str] = None) -> Dict:
        """Post to LinkedIn"""
        try:
            # First get user info to get person URN
            headers = {"Authorization": f"Bearer {access_token}"}
            user_response = requests.get("https://api.linkedin.com/v2/people/~", headers=headers)
            user_response.raise_for_status()
            user_data = user_response.json()
            person_urn = user_data.get("id")
            
            if not person_urn:
                return {
                    "platform": "linkedin",
                    "status": "error",
                    "message": "Could not retrieve LinkedIn user ID",
                    "metadata": {"message_id": message_id}
                }
            
            # Post to LinkedIn
            url = "https://api.linkedin.com/v2/ugcPosts"
            headers = {
                "Authorization": f"Bearer {access_token}",
                "Content-Type": "application/json",
                "X-Restli-Protocol-Version": "2.0.0",
            }
            
            data = {
                "author": f"urn:li:person:{person_urn}",
                "lifecycleState": "PUBLISHED",
                "specificContent": {
                    "com.linkedin.ugc.ShareContent": {
                        "shareCommentary": {"text": content},
                        "shareMediaCategory": "NONE"
                    }
                },
                "visibility": {"com.linkedin.ugc.MemberNetworkVisibility": "PUBLIC"}
            }
            
            response = requests.post(url, headers=headers, json=data)
            response.raise_for_status()
            
            result = response.json()
            post_id = result.get("id")
            
            return {
                "platform": "linkedin",
                "post_id": post_id,
                "status": "success",
                "message": "LinkedIn post created successfully",
                "url": f"https://www.linkedin.com/feed/update/{post_id}/" if post_id else None,
                "metadata": {
                    "message_id": message_id,
                    "posted_at": datetime.utcnow().isoformat(),
                }
            }
        except requests.exceptions.RequestException as e:
            return {
                "platform": "linkedin",
                "status": "error",
                "message": f"Failed to post to LinkedIn: {str(e)}",
                "metadata": {"message_id": message_id}
            }
    
    def _post_to_facebook(self, content: str, access_token: str, message_id: Optional[str] = None) -> Dict:
        """Post to Facebook"""
        try:
            # Get user pages (if posting to a page) or use user feed
            # For simplicity, we'll post to user's feed
            url = f"https://graph.facebook.com/me/feed"
            
            data = {
                "message": content,
                "access_token": access_token,
            }
            
            response = requests.post(url, data=data)
            response.raise_for_status()
            
            result = response.json()
            post_id = result.get("id")
            
            return {
                "platform": "facebook",
                "post_id": post_id,
                "status": "success",
                "message": "Facebook post created successfully",
                "url": f"https://www.facebook.com/{post_id}" if post_id else None,
                "metadata": {
                    "message_id": message_id,
                    "posted_at": datetime.utcnow().isoformat(),
                }
            }
        except requests.exceptions.RequestException as e:
            return {
                "platform": "facebook",
                "status": "error",
                "message": f"Failed to post to Facebook: {str(e)}",
                "metadata": {"message_id": message_id}
            }
    
    def get_auth_url(self, platform: str) -> Dict:
        """Get OAuth authorization URL for a platform"""
        platform = platform.lower()
        
        if platform == "twitter":
            return self._get_twitter_auth_url()
        elif platform == "linkedin":
            return self._get_linkedin_auth_url()
        elif platform == "facebook":
            return self._get_facebook_auth_url()
        else:
            raise ValueError(f"Unsupported platform: {platform}")
    
    def _get_twitter_auth_url(self) -> Dict:
        """Get Twitter OAuth URL"""
        client_id = os.getenv("TWITTER_CLIENT_ID")
        if not client_id:
            return {
                "platform": "twitter",
                "status": "error",
                "message": "Twitter API credentials not configured"
            }
        
        # Twitter OAuth 2.0 PKCE flow would be implemented here
        # For now, return placeholder
        return {
            "platform": "twitter",
            "status": "needs_auth",
            "message": "Twitter authentication not yet implemented",
            "auth_url": None
        }
    
    def _get_linkedin_auth_url(self) -> Dict:
        """Get LinkedIn OAuth URL"""
        client_id = os.getenv("LINKEDIN_CLIENT_ID")
        redirect_uri = os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:8000/share/auth/callback")
        
        if not client_id:
            return {
                "platform": "linkedin",
                "status": "error",
                "message": "LinkedIn API credentials not configured"
            }
        
        scope = "w_member_social,r_liteprofile"
        auth_url = (
            f"https://www.linkedin.com/oauth/v2/authorization?"
            f"response_type=code&client_id={client_id}&redirect_uri={quote(redirect_uri)}"
            f"&scope={quote(scope)}&state=linkedin"
        )
        
        return {
            "platform": "linkedin",
            "status": "needs_auth",
            "auth_url": auth_url,
            "message": "Click to authenticate with LinkedIn"
        }
    
    def _get_facebook_auth_url(self) -> Dict:
        """Get Facebook OAuth URL"""
        app_id = os.getenv("FACEBOOK_APP_ID")
        redirect_uri = os.getenv("FACEBOOK_REDIRECT_URI", "http://localhost:8000/share/auth/callback")
        
        if not app_id:
            return {
                "platform": "facebook",
                "status": "error",
                "message": "Facebook API credentials not configured"
            }
        
        scope = "pages_manage_posts,publish_to_groups"
        auth_url = (
            f"https://www.facebook.com/v18.0/dialog/oauth?"
            f"client_id={app_id}&redirect_uri={quote(redirect_uri)}"
            f"&scope={quote(scope)}&response_type=code&state=facebook"
        )
        
        return {
            "platform": "facebook",
            "status": "needs_auth",
            "auth_url": auth_url,
            "message": "Click to authenticate with Facebook"
        }
