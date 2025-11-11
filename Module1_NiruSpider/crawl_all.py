"""
Run all spiders sequentially
"""
import os
import sys
from pathlib import Path
from scrapy.crawler import CrawlerProcess
from scrapy.utils.project import get_project_settings

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent))

from niruspider.spiders.kenya_law_spider import KenyaLawSpider
from niruspider.spiders.parliament_spider import ParliamentSpider
from niruspider.spiders.news_rss_spider import NewsRSSSpider
from niruspider.spiders.global_trends_spider import GlobalTrendsSpider


def main():
    """Run all spiders"""
    print("=" * 60)
    print("🕷️  Starting AmaniQuery Data Crawl")
    print("=" * 60)
    
    # Get Scrapy settings
    settings = get_project_settings()
    
    # Create crawler process
    process = CrawlerProcess(settings)
    
    # Add all spiders
    spiders = [
        ("Kenya Law", KenyaLawSpider),
        ("Parliament", ParliamentSpider),
        ("Kenyan News (RSS)", NewsRSSSpider),
        ("Global Trends (RSS)", GlobalTrendsSpider),
    ]
    
    for name, spider in spiders:
        print(f"\n📥 Queuing spider: {name}")
        process.crawl(spider)
    
    print("\n🚀 Starting crawl process...\n")
    
    # Start crawling (blocking)
    process.start()
    
    print("\n" + "=" * 60)
    print("✅ Crawl complete!")
    print("📁 Data saved to: ../data/raw/")
    print("=" * 60)


if __name__ == "__main__":
    main()
