# Kubernetes Deployment Guide for AmaniQuery

## Overview

This guide covers deploying AmaniQuery to Kubernetes clusters (GKE, EKS, AKS, or on-premises) using production-ready configurations with auto-scaling, persistent storage, and security best practices.

## Architecture

```
┌─────────────────────────────────────────────────────────┐
│                    Ingress Controller                    │
│              (NGINX + cert-manager/TLS)                  │
└─────────────────┬───────────────────────┬────────────────┘
                  │                       │
          ┌───────▼────────┐      ┌──────▼───────┐
          │   Frontend      │      │     API      │
          │  (Next.js)      │      │  (FastAPI)   │
          │   2-5 replicas  │      │  2-10 replicas│
          └────────────────┘      └──────┬────────┘
                                         │
                  ┌──────────────────────┼──────────────────┐
                  │                      │                  │
          ┌───────▼────────┐  ┌─────────▼──────┐  ┌───────▼────────┐
          │   PostgreSQL    │  │   ChromaDB     │  │     Redis      │
          │  (StatefulSet)  │  │ (StatefulSet)  │  │ (StatefulSet)  │
          │   + PVC (10Gi)  │  │  + PVC (20Gi)  │  │  + PVC (5Gi)   │
          └────────────────┘  └────────────────┘  └────────────────┘
                                       │
                                ┌──────▼────────┐
                                │     MinIO     │
                                │ (StatefulSet) │
                                │ + PVC (50Gi)  │
                                └───────────────┘
```

## Prerequisites

### Required Tools

```bash
# kubectl (Kubernetes CLI)
kubectl version --client

# kustomize (built into kubectl 1.14+)
kubectl kustomize --help

# Optional: Helm (for ingress-nginx, cert-manager)
helm version

# Optional: k9s (Kubernetes dashboard)
k9s version
```

### Cluster Requirements

- **Kubernetes**: v1.24+
- **CPU**: 8+ cores (production), 4+ cores (dev)
- **Memory**: 16GB+ (production), 8GB+ (dev)
- **Storage**: Dynamic provisioning support (StorageClass)
- **Ingress Controller**: NGINX Ingress Controller
- **Cert Manager**: For automatic TLS certificates (optional but recommended)

## Quick Start

### 1. Clone and Navigate

```bash
cd AmaniQuery/k8s
```

### 2. Configure Secrets

**IMPORTANT**: Never commit real secrets to git!

```bash
# Create secrets from environment variables
kubectl create namespace amaniquery

kubectl create secret generic amaniquery-secrets \
  --from-literal=POSTGRES_PASSWORD='your_secure_password' \
  --from-literal=MOONSHOT_API_KEY='your_moonshot_key' \
  --from-literal=OPENAI_API_KEY='your_openai_key' \
  --from-literal=MINIO_ACCESS_KEY='admin' \
  --from-literal=MINIO_SECRET_KEY='your_minio_password' \
  --from-literal=AFRICASTALKING_API_KEY='your_at_key' \
  --from-literal=AFRICASTALKING_USERNAME='your_at_username' \
  --namespace amaniquery
```

### 3. Build and Push Docker Images

```bash
# Build images
docker build -t your-registry/amaniquery-api:v1.0.0 -f Dockerfile .
docker build -t your-registry/amaniquery-frontend:v1.0.0 -f frontend/Dockerfile ./frontend

# Push to registry
docker push your-registry/amaniquery-api:v1.0.0
docker push your-registry/amaniquery-frontend:v1.0.0
```

### 4. Update Image References

Edit `k8s/base/kustomization.yaml` or environment-specific overlays:

```yaml
images:
  - name: amaniquery-api
    newName: your-registry/amaniquery-api
    newTag: v1.0.0
  - name: amaniquery-frontend
    newName: your-registry/amaniquery-frontend
    newTag: v1.0.0
```

### 5. Deploy to Development

```bash
# Preview manifests
kubectl kustomize overlays/dev

# Apply to cluster
kubectl apply -k overlays/dev

# Watch deployment progress
kubectl get pods -n amaniquery -w
```

### 6. Deploy to Production

```bash
# Update production image tags in overlays/prod/kustomization.yaml
kubectl apply -k overlays/prod

# Verify deployment
kubectl get all -n amaniquery
```

## Environment-Specific Deployments

### Development Environment

```bash
kubectl apply -k overlays/dev
```

