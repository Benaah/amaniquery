---
description: Docker Compose Local Development
---

# Docker Compose Local Development Workflow

This workflow starts the AmaniQuery stack (API, Frontend, Database, Vector DB, Redis) using Docker Compose for local development.

1. Ensure Docker and Docker Compose are installed and running.
2. (Optional) Copy `.env.example` to `.env` if you haven't already, and populate your API keys:

   ```bash
   cp .env.example .env
   ```

3. Build the Docker images (only necessary on first run or after adding dependencies):

   ```bash
   make build
   ```

   *Alternative: `docker-compose build`*
4. Start all services in the background:
   // turbo

   ```bash
   make up
   ```

   *Alternative: `docker-compose up -d`*
5. Check the status of the running containers:

   ```bash
   make status
   ```

   *Alternative: `docker-compose ps`*
6. View logs for all services to ensure they started correctly:

   ```bash
   make logs
   ```

   *To view specific logs: `make logs-api`, `make logs-frontend`, `make logs-db`*
7. Access the application:
   - Frontend: `http://localhost:3000`
   - API Docs: `http://localhost:8000/docs`
8. To stop all services without deleting data:
   // turbo

   ```bash
   make down
   ```

   *Alternative: `docker-compose down`*
9. To completely clean up containers, volumes, and images (WARNING: deletes data!):

   ```bash
   make clean
   ```
