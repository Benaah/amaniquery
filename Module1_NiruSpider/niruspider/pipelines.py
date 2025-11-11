"""
NiruSpider - Item Pipelines
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse

import scrapy
from scrapy.pipelines.files import FilesPipeline
from itemadapter import ItemAdapter


class DataValidationPipeline:
    """Validate and clean scraped data"""
    
    def process_item(self, item, spider):
        adapter = ItemAdapter(item)
        
        # Ensure required fields
        if not adapter.get("url"):
            raise scrapy.exceptions.DropItem("Missing URL")
        
        if not adapter.get("title"):
            raise scrapy.exceptions.DropItem("Missing title")
        
        # Add crawl timestamp
        adapter["crawl_date"] = datetime.utcnow().isoformat()
        
        # Clean title
        if adapter.get("title"):
            adapter["title"] = adapter["title"].strip()
        
        # Ensure category is set
        if not adapter.get("category"):
            adapter["category"] = "Unknown"
        
        spider.logger.info(f"Validated item: {adapter['title'][:50]}...")
        return item


class PDFDownloadPipeline(FilesPipeline):
    """Handle PDF downloads"""
    
    def get_media_requests(self, item, info):
        adapter = ItemAdapter(item)
        
        # If content_type is PDF, download it
        if adapter.get("content_type") == "pdf" and adapter.get("url"):
            yield scrapy.Request(
                adapter["url"],
                meta={"item": item}
            )
    
    def file_path(self, request, response=None, info=None, *, item=None):
        """Generate file path for PDFs"""
        adapter = ItemAdapter(item)
        
        # Create hash of URL for unique filename
        url_hash = hashlib.md5(adapter["url"].encode()).hexdigest()[:12]
        
        # Extract filename or use hash
        parsed = urlparse(adapter["url"])
        filename = Path(parsed.path).name or f"{url_hash}.pdf"
        
        # Organize by category
        category = adapter.get("category", "unknown").replace(" ", "_").lower()
        return f"{category}/{filename}"
    
    def item_completed(self, results, item, info):
        """Update item with PDF path"""
        adapter = ItemAdapter(item)
        
        # results is a list of (success, file_info) tuples
        file_paths = [x["path"] for ok, x in results if ok]
        
        if file_paths:
            adapter["pdf_path"] = file_paths[0]
            info.spider.logger.info(f"Downloaded PDF: {file_paths[0]}")
        
        return item


class FileStoragePipeline:
    """Save items to structured files"""
    
    def __init__(self, raw_data_path):
        self.raw_data_path = Path(raw_data_path)
        self.files = {}
    
    @classmethod
    def from_crawler(cls, crawler):
        return cls(
            raw_data_path=crawler.settings.get("RAW_DATA_PATH")
        )
    
    def open_spider(self, spider):
        """Create output directory for this spider"""
        self.spider_dir = self.raw_data_path / spider.name
        self.spider_dir.mkdir(parents=True, exist_ok=True)
        
        # Create separate JSON file for this crawl session
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.output_file = self.spider_dir / f"{spider.name}_{timestamp}.jsonl"
        self.files[spider] = open(self.output_file, "w", encoding="utf-8")
        
        spider.logger.info(f"Saving data to: {self.output_file}")
    
    def close_spider(self, spider):
        """Close output file"""
        if spider in self.files:
            self.files[spider].close()
            del self.files[spider]
    
    def process_item(self, item, spider):
        """Write item to JSONL file"""
        line = json.dumps(dict(item), ensure_ascii=False, default=str) + "\n"
        self.files[spider].write(line)
        return item
