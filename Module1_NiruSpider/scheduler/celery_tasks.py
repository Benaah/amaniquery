"""
Celery Tasks for Crawler Scheduling

These tasks handle the actual crawling work when using Celery as the scheduler backend.
Each task runs a specific spider with proper error handling and timeout management.
"""
import sys
import subprocess
from pathlib import Path
from celery import Task
from celery.exceptions import SoftTimeLimitExceeded
from datetime import datetime
from loguru import logger

# Add project root to path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from .celery_app import celery_app


class CrawlTask(Task):
    """Base task class with error handling and retry logic"""
    
    autoretry_for = (Exception,)
    retry_kwargs = {'max_retries': 3}
    retry_backoff = True
    retry_backoff_max = 600  # Max 10 minutes between retries
    retry_jitter = True
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        crawler_name = args[0] if args else "unknown"
        logger.error(f"Task {task_id} ({crawler_name}) failed: {exc}")
        logger.error(f"Exception info: {einfo}")
        
        # Record failure in database if available
        try:
            self._record_status(crawler_name, "failed", str(exc))
        except Exception as e:
            logger.warning(f"Could not record failure status: {e}")
    
    def on_success(self, retval, task_id, args, kwargs):
        crawler_name = args[0] if args else "unknown"
        logger.info(f"Task {task_id} ({crawler_name}) completed successfully")
        
        # Record success in database if available
        try:
            self._record_status(crawler_name, "completed", None)
        except Exception as e:
            logger.warning(f"Could not record success status: {e}")
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        crawler_name = args[0] if args else "unknown"
        logger.warning(f"Task {task_id} ({crawler_name}) retrying due to: {exc}")
    
    def _record_status(self, crawler_name: str, status: str, error: str = None):
        """Record crawler status in database"""
        try:
            from Module4_NiruAPI.crawler_models import CrawlerDatabaseManager
            db_manager = CrawlerDatabaseManager()
            if db_manager._initialized:
                db_manager.update_crawler_status(
                    crawler_name,
                    status,
                    last_run=datetime.utcnow()
                )
                if error:
                    db_manager.add_log(crawler_name, f"Celery task failed: {error}")
                else:
                    db_manager.add_log(crawler_name, f"Celery task completed successfully")
        except Exception as e:
            logger.debug(f"Could not record status: {e}")


# Spider name mapping
SPIDER_MAPPING = {
    "kenya_law": "kenya_law",
    "parliament": "parliament_spider",
    "parliament_videos": "parliament_video_spider",
    "news_rss": "news_rss_spider",
    "global_trends": "global_trends_spider",
}

# Timeout settings per crawler (in seconds)
CRAWLER_TIMEOUTS = {
    "kenya_law": 5400,      # 90 minutes
    "parliament": 3600,      # 60 minutes
    "parliament_videos": 2700,  # 45 minutes
    "news_rss": 1800,        # 30 minutes
    "global_trends": 1800,   # 30 minutes
}


@celery_app.task(
    base=CrawlTask,
    bind=True,
    name="run_crawler",
    soft_time_limit=3600,
    time_limit=3900
)
def run_crawler_task(self, crawler_name: str, timeout: int = None):
    """
    Run a specific crawler
    
    Args:
        crawler_name: Name of the crawler to run
        timeout: Optional custom timeout in seconds
    
    Returns:
        Dictionary with crawl results
    """
    spider_name = SPIDER_MAPPING.get(crawler_name)
    if not spider_name:
        raise ValueError(f"Unknown crawler: {crawler_name}. Valid options: {list(SPIDER_MAPPING.keys())}")
    
    # Get timeout
    timeout = timeout or CRAWLER_TIMEOUTS.get(crawler_name, 3600)
    
    logger.info(f"[Celery] Starting crawler: {crawler_name} (timeout: {timeout}s)")
    
    spider_dir = project_root / "Module1_NiruSpider"
    
    try:
        # Build command
        cmd = [
            sys.executable,
            "crawl_spider.py",
            spider_name,
            "--timeout",
            str(timeout)
        ]
        
        # Run subprocess
        result = subprocess.run(
            cmd,
            cwd=str(spider_dir),
            capture_output=True,
            text=True,
            timeout=timeout + 120  # Extra buffer
        )
        
        if result.returncode == 0:
            logger.info(f"[Celery] Crawler {crawler_name} completed successfully")
            
            # Trigger vector store update
            try:
                update_vector_store.delay()
            except Exception as e:
                logger.warning(f"Could not trigger vector store update: {e}")
            
            return {
                "status": "completed",
                "crawler": crawler_name,
                "exit_code": 0
            }
        else:
            logger.error(f"[Celery] Crawler {crawler_name} failed: {result.stderr}")
            raise Exception(f"Crawler failed with exit code {result.returncode}")
            
    except subprocess.TimeoutExpired:
        logger.error(f"[Celery] Crawler {crawler_name} timed out")
        raise Exception(f"Crawler timed out after {timeout}s")
        
    except SoftTimeLimitExceeded:
        logger.error(f"[Celery] Crawler {crawler_name} exceeded soft time limit")
        raise


