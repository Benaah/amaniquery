# AmaniQuery Vision/Multimedia Module

This document describes the multimodal RAG expansion for AmaniQuery, enabling processing of images, PDFs, audio, and video content alongside the existing text pipeline.

## Overview

The vision/multimedia module extends AmaniQuery's RAG capabilities to handle:
- **Images**: OCR extraction, visual embedding, visual QA
- **PDFs**: Page extraction, OCR, multi-page processing
- **Audio**: Speech-to-text transcription, audio RAG
- **Video**: Frame extraction, audio transcription, video QA

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                        API Layer                                │
│   /api/v1/media/upload  →  File Type Detection  →  Router      │
└─────────────────────────────────────────────────────────────────┘
                                │
        ┌───────────────────────┼───────────────────────┐
        ▼                       ▼                       ▼
┌───────────────┐     ┌───────────────┐     ┌───────────────┐
│ Image/PDF     │     │ Video         │     │ Audio         │
│ Processor     │     │ Processor     │     │ Processor     │
│               │     │               │     │               │
│ - OCR         │     │ - Frame       │     │ - Whisper STT │
│ - Embedding   │     │   Extraction  │     │ - Embedding   │
│ - VQA         │     │ - Audio Track │     │ - Segments    │
└───────┬───────┘     └───────┬───────┘     └───────┬───────┘
        │                     │                     │
        └──────────────────┬──┴─────────────────────┘
                           ▼
            ┌───────────────────────────────┐
            │ Multimodal Storage Service    │
            │ (PostgreSQL + Cloudinary)     │
            │                               │
            │ - Session management          │
            │ - Asset lifecycle             │
            │ - Embedding storage           │
            └───────────────┬───────────────┘
                            ▼
            ┌───────────────────────────────┐
            │ VisionRAGService              │
            │                               │
            │ - Multimodal retrieval        │
            │ - Visual question answering   │
            │ - Unified query interface     │
            └───────────────────────────────┘
```

## Components

### 1. Video Processor (`Module4_NiruAPI/services/video_processor.py`)

Extracts frames and audio from video files:

```python
from Module4_NiruAPI.services.video_processor import VideoProcessor

processor = VideoProcessor()
result = processor.process_video(
    video_path="path/to/video.mp4",
    num_frames=10,
    extract_audio=True,
)

print(f"Extracted {len(result.frames)} frames")
print(f"Audio at: {result.audio_path}")
```

### 2. Whisper Provider (`Module6_NiruVoice/providers/whisper_provider.py`)

Audio transcription with OpenAI Whisper API and local fallback:

```python
from Module6_NiruVoice.providers import WhisperProvider

provider = WhisperProvider()
result = provider.transcribe("path/to/audio.wav")

print(f"Transcript: {result.text}")
print(f"Language: {result.language}")
print(f"Duration: {result.duration}s")
```

### 3. Extended VisionRAGService (`Module4_NiruAPI/services/vision_rag.py`)

Now supports video and audio in addition to images:

```python
from Module4_NiruAPI.services.vision_rag import VisionRAGService

service = VisionRAGService(
    enable_video=True,
    enable_audio=True,
)

# Process video
video_result = service.process_video(
    "path/to/video.mp4",
    num_frames=10,
    transcribe_audio=True,
)

# Transcribe audio
audio_result = service.embed_audio_transcript("path/to/audio.wav")

# Unified multimodal query
query_result = service.query_multimodal(
    question="What was discussed in the video?",
    session_images=video_result["frames"],
    session_transcripts=[audio_result],
)
```

### 4. Multimodal Storage (`Module4_NiruAPI/services/multimodal_storage.py`)

Persistent storage for media assets:

```python
from Module4_NiruAPI.services.multimodal_storage import MultimodalStorageService

storage = MultimodalStorageService()

# Create session
session = storage.create_session(user_id="user123")

# Add asset
asset = storage.add_asset(
    session_id=session["id"],
    file_type="image",
    file_name="photo.jpg",
    embedding=[0.1, 0.2, ...],
)

