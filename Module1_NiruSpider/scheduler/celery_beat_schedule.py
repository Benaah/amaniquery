"""
Celery Beat Schedule Configuration
"""
from celery.schedules import crontab

# Schedule for periodic news crawling
beat_schedule = {
    # Crawl Kenyan news every 6 hours
    "crawl-kenyan-news": {
        "task": "Module1_NiruSpider.scheduler.celery_tasks.crawl_news_sources",
        "schedule": crontab(minute=0, hour="*/6"),  # Every 6 hours
        "args": (["news_rss"],),
    },
    
    # Crawl sitemaps daily at 2 AM
    "crawl-sitemaps": {
        "task": "Module1_NiruSpider.scheduler.celery_tasks.crawl_news_sources",
        "schedule": crontab(minute=0, hour=2),  # Daily at 2 AM
        "args": (["sitemap"],),
    },
}