**Characteristics**:
- 1 replica for API and frontend
- Lower resource limits (512Mi RAM, 250m CPU)
- Scheduler disabled
- API reload enabled

### Production Environment

```bash
kubectl apply -k overlays/prod
```

**Characteristics**:
- 3+ replicas with auto-scaling (up to 10 for API)
- Higher resource limits (2-8Gi RAM, 1-4 CPU)
- Pod anti-affinity for high availability
- Scheduler enabled
- Production-grade monitoring

## Installation Steps (Detailed)

### Step 1: Install Prerequisites

#### Install NGINX Ingress Controller

```bash
# Using Helm
helm repo add ingress-nginx https://kubernetes.github.io/ingress-nginx
helm repo update
helm install ingress-nginx ingress-nginx/ingress-nginx \
  --namespace ingress-nginx \
  --create-namespace

# Verify installation
kubectl get pods -n ingress-nginx
```

#### Install cert-manager (for TLS)

```bash
# Install cert-manager
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/download/v1.13.0/cert-manager.yaml

# Create ClusterIssuer for Let's Encrypt
cat <<EOF | kubectl apply -f -
apiVersion: cert-manager.io/v1
kind: ClusterIssuer
metadata:
  name: letsencrypt-prod
spec:
  acme:
    server: https://acme-v02.api.letsencrypt.org/directory
    email: your-email@example.com
    privateKeySecretRef:
      name: letsencrypt-prod
    solvers:
    - http01:
        ingress:
          class: nginx
EOF
```

### Step 2: Configure Storage

#### Check Available StorageClasses

```bash
kubectl get storageclass
```

Update PVC manifests if your cluster uses a different StorageClass:

```yaml
# In k8s/base/persistentvolume.yaml
storageClassName: gp2  # For AWS EKS
# or
storageClassName: standard-rwo  # For GKE
# or
storageClassName: managed-premium  # For AKS
```

### Step 3: Update Configuration

#### Edit ConfigMap (k8s/base/configmap.yaml)

```yaml
data:
  CORS_ORIGINS: "https://yourdomain.com,https://www.yourdomain.com"
  LLM_PROVIDER: "moonshot"  # or openai, anthropic
  DEFAULT_MODEL: "moonshot-v1-8k"
```

#### Edit Ingress (k8s/base/ingress.yaml)

```yaml
spec:
  tls:
  - hosts:
    - amaniquery.yourdomain.com
    - api.amaniquery.yourdomain.com
    secretName: amaniquery-tls-cert
  rules:
  - host: amaniquery.yourdomain.com
    # ... rest of config
```

### Step 4: Deploy Base Resources

```bash
# Create namespace
kubectl apply -f base/namespace.yaml

# Create secrets (see step 2 in Quick Start)

# Apply base configuration
kubectl apply -k base/
```

### Step 5: Verify Deployment

```bash
# Check all resources
kubectl get all -n amaniquery

# Check pods status
kubectl get pods -n amaniquery

# Check persistent volumes
kubectl get pvc -n amaniquery

# Check services
kubectl get svc -n amaniquery

# Check ingress
kubectl get ingress -n amaniquery
```

### Step 6: Access the Application

```bash
# Get LoadBalancer IP (if using LoadBalancer service)
kubectl get svc amaniquery-loadbalancer -n amaniquery

# Get Ingress IP
kubectl get ingress amaniquery-ingress -n amaniquery

# Port-forward for local testing
kubectl port-forward -n amaniquery svc/api-service 8000:8000
kubectl port-forward -n amaniquery svc/frontend-service 3000:3000
```

## Monitoring and Debugging

### View Logs

```bash
# API logs
kubectl logs -n amaniquery -l app=api --tail=100 -f

# Frontend logs
kubectl logs -n amaniquery -l app=frontend --tail=100 -f

# Database logs
kubectl logs -n amaniquery -l app=postgres --tail=100 -f
kubectl logs -n amaniquery -l app=chromadb --tail=100 -f
```

### Exec into Pods

```bash
# Access API container
kubectl exec -it -n amaniquery deployment/api -- /bin/bash

# Access PostgreSQL
kubectl exec -it -n amaniquery statefulset/postgres -- psql -U amaniquery
```

### Check Resource Usage

```bash
# Pod resource usage
kubectl top pods -n amaniquery

# Node resource usage
kubectl top nodes
```

