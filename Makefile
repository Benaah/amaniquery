# AmaniQuery Makefile - Docker & Kubernetes

.PHONY: help build up down restart logs clean dev prod k8s-help

# Default target
help: ## Show this help message
	@echo "AmaniQuery Commands:"
	@echo ""
	@echo "DOCKER COMMANDS:"
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | grep -v "k8s-" | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "KUBERNETES COMMANDS:"
	@grep -E '^k8s-[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[35m%-20s\033[0m %s\n", $$1, $$2}'
	@echo ""
	@echo "For detailed K8s help: make k8s-help"

# Development commands
build: ## Build all services
	docker-compose build

up: ## Start all services
	docker-compose up -d

dev: ## Start in development mode with logs
	docker-compose up

down: ## Stop all services
	docker-compose down

restart: ## Restart all services
	docker-compose restart

logs: ## Show logs from all services
	docker-compose logs -f

logs-api: ## Show API logs
	docker-compose logs -f api

logs-frontend: ## Show frontend logs
	docker-compose logs -f frontend

logs-db: ## Show database logs
	docker-compose logs -f chroma postgres

# Production commands
prod-build: ## Build for production
	docker-compose -f docker-compose.prod.yml build

prod-up: ## Start production services
	docker-compose -f docker-compose.prod.yml up -d

prod-down: ## Stop production services
	docker-compose -f docker-compose.prod.yml down

prod-logs: ## Show production logs
	docker-compose -f docker-compose.prod.yml logs -f

# Maintenance commands
clean: ## Remove all containers, volumes, and images
	docker-compose down -v --rmi all

clean-volumes: ## Remove all volumes (WARNING: This deletes data!)
	docker-compose down -v

clean-images: ## Remove all images
	docker-compose down --rmi all

# Utility commands
status: ## Show status of all services
	docker-compose ps

shell-api: ## Open shell in API container
	docker-compose exec api bash

shell-frontend: ## Open shell in frontend container
	docker-compose exec frontend sh

shell-db: ## Open shell in ChromaDB container
	docker-compose exec chroma bash

shell-postgres: ## Open shell in PostgreSQL container
	docker-compose exec postgres bash

# Database commands
db-backup: ## Backup PostgreSQL database
	docker-compose exec postgres pg_dump -U amaniquery amaniquery > backup_$(shell date +%Y%m%d_%H%M%S).sql

db-restore: ## Restore PostgreSQL database (usage: make db-restore FILE=backup.sql)
	docker-compose exec -T postgres psql -U amaniquery amaniquery < $(FILE)

# Testing commands
test-api: ## Run API tests
	docker-compose exec api python -m pytest

test-frontend: ## Run frontend tests
	docker-compose exec frontend npm test

# Update commands
update: ## Pull latest images and rebuild
	docker-compose pull
	docker-compose build --no-cache
	docker-compose up -d

# Quick setup for new developers
setup: ## Initial setup for new developers
	cp .env.example .env
	@echo "Please edit .env file with your API keys"
	@echo "Then run: make build && make up"

# ============================================================================
# KUBERNETES COMMANDS
# ============================================================================

k8s-help: ## Show detailed Kubernetes commands
	@echo "Kubernetes Deployment Commands:"
	@echo ""
	@echo "Quick Start:"
	@echo "  make k8s-dev          - Deploy to development environment"
	@echo "  make k8s-prod         - Deploy to production environment"
	@echo ""
	@echo "Build & Deploy:"
	@echo "  make k8s-build        - Build and push Docker images"
	@echo "  make k8s-deploy-dev   - Deploy dev with kubectl"
	@echo "  make k8s-deploy-prod  - Deploy prod with kubectl"
	@echo ""
	@echo "Management:"
	@echo "  make k8s-status       - Check deployment status"
	@echo "  make k8s-logs         - View pod logs"
	@echo "  make k8s-shell        - Open shell in API pod"
	@echo "  make k8s-delete       - Delete all resources"
	@echo ""
	@echo "Secrets:"
	@echo "  make k8s-secrets      - Create secrets from .env"
	@echo ""
	@echo "See k8s/KUBECTL_COMMANDS.md for more details"

