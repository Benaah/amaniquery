"""
Web Search Tool using DuckDuckGo
"""
from typing import Dict, Any, List, Optional
from loguru import logger

try:
    # Try new package name first (ddgs)
    from ddgs import DDGS
except ImportError:
    try:
        # Fallback to old package name for backwards compatibility
        from duckduckgo_search import DDGS
    except ImportError:
        DDGS = None
        logger.warning("ddgs package not installed. Install with: pip install ddgs")


class WebSearchTool:
    """Web search tool using DuckDuckGo (no API key required)"""
    
    def __init__(self):
        """Initialize web search tool"""
        if DDGS is None:
            raise ImportError("duckduckgo-search package required")
        self.ddgs = DDGS()
    
    def execute(self, query: str, max_results: int = 10, region: str = "us-en") -> Dict[str, Any]:
        """
        Execute web search
        
        Args:
            query: Search query
            max_results: Maximum number of results
            region: Search region
            
        Returns:
            Search results with sources
        """
        try:
            # Updated API: query is now a positional argument
            results = list(self.ddgs.text(
                query,
                max_results=max_results,
                region=region
            ))
            
            formatted_results = []
            sources = []
            
            for result in results:
                formatted_results.append({
                    'title': result.get('title', ''),
                    'snippet': result.get('body', ''),
                    'url': result.get('href', '')
                })
                
                sources.append({
                    'type': 'web',
                    'title': result.get('title', ''),
                    'url': result.get('href', ''),
                    'snippet': result.get('body', '')[:200]
                })
            
            return {
                'query': query,
                'results': formatted_results,
                'sources': sources,
                'count': len(formatted_results)
            }
        except Exception as e:
            logger.error(f"Error in web search: {e}")
            return {
                'query': query,
                'results': [],
                'sources': [],
                'error': str(e),
                'count': 0
            }