### Debug Failing Pods

```bash
# Describe pod
kubectl describe pod -n amaniquery <pod-name>

# Get events
kubectl get events -n amaniquery --sort-by='.lastTimestamp'

# Check pod logs
kubectl logs -n amaniquery <pod-name> --previous
```

## Scaling

### Manual Scaling

```bash
# Scale API deployment
kubectl scale deployment api -n amaniquery --replicas=5

# Scale frontend
kubectl scale deployment frontend -n amaniquery --replicas=3
```

### Auto-scaling

HPA is configured in `base/hpa.yaml`:

```bash
# Check HPA status
kubectl get hpa -n amaniquery

# Describe HPA
kubectl describe hpa api-hpa -n amaniquery
```

## Updates and Rollouts

### Rolling Updates

```bash
# Update image
kubectl set image deployment/api api=your-registry/amaniquery-api:v1.1.0 -n amaniquery

# Check rollout status
kubectl rollout status deployment/api -n amaniquery

# View rollout history
kubectl rollout history deployment/api -n amaniquery
```

### Rollback

```bash
# Rollback to previous version
kubectl rollout undo deployment/api -n amaniquery

# Rollback to specific revision
kubectl rollout undo deployment/api --to-revision=2 -n amaniquery
```

## Backup and Restore

### Backup PostgreSQL

```bash
# Create backup
kubectl exec -n amaniquery statefulset/postgres -- pg_dump -U amaniquery amaniquery > backup.sql

# Restore backup
kubectl exec -i -n amaniquery statefulset/postgres -- psql -U amaniquery amaniquery < backup.sql
```

### Backup ChromaDB

```bash
# Copy data from PVC
kubectl cp amaniquery/chromadb-0:/chroma/chroma ./chromadb-backup
```

## Troubleshooting

### Pods Not Starting

```bash
# Check pod status
kubectl describe pod <pod-name> -n amaniquery

# Common issues:
# 1. Image pull errors - verify image name/tag and registry credentials
# 2. Insufficient resources - check node capacity
# 3. Volume mount errors - verify PVC is bound
```

### Database Connection Issues

```bash
# Verify database is running
kubectl get pods -n amaniquery -l app=postgres

# Test connection from API pod
kubectl exec -n amaniquery deployment/api -- nc -zv postgres-service 5432

# Check database logs
kubectl logs -n amaniquery statefulset/postgres
```

### Ingress Not Working

```bash
# Verify ingress controller
kubectl get pods -n ingress-nginx

# Check ingress resource
kubectl describe ingress amaniquery-ingress -n amaniquery

# Verify DNS points to ingress IP
kubectl get ingress amaniquery-ingress -n amaniquery
```

## Security Best Practices

1. **Never commit secrets to git** - Use `kubectl create secret` or external secret management
2. **Use RBAC** - Limit service account permissions
3. **Network Policies** - Restrict pod-to-pod communication
4. **Resource Limits** - Prevent resource exhaustion
5. **Security Context** - Run containers as non-root
6. **Image Scanning** - Scan images for vulnerabilities
7. **TLS Everywhere** - Use cert-manager for automatic certificates

## Cost Optimization

1. **Right-size resources** - Adjust requests/limits based on actual usage
2. **Use spot instances** - For non-critical workloads
3. **Enable cluster autoscaler** - Scale nodes based on demand
4. **Use PVC resize** - Expand volumes instead of creating new ones
5. **Monitor idle resources** - Remove unused PVCs and services

## Cloud Provider Specifics

### AWS EKS

```bash
# Storage class
storageClassName: gp3

# Load balancer annotations
service.beta.kubernetes.io/aws-load-balancer-type: "nlb"
```

### Google GKE

```bash
# Storage class
storageClassName: standard-rwo

# Load balancer annotations
cloud.google.com/load-balancer-type: "Internal"
```

### Azure AKS

```bash
# Storage class
storageClassName: managed-premium

# Load balancer annotations
service.beta.kubernetes.io/azure-load-balancer-internal: "true"
```

## Additional Resources

- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Kustomize Guide](https://kustomize.io/)
- [NGINX Ingress Controller](https://kubernetes.github.io/ingress-nginx/)
- [cert-manager Documentation](https://cert-manager.io/docs/)

## Support

For issues or questions:
- GitHub Issues: https://github.com/Benaah/amaniquery/issues
- Documentation: See `docs/` directory
