# Module 1: NiruSpider - Data Ingestion Crawler

This module handles automated web crawling and data collection from various Kenyan and global sources.

## Structure

```
Module1_NiruSpider/
├── niruspider/
│   ├── __init__.py
│   ├── spiders/
│   │   ├── __init__.py
│   │   ├── kenya_law_spider.py
│   │   ├── parliament_spider.py
│   │   ├── news_rss_spider.py
│   │   └── global_trends_spider.py
│   ├── items.py
│   ├── middlewares.py
│   ├── pipelines.py
│   └── settings.py
├── scrapy.cfg
└── crawl_all.py
```

## Features

- **Asynchronous Crawling**: Uses Scrapy for high-performance concurrent requests
- **Polite Crawling**: Respects robots.txt and implements delays
- **RSS Feed Support**: Efficient parsing of news feeds
- **PDF Handling**: Downloads and queues PDFs for processing
- **Error Handling**: Robust retry logic and error logging

## Usage

### Single Spider
```bash
cd Module1_NiruSpider
scrapy crawl kenya_law
scrapy crawl parliament
scrapy crawl news_rss
scrapy crawl global_trends
```

### All Spiders
```bash
python crawl_all.py
```

## Configuration

Edit `settings.py` for:
- Download delays
- Concurrent requests
- User agent
- Output formats

## Output

Raw data saved to: `../data/raw/<source_name>/`
- HTML files
- PDF files
- JSON metadata
