from typing import List, Dict, Optional
from .base_formatter import BaseFormatter

class TikTokFormatter(BaseFormatter):
    """Formatter for TikTok captions."""
    
    def __init__(self):
        super().__init__()
        self.MAX_CHARS = 2200
        
    def format_post(
        self,
        answer: str,
        sources: List[Dict],
        query: Optional[str] = None,
        max_length: Optional[int] = None
    ) -> List[str]:
        """
        Format answer for TikTok caption.
        TikTok allows 2200 chars, so we can be verbose.
        """
        limit = max_length or self.MAX_CHARS
        
        # TikTok captions often start with a hook
        content = ""
        if query:
            content += f"Question: {query} 🤔\n\n"
            
        content += f"Here's the breakdown:\n\n{answer}\n\n"
        
        # Formatting sources nicely since we have space
        sources_text = self._format_sources_plain(sources)
        if sources_text:
            content += f"📚 Sources:\n{sources_text}\n\n"
            
        # TikTok relies heavily on hashtags
        hashtags = self._generate_hashtags(answer, 5)
        # Add some generic trending ones if relevant (but keeping it safe for now)
        hashtags.append("#learning")
        hashtags.append("#facts")
        
        content += " ".join(hashtags)
        
        # Ensure limit
        if len(content) > limit:
            content = self._truncate_smart(content, limit)
            
        return [content]
