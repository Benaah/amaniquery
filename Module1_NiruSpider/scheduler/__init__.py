"""
Scheduler Module for Automated Crawler Scheduling

This module provides automatic scheduling for AmaniQuery crawlers to keep
the vector store up to date with new legal documents and news.

Two backends are supported:
1. Celery + Redis (production, distributed)
2. APScheduler (standalone, no Redis required)

Quick Start:
    # Using APScheduler (standalone)
    python -m Module1_NiruSpider.scheduler.scheduler_service --backend apscheduler
    
    # Using Celery (requires Redis)
    celery -A Module1_NiruSpider.scheduler.celery_app worker --beat -Q crawling

Programmatic Usage:
    from Module1_NiruSpider.scheduler import SchedulerService, CrawlerType
    
    service = SchedulerService(backend="apscheduler")
    service.start()
    
    # Manually trigger a crawler
    service.trigger_crawler(CrawlerType.NEWS_RSS)
"""

from .celery_app import celery_app
from .celery_tasks import (
    run_crawler_task,
    crawl_news_sources,
    crawl_legal_sources,
    crawl_all_sources,
    update_vector_store,
)
from .scheduler_service import (
    SchedulerService,
    SchedulerConfig,
    CrawlerSchedule,
    CrawlerType,
    CrawlerRunner,
    APSchedulerBackend,
    CeleryBackend,
)

__all__ = [
    # Celery
    "celery_app",
    "run_crawler_task",
    "crawl_news_sources",
    "crawl_legal_sources",
    "crawl_all_sources",
    "update_vector_store",
    
    # Scheduler Service
    "SchedulerService",
    "SchedulerConfig",
    "CrawlerSchedule",
    "CrawlerType",
    "CrawlerRunner",
    "APSchedulerBackend",
    "CeleryBackend",
]

