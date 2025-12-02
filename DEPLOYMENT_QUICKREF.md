# AmaniQuery Deployment Quick Reference

## 🚀 Choose Your Deployment

```
┌─────────────────────────────────────────────────────────────┐
│  I want to...                    │  Use...                   │
├──────────────────────────────────┼───────────────────────────┤
│  Test locally                    │  Docker Compose           │
│  Deploy a demo                   │  HuggingFace Spaces       │
│  Deploy to production (small)    │  Render                   │
│  Deploy to production (scale)    │  Kubernetes               │
└──────────────────────────────────┴───────────────────────────┘
```

## ⚡ Quick Commands

### Docker Compose (Local)
```bash
docker-compose --profile full up -d
# Access: http://localhost:3000
```

### Kubernetes (Production)
```bash
# Create secrets
kubectl create secret generic amaniquery-secrets \
  --from-literal=POSTGRES_PASSWORD=pwd \
  --namespace amaniquery

# Deploy
kubectl apply -k k8s/overlays/prod

# Check status
kubectl get all -n amaniquery
```

### HuggingFace Spaces (Demo)
```bash
export HF_TOKEN=your_token
python deploy_to_hf.py
```

### Using Build Scripts
```powershell
# Windows
.\build_and_deploy.ps1 k8s prod

# Linux/Mac
./build_and_deploy.sh k8s prod
```

## 📊 Comparison

| Metric | Docker Compose | Kubernetes | HuggingFace |
|--------|---------------|------------|-------------|
| Setup | 5 min | 1-2 hours | 10 min |
| Cost | $0-50/mo | $70-500/mo | $0-22/mo |
| Scaling | Manual | Auto | None |
| Persistence | Yes | Yes | No |

## 🔗 Documentation

- Full Guide: `docs/DEPLOYMENT_GUIDE.md`
- Kubernetes: `docs/KUBERNETES_DEPLOYMENT.md`
- HuggingFace: `docs/HUGGINGFACE_DEPLOYMENT.md`
- K8s Quick Ref: `k8s/KUBECTL_COMMANDS.md`

## 📞 Support

Issues: https://github.com/Benaah/amaniquery/issues
