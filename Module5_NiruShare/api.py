"""
Sharing API endpoints
"""
import sys
from pathlib import Path

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
            },
            {
                "name": "linkedin",
                "display_name": "LinkedIn",
                "char_limit": 3000,
                "supports_threads": False,
            },
            {
                "name": "facebook",
                "display_name": "Facebook",
                "char_limit": None,
                "supports_threads": False,
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
