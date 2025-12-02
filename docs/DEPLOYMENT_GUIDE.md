# AmaniQuery Deployment Guide

## Overview

AmaniQuery supports multiple deployment options to suit different needs and environments:

| Deployment Method | Use Case | Complexity | Cost | Scalability |
|------------------|----------|------------|------|-------------|
| **Docker Compose** | Local development, testing | Low | Free | Limited |
| **Kubernetes** | Production, enterprise | High | Variable | High |
| **HuggingFace Spaces** | Demo, showcase | Low | Free-Low | Limited |
| **Render** | Quick production | Medium | Low | Medium |

## Quick Links

- 🐳 [Docker Compose](./DOCKER_README.md) - Local development
- ☸️ [Kubernetes](./KUBERNETES_DEPLOYMENT.md) - Production deployment
- 🤗 [HuggingFace Spaces](./HUGGINGFACE_DEPLOYMENT.md) - Demo hosting
- 🚀 [Render](./RENDER_DEPLOYMENT.md) - Managed hosting

## Decision Tree

```
┌─────────────────────────────────────┐
│   What do you want to deploy?       │
└──────────────┬──────────────────────┘
               │
       ┌───────┴────────┐
       │                │
    Demo/Test      Production
       │                │
       │         ┌──────┴─────────┐
       │         │                │
       │    Small Scale    Enterprise Scale
       │         │                │
       │         │                │
    HuggingFace  │           Kubernetes
    Spaces       │                │
                 │                │
              Render         (GKE/EKS/AKS)
           Docker Compose
```

## Comparison

### Docker Compose
**Pros**:
- Simple setup
- Quick local testing
- All services in one command
- Good for development

**Cons**:
- Not production-ready
- No auto-scaling
- Single machine limitation
- Manual updates

**When to use**: Local development, testing, small demos

### Kubernetes
**Pros**:
- Production-grade
- Auto-scaling
- High availability
- Multi-cloud support
- Rolling updates
- Self-healing

**Cons**:
- Complex setup
- Requires K8s knowledge
- Higher operational overhead
- Can be expensive

**When to use**: Production deployments, enterprise, high traffic

### HuggingFace Spaces
**Pros**:
- Free tier available
- Zero DevOps
- Automatic HTTPS
- Great for demos
- Easy sharing

**Cons**:
- No persistent storage
- Limited resources
- Not for production
- Restarts lose data

**When to use**: Demos, showcases, testing, portfolio

### Render
**Pros**:
- Simple deployment
- Persistent storage
- Automatic HTTPS
- Git-based deployments
- Reasonable pricing

**Cons**:
- Limited free tier
- Less control than K8s
- Single provider lock-in

**When to use**: Quick production, small-medium scale, MVP

## Architecture Components

All deployment methods include:

### Core Services

1. **API (FastAPI)**
   - REST endpoints
   - RAG query processing
   - Authentication
   - Rate limiting

2. **Frontend (Next.js)**
   - User interface
   - Chat interface
   - Dashboard

3. **ChromaDB**
   - Vector database
   - Document embeddings
   - Similarity search

4. **PostgreSQL**
   - User data
   - Chat history
   - Session management

5. **Redis**
   - Caching
   - Rate limiting
   - Session storage

6. **MinIO** (optional)
   - Object storage
   - File uploads
   - Media storage

## Deployment Guides

### 1. Local Development (Docker Compose)

```bash
# Clone repository
git clone https://github.com/Benaah/amaniquery.git
cd amaniquery

# Set up environment
cp .env.example .env
# Edit .env with your API keys

# Start all services
docker-compose --profile full up -d

# Access application
# Frontend: http://localhost:3000
# API: http://localhost:8000
# API Docs: http://localhost:8000/docs
```

See [DOCKER_README.md](./DOCKER_README.md) for details.

### 2. Production (Kubernetes)

```bash
# Prerequisites: kubectl, cluster access

# Create namespace and secrets
kubectl create namespace amaniquery
kubectl create secret generic amaniquery-secrets \
  --from-literal=POSTGRES_PASSWORD=your_password \
  --from-literal=MOONSHOT_API_KEY=your_key \
  --namespace amaniquery

# Deploy to production
kubectl apply -k k8s/overlays/prod

# Verify deployment
kubectl get all -n amaniquery
```

See [KUBERNETES_DEPLOYMENT.md](./KUBERNETES_DEPLOYMENT.md) for details.

### 3. Demo (HuggingFace Spaces)

```bash
# Set HuggingFace token
export HF_TOKEN=your_token

# Deploy to HuggingFace
python deploy_to_hf.py

# Configure secrets in HF UI
# https://huggingface.co/spaces/YourUsername/amaniquery/settings
```

See [HUGGINGFACE_DEPLOYMENT.md](./HUGGINGFACE_DEPLOYMENT.md) for details.

### 4. Managed Hosting (Render)

```bash
# Connect GitHub repository to Render
# Render will automatically detect render.yaml

# Or use Render CLI
render deploy
```

