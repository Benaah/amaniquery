# AmaniQuery Docker Makefile

.PHONY: help build up down restart logs clean dev prod

# Default target
help: ## Show this help message
	@echo "AmaniQuery Docker Commands:"
	@echo ""
	@grep -E '^[a-zA-Z_-]+:.*?## .*$$' $(MAKEFILE_LIST) | sort | awk 'BEGIN {FS = ":.*?## "}; {printf "  \033[36m%-15s\033[0m %s\n", $$1, $$2}'

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