"""
Module 5: NiruShare - Social Media Sharing
"""

__version__ = "2.0.0"

from .service import ShareService
from .formatters import TwitterFormatter, LinkedInFormatter, FacebookFormatter
from .formatters.natural_formatter import NaturalFormatter
from .image_generator import ImageGenerator
from .platforms import (
    PlatformRegistry,
    BasePlatform,
    PlatformMetadata,
    TwitterPlatform,
    LinkedInPlatform,
    FacebookPlatform,
    InstagramPlatform,
    RedditPlatform,
    TelegramPlatform,
    WhatsAppPlatform,
    MastodonPlatform,
)

__all__ = [
    "ShareService",
    "TwitterFormatter",
    "LinkedInFormatter",
    "FacebookFormatter",
    "NaturalFormatter",
    "ImageGenerator",
    "PlatformRegistry",
    "BasePlatform",
    "PlatformMetadata",
    "TwitterPlatform",
    "LinkedInPlatform",
    "FacebookPlatform",
    "InstagramPlatform",
    "RedditPlatform",
    "TelegramPlatform",
    "WhatsAppPlatform",
    "MastodonPlatform",
]