See [RENDER_DEPLOYMENT.md](./RENDER_DEPLOYMENT.md) for details.

## Environment Variables

### Required for All Deployments

```bash
# LLM Provider
LLM_PROVIDER=moonshot  # or openai, anthropic
DEFAULT_MODEL=moonshot-v1-8k
EMBEDDING_MODEL=all-MiniLM-L6-v2

# API Keys (choose one or more)
MOONSHOT_API_KEY=your_key
OPENAI_API_KEY=your_key
ANTHROPIC_API_KEY=your_key

# Database
POSTGRES_PASSWORD=secure_password
DATABASE_URL=postgresql://user:pass@host:5432/db

# Vector Database
CHROMA_HOST=chromadb-service
CHROMA_PORT=8000

# Redis
REDIS_URL=redis://redis-service:6379/0
```

### Optional Features

```bash
# SMS Gateway (Africa's Talking)
AFRICASTALKING_API_KEY=your_key
AFRICASTALKING_USERNAME=your_username

# Voice Agent (LiveKit)
LIVEKIT_URL=wss://your-livekit-server
LIVEKIT_API_KEY=your_key
LIVEKIT_API_SECRET=your_secret

# MinIO (Object Storage)
MINIO_ENDPOINT=minio-service:9000
MINIO_ACCESS_KEY=admin
MINIO_SECRET_KEY=your_secret

# Scheduler
ENABLE_SCHEDULER=true  # For automatic data crawling
SCHEDULER_BACKEND=apscheduler
```

## Security Best Practices

1. **Never commit secrets**
   - Use `.env` files locally (gitignored)
   - Use Kubernetes Secrets for K8s
   - Use HF Space secrets for HuggingFace
   - Use Render environment variables

2. **Use HTTPS everywhere**
   - Let's Encrypt with cert-manager (K8s)
   - Automatic HTTPS on Render/HF

3. **Enable authentication**
   - JWT tokens for API access
   - OAuth for user login

4. **Rate limiting**
   - Prevent abuse
   - Protect API from overload

5. **Network policies**
   - Restrict pod-to-pod communication (K8s)
   - Use private networks when possible

## Monitoring

### Logs

```bash
# Docker Compose
docker-compose logs -f api

# Kubernetes
kubectl logs -f -n amaniquery deployment/api

# HuggingFace
# View in HF Spaces UI > Logs tab
```

### Metrics

```bash
# Kubernetes (with Prometheus)
kubectl port-forward -n monitoring svc/prometheus 9090:9090

# Access Grafana dashboards
kubectl port-forward -n monitoring svc/grafana 3000:3000
```

### Health Checks

```bash
# API health
curl http://localhost:8000/health

# Database status
curl http://localhost:8000/api/stats
```

## Troubleshooting

### Common Issues

1. **Container won't start**
   - Check logs: `docker logs <container>`
   - Verify environment variables
   - Check port conflicts

2. **Database connection failed**
   - Verify database is running
   - Check connection string
   - Verify credentials

3. **Out of memory**
   - Increase resource limits
   - Reduce model size
   - Enable swap (not recommended for prod)

4. **Slow queries**
   - Check vector database size
   - Optimize chunk size
   - Increase vector search limit

See deployment-specific guides for detailed troubleshooting.

## Migration Between Deployments

### From Docker Compose to Kubernetes

1. Export data from Docker volumes
2. Build and push images to registry
3. Deploy to K8s cluster
4. Import data to K8s persistent volumes

### From HuggingFace to Kubernetes

1. Download data from HF Space
2. Set up K8s cluster
3. Configure persistent storage
4. Deploy and import data

## Cost Estimation

### Docker Compose (Self-hosted)
- **Cloud VM**: $5-50/month (DigitalOcean, Linode)
- **Hardware**: Free (local machine)

### Kubernetes
- **Managed K8s**: $70-500/month
  - GKE: ~$70/month (1 node)
  - EKS: ~$150/month (1 node + EKS fee)
  - AKS: ~$70/month (1 node)
- **On-premise**: Hardware cost only

### HuggingFace Spaces
- **Free tier**: $0 (with limitations)
- **CPU Basic**: ~$22/month
- **GPU T4**: ~$432/month

### Render
- **Free tier**: $0 (limited)
- **Starter**: $7-25/month per service
- **Standard**: $25-85/month per service

## Support and Resources

- **Documentation**: See `docs/` directory
- **Issues**: https://github.com/Benaah/amaniquery/issues
- **Discussions**: GitHub Discussions
- **Email**: support@amaniquery.example.com

## Next Steps

Choose your deployment method and follow the detailed guide:

1. 🧪 **Testing/Development**: Start with [Docker Compose](./DOCKER_README.md)
2. 🎯 **Demo/Showcase**: Deploy to [HuggingFace](./HUGGINGFACE_DEPLOYMENT.md)
3. 🚀 **Quick Production**: Use [Render](./RENDER_DEPLOYMENT.md)
4. 🏢 **Enterprise/Scale**: Set up [Kubernetes](./KUBERNETES_DEPLOYMENT.md)
