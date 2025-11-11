"""
Global Trends Spider - Fetches global news, geopolitics, international organizations & policy
"""
import scrapy
import feedparser
from datetime import datetime
from dateutil import parser as date_parser
from niruspider.items import RSSItem, DocumentItem


class GlobalTrendsSpider(scrapy.Spider):
    name = "global_trends"
    
    # Global news, geopolitics, and policy RSS feeds
    rss_feeds = [
        # Geopolitics & International Affairs
        {
            "url": "https://www.reuters.com/world/rss",
            "name": "Reuters World News",
        },
        {
            "url": "https://feeds.bbci.co.uk/news/world/rss.xml",
            "name": "BBC World News",
        },
        {
            "url": "https://www.aljazeera.com/xml/rss/all.xml",
            "name": "Al Jazeera International",
        },
        {
            "url": "https://foreignpolicy.com/feed/",
            "name": "Foreign Policy",
        },
        
        # International Organizations
        {
            "url": "https://news.un.org/feed/subscribe/en/news/all/rss.xml",
            "name": "United Nations News",
        },
        {
            "url": "https://www.who.int/feeds/entity/mediacentre/news/en/rss.xml",
            "name": "World Health Organization",
        },
        {
            "url": "https://www.worldbank.org/en/news/rss",
            "name": "World Bank News",
        },
        {
            "url": "https://www.imf.org/en/News/RSS",
            "name": "IMF News",
        },
        {
            "url": "https://au.int/en/rss.xml",
            "name": "African Union",
        },
        
        # Technology & Innovation
        {
            "url": "https://www.reuters.com/technology/rss",
            "name": "Reuters Technology",
        },
        {
            "url": "https://techcrunch.com/feed/",
            "name": "TechCrunch",
        },
        {
            "url": "https://www.technologyreview.com/feed/",
            "name": "MIT Technology Review",
        },
        
        # Policy & Governance
        {
            "url": "https://www.economist.com/international/rss.xml",
            "name": "The Economist",
        },
        {
            "url": "https://www.brookings.edu/feed/",
            "name": "Brookings Institution",
        },
        {
            "url": "https://www.cfr.org/rss",
            "name": "Council on Foreign Relations",
        },
        
        # Climate & Development
        {
            "url": "https://unfccc.int/news/rss",
            "name": "UN Climate Change",
        },
        {
            "url": "https://www.undp.org/rss.xml",
            "name": "UNDP News",
        },
    ]
    
    # Keywords to filter for relevance
    filter_keywords = [
        "africa", "kenya", "policy", "governance", "regulation", 
        "ai", "technology", "artificial intelligence", "data", "privacy",
        "government", "development", "climate", "trade", "diplomacy",
        "international law", "human rights", "health policy", "economic policy",
        "united nations", "world bank", "imf", "who", "african union",
        "geopolitics", "foreign policy", "international relations",
    ]
    
    custom_settings = {
        "DOWNLOAD_DELAY": 2.0,
        "ROBOTSTXT_OBEY": False,
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
        for entry in feed.entries[:50]:  # Limit to 50 most recent
            # Filter by keywords
            title = entry.title.lower()
            summary = getattr(entry, 'summary', '').lower()
            
            # Check if article is relevant
            is_relevant = any(
                keyword in title or keyword in summary
                for keyword in self.filter_keywords
            )
            
            if not is_relevant:
                continue  # Skip irrelevant articles
            
            self.logger.info(f"Relevant article found: {entry.title[:50]}...")
            
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
            summary_text = ""
            if hasattr(entry, 'summary'):
                summary_text = entry.summary
            elif hasattr(entry, 'description'):
                summary_text = entry.description
            
            # Create RSS item
            rss_item = RSSItem(
                url=entry.link,
                title=entry.title,
                summary=summary_text,
                published=pub_date,
                author=author,
                category="Global Trend",
                source_name=feed_name,
                feed_url=feed_url,
            )
            
            # Fetch the full article
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
        content_selectors = [
            'article .article-body::text',
            '.article-content::text',
            '.story-body::text',
            '[itemprop="articleBody"]::text',
            'article p::text',
            '.post-content p::text',
            '.entry-content p::text',
        ]
        
        content = []
        for selector in content_selectors:
            content = response.css(selector).getall()
            if content:
                break
        
        # Fallback
        if not content:
            content = response.css('article p::text, main p::text').getall()
        
        full_content = '\n'.join([t.strip() for t in content if t.strip()])
        
        # Extract keywords/tags if available
        keywords = response.css('meta[name="keywords"]::attr(content)').get()
        
        yield DocumentItem(
            url=rss_item["url"],
            title=rss_item["title"],
            content=full_content,
            content_type="html",
            category="Global Trend",
            source_name=rss_item["source_name"],
            author=rss_item.get("author"),
            publication_date=rss_item.get("published"),
            summary=rss_item.get("summary"),
            keywords=keywords,
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
                category="Global Trend",
                source_name=rss_item["source_name"],
                author=rss_item.get("author"),
                publication_date=rss_item.get("published"),
                summary=rss_item.get("summary"),
                raw_html="",
            )
