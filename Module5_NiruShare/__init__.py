"""
Module 5: NiruShare - Social Media Sharing
"""

__version__ = "2.0.0"

from .service import ShareService
from .formatters import (
    BaseFormatter,
    TwitterFormatter,
    LinkedInFormatter,
    FacebookFormatter,
    NaturalFormatter,
    BlueskyFormatter,
    ThreadsFormatter,
    TikTokFormatter,
    InstagramFormatter,
    MastodonFormatter,
    RedditFormatter,
    TelegramFormatter,
    WhatsAppFormatter,
)
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
    ThreadsPlatform,
    BlueskyPlatform,
    TikTokPlatform,
)

__all__ = [
    "ShareService",
    "BaseFormatter",
    "TwitterFormatter",
    "LinkedInFormatter",
    "FacebookFormatter",
    "NaturalFormatter",
    "BlueskyFormatter",
    "ThreadsFormatter",
    "TikTokFormatter",
    "InstagramFormatter",
    "MastodonFormatter",
    "RedditFormatter",
    "TelegramFormatter",
    "WhatsAppFormatter",
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
    "ThreadsPlatform",
    "BlueskyPlatform",
    "TikTokPlatform",
]
