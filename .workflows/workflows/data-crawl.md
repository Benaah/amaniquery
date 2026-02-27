---
description: Trigger Data Crawlers
---

# Data Crawling Workflow

This workflow provides guidance on how to manually execute and monitor the AmaniQuery web crawlers.

1. The API includes an integrated scheduler (APScheduler). Ensure `ENABLE_SCHEDULER=true` in your `.env`. Crawlers execute automatically based on the schedules defined (e.g., `CRAWL_NEWS_SCHEDULE=daily`).
2. To manually trigger all Scrapy spiders locally:

   ```bash
   python Module1_NiruSpider/crawl_all.py
   ```

3. To trigger a specific spider manually by name (inside `Module1_NiruSpider/niruspider/spiders/`):

   ```bash
   scrapy crawl SPIDER_NAME
   ```

4. If deploying inside Kubernetes, access the API container shell securely:

   ```bash
   make k8s-shell
   ```

   Then run the manual crawl command:

   ```bash
   python Module1_NiruSpider/crawl_all.py
   ```

5. Crawled raw data is output to `data/raw/`. Ensure you frequently monitor disk space. To clear old crawl data:

   ```bash
   rm -f data/raw/*.html data/raw/*.pdf
   ```

   *(Data should ideally be shipped to S3/MinIO/PostgreSQL using the configured pipelines).*
