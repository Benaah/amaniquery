# Module 5: NiruShare - Social Media Sharing Service

This module provides social media sharing and posting functionality for AmaniQuery responses.

## Features

- **Post Formatting**: Automatically format RAG responses into social media posts
- **Multiple Platforms**: Support for X (Twitter), LinkedIn, Facebook
- **Smart Truncation**: Handle character limits intelligently
- **Hashtag Generation**: Auto-generate relevant hashtags
- **Source Attribution**: Include proper citations
- **Share Links**: Generate shareable URLs
- **Direct Posting**: Post directly to platforms (LinkedIn, Facebook)
- **OAuth Authentication**: Secure authentication flows

## Supported Platforms

### X (Twitter)
- Character limit: 280 characters (with thread support)
- Automatic thread creation for long responses
- Hashtag optimization
- Source links
- **Posting**: Not yet implemented

### LinkedIn
- Character limit: 3000 characters
- Professional formatting
- Rich citations
- **Posting**: ✅ Supported

### Facebook
- No strict character limit
- Engaging format
- **Posting**: ✅ Supported

## Components

### ShareFormatter (`formatters/`)
- Platform-specific formatting
- Truncation with context preservation
- Hashtag generation

### ShareService (`service.py`)
- Share URL generation
- Post preview
- Direct platform posting
- OAuth authentication handling
- Analytics tracking

## API Endpoints

### Formatting & Sharing
- `POST /share/format` - Format response for specific platform
- `POST /share/preview` - Preview formatted post for all platforms
- `POST /share/generate-link` - Generate share link for platform

### Direct Posting
- `POST /share/post` - Post directly to platform (requires authentication)
- `POST /share/auth` - Initiate OAuth authentication
- `POST /share/auth/callback` - Handle OAuth callback

### Utilities
- `GET /share/platforms` - Get supported platforms info
- `POST /share/stats` - Get post statistics

## Authentication Setup

To enable direct posting, configure API credentials in your `.env` file:

```bash
# LinkedIn API
LINKEDIN_CLIENT_ID=your_client_id
LINKEDIN_CLIENT_SECRET=your_client_secret
LINKEDIN_REDIRECT_URI=http://localhost:8000/share/auth/callback

# Facebook API
FACEBOOK_APP_ID=your_app_id
FACEBOOK_APP_SECRET=your_app_secret
FACEBOOK_REDIRECT_URI=http://localhost:8000/share/auth/callback
```

See `social_media_config.env.example` for detailed setup instructions.

## Usage

### Format for Platform
```python
POST /share/format
{
  "answer": "Long answer...",
  "sources": [...],
  "platform": "linkedin"
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

## Security Notes

- Access tokens are stored in environment variables (production should use secure storage)
- OAuth state validation is implemented
- Rate limiting should be added for production use
- User consent is required for posting
