"""
News RSS Spider - Fetches Kenyan news from RSS feeds
"""
import scrapy
import feedparser
from datetime import datetime
from dateutil import parser as date_parser
from ..items import RSSItem, DocumentItem
import time


class NewsRSSSpider(scrapy.Spider):
    name = "news_rss"
    
    # Kenyan news RSS feeds
    rss_feeds = [
        {
            "url": "https://nation.africa/kenya/rss",
            "name": "Nation Africa",
        },
        {
            "url": "https://www.standardmedia.co.ke/rss/headlines.xml",
            "name": "Standard Media",
        },
        {
            "url": "https://www.the-star.co.ke/rss",
            "name": "The Star",
        },
        {
            "url": "https://www.businessdailyafrica.com/bd/rss",
            "name": "Business Daily Africa",
        },
    ]
    
    custom_settings = {
        "DOWNLOAD_DELAY": 2.0,
        "ROBOTSTXT_OBEY": False,  # RSS feeds often not in robots.txt
    }
    
    def start_requests(self):
        """Generate requests for each RSS feed"""
        for feed in self.rss_feeds:
            yield scrapy.Request(
                url=feed["url"],
                callback=self.parse_rss,
                meta={"feed_name": feed["name"], "feed_url": feed["url"]},
                dont_filter=True,
            )
    
    def parse_rss(self, response):
        """Parse RSS feed using feedparser"""
        feed_name = response.meta["feed_name"]
        feed_url = response.meta["feed_url"]
        
        self.logger.info(f"Parsing RSS feed: {feed_name}")
        
        # Parse feed
        feed = feedparser.parse(response.text)
        
        if not feed.entries:
            self.logger.warning(f"No entries found in feed: {feed_name}")
            return
        
        self.logger.info(f"Found {len(feed.entries)} articles in {feed_name}")
        
        # Process each entry
        for entry in feed.entries[:100]:  # Limit to 100 most recent
            # Extract publication date
            pub_date = None
            if hasattr(entry, 'published'):
                try:
                    pub_date = date_parser.parse(entry.published).isoformat()
                except:
                    pub_date = entry.published
            
            # Extract author
            author = None
            if hasattr(entry, 'author'):
                author = entry.author
            
            # Get summary/description
            summary = ""
            if hasattr(entry, 'summary'):
                summary = entry.summary
            elif hasattr(entry, 'description'):
                summary = entry.description
            
            # Create RSS item
            rss_item = RSSItem(
                url=entry.link,
                title=entry.title,
                summary=summary,
                published=pub_date,
                author=author,
                category="Kenyan News",
                source_name=feed_name,
                feed_url=feed_url,
            )
            
            # Now fetch the full article
            yield scrapy.Request(
                url=entry.link,
                callback=self.parse_article,
                meta={"rss_item": rss_item},
                errback=self.errback_article,
            )
    
    def parse_article(self, response):
        """Parse full article from URL"""
        rss_item = response.meta["rss_item"]
        
        # Extract main article content
        # Try multiple common selectors
        content_selectors = [
            'article .article-body::text',
            '.article-content::text',
            '.story-body::text',
            '[itemprop="articleBody"]::text',
            'article p::text',
            '.entry-content p::text',
        ]
        
        content = []
        for selector in content_selectors:
            content = response.css(selector).getall()
            if content:
                break
        
        # Fallback: get all paragraph text from article tag
        if not content:
            content = response.css('article p::text, main p::text').getall()
        
        full_content = '\n'.join([t.strip() for t in content if t.strip()])
        
        # Create document item
        yield DocumentItem(
            url=rss_item["url"],
            title=rss_item["title"],
            content=full_content,
            content_type="html",
            category="Kenyan News",
            source_name=rss_item["source_name"],
            author=rss_item.get("author"),
            publication_date=rss_item.get("published"),
            summary=rss_item.get("summary"),
            raw_html=response.text,
            status_code=response.status,
        )
    
    def errback_article(self, failure):
        """Handle failed article fetches"""
        self.logger.error(f"Failed to fetch article: {failure.request.url}")
        
        # Still yield the RSS item with summary only
        rss_item = failure.request.meta.get("rss_item")
        if rss_item:
            yield DocumentItem(
                url=rss_item["url"],
                title=rss_item["title"],
                content=rss_item.get("summary", ""),
                content_type="text",
                category="Kenyan News",
                source_name=rss_item["source_name"],
                author=rss_item.get("author"),
                publication_date=rss_item.get("published"),
                summary=rss_item.get("summary"),
                raw_html="",
            )
