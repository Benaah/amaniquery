"""
Celery Tasks for News Crawling
"""
import sys
from pathlib import Path
from celery import Task
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from .celery_app import celery_app


class CrawlTask(Task):
    """Base task class with error handling"""
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        logger.error(f"Task {task_id} failed: {exc}")
        logger.error(f"Exception info: {einfo}")


@celery_app.task(base=CrawlTask, bind=True, name="crawl_news_sources")
def crawl_news_sources(self, source_names=None):
    """
    Crawl all news sources or specified sources
    
    Args:
        source_names: List of source names to crawl (None = all)
    
    Returns:
        Dictionary with crawl results
    """
    try:
        from scrapy.crawler import CrawlerProcess
        from scrapy.utils.project import get_project_settings
        
        # Import spiders
        from Module1_NiruSpider.niruspider.spiders.news_rss_spider import NewsRSSSpider
        from Module1_NiruSpider.niruspider.spiders.sitemap_spider import SitemapSpider
        
        logger.info(f"Starting crawl task for sources: {source_names or 'all'}")
        
        # Get Scrapy settings
        settings = get_project_settings()
        
        # Create crawler process
        process = CrawlerProcess(settings)
        
        # Add spiders
        spiders_to_run = []
        
        if source_names is None or "news_rss" in source_names:
            spiders_to_run.append(("News RSS", NewsRSSSpider))
        
        if source_names is None or "sitemap" in source_names:
            spiders_to_run.append(("Sitemap", SitemapSpider))
        
        results = {}
        for name, spider_class in spiders_to_run:
            try:
                logger.info(f"Crawling {name}...")
                process.crawl(spider_class)
                results[name] = "started"
            except Exception as e:
                logger.error(f"Error starting {name} spider: {e}")
                results[name] = f"error: {str(e)}"
        
        # Start crawling (blocking)
        process.start()
        
        logger.info("Crawl task completed")
        return {
            "status": "completed",
            "sources": results
        }
        
    except Exception as e:
        logger.error(f"Crawl task failed: {e}")
        raise


@celery_app.task(base=CrawlTask, bind=True, name="crawl_single_source")
def crawl_single_source(self, source_name: str):
    """
    Crawl a single news source
    
    Args:
        source_name: Name of the source to crawl
    
    Returns:
        Dictionary with crawl results
    """
    try:
        from scrapy.crawler import CrawlerProcess
        from scrapy.utils.project import get_project_settings
        
        logger.info(f"Starting crawl for single source: {source_name}")
        
        # Map source names to spider classes
        spider_mapping = {
            "news_rss": "Module1_NiruSpider.niruspider.spiders.news_rss_spider.NewsRSSSpider",
            "sitemap": "Module1_NiruSpider.niruspider.spiders.sitemap_spider.SitemapSpider",
        }
        
        if source_name not in spider_mapping:
            raise ValueError(f"Unknown source: {source_name}")
        
        # Get Scrapy settings
        settings = get_project_settings()
        
        # Create crawler process
        process = CrawlerProcess(settings)
        
        # Import and add spider
        module_path, class_name = spider_mapping[source_name].rsplit('.', 1)
        module = __import__(module_path, fromlist=[class_name])
        spider_class = getattr(module, class_name)
        
        process.crawl(spider_class)
        process.start()
        
        logger.info(f"Crawl completed for {source_name}")
        return {
            "status": "completed",
            "source": source_name
        }
        
    except Exception as e:
        logger.error(f"Crawl task failed for {source_name}: {e}")
        raise


@celery_app.task(base=CrawlTask, bind=True, name="schedule_periodic_crawl")
def schedule_periodic_crawl(self):
    """
    Periodic crawl task (called by Celery Beat)
    Crawls all news sources on a schedule
    """
    return crawl_news_sources.delay()

