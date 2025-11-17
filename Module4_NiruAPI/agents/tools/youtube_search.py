"""
YouTube Video Search Tool using SerpAPI
"""
from typing import Dict, Any, List, Optional
import os
from loguru import logger

try:
    from serpapi import GoogleSearch
except ImportError:
    GoogleSearch = None
    logger.warning("google-search-results not installed. Install with: pip install google-search-results")


class YouTubeSearchTool:
    """YouTube video search tool using SerpAPI"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize YouTube search tool
        
        Args:
            api_key: SerpAPI key (defaults to SERPAPI_API_KEY env var)
        """
        if GoogleSearch is None:
            raise ImportError("google-search-results package required")
        
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        if not self.api_key:
            logger.warning("SERPAPI_API_KEY not set. YouTube search will not work.")
    
    def execute(
        self,
        query: str,
        max_results: int = 10
    ) -> Dict[str, Any]:
        """
        Search YouTube videos
        
        Args:
            query: Search query
            max_results: Maximum number of results
            
        Returns:
            YouTube search results with sources
        """
        if not self.api_key:
            return {
                'query': query,
                'results': [],
                'sources': [],
                'error': 'SERPAPI_API_KEY not configured',
                'count': 0
            }
        
        try:
            params = {
                "q": query,
                "tbm": "vid",  # Video search
                "api_key": self.api_key,
                "num": max_results
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            formatted_results = []
            sources = []
            
            video_results = results.get("video_results", [])
            
            for item in video_results[:max_results]:
                formatted_results.append({
                    'title': item.get('title', ''),
                    'snippet': item.get('snippet', ''),
                    'link': item.get('link', ''),
                    'duration': item.get('duration', ''),
                    'channel': item.get('channel', '')
                })
                
                sources.append({
                    'type': 'youtube',
                    'title': item.get('title', ''),
                    'url': item.get('link', ''),
                    'channel': item.get('channel', ''),
                    'snippet': item.get('snippet', '')[:200],
                    'duration': item.get('duration', '')
                })
            
            return {
                'query': query,
                'results': formatted_results,
                'sources': sources,
                'count': len(formatted_results)
            }
        except Exception as e:
            logger.error(f"Error in YouTube search: {e}")
            return {
                'query': query,
                'results': [],
                'sources': [],
                'error': str(e),
                'count': 0
            }

