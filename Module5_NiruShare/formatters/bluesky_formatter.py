from typing import List, Dict, Optional
from .base_formatter import BaseFormatter

class BlueskyFormatter(BaseFormatter):
    """Formatter for Bluesky posts."""
    
    def __init__(self):
        super().__init__()
        self.MAX_CHARS = 300
        
    def format_post(
        self,
        answer: str,
        sources: List[Dict],
        query: Optional[str] = None,
        max_length: Optional[int] = None
    ) -> List[str]:
        """
        Format answer for Bluesky. 
        Bluesky currently (2024/2025) has a 300 char limit.
        """
        limit = max_length or self.MAX_CHARS
        
        # Similar logic to Twitter but slightly more permissive than 280, less than 500
        # We will try to condense the answer into one post if possible, or a short thread.
        
        content = ""
        if query:
            content += f"{query}\n\n"
            
        # Try to summarize or extract main point since 300 is tight
        key_points = self._extract_key_points(answer, max_points=2)
        if key_points:
            content += " ".join(key_points)
        else:
            content += answer
            
        # Truncate to make space for sources/tags
        reserved_space = 50 # for hashtags
        available_content = limit - reserved_space
        
        if len(content) > available_content:
             content = self._truncate_smart(content, available_content)
             
        hashtags = self._generate_hashtags(answer, 2) # fewer tags for bsky
        
        final_post = f"{content}\n\n{' '.join(hashtags)}"
        
        # Note: Bluesky also supports threads, but for V1 we'll return a single optimized post 
        # or a list if it really needs splitting. For consistency with other formatters returning List[str]:
        
        return [final_post]
