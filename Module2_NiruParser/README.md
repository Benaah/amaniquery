# Module 2: NiruParser - ETL & Embedding Pipeline

This module processes raw crawled data into clean, chunked, and embedded documents ready for the vector database.

## Pipeline Flow

```
Raw Data → Extract → Clean → Chunk → Enrich → Embed → Store
```

## Components

### 1. Extractors (`extractors/`)
- **HTMLExtractor**: Uses Trafilatura to extract clean text from HTML
- **PDFExtractor**: Uses pdfplumber to extract text from PDFs
- **TextExtractor**: Handles plain text files

### 2. Cleaners (`cleaners/`)
- Remove excessive whitespace
- Fix encoding issues
- Strip HTML remnants
- Normalize Unicode

### 3. Chunkers (`chunkers/`)
- **RecursiveChunker**: Splits text at natural boundaries
- Configurable chunk size (500-1000 chars)
- Overlap to preserve context (100 chars)

### 4. Enrichers (`enrichers/`)
- Add metadata to each chunk
- Generate chunk IDs
- Extract keywords
- Create summaries

### 5. Embedders (`embedders/`)
- Generate vector embeddings using Sentence Transformers
- Model: `all-MiniLM-L6-v2`
- Batch processing for efficiency

## Usage

### Process Single File
```python
from Module2_NiruParser import ProcessingPipeline

pipeline = ProcessingPipeline()
chunks = pipeline.process_file("path/to/document.html")
```

### Process All Raw Data
```bash
python -m Module2_NiruParser.process_all
```

## Output

Processed data saved to: `../data/processed/`
- Chunks with metadata (JSONL)
- Vector embeddings (NumPy arrays)
- Processing logs

## Configuration

Edit `config.py` for:
- Chunk size and overlap
- Embedding model
- Batch sizes
- Output formats
