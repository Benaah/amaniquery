# HuggingFace Spaces Deployment Guide for AmaniQuery

## Overview

Deploy AmaniQuery to HuggingFace Spaces for demo and testing purposes. HF Spaces provides free Docker-based hosting with automatic HTTPS and simple deployment.

## Limitations

⚠️ **Important Constraints**:
- **RAM**: 16GB maximum (free tier)
- **Storage**: No persistent storage - data resets on restart
- **CPU**: Shared CPU instances only
- **Use Case**: Demos, testing, not production at scale

## Prerequisites

1. **HuggingFace Account**: Sign up at https://huggingface.co
2. **HuggingFace Token**: Generate at https://huggingface.co/settings/tokens
   - Permissions: `write`

## Quick Start

### 1. Set Up Environment

```bash
# Install dependencies
pip install huggingface-hub python-dotenv

# Set your HuggingFace token
export HF_TOKEN=your_token_here

# Or add to .env file
echo "HF_TOKEN=your_token_here" >> .env
```

### 2. Deploy Using Script

```bash
# Deploy with optimized Dockerfile
python deploy_to_hf.py

# Custom space ID
python deploy_to_hf.py --space-id YourUsername/your-space-name

# Dry run (test without uploading)
python deploy_to_hf.py --dry-run
```

### 3. Configure Space Settings

After deployment, configure in HuggingFace UI:

1. Go to `https://huggingface.co/spaces/YourUsername/amaniquery/settings`
2. Set **Environment Variables** (Secrets):
   ```
   MOONSHOT_API_KEY=your_key
   OPENAI_API_KEY=your_key
   POSTGRES_PASSWORD=secure_password
   ```
3. Set **Space Hardware**: Docker SDK (free tier)
4. **Save Settings**

## Manual Deployment (Alternative)

### Option 1: Using HuggingFace CLI

```bash
# Install HF CLI
pip install huggingface-hub[cli]

# Login
huggingface-cli login

# Create space
huggingface-cli repo create amaniquery --type space --space_sdk docker

# Upload files
git clone https://huggingface.co/spaces/Benaah/amaniquery
cd amaniquery

# Copy your code
cp -r /path/to/AmaniQuery/* .

# Commit and push
git add .
git commit -m "Initial deployment"
git push
```

### Option 2: Using Web UI

1. Go to https://huggingface.co/new-space
2. Choose **Docker SDK**
3. Upload files manually or connect GitHub repository

## Dockerfile Comparison

### Standard Dockerfile (Multi-service)
- Includes Redis, scheduler, and all modules
- **Size**: ~3-4GB
- **Best for**: Full local deployment

### Dockerfile.huggingface (Optimized)
- API-only, no scheduler or Redis
- CPU-optimized PyTorch
- Pre-downloaded models
- **Size**: ~2GB
- **Best for**: HuggingFace Spaces

## Configuration

### Environment Variables (Secrets)

Set in HuggingFace Space settings:

| Variable | Required | Description |
|----------|----------|-------------|
| `MOONSHOT_API_KEY` | Yes | Moonshot AI API key |
| `OPENAI_API_KEY` | Optional | OpenAI API key |
| `ANTHROPIC_API_KEY` | Optional | Anthropic API key |
| `POSTGRES_PASSWORD` | Yes | PostgreSQL password |
| `AFRICASTALKING_API_KEY` | Optional | SMS gateway |
| `AFRICASTALKING_USERNAME` | Optional | SMS gateway |

### Space Settings

**README.md Frontmatter**:
```yaml
---
title: AmaniQuery
emoji: ⚖️
colorFrom: green
colorTo: blue
sdk: docker
app_port: 7860
pinned: false
---
```

## Features Available on HuggingFace

✅ **Supported**:
- RAG query interface (legal, parliamentary, news)
- Constitutional alignment analysis
- Public sentiment gauge
- Multi-model LLM support (via API keys)
- REST API endpoints
- Authentication system

❌ **Not Supported** (due to limitations):
- Automatic data crawling (no scheduler)
- Persistent data storage (resets on restart)
- Large file uploads (limited storage)
- High-traffic production use

## Data Management

### Pre-populate Data (Recommended)

Since HF Spaces resets on restart, bake data into the Docker image:

```dockerfile
# In Dockerfile.huggingface
COPY data/chroma_db /app/data/chroma_db
```

Then rebuild and redeploy.

### Upload Data After Deployment

Use the API to upload data after space starts:

```bash
# Upload documents via API
curl -X POST https://yourspace.hf.space/api/upload \
  -H "Content-Type: application/json" \
  -d '{"documents": [...]}'
```

## Monitoring

### View Logs

1. Go to your Space page
2. Click **Logs** tab
3. Monitor real-time application logs

### Health Check

```bash
# Check if API is running
curl https://yourspace.hf.space/health

# Test query
curl https://yourspace.hf.space/api/query \
  -H "Content-Type: application/json" \
  -d '{"query": "What is the constitution?"}'
```

## Updates and Redeployment

### Update Code

```bash
# Make changes locally
git add .
git commit -m "Update feature"

# Redeploy
python deploy_to_hf.py
```

### Restart Space

From HuggingFace UI:
1. Go to space settings
2. Click **Factory Reboot**

## Troubleshooting

### Build Failures

**Error**: Out of memory during build
```bash
# Solution: Reduce image size
# - Remove unnecessary dependencies
# - Use smaller base image
# - Multi-stage builds
```

**Error**: Timeout during build
```bash
# Solution: Pre-download models locally
# - Remove download_model.py step
# - Commit model files to repo
```

### Runtime Errors

**Error**: Port binding failed
```bash
# Solution: Ensure PORT env variable is used
# In start command: --port ${PORT}
```

**Error**: Module not found
```bash
# Solution: Check PYTHONPATH and module structure
ENV PYTHONPATH=/app
```

### Database Connection Issues

**Error**: Cannot connect to PostgreSQL
```bash
# For HF Spaces, use SQLite or external DB
# Update DATABASE_URL to use SQLite:
DATABASE_URL=sqlite:///./amaniquery.db
```

## Cost Considerations

### Free Tier
- **CPU**: Shared
- **RAM**: 16GB
- **Storage**: ~50GB (ephemeral)
- **Limitations**: Auto-sleep after inactivity

### Paid Tiers (if needed)
- **CPU Basic**: $0.03/hour
- **CPU Upgraded**: $0.06/hour
- **GPU T4**: $0.60/hour

## Alternative to HuggingFace

If HF Spaces doesn't meet your needs:

1. **Render**: Better for production, persistent storage
2. **Railway**: Easy deployment, persistent volumes
3. **Fly.io**: Global edge deployment
4. **Google Cloud Run**: Serverless containers
5. **Kubernetes**: Full control (see KUBERNETES_DEPLOYMENT.md)

## Example Spaces

Public AmaniQuery Spaces:
- Demo: https://huggingface.co/spaces/Benaah/amaniquery
- API Documentation: Built-in FastAPI docs at `/docs`

## Best Practices

1. **Use lightweight models** - Avoid large model downloads
2. **Optimize Dockerfile** - Multi-stage builds, layer caching
3. **Set resource limits** - Prevent OOM errors
4. **Use external services** - For databases, use managed services
5. **Monitor logs** - Check for errors regularly
6. **Version control** - Tag releases for easy rollback

## Support

- HuggingFace Docs: https://huggingface.co/docs/hub/spaces
- AmaniQuery Issues: https://github.com/Benaah/amaniquery/issues
- Community: HuggingFace Discord
