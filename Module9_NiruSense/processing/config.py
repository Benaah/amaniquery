import os
from pydantic import BaseSettings

class Settings(BaseSettings):
    # Redis
    REDIS_HOST: str = "localhost"
    REDIS_PORT: int = 6379
    REDIS_STREAM_KEY: str = "niru_ingestion_stream"
    REDIS_CONSUMER_GROUP: str = "niru_processing_group"

    # Postgres (Neon.tech)
    DATABASE_URL: str = "postgresql://user:password@ep-xyz.aws.neon.tech/sautisense?sslmode=require"

    # Qdrant (Cloud)
    QDRANT_URL: str = "https://xyz-example.eu-central.aws.cloud.qdrant.io:6333"
    QDRANT_API_KEY: str = "your-api-key"
    QDRANT_COLLECTION: str = "amaniquery_sense"

    # Model IDs (HuggingFace)
    MODEL_EMBEDDING: str = "nomic-ai/nomic-embed-text-v1.5"
    MODEL_LANGUAGE: str = "Davlan/afro-xlmr-mini"
    MODEL_TOPIC: str = "MoritzLaurer/mDeBERTa-v3-base-mnli-xnli"
    MODEL_NER: str = "Davlan/xlm-roberta-base-ner-hrl"
    MODEL_SENTIMENT: str = "Davlan/afro-xlmr-mini" # Fine-tuned head
    MODEL_SUMMARIZER: str = "google/mt5-small"

    class Config:
        env_file = ".env"

settings = Settings()
