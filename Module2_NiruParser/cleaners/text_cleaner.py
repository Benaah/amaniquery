"""
Text Cleaner - Clean and normalize extracted text
"""
import re
import unicodedata
from typing import str
from loguru import logger


class TextCleaner:
    """Clean and normalize text"""
    
    def __init__(self):
        # Patterns to clean
        self.patterns = {
            # Multiple whitespace
            "whitespace": re.compile(r'\s+'),
            # Multiple newlines
            "newlines": re.compile(r'\n{3,}'),
            # HTML entities
            "html_entities": re.compile(r'&[a-zA-Z]+;'),
            # URLs (optional - keep for context)
            # "urls": re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+'),
            # Email addresses (optional - keep for context)
            # "emails": re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'),
        }
    
    def clean(self, text: str, aggressive: bool = False) -> str:
        """
        Clean and normalize text
        
        Args:
            text: Raw text
            aggressive: If True, apply more aggressive cleaning
        
        Returns:
            Cleaned text
        """
        if not text:
            return ""
        
        try:
            # Normalize Unicode
            text = unicodedata.normalize('NFKC', text)
            
            # Remove HTML entities
            text = self.patterns["html_entities"].sub(' ', text)
            
            # Remove excessive newlines (keep paragraph breaks)
            text = self.patterns["newlines"].sub('\n\n', text)
            
            # Normalize whitespace
            text = self.patterns["whitespace"].sub(' ', text)
            
            # Remove leading/trailing whitespace from each line
            lines = [line.strip() for line in text.split('\n')]
            text = '\n'.join(line for line in lines if line)
            
            if aggressive:
                # Remove very short lines (likely artifacts)
                lines = [line for line in text.split('\n') if len(line) > 20]
                text = '\n'.join(lines)
                
                # Remove lines that are mostly numbers/special chars
                lines = []
                for line in text.split('\n'):
                    alpha_ratio = sum(c.isalpha() for c in line) / max(len(line), 1)
                    if alpha_ratio > 0.5:  # At least 50% alphabetic
                        lines.append(line)
                text = '\n'.join(lines)
            
            # Final cleanup
            text = text.strip()
            
            return text
            
        except Exception as e:
            logger.error(f"Error cleaning text: {e}")
            return text
    
    def remove_boilerplate(self, text: str) -> str:
        """Remove common boilerplate text"""
        # Common phrases to remove
        boilerplate_phrases = [
            r'Cookie Policy',
            r'Privacy Policy',
            r'Terms of Service',
            r'Subscribe to our newsletter',
            r'Share this article',
            r'Follow us on',
            r'Advertisement',
        ]
        
        for phrase in boilerplate_phrases:
            text = re.sub(phrase, '', text, flags=re.IGNORECASE)
        
        return text
    
    def fix_encoding(self, text: str) -> str:
        """Fix common encoding issues"""
        # Common encoding fixes
        replacements = {
            'â€™': "'",
            'â€œ': '"',
            'â€': '"',
            'â€"': '—',
            'â€"': '–',
            'Ã©': 'é',
            'Ã¨': 'è',
            'Ã¡': 'á',
        }
        
        for wrong, right in replacements.items():
            text = text.replace(wrong, right)
        
        return text
