# Docker Deployment Guide

This guide explains how to deploy AmaniQuery using Docker and Docker Compose.

## Prerequisites

- Docker Engine 20.10+
- Docker Compose 2.0+
- At least 4GB RAM available
- At least 10GB free disk space

## Deployment Options

### Option 1: Single Container (Recommended for Simple Deployment)

Build and run both frontend and backend in a single container with Nginx reverse proxy:

```bash
# Clone the repository
git clone <your-repo-url>
cd amaniquery

# Set up environment variables
cp .env.example .env
# Edit .env with your API keys

# Build the image
docker build -t amaniquery .

# Run the container
docker run -d \
  --name amaniquery \
  -p 80:80 \
  -v $(pwd)/data:/app/data \
  -v $(pwd)/config:/app/config \
  --env-file .env \
  amaniquery
```

**Access the application at:** http://localhost

**What's included:**
- Next.js frontend served on port 80
- FastAPI backend running internally on port 8000
- Nginx reverse proxy routing requests
- Supervisor process manager
- Health checks and monitoring

**Environment Variables for Single Container:**
```bash
# Required
LLM_PROVIDER=moonshot
MOONSHOT_API_KEY=your_api_key_here

# Optional
GEMINI_API_KEY=your_gemini_key
AT_USERNAME=your_africastalking_username
AT_API_KEY=your_africastalking_key
```

### Option 2: Multi-Container with Docker Compose

Use separate containers for better scalability and development workflow.

## Quick Start (Multi-Container)

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd amaniquery
   ```

2. **Set up environment variables**
   ```bash
   cp .env.example .env
   # Edit .env with your API keys and configuration
   ```

3. **Build and start the services**
   ```bash
   docker-compose up --build
   ```

4. **Access the application**
   - Frontend: http://localhost:3000
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs
   - ChromaDB: http://localhost:8001

## Services

### Frontend (Next.js)
- **Port**: 3000
- **Build**: Multi-stage Dockerfile with standalone output
- **Environment**: Production optimized

### API (FastAPI)
- **Port**: 8000
- **Dependencies**: Python 3.11, all requirements from requirements.txt
- **Health Check**: Automatic health monitoring

### ChromaDB (Vector Database)
- **Port**: 8001 (internal), 8001 (external)
- **Persistence**: Data stored in named Docker volume
- **Health Check**: Automatic heartbeat monitoring

### PostgreSQL (Optional)
- **Port**: 5432
- **Database**: amaniquery
- **Persistence**: Data stored in named Docker volume

## Environment Variables

Copy `.env.example` to `.env` and configure:

### Required
- `LLM_PROVIDER`: Choose from moonshot, openai, anthropic
- `MOONSHOT_API_KEY` or `OPENAI_API_KEY` or `ANTHROPIC_API_KEY`: Your API key
- `GEMINI_API_KEY`: For research features (optional)

### Optional
- `AT_USERNAME` and `AT_API_KEY`: For SMS features
- `DATABASE_URL`: PostgreSQL connection string
- `CORS_ORIGINS`: Allowed origins for API

## Development

### Start in development mode
```bash
docker-compose -f docker-compose.dev.yml up --build
```

### View logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f api
docker-compose logs -f frontend
```

### Rebuild specific service
```bash
docker-compose up --build api
```

### Stop and clean up
```bash
docker-compose down
docker-compose down -v  # Also remove volumes
```

## Production Deployment

### Using Docker Compose
```bash
# Build for production
docker-compose -f docker-compose.prod.yml up --build -d

# Scale services
docker-compose up -d --scale api=3
```

### Using Docker Swarm
```bash
docker stack deploy -c docker-compose.yml amaniquery
```

### Using Kubernetes
Convert docker-compose.yml to Kubernetes manifests using `kompose`:
```bash
kompose convert -f docker-compose.yml
```

## Data Persistence

- **ChromaDB data**: Stored in `chroma_data` volume
- **PostgreSQL data**: Stored in `postgres_data` volume
- **Application data**: Mounted from `./data` directory

## Troubleshooting

### Common Issues

1. **Port conflicts**
   ```bash
   # Check what's using ports
   netstat -tulpn | grep :3000
   netstat -tulpn | grep :8000

   # Change ports in docker-compose.yml
   ```

2. **Memory issues**
   ```bash
   # Increase Docker memory limit
   # Docker Desktop: Settings > Resources > Memory
   ```

3. **Build failures**
   ```bash
   # Clear Docker cache
   docker system prune -a

   # Rebuild without cache
   docker-compose build --no-cache
   ```

4. **Database connection issues**
   ```bash
   # Check ChromaDB health
   curl http://localhost:8001/api/v1/heartbeat

   # Check PostgreSQL
   docker-compose exec postgres psql -U amaniquery -d amaniquery
   ```

### Logs and Debugging

```bash
# View all logs
docker-compose logs

# Follow logs in real-time
docker-compose logs -f

# View specific service logs
docker-compose logs api

# Enter container shell
docker-compose exec api bash
docker-compose exec frontend sh
```

## Security Considerations

1. **Environment Variables**: Never commit `.env` file
2. **API Keys**: Use Docker secrets or external secret management
3. **Network**: Use internal networks for service communication
4. **Updates**: Regularly update base images and dependencies

## Performance Tuning

### Resource Limits
```yaml
services:
  api:
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '1.0'
        reservations:
          memory: 1G
          cpus: '0.5'
```

### Scaling
```bash
# Scale API service
docker-compose up -d --scale api=3

# Load balancing with nginx
# Add nginx service to docker-compose.yml
```

## Backup and Restore

### Database Backup
```bash
# ChromaDB backup
docker run --rm -v amaniquery_chroma_data:/data -v $(pwd):/backup alpine tar czf /backup/chroma_backup.tar.gz -C /data .

# PostgreSQL backup
docker-compose exec postgres pg_dump -U amaniquery amaniquery > backup.sql
```

### Restore
```bash
# ChromaDB restore
docker run --rm -v amaniquery_chroma_data:/data -v $(pwd):/backup alpine tar xzf /backup/chroma_backup.tar.gz -C /data

# PostgreSQL restore
docker-compose exec -T postgres psql -U amaniquery amaniquery < backup.sql
```