@celery_app.task(
    base=CrawlTask,
    bind=True,
    name="crawl_news_sources",
    soft_time_limit=2400,
    time_limit=2700
)
def crawl_news_sources(self, source_names: list = None):
    """
    Crawl multiple news sources
    
    Args:
        source_names: List of source names to crawl (None = all news sources)
    
    Returns:
        Dictionary with crawl results
    """
    news_sources = ["news_rss", "global_trends"]
    
    if source_names:
        sources_to_crawl = [s for s in source_names if s in news_sources]
    else:
        sources_to_crawl = news_sources
    
    results = {}
    
    for source in sources_to_crawl:
        try:
            result = run_crawler_task(source)
            results[source] = result
        except Exception as e:
            logger.error(f"Error crawling {source}: {e}")
            results[source] = {"status": "failed", "error": str(e)}
    
    return {
        "status": "completed",
        "sources": results
    }


@celery_app.task(
    base=CrawlTask,
    bind=True,
    name="crawl_legal_sources",
    soft_time_limit=7200,
    time_limit=7500
)
def crawl_legal_sources(self, source_names: list = None):
    """
    Crawl legal/government sources
    
    Args:
        source_names: List of source names to crawl (None = all legal sources)
    
    Returns:
        Dictionary with crawl results
    """
    legal_sources = ["kenya_law", "parliament", "parliament_videos"]
    
    if source_names:
        sources_to_crawl = [s for s in source_names if s in legal_sources]
    else:
        sources_to_crawl = legal_sources
    
    results = {}
    
    for source in sources_to_crawl:
        try:
            result = run_crawler_task(source)
            results[source] = result
        except Exception as e:
            logger.error(f"Error crawling {source}: {e}")
            results[source] = {"status": "failed", "error": str(e)}
    
    return {
        "status": "completed",
        "sources": results
    }


@celery_app.task(
    base=CrawlTask,
    bind=True,
    name="crawl_all_sources"
)
def crawl_all_sources(self):
    """
    Crawl all available sources
    Runs sources in priority order with delays between them
    """
    import time
    
    # Order by priority (news first, then legal)
    all_sources = ["news_rss", "global_trends", "parliament", "parliament_videos", "kenya_law"]
    
    results = {}
    
    for source in all_sources:
        try:
            logger.info(f"[Celery] Starting crawl for: {source}")
            result = run_crawler_task(source)
            results[source] = result
            
            # Brief delay between crawlers
            time.sleep(30)
            
        except Exception as e:
            logger.error(f"Error crawling {source}: {e}")
            results[source] = {"status": "failed", "error": str(e)}
    
    return {
        "status": "completed",
        "sources": results
    }


@celery_app.task(
    name="update_vector_store",
    soft_time_limit=1800,
    time_limit=2100
)
def update_vector_store(incremental: bool = True):
    """
    Update the vector store with new documents
    
    Args:
        incremental: If True, only add new documents. If False, rebuild entirely.
    
    Returns:
        Dictionary with update results
    """
    logger.info(f"[Celery] Updating vector store (incremental={incremental})")
    
    try:
        update_script = project_root / "populate_qdrant.py"
        
        if not update_script.exists():
            logger.warning("populate_qdrant.py not found")
            return {"status": "skipped", "reason": "Script not found"}
        
        cmd = [sys.executable, str(update_script)]
        if incremental:
            cmd.append("--incremental")
        
        result = subprocess.run(
            cmd,
            cwd=str(project_root),
            capture_output=True,
            text=True,
            timeout=1800
        )
        
        if result.returncode == 0:
            logger.info("[Celery] Vector store updated successfully")
            return {"status": "completed"}
        else:
            logger.error(f"[Celery] Vector store update failed: {result.stderr}")
            return {"status": "failed", "error": result.stderr}
            
    except subprocess.TimeoutExpired:
        logger.error("[Celery] Vector store update timed out")
        return {"status": "failed", "error": "Timeout"}
    except Exception as e:
        logger.error(f"[Celery] Vector store update error: {e}")
        return {"status": "failed", "error": str(e)}


@celery_app.task(name="scheduler_health_check")
def scheduler_health_check():
    """
    Health check task - verifies the scheduler is working
    """
    logger.info("[Celery] Health check - scheduler is running")
    return {
        "status": "healthy",
        "timestamp": datetime.utcnow().isoformat()
    }

