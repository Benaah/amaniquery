# NiruSense Quick Start Guide

## ✅ What's Been Completed

### 1. Integration with AmaniQuery

- ✅ NiruSense now starts automatically with `start_api.py`
- ✅ Health endpoints at `/nirusense/*`
- ✅ Loads configuration from root `.env` file
- ✅ Runs in background thread alongside other modules

### 2. Scheduler Added

- ✅ 4 automated jobs:
  - **Batch Processing**: Every 30 mins (configurable)
  - **Daily Cleanup**: 3 AM UTC (configurable)  
  - **Metrics Update**: Every 15 mins
  - **Failed Reprocessing**: Weekly (Sunday 2 AM)

## 🚀 How to Enable

### Step 1: Add to Root .env

Copy these lines to your root `.env` file:

```bash
# NiruSense - Kenyan NLP Processing Pipeline
ENABLE_NIRUSENSE=true
ENABLE_NIRUSENSE_SCHEDULER=true

# Processing Configuration
REDIS_STREAM_KEY=niru_ingestion_stream
REDIS_CONSUMER_GROUP=niru_processing_group
QDRANT_COLLECTION=amaniquery_sense

# Scheduler Configuration (optional - defaults shown)
NIRUSENSE_BATCH_INTERVAL=30  # Process pending every 30 mins
NIRUSENSE_CLEANUP_HOUR=3  # Daily cleanup at 3 AM UTC
NIRUSENSE_METRICS_INTERVAL=15  # Update metrics every 15 mins
```

### Step 2: Configure Storage

You'll need actual credentials for:

- **PostgreSQL** (Neon.tech): `DATABASE_URL`
- **Qdrant Cloud**: `QDRANT_URL` and `QDRANT_API_KEY`

### Step 3: Start AmaniQuery

```bash
python start_api.py
```

You should see:

```
🧠 NiruSense Processing Pipeline Configuration:
   Enabled: True
   ...
🧠 Starting NiruSense Processing Pipeline...
✔ NiruSense orchestrator is running
✔ NiruSense scheduler started
📅 Scheduled: Batch processing every 30 minutes
📅 Scheduled: Cleanup daily at 3:00 UTC
```

## 📊 Monitoring

### Check Health

```bash
curl http://localhost:8000/nirusense/health
```

### View Metrics

```bash
curl http://localhost:8000/nirusense/metrics
```

### Check Scheduler Status

```bash
curl http://localhost:8000/nirusense/status
```

## 🗓️ Scheduled Jobs Explained

### 1. Batch Processing (Every 30 mins)

- Checks Redis stream for pending documents
- Logs number of documents waiting
- Orchestrator processes them automatically

### 2. Daily Cleanup (3 AM UTC)

- Deletes analysis results older than 90 days
- Keeps database size manageable
- Configurable with `NIRUSENSE_CLEANUP_DAYS`

### 3. Metrics Update (Every 15 mins)

- Logs current processing statistics
- Success rate, total processed, failures
- Useful for monitoring dashboard

### 4. Failed Reprocessing (Weekly, Sunday 2 AM)

- Retries documents from Dead Letter Queue
- Gives failed documents another chance
- Helps recover from transient errors

## ⚙️ Configuration Options

All settings are in root `.env` file:

| Variable | Default | Description |
|----------|---------|-------------|
| `ENABLE_NIRUSENSE` | `false` | Enable the processing pipeline |
| `ENABLE_NIRUSENSE_SCHEDULER` | `false` | Enable scheduled jobs |
| `NIRUSENSE_BATCH_INTERVAL` | `30` | Minutes between batch processing |
| `NIRUSENSE_CLEANUP_HOUR` | `3` | UTC hour for daily cleanup (0-23) |  
| `NIRUSENSE_CLEANUP_DAYS` | `90` | Delete documents older than N days |
| `ENABLE_PARALLEL_AGENTS` | `true` | Run agents in parallel |
| `MAX_TEXT_LENGTH` | `10000` | Maximum text length to process |

## 🎯 Production Deployment Checklist

- [ ] Set `ENABLE_NIRUSENSE=true` in production `.env`
- [ ] Configure real Neon.tech PostgreSQL URL
- [ ] Configure Qdrant Cloud credentials
- [ ] Set `ENABLE_NIRUSENSE_SCHEDULER=true`
- [ ] Adjust `NIRUSENSE_BATCH_INTERVAL` based on traffic
- [ ] Monitor health endpoints after launch
- [ ] Check metrics after first 100 documents

## 🔧 Troubleshooting

**NiruSense not starting?**

- Check `ENABLE_NIRUSENSE=true` in .env
- Verify Redis is running (`redis-cli ping`)
- Check logs for import errors

**Scheduler not running?**

- Set `ENABLE_NIRUSENSE_SCHEDULER=true`
- Verify APScheduler is installed
- Check logs for schedule registration

**No documents being processed?**

- Verify Redis stream has messages
- Check `REDIS_STREAM_KEY` matches ingestion
- Monitor `/nirusense/metrics` for activity

## 📝 Notes

- **First Run**: Models will download (~5GB) - only once
- **Storage**: Requires ~10GB for all models  
- **Memory**: ~2-4GB RAM during processing
- **CPU**: Runs on CPU (no GPU required)
- **Latency**: Target < 5s per document

For full documentation, see `README.md` in Module9_NiruSense.
