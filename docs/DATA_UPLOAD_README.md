# Data Upload Script

This script uploads processed data from JSONL files to PostgreSQL database and configures cloud database settings from environment variables.

## Prerequisites

1. PostgreSQL database running and accessible
2. Python environment with required packages installed
3. Environment variables configured (see .env.example)

## Installation

Install the required Python packages:

```bash
pip install -r requirements.txt
```

## Configuration

1. Copy `.env.example` to `.env`
2. Configure your database settings in `.env`:

```bash
# Required database settings
DB_HOST=localhost
DB_PORT=5432
DB_NAME=amaniquery
DB_USER=postgres
DB_PASSWORD=your_password_here

# Optional cloud database settings
UPSTASH_REDIS_URL=https://your-redis-url.upstash.io
UPSTASH_REDIS_TOKEN=your_token_here
QDRANT_URL=https://your-qdrant-url.com
QDRANT_API_KEY=your_api_key_here
ELASTICSEARCH_URL=https://your-elasticsearch-url.com
ELASTICSEARCH_USERNAME=your_username
ELASTICSEARCH_PASSWORD=your_password
```

## Usage

Run the upload script:

```bash
python upload_data.py
```

The script will:

1. Connect to PostgreSQL database
2. Create necessary tables if they don't exist
3. Upload processed chunks from `data/embeddings/processed/*.jsonl` files
4. Configure cloud database settings from environment variables
5. Log progress and results

## Data Format

### Processed Chunks (data/embeddings/processed/*.jsonl)

Each line should be a JSON object with the following fields:

```json
{
  "text": "The chunk text content",
  "chunk_id": "unique_identifier_for_chunk",
  "chunk_index": 0,
  "total_chunks": 10,
  "url": "https://source-url.com",
  "title": "Document Title",
  "category": "Kenyan Constitution",
  "source_name": "Parliament of Kenya",
  "author": "Government of Kenya",
  "publication_date": "2024-01-15",
  "crawl_date": "2024-01-15T10:30:00Z",
  "processed_at": "2024-01-15T11:00:00Z",
  "keywords": ["keyword1", "keyword2"],
  "char_count": 500,
  "word_count": 80,
  "embedding": [0.1, 0.2, 0.3, ...],
  "metadata": {
    "additional_field": "value"
  }
}
```

### Raw Documents (data/raw/*.jsonl) - Optional

Each line should be a JSON object with:

```json
{
  "url": "https://source-url.com",
  "title": "Document Title",
  "content": "base64_encoded_content",
  "metadata": {},
  "crawl_date": "2024-01-15T10:30:00Z",
  "processed_at": "2024-01-15T11:00:00Z"
}
```

## Database Schema

### processed_chunks table

- `id`: SERIAL PRIMARY KEY
- `text`: TEXT NOT NULL (chunk content)
- `chunk_id`: TEXT UNIQUE NOT NULL (unique identifier)
- `chunk_index`: INTEGER (index within document)
- `total_chunks`: INTEGER (total chunks in document)
- `url`: TEXT (source URL)
- `title`: TEXT (document title)
- `category`: TEXT (content category)
- `source_name`: TEXT (source name)
- `author`: TEXT (author)
- `publication_date`: DATE (publication date)
- `crawl_date`: TIMESTAMP (when crawled)
- `processed_at`: TIMESTAMP (when processed)
- `keywords`: TEXT[] (array of keywords)
- `char_count`: INTEGER (character count)
- `word_count`: INTEGER (word count)
- `embedding`: VECTOR(384) (embedding vector)
- `metadata_json`: JSONB (additional metadata)

### raw_documents table

- `id`: SERIAL PRIMARY KEY
- `url`: TEXT (source URL)
- `title`: TEXT (document title)
- `content`: TEXT (base64 encoded content)
- `metadata_json`: JSONB (additional metadata)
- `crawl_date`: TIMESTAMP (when crawled)
- `processed_at`: TIMESTAMP (when processed, defaults to CURRENT_TIMESTAMP)

## Features

- **Bulk Upload**: Efficient bulk insertion of data
- **Conflict Resolution**: Updates existing chunks on conflict
- **Error Handling**: Comprehensive error handling and logging
- **Cloud Configuration**: Automatically configures cloud services from environment variables
- **Progress Logging**: Detailed logging of upload progress
- **Data Validation**: Validates data format and handles missing fields gracefully

## Troubleshooting

### Database Connection Issues

- Ensure PostgreSQL is running and accessible
- Check DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD in .env
- Verify database user has necessary permissions

### Missing Dependencies

```bash
pip install psycopg2-binary python-dotenv
```

### Data Format Issues

- Ensure JSONL files contain valid JSON objects
- Check that embedding arrays are proper numeric arrays
- Verify date formats are ISO 8601 compliant

### Permission Issues

- Ensure the script has read access to data files
- Check database user permissions for CREATE TABLE and INSERT operations

## Cloud Services Configuration

The script automatically configures the following cloud services if environment variables are provided:

- **Upstash Redis**: For caching and vector storage
- **QDrant**: For vector database operations
- **Elasticsearch**: For document indexing and search

Configurations are encrypted and stored using the ConfigManager.