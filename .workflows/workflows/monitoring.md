---
description: Monitoring and Observability
---

# Monitoring Workflow

This workflow covers how to monitor the health and performance of the AmaniQuery platform in Docker and Kubernetes.

## Docker Environments

1. View overall container status:
   // turbo

   ```bash
   make status
   ```

2. Tail logs for all running services:

   ```bash
   make logs
   ```

3. Tail specific service logs:

   ```bash
   make logs-api
   # or make logs-frontend, make logs-db
   ```

4. Access a shell within a specific container for debugging:

   ```bash
   make shell-api
   ```

## Kubernetes Environments

1. Check the status of all pods and resources in the namespace:
   // turbo

   ```bash
   make k8s-status
   ```

2. Tail logs from the API pods:

   ```bash
   make k8s-logs-api
   ```

3. View recent cluster events (useful for diagnosing CrashLoopBackOff or pending pods):
   // turbo

   ```bash
   make k8s-events
   ```

4. View resource utilization (CPU and Memory) using the metrics server:
   // turbo

   ```bash
   make k8s-top
   ```

5. Port-forward the API securely to your local machine for debugging:

   ```bash
   make k8s-port-forward
   ```

   *(API becomes available on <http://localhost:8000>)*
