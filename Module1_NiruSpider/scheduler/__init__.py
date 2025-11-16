"""
Scheduler Module for Async News Crawling
"""
from .celery_app import celery_app
from .celery_tasks import crawl_news_sources, crawl_single_source

__all__ = ["celery_app", "crawl_news_sources", "crawl_single_source"]

