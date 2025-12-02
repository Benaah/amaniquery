# AmaniQuery Kubernetes Deployment

Complete Kubernetes manifests for deploying AmaniQuery to production with NGINX reverse proxy.

## Structure

```
k8s/
├── base/                          # Base Kubernetes resources
│   ├── namespace.yaml             # Namespace definition
│   ├── configmap.yaml             # App config + NGINX config
│   ├── secrets.yaml               # Secret templates (DO NOT commit real secrets!)
│   ├── persistentvolume.yaml      # PVC definitions
│   ├── statefulsets.yaml          # Databases (PostgreSQL, ChromaDB, Redis, MinIO)
│   ├── deployments.yaml           # API and Frontend deployments
│   ├── nginx-deployment.yaml      # NGINX reverse proxy
│   ├── services.yaml              # Service definitions
│   ├── ingress.yaml               # Ingress rules with TLS
│   ├── ingress-options.yaml       # Alternative ingress configurations
│   ├── hpa.yaml                   # HorizontalPodAutoscaler (API, Frontend)
│   ├── nginx-hpa.yaml             # NGINX autoscaling
│   └── kustomization.yaml         # Kustomize config
├── overlays/
│   ├── dev/                       # Development environment
│   │   ├── kustomization.yaml
│   │   ├── deployment-patch.yaml  # Lower resources
│   │   └── hpa-patch.yaml         # Smaller scale
│   ├── staging/                   # Staging environment
│   │   └── kustomization.yaml
│   └── prod/                      # Production environment
│       ├── kustomization.yaml
│       └── deployment-patch.yaml  # Higher resources, anti-affinity
├── KUBECTL_COMMANDS.md            # Quick reference commands
├── NGINX_README.md                # NGINX deployment options
└── README.md                      # This file
```

## Architecture with NGINX

```
Internet
    │
    ▼
Ingress Controller (TLS)
    │
    ▼
NGINX Pods (2-5 replicas)
├─ Rate Limiting
├─ Caching
├─ Compression
└─ Load Balancing
    │
    ├──▶ Frontend Service (3000)
    └──▶ API Service (8000)
         └──▶ Databases (PostgreSQL, ChromaDB, Redis, MinIO)
```

## Quick Start

### 1. Prerequisites

- Kubernetes cluster (v1.24+)
- kubectl configured
- Docker images built and pushed to registry

### 2. Create Secrets

```bash
kubectl create namespace amaniquery

kubectl create secret generic amaniquery-secrets \
  --from-literal=POSTGRES_PASSWORD='your_password' \
  --from-literal=MOONSHOT_API_KEY='your_key' \
  --from-literal=OPENAI_API_KEY='your_key' \
  --from-literal=MINIO_ACCESS_KEY='admin' \
  --from-literal=MINIO_SECRET_KEY='your_secret' \
  --namespace amaniquery
```

### 3. Update Image References

Edit `base/kustomization.yaml`:

```yaml
images:
  - name: amaniquery-api
    newName: your-registry/amaniquery-api
    newTag: v1.0.0
  - name: amaniquery-frontend
    newName: your-registry/amaniquery-frontend
    newTag: v1.0.0
```

### 4. Deploy

```bash
# Development
kubectl apply -k overlays/dev

# Production
kubectl apply -k overlays/prod
```

### 5. Verify

```bash
kubectl get all -n amaniquery
kubectl get ingress -n amaniquery
```

## Components

### StatefulSets (Databases)
- **PostgreSQL**: User data, chat history
- **ChromaDB**: Vector database for embeddings
- **Redis**: Caching and rate limiting
- **MinIO**: Object storage for files

### Deployments (Applications)
- **NGINX**: Reverse proxy with rate limiting (2-5 replicas)
- **API**: FastAPI backend (2-10 replicas)
- **Frontend**: Next.js UI (2-5 replicas)

### Services
- ClusterIP for internal communication
- LoadBalancer for NGINX external access (or use Ingress)

### Ingress
- NGINX Ingress Controller
- TLS termination with cert-manager
- Path-based or subdomain routing

### Auto-scaling
- HPA for API and Frontend
- CPU and memory-based scaling

## Environment-Specific Configurations

| Environment | Replicas | Resources | Features |
|-------------|----------|-----------|----------|
| **Dev** | 1 | Low (512Mi/250m) | Scheduler off, reload on |
| **Staging** | 2 | Medium (1Gi/500m) | Production-like |
| **Prod** | 3-10 | High (2-8Gi/1-4CPU) | HA, anti-affinity |

## Storage

All stateful services use PersistentVolumeClaims:

- `postgres-pvc`: 10Gi
- `chromadb-pvc`: 20Gi
- `redis-pvc`: 5Gi
- `minio-pvc`: 50Gi
- `api-data-pvc`: 10Gi (shared)
- `api-logs-pvc`: 5Gi (shared)
- `models-cache-pvc`: 15Gi (shared)

Update `storageClassName` based on your cluster (gp2, standard-rwo, managed-premium).

## Security

### Secrets Management
- Never commit real secrets to git
- Use `kubectl create secret` or external secret managers
- Consider: Sealed Secrets, External Secrets Operator, Vault

### Network Policies
- Add network policies to restrict pod-to-pod communication
- Example in `base/networkpolicy.yaml` (create if needed)

### RBAC
- Create service accounts with minimal permissions
- Limit access to namespaces and resources

## Monitoring

### Logs
```bash
kubectl logs -f deployment/api -n amaniquery
kubectl logs -f statefulset/postgres -n amaniquery
```

### Metrics
Install Prometheus and Grafana for metrics visualization.

### Alerts
Set up alerts for:
- Pod crashes
- High memory usage
- Database connection failures
- API latency

## Backup

### PostgreSQL
```bash
kubectl exec statefulset/postgres -n amaniquery -- pg_dump -U amaniquery amaniquery > backup.sql
```

### ChromaDB
```bash
kubectl cp amaniquery/chromadb-0:/chroma/chroma ./chromadb-backup
```

## Troubleshooting

See [KUBECTL_COMMANDS.md](./KUBECTL_COMMANDS.md) for common commands.

Common issues:
1. **Image pull errors**: Verify registry credentials
2. **PVC binding failures**: Check StorageClass availability
3. **Pod crashes**: Check logs and resource limits
4. **Ingress not working**: Verify ingress controller and DNS

## Documentation

Full deployment guide: [KUBERNETES_DEPLOYMENT.md](../docs/KUBERNETES_DEPLOYMENT.md)

## Support

- GitHub Issues: https://github.com/Benaah/amaniquery/issues
- Docs: See `docs/` directory
