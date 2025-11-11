"""
LinkedIn formatter
"""
from typing import List, Dict, Optional
from .base_formatter import BaseFormatter


class LinkedInFormatter(BaseFormatter):
    """Format responses for LinkedIn"""
    
    CHAR_LIMIT = 3000
    OPTIMAL_LENGTH = 1300  # Sweet spot for engagement
    
    def __init__(self):
        super().__init__(char_limit=self.CHAR_LIMIT)
    
    def format_post(
        self,
        answer: str,
        sources: List[Dict],
        query: Optional[str] = None,
        include_hashtags: bool = True,
    ) -> Dict:
        """Format response for LinkedIn"""
        
        # Professional opening
        opening = self._create_opening(query)
        
        # Format main content
        main_content = self._format_content(answer)
        
        # Key insights section
        insights = self._create_insights_section(answer)
        
        # Sources section
        sources_section = self._format_linkedin_sources(sources)
        
        # Hashtags
        hashtags = self._generate_hashtags(answer, sources, max_tags=10) if include_hashtags else []
        hashtag_text = "\n\n" + " ".join(hashtags) if hashtags else ""
        
        # Combine all sections
        full_post = f"{opening}\n\n{main_content}\n\n{insights}\n\n{sources_section}{hashtag_text}"
        
        # Ensure within limit
        if len(full_post) > self.CHAR_LIMIT:
            # Truncate main content
            overflow = len(full_post) - self.CHAR_LIMIT
            main_content = main_content[:-overflow-50] + "...\n\n[Full analysis available]"
            full_post = f"{opening}\n\n{main_content}\n\n{insights}\n\n{sources_section}{hashtag_text}"
        
        return {
            "platform": "linkedin",
            "content": full_post.strip(),
            "character_count": len(full_post),
            "hashtags": hashtags,
            "optimal_length": len(full_post) <= self.OPTIMAL_LENGTH,
        }
    
    def _create_opening(self, query: Optional[str]) -> str:
        """Create professional opening"""
        if query:
            return f"💡 Question: {query}\n\n📊 Analysis:"
        return "📊 Key Insights from AmaniQuery:"
    
    def _format_content(self, answer: str) -> str:
        """Format main content with proper structure"""
        # Split into paragraphs
        paragraphs = answer.split('\n\n')
        
        # Add professional formatting
        formatted = []
        for para in paragraphs[:4]:  # Limit paragraphs
            if para.strip():
                formatted.append(para.strip())
        
        return "\n\n".join(formatted)
    
    def _create_insights_section(self, answer: str) -> str:
        """Create key insights section"""
        key_points = self._extract_key_points(answer, max_points=3)
        
        if not key_points:
            return ""
        
        insights = "🔑 Key Takeaways:\n"
        for i, point in enumerate(key_points, 1):
            # Truncate each point
            point = self._truncate_smart(point, 150, suffix="...")
            insights += f"  {i}. {point}\n"
        
        return insights.strip()
    
    def _format_linkedin_sources(self, sources: List[Dict]) -> str:
        """Format sources for LinkedIn"""
        if not sources:
            return ""
        
        sources_text = "📚 References:\n"
        for i, source in enumerate(sources[:5], 1):
            title = source.get('title', 'Untitled')
            url = source.get('url', '')
            source_name = source.get('source_name', '')
            category = source.get('category', '')
            
            # LinkedIn format with category
            if category:
                sources_text += f"{i}. {title} [{category}]\n"
            else:
                sources_text += f"{i}. {title}\n"
            
            if source_name:
                sources_text += f"   Source: {source_name}\n"
            if url:
                sources_text += f"   Link: {url}\n"
        
        sources_text += "\n🤖 Powered by AmaniQuery - RAG for Kenyan Intelligence"
        
        return sources_text.strip()
