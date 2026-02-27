---
description: Docker Production Build & Deploy
---

# Docker Production Workflow

This workflow covers building and running the AmaniQuery stack using the production Docker Compose configuration.

1. Ensure you are on the `master` branch and have pulled the latest code.
2. Build the production Docker images:

   ```bash
   make prod-build
   ```

   *Alternative: `docker-compose -f docker-compose.prod.yml build`*
3. Start the production services in detached mode:

   ```bash
   make prod-up
   ```

   *Alternative: `docker-compose -f docker-compose.prod.yml up -d`*
4. Monitor the production logs to ensure successful startup:

   ```bash
   make prod-logs
   ```

5. Verify that the NGINX reverse proxy is serving the frontend correctly by navigating to your domain or `http://localhost:8080`.
6. To update the deployment with new code:

   ```bash
   git pull origin master
   make prod-build
   make prod-up
   ```

7. To stop the production services:

   ```bash
   make prod-down
   ```
