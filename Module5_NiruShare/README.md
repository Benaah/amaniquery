# Module 5: NiruShare - Social Media Sharing Service

This module provides social media sharing functionality for AmaniQuery responses.

## Features

- **Post Formatting**: Automatically format RAG responses into social media posts
- **Multiple Platforms**: Support for X (Twitter), LinkedIn, Facebook
- **Smart Truncation**: Handle character limits intelligently
- **Hashtag Generation**: Auto-generate relevant hashtags
- **Source Attribution**: Include proper citations
- **Share Links**: Generate shareable URLs

## Supported Platforms

### X (Twitter)
- Character limit: 280 characters (with thread support)
- Automatic thread creation for long responses
- Hashtag optimization
- Source links

### LinkedIn
- Character limit: 3000 characters
- Professional formatting
- Rich citations

### Facebook
- No strict character limit
- Engaging format

## Components

### ShareFormatter (`formatters/`)
- Platform-specific formatting
- Truncation with context preservation
- Hashtag generation

### ShareService (`service.py`)
- Share URL generation
- Post preview
- Analytics tracking

## API Endpoints

### `POST /share/format`
Format response for specific platform

### `POST /share/preview`
Preview formatted post

### `POST /share/generate-link`
Generate share link for platform

## Usage

### Format for X (Twitter)
```python
POST /share/format
{
  "answer": "Long answer...",
  "sources": [...],
  "platform": "twitter"
}
```

### Generate Share Link
```python
POST /share/generate-link
{
  "formatted_post": "...",
  "platform": "twitter"
}
```
