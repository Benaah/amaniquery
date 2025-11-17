"""
Google News Search Tool using SerpAPI
"""
from typing import Dict, Any, List, Optional
import os
from loguru import logger

try:
    from serpapi import GoogleSearch
except ImportError:
    GoogleSearch = None
    logger.warning("google-search-results not installed. Install with: pip install google-search-results")


class NewsSearchTool:
    """Google News search tool using SerpAPI"""
    
    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize news search tool
        
        Args:
            api_key: SerpAPI key (defaults to SERPAPI_API_KEY env var)
        """
        if GoogleSearch is None:
            raise ImportError("google-search-results package required")
        
        self.api_key = api_key or os.getenv("SERPAPI_API_KEY")
        if not self.api_key:
            logger.warning("SERPAPI_API_KEY not set. News search will not work.")
    
    def execute(
        self,
        query: str,
        max_results: int = 10,
        location: str = "Kenya"
    ) -> Dict[str, Any]:
        """
        Search Google News
        
        Args:
            query: Search query
            max_results: Maximum number of results
            location: Location for news search
            
        Returns:
            News search results with sources
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
                "tbm": "nws",  # News search
                "api_key": self.api_key,
                "num": max_results,
                "location": location
            }
            
            search = GoogleSearch(params)
            results = search.get_dict()
            
            formatted_results = []
            sources = []
            
            news_results = results.get("news_results", [])
            
            for item in news_results[:max_results]:
                formatted_results.append({
                    'title': item.get('title', ''),
                    'snippet': item.get('snippet', ''),
                    'source': item.get('source', ''),
                    'date': item.get('date', ''),
                    'link': item.get('link', '')
                })
                
                sources.append({
                    'type': 'news',
                    'title': item.get('title', ''),
                    'url': item.get('link', ''),
                    'source': item.get('source', ''),
                    'snippet': item.get('snippet', '')[:200],
                    'date': item.get('date', '')
                })
            
            return {
                'query': query,
                'results': formatted_results,
                'sources': sources,
                'count': len(formatted_results)
            }
        except Exception as e:
            logger.error(f"Error in news search: {e}")
            return {
                'query': query,
                'results': [],
                'sources': [],
                'error': str(e),
                'count': 0
            }

