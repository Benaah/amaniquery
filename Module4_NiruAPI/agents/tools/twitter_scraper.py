"""
Twitter Scraper Tool using twikit (no API key needed)
"""
from typing import Dict, Any, List, Optional
from loguru import logger

try:
    from twikit import Client
except ImportError:
    Client = None
    logger.warning("twikit not installed. Install with: pip install twikit")


class TwitterScraperTool:
    """Twitter scraping tool using twikit"""
    
    def __init__(self):
        """Initialize Twitter scraper"""
        if Client is None:
            raise ImportError("twikit package required")
        self.client = Client()
    
    def execute(
        self,
        query: str,
        max_results: int = 20,
        search_type: str = "tweet"
    ) -> Dict[str, Any]:
        """
        Search Twitter for tweets
        
        Args:
            query: Search query
            max_results: Maximum number of results
            search_type: Type of search (tweet, user, etc.)
            
        Returns:
            Twitter search results with sources
        """
        try:
            # Note: twikit requires authentication for some operations
            # For basic scraping, we'll use a simplified approach
            # In production, you may need to handle authentication
            
            # Search tweets
            tweets = self.client.search_tweet(query, count=max_results)
            
            formatted_results = []
            sources = []
            
            for tweet in tweets[:max_results]:
                tweet_data = {
                    'text': tweet.full_text if hasattr(tweet, 'full_text') else str(tweet),
                    'author': tweet.user.screen_name if hasattr(tweet, 'user') else 'unknown',
                    'created_at': str(tweet.created_at) if hasattr(tweet, 'created_at') else '',
                    'url': f"https://twitter.com/{tweet.user.screen_name}/status/{tweet.id}" if hasattr(tweet, 'id') and hasattr(tweet, 'user') else ''
                }
                
                formatted_results.append(tweet_data)
                
                sources.append({
                    'type': 'twitter',
                    'text': tweet_data['text'][:200],
                    'author': tweet_data['author'],
                    'url': tweet_data['url']
                })
            
            return {
                'query': query,
                'results': formatted_results,
                'sources': sources,
                'count': len(formatted_results)
            }
        except Exception as e:
            logger.error(f"Error in Twitter search: {e}")
            # Fallback: return empty results
            return {
                'query': query,
                'results': [],
                'sources': [],
                'error': str(e),
                'count': 0,
                'note': 'Twitter scraping may require authentication. Check twikit documentation.'
            }

