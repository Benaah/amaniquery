"""
Facebook formatter
"""
from typing import List, Dict, Optional
from .base_formatter import BaseFormatter


class FacebookFormatter(BaseFormatter):
    """Format responses for Facebook"""
    
    OPTIMAL_LENGTH = 500  # For better engagement
    
    def __init__(self):
        super().__init__(char_limit=None)  # No strict limit
    
    def format_post(
        self,
        answer: str,
        sources: List[Dict],
        query: Optional[str] = None,
        include_hashtags: bool = True,
    ) -> Dict:
        """Format response for Facebook"""
        
        # Engaging opening
        opening = self._create_opening(query)
        
        # Format main content
        main_content = self._format_content(answer)
        
        # Call to action
        cta = self._create_cta()
        
        # Sources
        sources_section = self._format_facebook_sources(sources)
        
        # Hashtags (less prominent on Facebook)
        hashtags = self._generate_hashtags(answer, sources, max_tags=5) if include_hashtags else []
        hashtag_text = "\n\n" + " ".join(hashtags) if hashtags else ""
        
        # Combine
        full_post = f"{opening}\n\n{main_content}\n\n{cta}\n\n{sources_section}{hashtag_text}"
        
        return {
            "platform": "facebook",
            "content": full_post.strip(),
            "character_count": len(full_post),
            "hashtags": hashtags,
            "word_count": len(full_post.split()),
        }
    
    def _create_opening(self, query: Optional[str]) -> str:
        """Create engaging opening"""
        if query:
            return f"🤔 Someone asked: \"{query}\"\n\nHere's what we found 👇"
        return "📢 Did you know? Here's an interesting insight 👇"
    
    def _format_content(self, answer: str) -> str:
        """Format content for Facebook engagement"""
        # Keep it concise for better engagement
        if len(answer) > 800:
            # Use key points format
            key_points = self._extract_key_points(answer, max_points=4)
            
            formatted = "📌 Key Points:\n\n"
            for i, point in enumerate(key_points, 1):
                formatted += f"{i}. {point}\n\n"
            
            return formatted.strip()
        else:
            return answer
    
    def _create_cta(self) -> str:
        """Create call to action"""
        ctas = [
            "💬 What do you think? Share your thoughts in the comments!",
            "👍 Found this helpful? Like and share with your network!",
            "🔔 Want more insights? Follow for daily updates!",
        ]
        
        # Return first CTA for consistency
        return ctas[0]
    
    def _format_facebook_sources(self, sources: List[Dict]) -> str:
        """Format sources for Facebook"""
        if not sources:
            return "📱 Powered by AmaniQuery"
        
        sources_text = "📚 Learn more:\n"
        for i, source in enumerate(sources[:3], 1):
            title = source.get('title', 'Untitled')
            url = source.get('url', '')
            
            sources_text += f"• {title}\n  {url}\n\n"
        
        sources_text += "📱 Powered by AmaniQuery - Your Kenyan Intelligence Hub"
        
        return sources_text.strip()
