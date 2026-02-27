---
description: Secrets Management (Env / K8s)
---

# Secrets Management Workflow

This workflow handles the creation, rotation, and distribution of sensitive configuration parameters like API keys and database credentials.

## Application Environment `.env`

1. The source of truth for local config is `.env`. Keep it secure and NEVER commit it.
2. When a secret needs rotating (e.g., `OPENAI_API_KEY`), modify it in your `.env` file.
3. Reload your local development servers by stopping and starting them (`docker-compose restart api`).

## Kubernetes Secrets

1. After updating the local `.env` file, regenerate the Kubernetes secrets bundle to reflect the new state. This avoids manual YAML manifest editing.
   // turbo

   ```bash
   make k8s-secrets
   ```

2. The Makefile handles `kubectl create secret generic amaniquery-secrets --from-env-file=.env ... --dry-run=client -o yaml | kubectl apply -f -`.
3. To view existing generic secrets in the cluster:
   // turbo

   ```bash
   kubectl get secrets -n amaniquery
   ```

4. Verify the secret applies to running pods. Pods using `envFrom: - secretRef: name: amaniquery-secrets` must be un-gracefully restarted or rollout-restarted to pull the new securely injected envs.
   // turbo

   ```bash
   kubectl rollout restart deployment api-deployment -n amaniquery
   kubectl rollout restart deployment frontend-deployment -n amaniquery
   ```

5. To completely delete the secret configuration from the cluster:

   ```bash
   make k8s-secrets-delete
   ```
