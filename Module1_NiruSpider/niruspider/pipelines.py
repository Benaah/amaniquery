"""
NiruSpider - Item Pipelines
"""
import json
import hashlib
from pathlib import Path
from datetime import datetime
from urllib.parse import urlparse
import sys
import os

import scrapy
from scrapy.pipelines.files import FilesPipeline
from itemadapter import ItemAdapter

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

class VectorStorePipeline:
    """Save scraped items directly to vector store"""
    
    def __init__(self):
        self.vector_store = None
        self.text_embedder = None
    
    def open_spider(self, spider):
        """Initialize vector store connection"""
        try:
            from Module3_NiruDB.vector_store import VectorStore
            from Module2_NiruParser.embedders.text_embedder import TextEmbedder
            
            self.vector_store = VectorStore()
            self.text_embedder = TextEmbedder()
            
            spider.logger.info("Vector store pipeline initialized")
        except Exception as e:
            spider.logger.error(f"Failed to initialize vector store: {e}")
            raise
    
    def process_item(self, item, spider):
        """Process and save item to vector store"""
        if not self.vector_store or not self.text_embedder:
            spider.logger.warning("Vector store or embedder not available, skipping item")
            return item
        
        try:
            adapter = ItemAdapter(item)
            
            # Prepare document data
            doc_id = hashlib.md5(adapter["url"].encode()).hexdigest()
            
            # Prepare metadata
            metadata = {
                "title": adapter.get("title", ""),
                "source_url": adapter["url"],
                "source_name": adapter.get("source_name", ""),
                "category": adapter.get("category", "Unknown"),
                "publication_date": adapter.get("publication_date", ""),
                "author": adapter.get("author", ""),
                "content_type": adapter.get("content_type", "html"),
                "crawl_date": adapter.get("crawl_date", datetime.utcnow().isoformat()),
            }
            
            # Prepare content for embedding
            content = adapter.get("content", "")
            if not content and adapter.get("summary"):
                content = adapter.get("summary")
            
            if content:
                # Chunk the content if it's too long
                chunk_size = 800  # Match the chunk size in settings
                chunks = []
                
                # Simple chunking by sentences/paragraphs
                paragraphs = content.split('\n\n')
                current_chunk = ""
                
                for para in paragraphs:
                    if len(current_chunk + para) <= chunk_size:
                        current_chunk += para + "\n\n"
                    else:
                        if current_chunk:
                            chunks.append(current_chunk.strip())
                        current_chunk = para + "\n\n"
                
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # If still no chunks, create one big chunk
                if not chunks:
                    chunks = [content[:chunk_size]]
                
                # Prepare chunks for embedding
                chunk_dicts = []
                for i, chunk in enumerate(chunks):
                    chunk_id = f"{doc_id}_chunk_{i}"
                    chunk_dict = {
                        "chunk_id": chunk_id,
                        "text": chunk,
                        "title": metadata["title"],
                        "category": metadata["category"],
                        "source_url": metadata["source_url"],
                        "source_name": metadata["source_name"],
                        "chunk_index": i,
                        "total_chunks": len(chunks),
                    }
                    
                    # Add optional metadata
                    if metadata.get("author"):
                        chunk_dict["author"] = metadata["author"]
                    if metadata.get("publication_date"):
                        chunk_dict["publication_date"] = metadata["publication_date"]
                    
                    chunk_dicts.append(chunk_dict)
                
                # Generate embeddings
                embedded_chunks = self.text_embedder.embed_chunks(chunk_dicts)
                
                # Add to vector store
                self.vector_store.add_documents(embedded_chunks)
                
                spider.logger.info(f"Added {len(embedded_chunks)} chunks for: {adapter['title'][:50]}...")
            
            return item
            
        except Exception as e:
            spider.logger.error(f"Error processing item for vector store: {e}")
            return item


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