# Development environment
k8s-dev: ## Deploy to Kubernetes development environment
	@echo "Deploying to development environment..."
	kubectl apply -k k8s/overlays/dev
	@echo "Waiting for pods to be ready..."
	kubectl wait --for=condition=ready pod -l app=amaniquery-api -n amaniquery --timeout=300s
	@echo "Development environment deployed!"
	@echo "Run 'make k8s-status' to check status"

# Production environment
k8s-prod: ## Deploy to Kubernetes production environment
	@echo "Deploying to production environment..."
	kubectl apply -k k8s/overlays/prod
	@echo "Waiting for pods to be ready..."
	kubectl wait --for=condition=ready pod -l app=amaniquery-api -n amaniquery --timeout=300s
	@echo "Production environment deployed!"
	@echo "Run 'make k8s-status' to check status"

# Build and push images
k8s-build: ## Build and push Docker images for Kubernetes
	@echo "Building Docker images..."
	docker build -t amaniquery-api:latest -f Dockerfile .
	docker build -t amaniquery-frontend:latest -f frontend/Dockerfile ./frontend
	docker build -t amaniquery-nginx:latest -f nginx/Dockerfile ./nginx
	@echo "Images built successfully!"
	@echo "Tag and push to your registry:"
	@echo "  docker tag amaniquery-api:latest YOUR_REGISTRY/amaniquery-api:latest"
	@echo "  docker push YOUR_REGISTRY/amaniquery-api:latest"

# Deploy with kubectl
k8s-deploy-dev: ## Deploy development environment with kubectl
	kubectl apply -k k8s/overlays/dev

k8s-deploy-prod: ## Deploy production environment with kubectl
	kubectl apply -k k8s/overlays/prod

# Status and monitoring
k8s-status: ## Check Kubernetes deployment status
	@echo "=== Namespace ==="
	kubectl get namespace amaniquery
	@echo ""
	@echo "=== Pods ==="
	kubectl get pods -n amaniquery -o wide
	@echo ""
	@echo "=== Services ==="
	kubectl get svc -n amaniquery
	@echo ""
	@echo "=== Ingress ==="
	kubectl get ingress -n amaniquery
	@echo ""
	@echo "=== PVCs ==="
	kubectl get pvc -n amaniquery

k8s-logs: ## View logs from API pods
	kubectl logs -n amaniquery -l app=amaniquery-api --tail=100 -f

k8s-logs-api: ## View API pod logs
	kubectl logs -n amaniquery -l app=amaniquery-api --tail=100 -f

k8s-logs-frontend: ## View frontend pod logs
	kubectl logs -n amaniquery -l app=amaniquery-frontend --tail=100 -f

k8s-logs-nginx: ## View NGINX pod logs
	kubectl logs -n amaniquery -l app=nginx --tail=100 -f

k8s-logs-all: ## View all pod logs
	kubectl logs -n amaniquery --all-containers=true --tail=50

# Shell access
k8s-shell: ## Open shell in API pod
	kubectl exec -it -n amaniquery $$(kubectl get pod -n amaniquery -l app=amaniquery-api -o jsonpath='{.items[0].metadata.name}') -- /bin/bash

k8s-shell-frontend: ## Open shell in frontend pod
	kubectl exec -it -n amaniquery $$(kubectl get pod -n amaniquery -l app=amaniquery-frontend -o jsonpath='{.items[0].metadata.name}') -- /bin/sh

k8s-shell-postgres: ## Open shell in PostgreSQL pod
	kubectl exec -it -n amaniquery postgres-0 -- /bin/bash

k8s-shell-nginx: ## Open shell in NGINX pod
	kubectl exec -it -n amaniquery $$(kubectl get pod -n amaniquery -l app=nginx -o jsonpath='{.items[0].metadata.name}') -- /bin/sh

# Database operations
k8s-db-connect: ## Connect to PostgreSQL database
	kubectl exec -it -n amaniquery postgres-0 -- psql -U amaniquery -d amaniquery

