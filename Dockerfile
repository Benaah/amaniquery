# Dockerfile for FastAPI backend deployment
FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    NODE_ENV=production \
    REDIS_URL=redis://localhost:6379/0

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        cmake \
        g++ \
        gcc \
        build-essential \
        redis-server && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=30s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

CMD ["sh", "-c", "redis-server --port 6379 --maxmemory 2gb --maxmemory-policy allkeys-lru --save \"\" --appendonly no --tcp-keepalive 300 --daemonize yes && python start_api.py"]
