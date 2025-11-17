# Module 5: NiruShare - Social Media Sharing Service

A robust, scalable social media sharing service with plugin-based architecture, natural post formatting, and image generation capabilities.

## Features

- **Plugin-Based Architecture**: Extensible platform system for easy addition of new social media platforms
- **Natural Post Formatting**: LLM-powered formatting for conversational, human-like posts
- **Multiple Formatting Styles**: Professional, casual, and engaging styles
- **Image Generation**: Create shareable images from text content with customizable templates
- **Multi-Platform Support**: Support for 8+ platforms (Twitter, LinkedIn, Facebook, Instagram, Reddit, Telegram, WhatsApp, Mastodon)
- **Smart Truncation**: Intelligent text truncation respecting platform limits
- **Hashtag Generation**: Auto-generate relevant hashtags based on content
- **Source Attribution**: Include proper citations and references
- **Share Links**: Generate platform-specific shareable URLs
- **Direct Posting**: Post directly to platforms (where supported)
- **OAuth Authentication**: Secure authentication flows
- **Caching**: In-memory caching for improved performance
- **Error Handling**: Comprehensive error handling with graceful degradation

## Supported Platforms

### X (Twitter)
- Character limit: 280 characters (with thread support)
- Automatic thread creation for long responses
- Hashtag optimization
- Source links
- **Posting**: ✅ Supported (requires API credentials)

### LinkedIn
- Character limit: 3000 characters
- Professional formatting
- Rich citations
- **Posting**: ✅ Supported

### Facebook
- No strict character limit
- Engaging format
- **Posting**: ✅ Supported

### Instagram
- Character limit: 2200 characters
- Image-focused platform
- Hashtag support (up to 15)
- **Posting**: Requires Instagram Graph API

### Reddit
- Character limit: 40,000 characters
- Markdown formatting support
- Link formatting
- **Posting**: Requires Reddit API

### Telegram
- Character limit: 4096 characters
- Markdown formatting
- Link support
- **Posting**: Requires Telegram Bot API

### WhatsApp
- No strict character limit (kept concise)
- Link support
- **Posting**: Requires WhatsApp Business API

### Mastodon
- Character limit: 500 characters
- Thread support via replies
- Hashtag support
- **Posting**: Requires Mastodon API

## Architecture

### Plugin System

The module uses a plugin-based architecture for easy extensibility:

- **BasePlatform**: Abstract base class defining platform interface
- **PlatformRegistry**: Central registry for managing platform plugins
- **Platform Plugins**: Individual platform implementations

To add a new platform, simply:
1. Create a class extending `BasePlatform`
2. Implement required methods
3. Register with the registry

### Components

#### ShareService (`service.py`)
- Platform registry management
- Post formatting with caching
- Share URL generation
- Direct platform posting
- Image generation
- OAuth authentication handling

#### Formatters (`formatters/`)
- **BaseFormatter**: Base class with common utilities
- **NaturalFormatter**: LLM-powered natural language formatting
- **Platform Formatters**: Platform-specific formatting (Twitter, LinkedIn, etc.)

#### Image Generator (`image_generator.py`)
- Text-to-image generation using PIL/Pillow
- Multiple color schemes (default, dark, professional, vibrant)
- Customizable dimensions and formats
- Branded templates

#### Platform Plugins (`platforms/`)
- Individual platform handlers
- Platform-specific metadata
- Share link generation
- Posting implementations

## API Endpoints

### Formatting & Sharing
- `POST /share/format` - Format response for specific platform
  - Supports `style` parameter (professional, casual, engaging)
- `POST /share/preview` - Preview formatted post for all platforms
- `POST /share/generate-link` - Generate share link for platform

### Image Generation
- `POST /share/generate-image` - Generate image from text
- `POST /share/generate-image-from-post` - Generate image from formatted post

### Direct Posting
- `POST /share/post` - Post directly to platform (requires authentication)
- `POST /share/auth` - Initiate OAuth authentication
- `POST /share/auth/callback` - Handle OAuth callback

### Utilities
- `GET /share/platforms` - Get supported platforms info
- `POST /share/stats` - Get post statistics

## Usage Examples

### Format for Platform with Style
```python
POST /share/format
{
  "answer": "Long answer about Kenyan Constitution...",
  "sources": [...],
  "platform": "linkedin",
  "query": "What does the Constitution say?",
  "style": "professional",
  "include_hashtags": true
}
```

