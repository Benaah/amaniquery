# AmaniQuery Deployment Guide

This guide covers streamlined deployment options for AmaniQuery using Docker and Render.

## Quick Start

### Option 1: Full Stack with Docker Compose (Recommended for Development)

```bash
# Start all services (frontend, API, databases)
docker-compose --profile full up -d

# Or use the blueprint version
docker-compose -f docker-compose.blueprint.yml --profile full up -d
```

### Option 2: Deploy to Render (Recommended for Production)

1. Connect your GitHub repository to Render
2. Use the `render.yaml` blueprint for automatic service creation
3. Services will be automatically configured with proper CORS and networking

## Deployment Profiles

### Docker Compose Profiles

- `full`: Complete stack (frontend + API + ChromaDB + PostgreSQL)
- `api-only`: API with databases (for API development/testing)
- `frontend-only`: Frontend only (requires external API)
- `db-only`: Databases only (for data management)

### Usage Examples

```bash
# Development with full stack
docker-compose --profile full up

# API development only
docker-compose --profile api-only up

# Frontend development (connect to production API)
NEXT_PUBLIC_API_URL=https://your-api.onrender.com docker-compose --profile frontend-only up

# Database management
docker-compose --profile db-only up
```

## Environment Variables

### Required for API
- `LLM_PROVIDER`: AI provider (moonshot, openai, anthropic)
- `DEFAULT_MODEL`: Default model name
- `EMBEDDING_MODEL`: Embedding model name
- `CORS_ORIGINS`: Allowed CORS origins (comma-separated)

### Optional
- `POSTGRES_*`: PostgreSQL connection details
- `CHROMA_HOST/CHROMA_PORT`: ChromaDB connection
- `API_PORT`: API port (default: 8000)

## CORS Configuration

CORS is automatically configured to allow:
- Local development: `http://localhost:3000`
- Docker networking: `http://frontend:3000`
- Render deployment: `https://amaniquery.onrender.com`

## File Structure

```
├── docker-compose.yml          # Original compose file
├── docker-compose.blueprint.yml # Streamlined compose with profiles
├── Dockerfile                  # Multi-service container (legacy)
├── Dockerfile.api              # API-only container
├── render.yaml                 # Render deployment blueprint
├── frontend/Dockerfile         # Frontend container
└── requirements.txt            # Python dependencies
```

## Production Deployment

### Render (Recommended)

1. Push code to GitHub
2. Connect repository to Render
3. Render will automatically create services based on `render.yaml`
4. Services will have proper networking and CORS configured

### Manual Docker Deployment

```bash
# Build and run API
docker build -f Dockerfile.api -t amaniquery-api .
docker run -p 8000:8000 -e LLM_PROVIDER=moonshot amaniquery-api

# Build and run frontend
cd frontend
docker build -t amaniquery-frontend .
docker run -p 3000:3000 -e NEXT_PUBLIC_API_URL=http://your-api-host amaniquery-frontend
```

## Troubleshooting

### CORS Issues
- Check `CORS_ORIGINS` environment variable
- Ensure frontend URL is included in allowed origins
- For Render, origins are automatically configured

### Database Connection
- ChromaDB should be healthy before API starts
- Check `CHROMA_HOST` and `CHROMA_PORT` settings
- PostgreSQL is optional but required for chat persistence

### Port Conflicts
- Default ports: API (8000), Frontend (3000), ChromaDB (8001), PostgreSQL (5432)
- Use environment variables to change ports if needed