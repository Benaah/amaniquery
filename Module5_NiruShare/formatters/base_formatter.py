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
    
    def _validate_input(self, answer: str, sources: List[Dict]) -> None:
        """Validate input parameters"""
        if not answer or not isinstance(answer, str):
            raise ValueError("Answer must be a non-empty string")
        if not isinstance(sources, list):
            raise ValueError("Sources must be a list")
    
    def _extract_key_points(self, text: str, max_points: int = 3) -> List[str]:
        """Extract key points from text"""
        if not text or not isinstance(text, str):
            return []
        
        # Improved sentence splitting - handle multiple delimiters properly
        # Split on sentence boundaries while preserving the delimiter
        sentences = re.split(r'([.!?]+[\s\n]+)', text)
        
        # Reconstruct sentences with their delimiters
        reconstructed = []
        for i in range(0, len(sentences) - 1, 2):
            if i + 1 < len(sentences):
                sentence = (sentences[i] + sentences[i + 1]).strip()
            else:
                sentence = sentences[i].strip()
            
            # Filter out very short sentences and empty strings
            if len(sentence) > 20:
                reconstructed.append(sentence)
        
        # If reconstruction didn't work well, fall back to simpler method
        if not reconstructed:
            sentences = re.split(r'[.!?]+\s+', text)
            reconstructed = [s.strip() for s in sentences if len(s.strip()) > 20]
        
        # Return first N sentences as key points
        return reconstructed[:max_points] if reconstructed else [text[:200] + "..." if len(text) > 200 else text]
    
    def _generate_hashtags(self, text: str, sources: List[Dict], max_tags: int = 5) -> List[str]:
        """Generate relevant hashtags"""
        if not text:
            text = ""
        if not sources:
            sources = []
        
        hashtags = set()
        
        # Category-based hashtags
        categories = set()
        for source in sources[:3]:
            if isinstance(source, dict):
                cat = source.get('category', '')
                if cat and isinstance(cat, str):
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
        text_lower = text.lower() if text else ""
        
        for keyword in keywords:
            if keyword.lower() in text_lower:
                hashtag = keyword.title().replace(' ', '')
                if hashtag:
                    hashtags.add(hashtag)
        
        # Limit and format
        hashtags_list = list(hashtags)[:max_tags]
        return [f"#{tag}" if not tag.startswith('#') else tag for tag in hashtags_list]
    
    def _truncate_smart(self, text: str, max_length: int, suffix: str = "...") -> str:
        """Truncate text at sentence boundary if possible"""
        if not text:
            return ""
        
        if not isinstance(text, str):
            text = str(text)
        
        if len(text) <= max_length:
            return text
        
        # Ensure suffix fits within max_length
        suffix_len = len(suffix)
        if max_length < suffix_len:
            return text[:max_length]
        
        available_length = max_length - suffix_len
        
        # Try to cut at sentence boundary
        for punct in ['. ', '! ', '? ', '.\n', '!\n', '?\n']:
            last_punct = text.rfind(punct, 0, available_length + len(punct))
            if last_punct > available_length * 0.6:  # At least 60% of max length
                return text[:last_punct + 1].strip() + suffix
        
        # Fall back to word boundary
        truncated = text[:available_length]
        last_space = truncated.rfind(' ')
        if last_space > available_length * 0.5:  # At least 50% of max length
            return truncated[:last_space].strip() + suffix
        
        # Last resort: hard truncate
        return truncated.strip() + suffix
    
    def _format_sources(self, sources: List[Dict], max_sources: int = 3) -> str:
        """Format source citations"""
        if not sources:
            return ""
        
        citations = []
        for i, source in enumerate(sources[:max_sources], 1):
            if not isinstance(source, dict):
                continue
            
            title = source.get('title', 'Untitled') or 'Untitled'
            url = source.get('url', '')
            
            # Sanitize title
            title = str(title).strip()
            
            if url:
                url = str(url).strip()
                citations.append(f"{i}. {title}\n   {url}")
            else:
                citations.append(f"{i}. {title}")
        
        if not citations:
            return ""
        
        return "\n\n📚 Sources:\n" + "\n".join(citations)
