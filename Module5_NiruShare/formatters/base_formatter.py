"""
Base formatter for social media posts
"""
from typing import List, Dict, Optional
from abc import ABC, abstractmethod
import re


class BaseFormatter(ABC):
    """Base class for social media formatters"""
    
    def __init__(self, char_limit: Optional[int] = None):
        self.char_limit = char_limit
    
    @abstractmethod
    def format_post(
        self,
        answer: str,
        sources: List[Dict],
        query: Optional[str] = None,
        include_hashtags: bool = True,
    ) -> Dict:
        """
        Format response into social media post
        
        Returns:
            Dictionary with formatted post and metadata
        """
        pass
    
    def _extract_key_points(self, text: str, max_points: int = 3) -> List[str]:
        """Extract key points from text"""
        # Split by sentences
        sentences = re.split(r'[.!?]+', text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        # Return first N sentences as key points
        return sentences[:max_points]
    
    def _generate_hashtags(self, text: str, sources: List[Dict], max_tags: int = 5) -> List[str]:
        """Generate relevant hashtags"""
        hashtags = set()
        
        # Category-based hashtags
        categories = set()
        for source in sources[:3]:
            cat = source.get('category', '')
            if cat:
                categories.add(cat)
        
        category_map = {
            "Kenyan Law": ["KenyanLaw", "LegalKenya", "KenyaConstitution"],
            "Parliament": ["KenyanParliament", "KenyaPolitics", "ParliamentKE"],
            "Kenyan News": ["KenyaNews", "KenyaToday", "KenyaUpdates"],
            "Global Trend": ["GlobalTech", "TechPolicy", "AIPolicy"],
        }
        
        for cat in categories:
            tags = category_map.get(cat, [])
            hashtags.update(tags[:2])
        
        # Always include Kenya tag
        hashtags.add("Kenya")
        
        # Keyword-based hashtags
        keywords = ['AI', 'technology', 'law', 'parliament', 'policy', 'constitution']
        text_lower = text.lower()
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                hashtags.add(keyword.title().replace(' ', ''))
        
        # Limit and format
        hashtags = list(hashtags)[:max_tags]
        return [f"#{tag}" for tag in hashtags]
    
    def _truncate_smart(self, text: str, max_length: int, suffix: str = "...") -> str:
        """Truncate text at sentence boundary if possible"""
        if len(text) <= max_length:
            return text
        
        # Try to cut at sentence
        truncated = text[:max_length - len(suffix)]
        
        # Find last sentence ending
        for punct in ['. ', '! ', '? ']:
            last_punct = truncated.rfind(punct)
            if last_punct > max_length * 0.6:  # At least 60% of max length
                return text[:last_punct + 1].strip()
        
        # Fall back to word boundary
        truncated = text[:max_length - len(suffix)]
        last_space = truncated.rfind(' ')
        if last_space > 0:
            return truncated[:last_space] + suffix
        
        return truncated + suffix
    
    def _format_sources(self, sources: List[Dict], max_sources: int = 3) -> str:
        """Format source citations"""
        if not sources:
            return ""
        
        citations = []
        for i, source in enumerate(sources[:max_sources], 1):
            title = source.get('title', 'Untitled')
            url = source.get('url', '')
            
            if url:
                citations.append(f"{i}. {title}\n   {url}")
            else:
                citations.append(f"{i}. {title}")
        
        return "\n\n📚 Sources:\n" + "\n".join(citations)
