# NiruSense Ingestion Services

This module contains three independent ingestion services for Sauti-Sense:
1.  **Twitter Scraper**: Nitter rotation + Playwright fallback.
2.  **TikTok Scraper**: Playwright with stealth plugin.
3.  **News Scraper**: RSS feeds + Newspaper3k.

## Prerequisites

1.  **Python 3.10+**
2.  **Redis** running locally (or configured in `.env`).
3.  **MinIO** running locally (or configured in `.env`).

## Setup

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    playwright install
    playwright install-deps
    ```

2.  Configure `.env`:
    Create a `.env` file in `Module9_NiruSense/ingestion/common/` (or root) with:
    ```env
    MINIO_ENDPOINT=localhost:9000
    MINIO_ACCESS_KEY=admin
    MINIO_SECRET_KEY=miniopassword123
    MINIO_BUCKET_RAW=bronze-raw
    
    REDIS_HOST=localhost
    REDIS_PORT=6379
    ```

## Running the Services

Each service runs as a standalone process. You can run them in separate terminals or using a process manager like Supervisor or Docker.

### 1. Twitter Scraper
```bash
python -m Module9_NiruSense.ingestion.twitter.main
```

### 2. TikTok Scraper
```bash
python -m Module9_NiruSense.ingestion.tiktok.main
```

### 3. News Scraper
```bash
python -m Module9_NiruSense.ingestion.news.main
```

## Monitoring

- **Logs**: Each service prints logs to stdout.
- **Data**: Check MinIO bucket `bronze-raw` for JSON files.
- **Events**: Monitor Redis stream `niru_ingestion_stream`.
