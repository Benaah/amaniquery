"""
Sharing API endpoints
"""
import sys
from pathlib import Path
import os
from typing import Dict
import requests

sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import APIRouter, HTTPException
from Module5_NiruShare.service import ShareService
from Module5_NiruShare.models import (
    FormatRequest,
    FormatResponse,
    ShareLinkRequest,
    ShareLinkResponse,
    PreviewRequest,
    PreviewResponse,
    PostRequest,
    PostResponse,
    AuthRequest,
    AuthResponse,
    AuthCallbackRequest,
)

# Create router
router = APIRouter(prefix="/share", tags=["Social Sharing"])

# Initialize service
share_service = ShareService()


@router.post("/format", response_model=FormatResponse)
async def format_for_platform(request: FormatRequest):
    """
    Format a response for specific social media platform
    
    **Supported platforms:**
    - `twitter`: 280 chars (or thread)
    - `linkedin`: Professional format (3000 char limit)
    - `facebook`: Engaging format
    
    **Example:**
    ```json
    {
      "answer": "The Kenyan Constitution protects freedom of expression...",
      "sources": [...],
      "platform": "twitter",
      "query": "What does the Constitution say about free speech?"
    }
    ```
    """
    try:
        formatted = share_service.format_for_platform(
            answer=request.answer,
            sources=request.sources,
            platform=request.platform,
            query=request.query,
            include_hashtags=request.include_hashtags,
        )
        
        return FormatResponse(
            platform=formatted["platform"],
            content=formatted["content"],
            character_count=formatted.get("character_count"),
            hashtags=formatted.get("hashtags", []),
            metadata={
                k: v for k, v in formatted.items()
                if k not in ["platform", "content", "character_count", "hashtags"]
            }
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error formatting post: {str(e)}")


@router.post("/generate-link", response_model=ShareLinkResponse)
async def generate_share_link(request: ShareLinkRequest):
    """
    Generate platform-specific share link
    
    **Example:**
    ```json
    {
      "platform": "twitter",
      "content": "Check out this insight from AmaniQuery! #Kenya",
      "url": "https://amaniquery.ke/query/123"
    }
    ```
    """
    try:
        # Handle thread case (take first tweet)
        content = request.content
        if isinstance(content, list):
            content = content[0]
        
        share_url = share_service.generate_share_link(
            platform=request.platform,
            formatted_content=content,
            url=request.url,
        )
        
        # Add platform-specific instructions
        instructions = {
            "twitter": "Click to open Twitter with pre-filled text. You can edit before posting.",
            "linkedin": "Click to open LinkedIn sharing dialog. Paste your formatted content.",
            "facebook": "Click to open Facebook sharing dialog. Paste your formatted content.",
        }
        
        return ShareLinkResponse(
            platform=request.platform,
            share_url=share_url,
            instructions=instructions.get(request.platform),
        )
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating link: {str(e)}")


@router.post("/preview", response_model=PreviewResponse)
async def preview_all_platforms(request: PreviewRequest):
    """
    Preview formatted posts for all platforms
    
    Returns formatted versions for Twitter, LinkedIn, and Facebook
    
    **Example:**
    ```json
    {
      "answer": "Recent parliamentary debates focused on...",
      "sources": [...],
      "query": "What are recent Parliament debates about?"
    }
    ```
    """
    try:
        previews = share_service.preview_all_platforms(
            answer=request.answer,
            sources=request.sources,
            query=request.query,
        )
        
        return PreviewResponse(
            twitter=previews.get("twitter", {}),
            linkedin=previews.get("linkedin", {}),
            facebook=previews.get("facebook", {}),
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating previews: {str(e)}")


@router.get("/platforms")
async def get_supported_platforms():
    """Get list of supported platforms"""
    return {
        "platforms": [
            {
                "name": "twitter",
                "display_name": "X (Twitter)",
                "char_limit": 280,
                "supports_threads": True,
                "posting_supported": False,  # Not yet implemented
            },
            {
                "name": "linkedin",
                "display_name": "LinkedIn",
                "char_limit": 3000,
                "supports_threads": False,
                "posting_supported": True,
            },
            {
                "name": "facebook",
                "display_name": "Facebook",
                "char_limit": None,
                "supports_threads": False,
                "posting_supported": True,
            },
        ]
    }


@router.post("/stats")
async def get_post_stats(formatted_post: dict):
    """Get statistics for a formatted post"""
    try:
        stats = share_service.get_platform_stats(formatted_post)
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating stats: {str(e)}")


@router.post("/post", response_model=PostResponse)
async def post_to_platform(request: PostRequest):
    """
    Post content directly to a social media platform
    
    **Supported platforms:** twitter, linkedin, facebook
    
    **Requirements:**
    - User must be authenticated with the platform
    - Valid access token must be provided (handled via auth flow)
    
    **Example:**
    ```json
    {
      "platform": "twitter",
      "content": "Check out this insight from AmaniQuery! #KenyaLaw",
      "message_id": "msg_123"
    }
    ```
    
    **Note:** Authentication flow must be completed first via /auth endpoints
    """
    try:
        # For now, we'll use a placeholder access token
        # In production, this would come from user session/auth storage
        access_token = os.getenv(f"{request.platform.upper()}_ACCESS_TOKEN")
        
        if not access_token:
            raise HTTPException(
                status_code=401, 
                detail=f"Not authenticated with {request.platform}. Please complete authentication first."
            )
        
        # Handle thread case (take first item for single posts)
        content = request.content
        if isinstance(content, list):
            content = content[0]
        
        result = share_service.post_to_platform(
            platform=request.platform,
            content=content,
            access_token=access_token,
            message_id=request.message_id,
        )
        
        return PostResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error posting to platform: {str(e)}")


@router.post("/auth", response_model=AuthResponse)
async def authenticate_platform(request: AuthRequest):
    """
    Initiate OAuth authentication flow for a platform
    
    **Supported platforms:** twitter, linkedin, facebook
    
    **Example:**
    ```json
    {
      "platform": "linkedin"
    }
    ```
    
    Returns authentication URL to redirect user to for OAuth consent.
    """
    try:
        result = share_service.get_auth_url(request.platform)
        return AuthResponse(**result)
        
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error initiating auth: {str(e)}")


@router.post("/auth/callback", response_model=AuthResponse)
async def handle_auth_callback(request: AuthCallbackRequest):
    """
    Handle OAuth callback from platform
    
    **Note:** This endpoint receives the authorization code from the OAuth redirect
    and exchanges it for access tokens. In production, this would be called by
    the platform's redirect URI.
    
    **Example:**
    ```json
    {
      "platform": "linkedin",
      "code": "auth_code_from_platform",
      "state": "linkedin"
    }
    ```
    """
    try:
        # Exchange authorization code for access token
        # This is a simplified implementation - in production you'd validate state, etc.
        
        if request.platform == "linkedin":
            token_result = await exchange_linkedin_code(request.code)
        elif request.platform == "facebook":
            token_result = await exchange_facebook_code(request.code)
        elif request.platform == "twitter":
            token_result = await exchange_twitter_code(request.code)
        else:
            raise HTTPException(status_code=400, detail=f"Unsupported platform: {request.platform}")
        
        if token_result.get("access_token"):
            # Store access token (in production, store in user session/database)
            os.environ[f"{request.platform.upper()}_ACCESS_TOKEN"] = token_result["access_token"]
            
            return AuthResponse(
                platform=request.platform,
                status="authenticated",
                message="Successfully authenticated",
                user_info=token_result.get("user_info")
            )
        else:
            raise HTTPException(status_code=400, detail="Failed to obtain access token")
            
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error handling auth callback: {str(e)}")


async def exchange_linkedin_code(code: str) -> Dict:
    """Exchange LinkedIn authorization code for access token"""
    client_id = os.getenv("LINKEDIN_CLIENT_ID")
    client_secret = os.getenv("LINKEDIN_CLIENT_SECRET")
    redirect_uri = os.getenv("LINKEDIN_REDIRECT_URI", "http://localhost:8000/share/auth/callback")
    
    if not client_id or not client_secret:
        raise HTTPException(status_code=500, detail="LinkedIn API credentials not configured")
    
    url = "https://www.linkedin.com/oauth/v2/accessToken"
    data = {
        "grant_type": "authorization_code",
        "code": code,
        "redirect_uri": redirect_uri,
        "client_id": client_id,
        "client_secret": client_secret,
    }
    
    response = requests.post(url, data=data)
    response.raise_for_status()
    
    token_data = response.json()
    access_token = token_data.get("access_token")
    
    # Get user info
    headers = {"Authorization": f"Bearer {access_token}"}
    user_response = requests.get("https://api.linkedin.com/v2/people/~", headers=headers)
    
    user_info = None
    if user_response.status_code == 200:
        user_data = user_response.json()
        user_info = {
            "id": user_data.get("id"),
            "name": f"{user_data.get('localizedFirstName', '')} {user_data.get('localizedLastName', '')}".strip(),
        }
    
    return {
        "access_token": access_token,
        "user_info": user_info,
    }


async def exchange_facebook_code(code: str) -> Dict:
    """Exchange Facebook authorization code for access token"""
    app_id = os.getenv("FACEBOOK_APP_ID")
    app_secret = os.getenv("FACEBOOK_APP_SECRET")
    redirect_uri = os.getenv("FACEBOOK_REDIRECT_URI", "http://localhost:8000/share/auth/callback")
    
    if not app_id or not app_secret:
        raise HTTPException(status_code=500, detail="Facebook API credentials not configured")
    
    url = "https://graph.facebook.com/v18.0/oauth/access_token"
    params = {
        "client_id": app_id,
        "redirect_uri": redirect_uri,
        "client_secret": app_secret,
        "code": code,
    }
    
    response = requests.get(url, params=params)
    response.raise_for_status()
    
    token_data = response.json()
    access_token = token_data.get("access_token")
    
    # Get user info
    user_response = requests.get(f"https://graph.facebook.com/me?access_token={access_token}")
    
    user_info = None
    if user_response.status_code == 200:
        user_data = user_response.json()
        user_info = {
            "id": user_data.get("id"),
            "name": user_data.get("name"),
        }
    
    return {
        "access_token": access_token,
        "user_info": user_info,
    }


async def exchange_twitter_code(code: str) -> Dict:
    """Exchange Twitter authorization code for access token"""
    # Twitter OAuth 2.0 implementation would go here
    # For now, return placeholder
    return {
        "access_token": None,
        "user_info": None,
        "error": "Twitter authentication not yet implemented"
    }
