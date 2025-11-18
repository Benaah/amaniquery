# Multi-stage Dockerfile for AmaniQuery (Frontend + Backend)
FROM node:20-alpine AS frontend-builder

# Build Frontend
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci --only=production

COPY frontend/ ./
RUN npm run build

# Python Backend Stage
FROM python:3.14-slim AS backend-builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        gcc \
        g++ \
        libpq-dev \
        curl \
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Final Production Stage
FROM python:3.14-slim

# Install runtime dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        curl \
        supervisor \
    && rm -rf /var/lib/apt/lists/*

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV PYTHONPATH=/app
ENV NODE_ENV=production

# Set work directory
WORKDIR /app

# Copy Python backend from builder
COPY --from=backend-builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=backend-builder /usr/local/bin /usr/local/bin

# Copy project files
COPY . .

# Copy built frontend from builder (using standalone output)
COPY --from=frontend-builder /frontend/.next/standalone ./frontend/
COPY --from=frontend-builder /frontend/.next/static ./frontend/.next/static
COPY --from=frontend-builder /frontend/public ./frontend/public

# Create non-root user
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app

# Configure Supervisor
RUN mkdir -p /var/log/supervisor
COPY <<EOF /etc/supervisor/conf.d/app.conf
[supervisord]
nodaemon=true
user=root

[program:api]
command=python -m uvicorn Module4_NiruAPI.api:app --host 0.0.0.0 --port 8000
directory=/app
user=app
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
environment=PYTHONPATH=/app,CORS_ORIGINS=http://localhost:3000,API_HOST=0.0.0.0,API_PORT=8000

[program:frontend]
command=node server.js
directory=/app/frontend
user=app
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
environment=NEXT_PUBLIC_API_URL=http://localhost:8000,NODE_ENV=production,PORT=3000,HOSTNAME=0.0.0.0
EOF

# Switch to non-root user
USER app

# Expose ports
EXPOSE 3000 8000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1

# Start all services
CMD ["/usr/bin/supervisord", "-c", "/etc/supervisor/conf.d/app.conf"]