# Kenya Law Spider Update - Migration to new.kenyalaw.org

## Summary

The Kenya Law spider has been completely updated to work with the new Kenya Law website at **https://new.kenyalaw.org**. The old spider for kenyalaw.org has been removed and replaced with a comprehensive new spider.

## What Changed

### Old Spider (Removed)
- **File**: `kenya_law_spider.py` (DELETED)
- **Website**: http://kenyalaw.org
- **Coverage**: Limited to Constitution and Acts
- **Status**: Deprecated due to website migration

### New Spider (Active)
- **File**: `kenya_law_new_spider.py`
- **Website**: https://new.kenyalaw.org
- **Coverage**: Comprehensive coverage of all legal resources
- **Status**: Active and production-ready

## Coverage Details

The new spider provides comprehensive coverage of:

1. **Constitution** (article-level extraction)
2. **Legislation** (500+ acts, section-level)
   - Acts of Parliament
   - Bills (all types)
   - Subsidiary Legislation
   - County Legislation
3. **Case Law** (300k+ judicial decisions)
   - Supreme Court
   - Court of Appeal
   - High Court
   - Lower Courts
4. **Kenya Gazette** (8,000+ gazettes from 1899-2025)
5. **Treaties & International Agreements**
6. **Publications** (legal journals, reports)
7. **Cause Lists** (daily court schedules)
8. **Blog Articles** (legal analysis)

## Usage

The spider mapping has been updated so that the name "kenya_law" now points to the new comprehensive spider:

### Run via Admin Dashboard
Use the admin dashboard at `/admin` to start/stop the crawler with one click.

### Run via Command Line

**Single spider:**
```bash
python crawl_spider.py kenya_law
```

**All spiders:**
```bash
python crawl_all.py
```

**Direct Scrapy (advanced):**
```bash
scrapy crawl kenya_law_new
```

## Migration Notes

- No action required for existing users - the crawler mapping has been automatically updated
- The admin dashboard will show "kenya_law" as the crawler name
- All existing data remains intact
- New crawls will fetch from new.kenyalaw.org

## Technical Details

- **Start URLs**: 31 comprehensive entry points
- **Spider Name**: `kenya_law_new`
- **Spider Class**: `KenyaLawNewSpider`
- **Allowed Domains**: `new.kenyalaw.org`, `kenyalaw.org`
- **Rate Limiting**: Respectful crawling with delays
- **Pagination**: Full support for all content types

## Documentation

For detailed documentation, see:
- **Quick Start**: `QUICKSTART_KENYA_LAW_NEW.md`
- **Full Documentation**: `KENYA_LAW_NEW_README.md`

## Troubleshooting

If you encounter any issues:
1. Ensure you're using the updated spider mapping
2. Check that old spider references are removed
3. Verify network access to new.kenyalaw.org
4. Review logs in the admin dashboard

## Last Updated

January 2025 - Complete migration to new.kenyalaw.org
