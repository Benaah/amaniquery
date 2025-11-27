"""
Celery Beat Schedule Configuration

This defines the automatic scheduling for all crawlers to keep the vector store
up to date with new legal documents and news.

Schedule Overview:
- News RSS: Every 4 hours (breaking news)
- Global Trends: Every 6 hours (international news)
- Parliament: Every 12 hours (Hansards, Bills)
- Parliament Videos: Daily at 3 AM
- Kenya Law: Every 2 days at 2 AM (comprehensive legal database)
- Vector Store Update: After each crawl batch
- Health Check: Every 30 minutes
"""
from celery.schedules import crontab

# Schedule for periodic crawling
beat_schedule = {
    # ============== HIGH FREQUENCY ==============
    
    # Crawl Kenyan news every 4 hours
    # Breaking news needs frequent updates
    "crawl-news-rss-4h": {
        "task": "run_crawler",
        "schedule": crontab(minute=0, hour="*/4"),  # Every 4 hours
        "args": ("news_rss",),
        "options": {"queue": "crawling"},
    },
    
    # Crawl global trends every 6 hours
    "crawl-global-trends-6h": {
        "task": "run_crawler",
        "schedule": crontab(minute=30, hour="*/6"),  # Every 6 hours, offset by 30 min
        "args": ("global_trends",),
        "options": {"queue": "crawling"},
    },
    
    # ============== MEDIUM FREQUENCY ==============
    
    # Crawl Parliament (Hansards, Bills) every 12 hours
    "crawl-parliament-12h": {
        "task": "run_crawler",
        "schedule": crontab(minute=0, hour="6,18"),  # 6 AM and 6 PM
        "args": ("parliament",),
        "options": {"queue": "crawling"},
    },
    
    # ============== LOW FREQUENCY ==============
    
    # Crawl Parliament videos daily at 3 AM
    "crawl-parliament-videos-daily": {
        "task": "run_crawler",
        "schedule": crontab(minute=0, hour=3),  # Daily at 3 AM
        "args": ("parliament_videos",),
        "options": {"queue": "crawling"},
    },
    
    # Crawl Kenya Law every 2 days at 2 AM
    # This is a comprehensive crawl of the legal database
    "crawl-kenya-law-48h": {
        "task": "run_crawler",
        "schedule": crontab(minute=0, hour=2, day_of_week="0,2,4,6"),  # Every other day
        "args": ("kenya_law",),
        "options": {"queue": "crawling"},
    },
    
    # ============== MAINTENANCE ==============
    
    # Update vector store every 4 hours (after news crawls)
    "update-vector-store-4h": {
        "task": "update_vector_store",
        "schedule": crontab(minute=45, hour="*/4"),  # 45 min after news crawl
        "kwargs": {"incremental": True},
        "options": {"queue": "crawling"},
    },
    
    # Full vector store rebuild weekly on Sunday at 4 AM
    "rebuild-vector-store-weekly": {
        "task": "update_vector_store",
        "schedule": crontab(minute=0, hour=4, day_of_week="0"),  # Sunday 4 AM
        "kwargs": {"incremental": False},
        "options": {"queue": "crawling"},
    },
    
    # Health check every 30 minutes
    "scheduler-health-check": {
        "task": "scheduler_health_check",
        "schedule": crontab(minute="*/30"),  # Every 30 minutes
    },
}


# Alternative schedules for different environments

# Development schedule - more frequent for testing
beat_schedule_dev = {
    "crawl-news-rss-dev": {
        "task": "run_crawler",
        "schedule": crontab(minute="*/30"),  # Every 30 minutes
        "args": ("news_rss",),
    },
    "health-check-dev": {
        "task": "scheduler_health_check",
        "schedule": crontab(minute="*/5"),  # Every 5 minutes
    },
}

# Minimal schedule - for low-resource environments
beat_schedule_minimal = {
    "crawl-news-daily": {
        "task": "crawl_news_sources",
        "schedule": crontab(minute=0, hour=8),  # Daily at 8 AM
    },
    "crawl-legal-weekly": {
        "task": "crawl_legal_sources",
        "schedule": crontab(minute=0, hour=2, day_of_week="0"),  # Sunday 2 AM
    },
}

