---
description: Rollback Deployments
---

# Rollback Workflow

This workflow details how to revert an AmaniQuery application deployment to a known healthy state if issues are encountered.

## Docker Compose

1. Stop the current deployment:

   ```bash
   docker-compose down
   ```

2. If you need to revert to a specific image tag, manually modify `docker-compose.yml` (or your override files) to specify the previous, known-working tag instead of `latest`.
3. Restart the stack:

   ```bash
   docker-compose up -d
   ```

## Kubernetes

1. Identify the recent rollout history for the API deployment:
   // turbo

   ```bash
   kubectl rollout history deployment/api-deployment -n amaniquery
   ```

2. Undo the rollout to the immediate previous revision:

   ```bash
   kubectl rollout undo deployment/api-deployment -n amaniquery
   ```

3. To roll back to a specific target revision seen in the history:

   ```bash
   kubectl rollout undo deployment/api-deployment -n amaniquery --to-revision=REVISION_NUMBER
   ```

4. Monitor the status of the undo process:
   // turbo

   ```bash
   kubectl rollout status deployment/api-deployment -n amaniquery
   ```

   *(Repeat for the `frontend-deployment` if applicable).*
5. Confirm application stability via testing or checking metrics.
