"""
Global Trends Spider - Fetches global news relevant to Kenya
Fetches international news that is relevant to Kenya (Kenya-specific or Africa policy context)
Enhanced with robust extraction and Kenya-specific filtering
"""
import scrapy
import feedparser
import re
from datetime import datetime
from dateutil import parser as date_parser
from ..items import RSSItem, DocumentItem
from ..extractors import ArticleExtractor


class GlobalTrendsSpider(scrapy.Spider):
    name = "global_trends"
    
    def __init__(self, *args, **kwargs):
        super(GlobalTrendsSpider, self).__init__(*args, **kwargs)
        self.article_extractor = ArticleExtractor()
    
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
    
    # Kenya-specific keywords (must include Kenya prominently)
    kenya_keywords = [
        "kenya", "kenyan", "nairobi", "mombasa", "kisumu", "nakuru",
        "kenya's", "kenyan government", "kenyan parliament", "kenyan law",
        "kenyan economy", "kenyan policy", "kenyan constitution",
        "kenya and", "kenya's", "in kenya", "to kenya", "from kenya",
        "kenya-", "kenya–", "kenya—",  # Various dash types
    ]
    
    # Africa-related keywords that must be combined with Kenya context
    africa_keywords = [
        "east africa", "east african", "eac", "east african community",
        "african union", "au", "africa and kenya", "kenya and africa",
    ]
    
    # Policy/governance keywords (must be combined with Kenya)
    policy_keywords = [
        "policy", "governance", "regulation", "government", "parliament",
        "legislation", "bill", "act", "law", "constitution",
    ]
    
    # Exclude patterns - articles that mention these are likely not about Kenya
    exclude_patterns = [
        r'\b(?:china|chinese|beijing)\b',
        r'\b(?:russia|russian|moscow|putin)\b',
        r'\b(?:ukraine|ukrainian|kyiv)\b',
        r'\b(?:israel|israeli|palestine|palestinian|gaza)\b',
        r'\b(?:iran|iranian|tehran)\b',
        r'\b(?:north korea|south korea|seoul|pyongyang)\b',
        r'\b(?:japan|japanese|tokyo)\b',
        r'\b(?:india|indian|delhi|mumbai)\b',
        r'\b(?:brazil|brazilian|brasilia)\b',
        r'\b(?:mexico|mexican|mexico city)\b',
        r'\b(?:canada|canadian|ottawa|toronto)\b',
        r'\b(?:australia|australian|sydney|melbourne)\b',
        r'\b(?:europe|european|eu|brussels|paris|berlin|london)\b',
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
            combined_text = f"{title} {summary}"
            
            # First check: exclude articles about non-Kenya regions
            if any(re.search(pattern, combined_text, re.IGNORECASE) for pattern in self.exclude_patterns):
                # Check if Kenya is also mentioned (might be relevant)
                if not any(keyword in combined_text for keyword in self.kenya_keywords):
                    continue  # Skip - not about Kenya
            
            # Second check: must include Kenya-specific keywords
            has_kenya_keyword = any(keyword in combined_text for keyword in self.kenya_keywords)
            
            # Third check: if no direct Kenya keyword, check for Africa + policy context
            has_africa_context = any(keyword in combined_text for keyword in self.africa_keywords)
            has_policy_context = any(keyword in combined_text for keyword in self.policy_keywords)
            
            # Article is relevant if:
            # 1. Has Kenya keyword, OR
            # 2. Has Africa context (EAC, AU) AND policy context
            is_relevant = has_kenya_keyword or (has_africa_context and has_policy_context)
            
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
        """Parse full article from URL using enhanced extractor"""
        rss_item = response.meta["rss_item"]
        
        # Use enhanced article extractor
        extracted = self.article_extractor.extract(response.text, url=response.url)
        
        # Use extracted content, fallback to RSS summary if extraction failed
        content = extracted.get("text", "")
        if not content or len(content) < 100:
            content = rss_item.get("summary", "")
            self.logger.warning(f"Extraction failed for {response.url}, using RSS summary")
        
        # Final Kenya relevance check on full content
        content_lower = content.lower()
        
        # Must have Kenya keyword in full content (not just title/summary)
        has_kenya_in_content = any(keyword in content_lower for keyword in self.kenya_keywords)
        
        # Exclude if content mentions excluded regions without Kenya
        has_excluded_region = any(re.search(pattern, content_lower, re.IGNORECASE) for pattern in self.exclude_patterns)
        
        if has_excluded_region and not has_kenya_in_content:
            self.logger.info(f"Skipping article - mentions excluded region without Kenya context: {rss_item.get('title', '')[:50]}")
            return  # Skip this article
        
        if not has_kenya_in_content:
            # Check for Africa + policy context in content
            has_africa_context = any(keyword in content_lower for keyword in self.africa_keywords)
            has_policy_context = any(keyword in content_lower for keyword in self.policy_keywords)
            
            if not (has_africa_context and has_policy_context):
                self.logger.info(f"Skipping article - no Kenya relevance in content: {rss_item.get('title', '')[:50]}")
                return  # Skip this article
        
        # Use extracted title if better than RSS title
        title = extracted.get("title", "") or rss_item["title"]
        
        # Use extracted author if available
        author = extracted.get("author", "") or rss_item.get("author", "")
        
        # Use extracted date if available
        publication_date = extracted.get("date", "") or rss_item.get("published", "")
        
        # Use extracted description if available
        summary = extracted.get("description", "") or rss_item.get("summary", "")
        
        # Extract keywords/tags if available
        keywords = response.css('meta[name="keywords"]::attr(content)').get() or extracted.get("tags", [])
        if isinstance(keywords, list):
            keywords = ", ".join(keywords)
        
        yield DocumentItem(
            url=rss_item["url"],
            title=title,
            content=content,
            content_type="html",
            category="Global Trend",
            source_name=rss_item["source_name"],
            author=author,
            publication_date=publication_date,
            summary=summary,
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
