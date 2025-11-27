# NiruSense Processing Layer

This module contains the core processing logic for Sauti-Sense, including the Orchestrator and the 9 specialized agents.

## Components

1.  **Orchestrator**: Consumes events from Redis and manages the pipeline.
2.  **Agents**:
    *   **Core**: LanguageID, SlangDecoder
    *   **Analysis**: Topic, Entity, Sentiment, Emotion
    *   **High-Level**: Bias, Summarizer, Quality
3.  **Storage**: Postgres (Neon.tech) and Qdrant.

## Setup

1.  Install dependencies:
    ```bash
    pip install -r requirements.txt
    ```

2.  Configure `.env`:
    Create a `.env` file in `Module9_NiruSense/processing/` (or root) with:
    ```env
    REDIS_HOST=localhost
    REDIS_PORT=6379
    
    POSTGRES_DSN=postgresql://user:password@ep-xyz.aws.neon.tech/sautisense?sslmode=require
    
    QDRANT_HOST=localhost
    QDRANT_PORT=6333
    ```

## Running the Orchestrator

```bash
python -m Module9_NiruSense.processing.orchestrator
```

The orchestrator will start listening for events on the Redis stream `niru_ingestion_stream`.
