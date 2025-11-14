"""
Run individual spider
"""
import os
import sys
from pathlib import Path
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

def run_spider(spider_name):
    """Run a specific spider"""
    print(f"🕷️  Starting spider: {spider_name}")

    # Get Scrapy settings
    settings = get_project_settings()

    # Create crawler process
    process = CrawlerProcess(settings)

    # Map spider names to classes
    spider_mapping = {
        "kenya_law_spider": ("Kenya Law", "niruspider.spiders.kenya_law_spider.KenyaLawSpider"),
        "parliament_spider": ("Parliament", "niruspider.spiders.parliament_spider.ParliamentSpider"),
        "news_rss_spider": ("Kenyan News (RSS)", "niruspider.spiders.news_rss_spider.NewsRSSSpider"),
        "global_trends_spider": ("Global Trends (RSS)", "niruspider.spiders.global_trends_spider.GlobalTrendsSpider"),
    }

    if spider_name not in spider_mapping:
        print(f"❌ Unknown spider: {spider_name}")
        return False

    display_name, spider_class_path = spider_mapping[spider_name]

    try:
        # Import the spider class dynamically
        module_path, class_name = spider_class_path.rsplit('.', 1)
        module = __import__(module_path, fromlist=[class_name])
        spider_class = getattr(module, class_name)

        # Add spider to process
        process.crawl(spider_class)

        print(f"🚀 Starting crawl for {display_name}...\n")

        # Start crawling (blocking)
        process.start()

        print(f"\n✅ {display_name} crawl complete!")
        return True

    except Exception as e:
        print(f"❌ Error running spider {spider_name}: {e}")
        return False


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python crawl_spider.py <spider_name>")
        print("Available spiders: kenya_law_spider, parliament_spider, news_rss_spider, global_trends_spider")
        sys.exit(1)

    spider_name = sys.argv[1]
    success = run_spider(spider_name)
    sys.exit(0 if success else 1)