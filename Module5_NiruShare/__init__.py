"""
Module 5: NiruShare - Social Media Sharing
"""

__version__ = "1.0.0"

from .service import ShareService
from .formatters import TwitterFormatter, LinkedInFormatter, FacebookFormatter

__all__ = [
    "ShareService",
    "TwitterFormatter",
    "LinkedInFormatter",
    "FacebookFormatter",
]
