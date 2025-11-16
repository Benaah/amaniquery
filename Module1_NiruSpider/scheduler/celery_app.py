"""
Celery Application Configuration
"""
import os
from celery import Celery
from loguru import logger

# Get Redis URL from environment
redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

# Create Celery app
celery_app = Celery(
    "niruspider",
    broker=redis_url,
    backend=redis_url,
    include=["Module1_NiruSpider.scheduler.celery_tasks"]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,  # 1 hour max per task
    task_soft_time_limit=3300,  # 55 minutes soft limit
    worker_prefetch_multiplier=1,  # Prefetch one task at a time
    worker_max_tasks_per_child=50,  # Restart worker after 50 tasks
    task_acks_late=True,  # Acknowledge tasks after completion
    task_reject_on_worker_lost=True,
)

# Task routing
celery_app.conf.task_routes = {
    "Module1_NiruSpider.scheduler.celery_tasks.*": {"queue": "crawling"},
}

logger.info("Celery app configured")

