"""
Metadata Enricher - Enhance chunks with additional metadata
"""
from typing import Dict, List
from datetime import datetime
from loguru import logger
import re


class MetadataEnricher:
    """Enrich chunks with additional metadata"""
    
    def __init__(self):
        pass
    
    def enrich(self, chunk: Dict) -> Dict:
        """
        Enrich a single chunk with metadata
        
        Args:
            chunk: Chunk dictionary
        
        Returns:
            Enriched chunk
        """
        try:
            # Add processing timestamp
            chunk["processed_at"] = datetime.utcnow().isoformat()
            
            # Extract keywords from chunk text
            if "text" in chunk and not chunk.get("keywords"):
                chunk["keywords"] = self._extract_keywords(chunk["text"])
            
            # Generate summary if text is long enough
            if "text" in chunk and len(chunk["text"]) > 200:
                if not chunk.get("summary"):
                    chunk["summary"] = self._generate_summary(chunk["text"])
            
            # Calculate text statistics
            chunk["char_count"] = len(chunk.get("text", ""))
            chunk["word_count"] = len(chunk.get("text", "").split())
            
            # Ensure required fields exist
            chunk.setdefault("source_url", "unknown")
            chunk.setdefault("title", "Untitled")
            chunk.setdefault("category", "Unknown")
            
            return chunk
            
        except Exception as e:
            logger.error(f"Error enriching chunk: {e}")
            return chunk
    
    def enrich_batch(self, chunks: List[Dict]) -> List[Dict]:
        """Enrich multiple chunks"""
        return [self.enrich(chunk) for chunk in chunks]
    
    def _extract_keywords(self, text: str, max_keywords: int = 10) -> List[str]:
        """
        Extract keywords from text
        (Simple implementation - can be enhanced with NLP)
        """
        # Convert to lowercase
        text = text.lower()
        
        # Remove punctuation
        text = re.sub(r'[^\w\s]', ' ', text)
        
        # Split into words
        words = text.split()
        
        # Remove common stop words
        stop_words = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'as', 'is', 'was', 'are', 'were', 'be',
            'been', 'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'should', 'could', 'may', 'might', 'must', 'can', 'this',
            'that', 'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
        }
        
        # Filter words
        words = [w for w in words if w not in stop_words and len(w) > 3]
        
        # Count frequency
        word_freq = {}
        for word in words:
            word_freq[word] = word_freq.get(word, 0) + 1
        
        # Sort by frequency
        sorted_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)
        
        # Return top keywords
        keywords = [word for word, freq in sorted_words[:max_keywords]]
        return keywords
    
    def _generate_summary(self, text: str, max_length: int = 200) -> str:
        """
        Generate a summary of the text
        (Simple implementation - first sentence or first N chars)
        """
        # Try to get first sentence
        sentences = re.split(r'[.!?]+', text)
        first_sentence = sentences[0].strip() if sentences else ""
        
        if len(first_sentence) > max_length:
            # Truncate to max_length
            summary = text[:max_length].rsplit(' ', 1)[0] + "..."
        else:
            summary = first_sentence + "."
        
        return summary
    
    def validate_metadata(self, chunk: Dict, required_fields: List[str]) -> bool:
        """Validate that chunk has all required metadata fields"""
        return all(field in chunk for field in required_fields)
