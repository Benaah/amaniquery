---
description: Deploy to Render Cloud
---

# Render Deployment Workflow

This workflow describes the deployment process to Render Cloud using the project's Docker files.

1. Ensure the `Dockerfile` in the root correctly builds the `api` image.
2. Ensure the `/frontend/Dockerfile` correctly builds the frontend application.
3. Access your Render Dashboard and navigate to the associated AmaniQuery web services.
4. Render deploys are typically triggered by push to the `master` branch. Ensure your commits are merged.
5. Watch the deployment logs in the Render Dashboard. The API requires the port to be dynamically bound, which is natively handled in `start_api.py` via the `PORT` environment variable.
6. Check that Render has the correct environment secrets mapped:
   - `DATABASE_URL` (requires a Render PostgreSQL instance)
   - `REDIS_URL` (requires a Render Redis instance)
   - `LLM_PROVIDER` and corresponding API keys
   - `ENABLE_SCHEDULER=true/false` (often better to run a separate background worker instance for the scheduler on Render)
7. Check the Render web service health endpoint.
