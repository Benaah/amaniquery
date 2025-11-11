"""
Main Processing Pipeline - Orchestrates ETL and embedding
"""
import json
from pathlib import Path
from typing import List, Dict, Optional
from loguru import logger

from .config import Config
from .extractors import HTMLExtractor, PDFExtractor
from .cleaners import TextCleaner
from .chunkers import TextChunker
from .enrichers import MetadataEnricher
from .embedders import TextEmbedder


class ProcessingPipeline:
    """Main ETL and embedding pipeline"""
    
    def __init__(self, config: Optional[Config] = None):
        """Initialize pipeline with all components"""
        self.config = config or Config()
        
        # Initialize components
        logger.info("Initializing processing pipeline")
        self.html_extractor = HTMLExtractor()
        self.pdf_extractor = PDFExtractor()
        self.cleaner = TextCleaner()
        self.chunker = TextChunker(
            chunk_size=self.config.CHUNK_SIZE,
            chunk_overlap=self.config.CHUNK_OVERLAP,
            separators=self.config.CHUNK_SEPARATORS,
        )
        self.enricher = MetadataEnricher()
        self.embedder = TextEmbedder(
            model_name=self.config.EMBEDDING_MODEL,
            batch_size=self.config.EMBEDDING_BATCH_SIZE,
            normalize=self.config.NORMALIZE_EMBEDDINGS,
        )
        
        logger.info("Pipeline initialized successfully")
    
    def process_document(self, raw_doc: Dict) -> List[Dict]:
        """
        Process a single document through the full pipeline
        
        Args:
            raw_doc: Raw document dictionary from crawler
        
        Returns:
            List of processed chunks with embeddings
        """
        try:
            # 1. Extract text based on content type
            logger.info(f"Processing: {raw_doc.get('title', 'Untitled')[:50]}...")
            
            content_type = raw_doc.get("content_type", "html")
            text = ""
            extracted_meta = {}
            
            if content_type == "pdf":
                pdf_path = raw_doc.get("pdf_path")
                if pdf_path:
                    result = self.pdf_extractor.extract(pdf_path)
                    text = result["text"]
                    extracted_meta = {
                        "author": result.get("author"),
                        "creation_date": result.get("creation_date"),
                    }
            elif content_type == "html":
                html = raw_doc.get("raw_html", "")
                result = self.html_extractor.extract(
                    html,
                    url=raw_doc.get("url")
                )
                text = result["text"]
                extracted_meta = {
                    "author": result.get("author"),
                    "date": result.get("date"),
                }
            else:
                # Plain text
                text = raw_doc.get("content", "")
            
            # Validate text length
            if len(text) < self.config.MIN_TEXT_LENGTH:
                logger.warning(f"Text too short ({len(text)} chars), skipping")
                return []
            
            if len(text) > self.config.MAX_TEXT_LENGTH:
                logger.warning(f"Text too long ({len(text)} chars), truncating")
                text = text[:self.config.MAX_TEXT_LENGTH]
            
            # 2. Clean text
            text = self.cleaner.clean(text, aggressive=False)
            text = self.cleaner.fix_encoding(text)
            
            # 3. Prepare metadata
            metadata = {
                "url": raw_doc.get("url", ""),
                "source_url": raw_doc.get("url", ""),
                "title": raw_doc.get("title", "Untitled"),
                "category": raw_doc.get("category", "Unknown"),
                "source_name": raw_doc.get("source_name", "Unknown"),
                "author": raw_doc.get("author") or extracted_meta.get("author"),
                "publication_date": (
                    raw_doc.get("publication_date") or
                    extracted_meta.get("date") or
                    extracted_meta.get("creation_date")
                ),
                "crawl_date": raw_doc.get("crawl_date"),
            }
            
            # 4. Chunk text
            chunks = self.chunker.chunk(text, metadata)
            
            if not chunks:
                logger.warning("No chunks created")
                return []
            
            # Limit chunks per document
            if len(chunks) > self.config.MAX_CHUNKS_PER_DOC:
                logger.info(f"Limiting to {self.config.MAX_CHUNKS_PER_DOC} chunks")
                chunks = chunks[:self.config.MAX_CHUNKS_PER_DOC]
            
            # 5. Enrich chunks with metadata
            chunks = self.enricher.enrich_batch(chunks)
            
            # 6. Generate embeddings
            chunks = self.embedder.embed_chunks(chunks)
            
            logger.info(f"Pipeline completed: {len(chunks)} chunks created")
        return chunks
    
    def _extract_youtube_transcript(self, document: Dict) -> str:
        """
        Extract transcript from YouTube video
        
        Args:
            document: Document with video_id or video_url
            
        Returns:
            Transcript text or empty string
        """
        if not self.transcript_extractor.available:
            logger.warning("Transcript extractor not available")
            return ""
        
        # Get video ID
        video_id = document.get("video_id")
        
        if not video_id:
            # Try to extract from URL
            url = document.get("url", "") or document.get("video_url", "")
            if "v=" in url:
                video_id = url.split("v=")[1].split("&")[0]
            elif "youtu.be/" in url:
                video_id = url.split("youtu.be/")[1].split("?")[0]
        
        if not video_id:
            logger.warning("No video ID found for YouTube document")
            return ""
        
        # Extract transcript
        transcript_data = self.transcript_extractor.extract_transcript(video_id)
        
        if not transcript_data:
            return ""
        
        # Store transcript data in document for later use
        document['transcript_data'] = transcript_data
        
        return transcript_data.get('full_text', "")
    
    def process_youtube_video(self, document: Dict) -> List[Dict]:
        """
        Process YouTube video with timestamp-based chunking
        
        Args:
            document: Document with video metadata
            
        Returns:
            List of chunks with timestamp metadata
        """
        if not self.transcript_extractor.available:
            logger.warning("Transcript extractor not available")
            return []
        
        # Extract video ID
        video_id = document.get("video_id")
        if not video_id:
            url = document.get("url", "") or document.get("video_url", "")
            if "v=" in url:
                video_id = url.split("v=")[1].split("&")[0]
            elif "youtu.be/" in url:
                video_id = url.split("youtu.be/")[1].split("?")[0]
        
        if not video_id:
            logger.warning("No video ID for YouTube processing")
            return []
        
        # Get transcript
        transcript_data = self.transcript_extractor.extract_transcript(video_id)
        
        if not transcript_data:
            logger.warning(f"No transcript for video {video_id}")
            return []
        
        # Chunk transcript by time (60-second chunks with 10-second overlap)
        time_chunks = self.transcript_extractor.chunk_transcript(
            transcript_data,
            chunk_duration=60,
            overlap_duration=10
        )
        
        # Create document chunks with metadata
        chunks = []
        for i, time_chunk in enumerate(time_chunks):
            chunk = {
                "text": time_chunk['text'],
                "chunk_id": i,
                "metadata": {
                    "video_id": video_id,
                    "video_url": document.get("video_url", f"https://www.youtube.com/watch?v={video_id}"),
                    "title": document.get("title", "Unknown"),
                    "category": document.get("category", "Parliamentary Record"),
                    "source_type": "YouTube Video",
                    "source_name": document.get("source_name", "Parliament YouTube"),
                    "start_time_seconds": time_chunk['start_time'],
                    "end_time_seconds": time_chunk['end_time'],
                    "duration_seconds": time_chunk['duration'],
                    "timestamp_url": time_chunk['timestamp_url'],
                    "timestamp_formatted": time_chunk['timestamp_formatted'],
                    "transcript_language": transcript_data.get('language', 'en'),
                    "is_generated": transcript_data.get('is_generated', True),
                    "upload_date": document.get("upload_date"),
                    "scraped_at": document.get("scraped_at"),
                }
            }
            
            # Enrich with metadata
            chunk = self.metadata_enricher.enrich(chunk, full_document_text=transcript_data.get('full_text'))
            
            # Generate embedding
            chunk = self.embedder.embed(chunk)
            
            chunks.append(chunk)
        
        logger.info(f"Processed YouTube video {video_id}: {len(chunks)} timestamped chunks")
        return chunks
    
    def process_document(self, document: Dict) -> List[Dict]:
        try:
            chunks = self.process_document(document)
            return chunks
            
        except Exception as e:
            logger.error(f"Error processing document: {e}")
            return []
    
    def process_batch(self, raw_docs: List[Dict]) -> List[Dict]:
        """Process multiple documents"""
        all_chunks = []
        
        for doc in raw_docs:
            chunks = self.process_document(doc)
            all_chunks.extend(chunks)
        
        return all_chunks
    
    def save_chunks(self, chunks: List[Dict], output_file: Path):
        """Save processed chunks to JSONL file"""
        try:
            output_file.parent.mkdir(parents=True, exist_ok=True)
            
            with open(output_file, "w", encoding="utf-8") as f:
                for chunk in chunks:
                    # Convert to JSON (embeddings are already lists)
                    line = json.dumps(chunk, ensure_ascii=False, default=str)
                    f.write(line + "\n")
            
            logger.info(f"Saved {len(chunks)} chunks to {output_file}")
            
        except Exception as e:
            logger.error(f"Error saving chunks: {e}")
    
    def load_raw_documents(self, jsonl_file: Path) -> List[Dict]:
        """Load raw documents from JSONL file"""
        try:
            docs = []
            with open(jsonl_file, "r", encoding="utf-8") as f:
                for line in f:
                    if line.strip():
                        docs.append(json.loads(line))
            
            logger.info(f"Loaded {len(docs)} documents from {jsonl_file}")
            return docs
            
        except Exception as e:
            logger.error(f"Error loading documents: {e}")
            return []
