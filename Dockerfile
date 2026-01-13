# Dockerfile for AmaniQuery Full Stack Deployment
# Includes: FastAPI API, VibeVoice voice services
# Optimized for HuggingFace Spaces deployment

FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    NODE_ENV=production \
    REDIS_URL=redis://localhost:6379/0 \
    ENABLE_SCHEDULER=true \
    SCHEDULER_BACKEND=apscheduler \
    HF_HOME=/app/models \
    # VibeVoice settings
    ENABLE_VIBEVOICE=true \
    MAX_UPLOAD_SIZE=52428800

# Install system dependencies
RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    curl \
    cmake \
    g++ \
    gcc \
    build-essential \
    redis-server \
    # Audio/voice dependencies for VibeVoice
    ffmpeg \
    libsndfile1 && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy and install main requirements
COPY requirements.txt ./
RUN pip install --no-cache-dir torch
RUN pip install --no-cache-dir -r requirements.txt

# Install VibeVoice dependencies
RUN pip install --no-cache-dir \
    soundfile \
    librosa \
    pydub \
    webrtcvad \
    silero-vad || true

# Pre-download embedding model to bake into image
COPY download_model.py .
RUN python download_model.py

# Copy all source code (including VibeVoice)
COPY . .

# Create required directories
RUN mkdir -p /app/uploads /app/processed /app/temp

# Create non-root user for security
RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app /app/uploads /app/processed /app/temp

USER app

# Expose ports (API + potential WebSocket)
EXPOSE 8000 7860

HEALTHCHECK --interval=30s --timeout=30s --start-period=60s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

# Start Redis and all services together
CMD ["sh", "-c", "redis-server --port 6379 --maxmemory 2gb --maxmemory-policy allkeys-lru --save \"\" --appendonly no --tcp-keepalive 300 --daemonize yes && python start_api.py"]
