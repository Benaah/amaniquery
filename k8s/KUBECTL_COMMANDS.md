# Quick Reference: Kubernetes Commands for AmaniQuery

## Deployment

```bash
# Development
kubectl apply -k k8s/overlays/dev

# Production
kubectl apply -k k8s/overlays/prod

# Delete all resources
kubectl delete -k k8s/overlays/prod
```

## Secrets Management

```bash
# Create secrets
kubectl create secret generic amaniquery-secrets \
  --from-literal=POSTGRES_PASSWORD='password' \
  --from-literal=MOONSHOT_API_KEY='key' \
  --namespace amaniquery

# View secrets (base64 encoded)
kubectl get secret amaniquery-secrets -n amaniquery -o yaml

# Delete secrets
kubectl delete secret amaniquery-secrets -n amaniquery
```

## Monitoring

```bash
# Get all resources
kubectl get all -n amaniquery

# Watch pods
kubectl get pods -n amaniquery -w

# Logs
kubectl logs -f deployment/api -n amaniquery
kubectl logs -f statefulset/postgres -n amaniquery

# Resource usage
kubectl top pods -n amaniquery
kubectl top nodes
```

## Scaling

```bash
# Manual scale
kubectl scale deployment api --replicas=5 -n amaniquery

# HPA status
kubectl get hpa -n amaniquery
kubectl describe hpa api-hpa -n amaniquery
```

## Debugging

```bash
# Describe pod
kubectl describe pod <pod-name> -n amaniquery

# Exec into container
kubectl exec -it deployment/api -n amaniquery -- /bin/bash

# Port forward
kubectl port-forward svc/api-service 8000:8000 -n amaniquery
kubectl port-forward svc/frontend-service 3000:3000 -n amaniquery

# Events
kubectl get events -n amaniquery --sort-by='.lastTimestamp'
```

## Updates

```bash
# Update image
kubectl set image deployment/api api=registry/image:v2 -n amaniquery

# Rollout status
kubectl rollout status deployment/api -n amaniquery

# Rollback
kubectl rollout undo deployment/api -n amaniquery
```

## Storage

```bash
# PVC status
kubectl get pvc -n amaniquery

# Describe PVC
kubectl describe pvc postgres-pvc -n amaniquery

# Resize PVC (if storageClass allows)
kubectl patch pvc postgres-pvc -n amaniquery -p '{"spec":{"resources":{"requests":{"storage":"20Gi"}}}}'
```

## Cleanup

```bash
# Delete namespace (deletes everything)
kubectl delete namespace amaniquery

# Delete specific resources
kubectl delete deployment api -n amaniquery
kubectl delete statefulset postgres -n amaniquery
```