# Retrieve for RAG
rag_data = storage.get_session_assets_for_rag(session["id"])
```

### 5. Media Router (`Module4_NiruAPI/routers/media_router.py`)

Unified API endpoint for media upload:

```bash
# Upload any media type
curl -X POST "http://localhost:8000/api/v1/media/upload" \
  -F "file=@video.mp4" \
  -F "session_id=vsession_abc123"

# Check processing status
curl "http://localhost:8000/api/v1/media/assets/{asset_id}"
```

## Configuration

### Environment Variables

```bash
# Feature Flags
ENABLE_VISION_RAG=true      # Enable image/PDF processing
ENABLE_VIDEO_RAG=true       # Enable video processing
ENABLE_AUDIO_RAG=true       # Enable audio transcription

# File Size Limits
MAX_IMAGE_SIZE_MB=10
MAX_VIDEO_SIZE_MB=100
MAX_AUDIO_SIZE_MB=50
MAX_PDF_SIZE_MB=20

# Video Processing
VIDEO_FRAME_COUNT=10
VIDEO_FRAME_STRATEGY=fixed_interval

# Audio Processing
AUDIO_MODEL=whisper-1
AUDIO_USE_LOCAL_FALLBACK=true

# Storage
MULTIMODAL_STORAGE_BACKEND=database
ASSET_EXPIRY_HOURS=24

# API Keys
COHERE_API_KEY=your-key      # For embeddings
GEMINI_API_KEY=your-key      # For visual QA
OPENAI_API_KEY=your-key      # For Whisper
```

## Database Migration

Run the migration to create vision assets tables:

```bash
python migrations/create_vision_assets.py
```

## Dependencies

Add to `requirements.txt`:

```
# Vision/Multimodal
opencv-python>=4.8.0
Pillow>=10.0.0
google-generativeai>=0.3.0
cohere>=4.0.0

# Audio
openai>=1.0.0
openai-whisper>=20231117  # For local Whisper fallback

# Video (system dependency)
# ffmpeg must be installed on system
```

## Resilience

The module includes circuit breaker and retry patterns:

```python
from Module4_NiruAPI.services.media_resilience import (
    get_vision_processor,
    get_transcription_processor,
)

# Get resilient processor
processor = get_vision_processor()

# Execute with automatic retry and circuit breaker
result = await processor.process_async(
    embed_function,
    image_path,
    fallback=text_only_fallback,
)

# Check health
health = processor.get_health_status()
```

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/v1/media/sessions` | Create media session |
| GET | `/api/v1/media/sessions/{id}` | Get session details |
| DELETE | `/api/v1/media/sessions/{id}` | Delete session and assets |
| POST | `/api/v1/media/upload` | Upload and process media |
| GET | `/api/v1/media/assets/{id}` | Get asset details |
| DELETE | `/api/v1/media/assets/{id}` | Delete asset |
| POST | `/api/v1/media/assets/{id}/reprocess` | Retry failed processing |
| GET | `/api/v1/media/health` | Check service health |

## Supported File Types

| Type | Extensions | Processing |
|------|------------|------------|
| Image | jpg, jpeg, png, gif, webp, bmp | OCR, embedding, VQA |
| PDF | pdf | Page extraction, OCR, embedding |
| Audio | mp3, wav, m4a, flac, ogg, aac | Transcription, embedding |
| Video | mp4, avi, mov, mkv, webm | Frame extraction, audio, VQA |

## Future Enhancements

1. **Scene Detection**: Smart frame extraction based on scene changes
2. **Object Detection**: YOLO-based object recognition in images/video
3. **Speaker Diarization**: Identify speakers in audio
4. **Multi-language OCR**: PaddleOCR integration for better multilingual support
5. **Streaming Processing**: Real-time video/audio analysis
6. **CLIP/BLIP Integration**: Advanced vision-text matching

## Troubleshooting

### ffmpeg not found
Install ffmpeg:
- Windows: `choco install ffmpeg` or download from https://ffmpeg.org
- macOS: `brew install ffmpeg`
- Linux: `apt install ffmpeg`

### OpenCV import error
Ensure you have the correct OpenCV package:
```bash
pip install opencv-python-headless  # For servers without GUI
```

### Whisper local model loading slow
The local Whisper model is loaded on first use. Consider:
- Using the "tiny" or "base" model for faster loading
- Pre-warming the model on startup
- Using OpenAI API as primary with local fallback
