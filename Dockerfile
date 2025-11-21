# Dockerfile for FastAPI backend deployment on Render
FROM python:3.14-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    NODE_ENV=production

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        curl \
        supervisor && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN useradd --create-home --shell /bin/bash app && \
    chown -R app:app /app

USER app

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=30s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:${PORT:-8000}/health || exit 1

COPY <<EOF /etc/supervisor/conf.d/app.conf
[supervisord]
nodaemon=true
user=root

[program:api]
command=python -m uvicorn Module4_NiruAPI.api:app --host 0.0.0.0 --port ${PORT:-8000}
directory=/app
user=app
autostart=true
autorestart=true
stdout_logfile=/dev/stdout
stdout_logfile_maxbytes=0
stderr_logfile=/dev/stderr
stderr_logfile_maxbytes=0
environment=PYTHONPATH=/app,CORS_ORIGINS=http://localhost:3000,API_HOST=0.0.0.0,API_PORT=${PORT:-8000},https://amaniquery.vercel.app,https://www.amaniquery.vercel.app
EOF

CMD ["/usr/bin/supervisord","-c","/etc/supervisor/conf.d/app.conf"]
