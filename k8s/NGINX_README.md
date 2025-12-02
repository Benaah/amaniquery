# NGINX Deployment Options for Kubernetes

## Two Deployment Patterns

### Option 1: NGINX as Reverse Proxy Pod (Recommended)

**Architecture:**
```
Internet → Ingress Controller → NGINX Pod → API/Frontend Services
```

**Benefits:**
- Full control over NGINX configuration
- Advanced rate limiting with multiple zones
- Custom caching strategies
- WebSocket and streaming optimization
- Consistent with Docker Compose setup

**Use:** `ingress-options.yaml` with `amaniquery-ingress-nginx`

**Deploy:**
```bash
kubectl apply -k k8s/base/
```

### Option 2: Direct Ingress to Services (Simpler)

**Architecture:**
```
Internet → Ingress Controller → API/Frontend Services
```

**Benefits:**
- Simpler architecture
- One less hop (slightly lower latency)
- Native Kubernetes ingress features
- Easier to debug

**Use:** `ingress-options.yaml` with `amaniquery-ingress-direct`

**Deploy:**
```bash
# Delete nginx deployment
kubectl delete deployment nginx -n amaniquery
kubectl delete service nginx-service -n amaniquery

# Use direct ingress
kubectl apply -f k8s/base/ingress-options.yaml
```

## NGINX Configuration Highlights

### Rate Limiting Zones

| Zone | Rate | Burst | Purpose |
|------|------|-------|---------|
| `general` | 100 req/s | 20 | Frontend pages |
| `api` | 10 req/s | 10 | Standard API calls |
| `research` | 2 req/s | 3 | Agentic research (slow) |
| `stream` | 5 req/s | 5 | WebSocket/streaming |

### Timeout Configuration

| Endpoint Pattern | Timeout | Reason |
|-----------------|---------|--------|
| `/api/*` | 60s | Standard queries |
| `/api/research/*` | 300s | Agentic operations |
| `/api/stream/*` | 300s | Streaming responses |
| `/ws/*` | 7 days | WebSocket connections |
| `/api/chat/*/messages` | 300s | Chat streaming |

### Special Features

- **Gzip compression** for text/JSON (6x compression)
- **Static file caching** (1 year for assets)
- **CORS headers** for API routes
- **Security headers** (XSS, frame options, CSP)
- **Client body size** up to 100MB
- **Connection keepalive** for performance

## Switching Between Options

### To Use NGINX Pod (Default)

```bash
# Ensure nginx deployment exists
kubectl get deployment nginx -n amaniquery

# Apply ingress that routes to nginx
kubectl apply -f - <<EOF
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: amaniquery-ingress
  namespace: amaniquery
spec:
  rules:
  - host: amaniquery.example.com
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: nginx-service
            port:
              number: 80
EOF
```

### To Use Direct Routing

```bash
# Scale down or delete nginx
kubectl scale deployment nginx --replicas=0 -n amaniquery

# Apply direct ingress
kubectl apply -f k8s/base/ingress-options.yaml
```

## Monitoring NGINX

```bash
# View nginx logs
kubectl logs -f deployment/nginx -n amaniquery

# Check nginx config
kubectl exec deployment/nginx -n amaniquery -- nginx -t

# Reload nginx config (after ConfigMap update)
kubectl rollout restart deployment/nginx -n amaniquery

# Check rate limiting
kubectl logs deployment/nginx -n amaniquery | grep "limiting requests"
```

## Updating NGINX Configuration

```bash
# Edit ConfigMap
kubectl edit configmap nginx-config -n amaniquery

# Or update from file
kubectl create configmap nginx-config \
  --from-file=nginx.conf=nginx/nginx.conf \
  --namespace amaniquery \
  --dry-run=client -o yaml | kubectl apply -f -

# Reload nginx
kubectl rollout restart deployment/nginx -n amaniquery
```

## Performance Tuning

### Worker Connections
Default: 1024 connections per worker

Increase for high traffic:
```nginx
events {
    worker_connections 4096;
}
```

### Upstream Keepalive
Default: 32 connections

Increase for high throughput:
```nginx
upstream api {
    server api-service:8000;
    keepalive 64;
}
```

### Buffer Sizes
Adjust for large requests:
```nginx
client_body_buffer_size 256k;
large_client_header_buffers 8 64k;
```

## Troubleshooting

### 502 Bad Gateway
```bash
# Check backend services
kubectl get pods -n amaniquery
kubectl logs deployment/api -n amaniquery

# Check nginx upstream health
kubectl exec deployment/nginx -n amaniquery -- curl -f http://api-service:8000/health
```

### Rate Limiting Too Strict
```bash
# Check logs for limiting messages
kubectl logs deployment/nginx -n amaniquery | grep "limiting"

# Temporarily increase limits in ConfigMap
# Edit: limit_req_zone $binary_remote_addr zone=api:10m rate=50r/s;
```

### WebSocket Connections Failing
```bash
# Verify WebSocket headers
kubectl logs deployment/nginx -n amaniquery | grep "Upgrade"

# Test WebSocket connection
kubectl port-forward deployment/nginx 8080:80 -n amaniquery
wscat -c ws://localhost:8080/ws/test
```

## Recommendation

**Use Option 1 (NGINX Pod)** if you need:
- Fine-grained rate limiting
- Custom caching strategies  
- Advanced request routing
- WebSocket optimization
- Consistent with local dev environment

**Use Option 2 (Direct Ingress)** if you prefer:
- Simpler architecture
- Native Kubernetes features
- Easier troubleshooting
- Slightly lower latency