### Generate Image
```python
POST /share/generate-image
{
  "text": "The Kenyan Constitution protects freedom of expression...",
  "title": "Constitutional Rights",
  "color_scheme": "professional",
  "format": "PNG",
  "width": 1080,
  "height": 1080
}
```

### Preview All Platforms
```python
POST /share/preview
{
  "answer": "Recent parliamentary debates focused on...",
  "sources": [...],
  "query": "What are recent Parliament debates about?",
  "style": "casual"
}
```

### Direct Posting (After Authentication)
```python
POST /share/post
{
  "platform": "linkedin",
  "content": "Formatted post content...",
  "message_id": "optional_chat_message_id"
}
```

### Authentication Flow
```python
# 1. Initiate auth
POST /share/auth
{
  "platform": "linkedin"
}

# 2. Redirect user to auth_url, then handle callback
POST /share/auth/callback
{
  "platform": "linkedin",
  "code": "auth_code_from_platform"
}
```

## Configuration

### Environment Variables

```bash
# LinkedIn API
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
LINKEDIN_REDIRECT_URI=http://localhost:8000/share/auth/callback

# Facebook API
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
FACEBOOK_REDIRECT_URI=http://localhost:8000/share/auth/callback

# Twitter API
TWITTER_CLIENT_ID=your_client_id

# LLM for Natural Formatting (optional)
OPENAI_API_KEY=your_key  # or
ANTHROPIC_API_KEY=your_key  # or
GEMINI_API_KEY=your_key  # or
MOONSHOT_API_KEY=your_key
```

### Dependencies

Required:
- `fastapi` - API framework
- `pydantic` - Data validation
- `requests` - HTTP client

Optional:
- `Pillow` - Image generation (`pip install Pillow`)
- `openai` - Natural formatting with OpenAI
- `anthropic` - Natural formatting with Claude
- `google-generativeai` - Natural formatting with Gemini

## Natural Formatting

The module includes an LLM-powered natural formatter that creates conversational, human-like posts:

- **Professional**: Authoritative, structured language
- **Casual**: Conversational, friendly tone
- **Engaging**: Enthusiastic, attention-grabbing

The natural formatter uses LLM providers (OpenAI, Anthropic, Gemini, Moonshot) to rewrite content in a more natural style. Falls back to rule-based formatting if LLM is unavailable.

## Image Generation

Generate shareable images from text content:

- **Color Schemes**: default, dark, professional, vibrant
- **Formats**: PNG, JPEG
- **Customizable**: Width, height, padding
- **Branded**: Includes AmaniQuery branding

Images are returned as base64-encoded strings for easy integration.

## Caching

The service includes in-memory caching for formatted posts:

- **TTL**: Configurable time-to-live (default: 1 hour)
- **Automatic**: Caching enabled by default
- **Configurable**: Can be disabled or customized

## Error Handling

- Comprehensive error handling with clear messages
- Graceful degradation when services unavailable
- Logging for debugging and monitoring
- Validation of inputs and platform support

## Security Notes

- Access tokens should be stored securely (not in environment variables in production)
- OAuth state validation recommended
- Rate limiting should be added for production use
- User consent required for posting
- API keys should be kept secure

## Extending the Module

### Adding a New Platform

1. Create a new file in `platforms/`:
```python
from .base_platform import BasePlatform, PlatformMetadata

class MyPlatform(BasePlatform):
    def get_metadata(self) -> PlatformMetadata:
        return PlatformMetadata(
            name="myplatform",
            display_name="My Platform",
            char_limit=500,
            # ... other metadata
        )
    
    def format_post(self, answer, sources, query=None, include_hashtags=True, style=None):
        # Implementation
        pass
    
    def generate_share_link(self, content, url=None):
        # Implementation
        pass
```

2. Register in `service.py`:
```python
from .platforms.my_platform import MyPlatform

# In _register_default_platforms:
platforms = [
    # ... existing platforms
    MyPlatform(),
]
```

3. The platform will be automatically available via the API!

## Performance

- **Caching**: Reduces redundant formatting operations
- **Async Support**: API endpoints are async-ready
- **Efficient**: Minimal overhead for platform registry lookups
- **Scalable**: Plugin architecture allows horizontal scaling

## License

Part of the AmaniQuery project.