k8s-db-backup: ## Backup PostgreSQL database
	@echo "Creating database backup..."
	kubectl exec -n amaniquery postgres-0 -- pg_dump -U amaniquery amaniquery > backup_k8s_$$(date +%Y%m%d_%H%M%S).sql
	@echo "Backup created: backup_k8s_$$(date +%Y%m%d_%H%M%S).sql"

# Secrets management
k8s-secrets: ## Create secrets from .env file
	@echo "Creating Kubernetes secrets from .env..."
	@if [ ! -f .env ]; then echo "Error: .env file not found"; exit 1; fi
	kubectl create secret generic amaniquery-secrets \
		--from-env-file=.env \
		-n amaniquery \
		--dry-run=client -o yaml | kubectl apply -f -
	@echo "Secrets created successfully!"

k8s-secrets-delete: ## Delete secrets
	kubectl delete secret amaniquery-secrets -n amaniquery

# Port forwarding for local access
k8s-port-forward: ## Forward API port to localhost:8000
	@echo "Forwarding API to http://localhost:8000"
	kubectl port-forward -n amaniquery svc/api-service 8000:8000

k8s-port-forward-frontend: ## Forward frontend port to localhost:3000
	@echo "Forwarding Frontend to http://localhost:3000"
	kubectl port-forward -n amaniquery svc/frontend-service 3000:3000

k8s-port-forward-nginx: ## Forward NGINX port to localhost:8080
	@echo "Forwarding NGINX to http://localhost:8080"
	kubectl port-forward -n amaniquery svc/nginx-service 8080:80

# Cleanup
k8s-delete: ## Delete all Kubernetes resources
	@echo "WARNING: This will delete all resources in the amaniquery namespace!"
	@read -p "Are you sure? [y/N] " -n 1 -r; echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		kubectl delete -k k8s/overlays/dev; \
		echo "Resources deleted!"; \
	else \
		echo "Cancelled."; \
	fi

k8s-delete-prod: ## Delete production resources
	@echo "WARNING: This will delete all PRODUCTION resources!"
	@read -p "Are you sure? [y/N] " -n 1 -r; echo; \
	if [[ $$REPLY =~ ^[Yy]$$ ]]; then \
		kubectl delete -k k8s/overlays/prod; \
		echo "Production resources deleted!"; \
	else \
		echo "Cancelled."; \
	fi

k8s-restart: ## Restart all deployments
	kubectl rollout restart deployment -n amaniquery

k8s-restart-api: ## Restart API deployment
	kubectl rollout restart deployment api-deployment -n amaniquery

k8s-restart-frontend: ## Restart frontend deployment
	kubectl rollout restart deployment frontend-deployment -n amaniquery

k8s-restart-nginx: ## Restart NGINX deployment
	kubectl rollout restart deployment nginx-deployment -n amaniquery

# Scaling
k8s-scale-api: ## Scale API pods (usage: make k8s-scale-api REPLICAS=5)
	kubectl scale deployment api-deployment -n amaniquery --replicas=$(REPLICAS)

k8s-scale-frontend: ## Scale frontend pods (usage: make k8s-scale-frontend REPLICAS=3)
	kubectl scale deployment frontend-deployment -n amaniquery --replicas=$(REPLICAS)

# HPA status
k8s-hpa: ## Show HorizontalPodAutoscaler status
	kubectl get hpa -n amaniquery

# Describe resources
k8s-describe-api: ## Describe API deployment
	kubectl describe deployment api-deployment -n amaniquery

k8s-describe-pod: ## Describe first API pod
	kubectl describe pod -n amaniquery $$(kubectl get pod -n amaniquery -l app=amaniquery-api -o jsonpath='{.items[0].metadata.name}')

# Events
k8s-events: ## Show recent events
	kubectl get events -n amaniquery --sort-by='.lastTimestamp' | tail -20

# Resource usage
k8s-top: ## Show resource usage
	@echo "=== Node Usage ==="
	kubectl top nodes
	@echo ""
	@echo "=== Pod Usage ==="
	kubectl top pods -n amaniquery