---
description: Kubernetes Deployment (Dev/Prod)
---

# Kubernetes Deployment Workflow

This workflow manages the deployment of AmaniQuery to a Kubernetes cluster using Kustomize overlays.

1. Ensure `kubectl` is authenticated to your target cluster.
2. Build and push the Docker images to your container registry:

   ```bash
   make k8s-build
   ```

   *Note: You must manually tag and push the images, e.g., `docker tag amaniquery-api:latest YOUR_REGISTRY/amaniquery-api:latest` and `docker push YOUR_REGISTRY/amaniquery-api:latest`.*
3. Ensure your Kubernetes secrets are created from your `.env` file:

   ```bash
   make k8s-secrets
   ```

4. Deploy to the **Development** environment:
   // turbo

   ```bash
   make k8s-dev
   ```

   *(Wait for the rollout to complete)*
5. Deploy to the **Production** environment:
   // turbo

   ```bash
   make k8s-prod
   ```

6. Check the status of the deployment (Pods, Services, PVCs, Ingress):
   // turbo

   ```bash
   make k8s-status
   ```

7. View logs from the API pods:

   ```bash
   make k8s-logs-api
   ```

8. To completely remove the deployment from an environment (WARNING: data loss!):

   ```bash
   make k8s-delete
   # OR for production
   make k8s-delete-prod
   ```
