from typing import List, Dict, Optional
from .base_formatter import BaseFormatter

class ThreadsFormatter(BaseFormatter):
    """Formatter for Threads posts."""
    
    def __init__(self):
        super().__init__()
        self.MAX_CHARS = 500
        # Threads supports threads natively, so we can split content
        self.SINGLE_POST_LIMIT = 500
        
    def format_post(
        self,
        answer: str,
        sources: List[Dict],
        query: Optional[str] = None,
        max_length: Optional[int] = None
    ) -> List[str]:
        """
        Format answer into a Threads post (or thread of posts).
        Returns a list of strings, where each string is a single post in the thread.
        """
        limit = max_length or self.MAX_CHARS
        
        # Threads are similar to Twitter threads but with more capacity (500 chars)
        return self._format_thread_structure(answer, sources, query, limit)

    def _format_thread_structure(
        self,
        answer: str,
        sources: List[Dict],
        query: Optional[str],
        limit: int
    ) -> List[str]:
        posts = []
        
        # First post: Query (if exists) + Intro
        start_text = ""
        if query:
            start_text = f"🧵 {query}\n\n"
        
        # Extract clear points
        key_points = self._extract_key_points(answer, max_points=10)
        
        if not key_points:
            # Fallback to smart chunking
            return self._smart_chunk(answer, limit)

        # Build thread
        current_post = start_text
        
        for point in key_points:
            # Check if point fits in current post
            if len(current_post) + len(point) + 5 < limit:
                current_post += f"• {point}\n\n"
            else:
                # Post is full, append it
                if current_post.strip():
                    posts.append(current_post.strip())
                # Start new post
                current_post = f"• {point}\n\n"
        
        # Append the last post content
        if current_post.strip():
            posts.append(current_post.strip())
            
        # Last post: Sources and Tags
        sources_text = self._format_sources_plain(sources)
        hashtags = self._generate_hashtags(answer, 3)
        tags_text = " ".join(hashtags)
        
        footer = ""
        if sources_text:
            footer += f"\n\nSources:\n{sources_text}"
        if tags_text:
            footer += f"\n\n{tags_text}"
            
        if len(posts[-1] + footer) < limit:
            posts[-1] += footer
        else:
            posts.append(footer.strip())
            
        return posts

    def _smart_chunk(self, text: str, limit: int) -> List[str]:
        """Fallback method to split long text into 500-char chunks."""
        words = text.split()
        chunks = []
        current_chunk = []
        current_len = 0
        
        for word in words:
            if current_len + len(word) + 1 > limit:
                chunks.append(" ".join(current_chunk))
                current_chunk = [word]
                current_len = len(word)
            else:
                current_chunk.append(word)
                current_len += len(word) + 1
        
        if current_chunk:
            chunks.append(" ".join(current_chunk))
            
        return chunks
