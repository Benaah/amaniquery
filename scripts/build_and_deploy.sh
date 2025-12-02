#!/bin/bash
# Build and Deploy Script for AmaniQuery
# Usage: ./build_and_deploy.sh [docker|k8s|hf] [environment]

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Configuration
REGISTRY="${DOCKER_REGISTRY:-your-registry}"
VERSION="${VERSION:-$(git describe --tags --always --dirty)}"
ENVIRONMENT="${2:-dev}"

echo -e "${GREEN}AmaniQuery Build and Deploy${NC}"
echo "=============================="
echo "Version: $VERSION"
echo "Environment: $ENVIRONMENT"
echo ""

# Function to build Docker images
build_images() {
    echo -e "${YELLOW}Building Docker images...${NC}"
    
    # Build API
    echo "Building API image..."
    docker build -t ${REGISTRY}/amaniquery-api:${VERSION} \
        -t ${REGISTRY}/amaniquery-api:latest \
        -f Dockerfile .
    
    # Build Frontend
    echo "Building Frontend image..."
    docker build -t ${REGISTRY}/amaniquery-frontend:${VERSION} \
        -t ${REGISTRY}/amaniquery-frontend:latest \
        -f frontend/Dockerfile ./frontend
    
    echo -e "${GREEN}✓ Images built successfully${NC}"
}

# Function to push images to registry
push_images() {
    echo -e "${YELLOW}Pushing images to registry...${NC}"
    
    docker push ${REGISTRY}/amaniquery-api:${VERSION}
    docker push ${REGISTRY}/amaniquery-api:latest
    docker push ${REGISTRY}/amaniquery-frontend:${VERSION}
    docker push ${REGISTRY}/amaniquery-frontend:latest
    
    echo -e "${GREEN}✓ Images pushed successfully${NC}"
}

# Function to deploy to Docker Compose
deploy_docker() {
    echo -e "${YELLOW}Deploying with Docker Compose...${NC}"
    
    docker-compose --profile full down
    docker-compose --profile full up -d
    
    echo -e "${GREEN}✓ Deployed to Docker Compose${NC}"
    echo "Frontend: http://localhost:3000"
    echo "API: http://localhost:8000"
    echo "API Docs: http://localhost:8000/docs"
}

# Function to deploy to Kubernetes
deploy_k8s() {
    echo -e "${YELLOW}Deploying to Kubernetes (${ENVIRONMENT})...${NC}"
    
    # Update image tags in kustomization
    cd k8s/overlays/${ENVIRONMENT}
    kustomize edit set image \
        amaniquery-api=${REGISTRY}/amaniquery-api:${VERSION} \
        amaniquery-frontend=${REGISTRY}/amaniquery-frontend:${VERSION}
    cd -
    
    # Apply to cluster
    kubectl apply -k k8s/overlays/${ENVIRONMENT}
    
    # Wait for rollout
    echo "Waiting for rollout to complete..."
    kubectl rollout status deployment/api -n amaniquery
    kubectl rollout status deployment/frontend -n amaniquery
    
    echo -e "${GREEN}✓ Deployed to Kubernetes${NC}"
    
    # Show status
    kubectl get pods -n amaniquery
    kubectl get ingress -n amaniquery
}

# Function to deploy to HuggingFace
deploy_hf() {
    echo -e "${YELLOW}Deploying to HuggingFace Spaces...${NC}"
    
    if [ -z "$HF_TOKEN" ]; then
        echo -e "${RED}Error: HF_TOKEN environment variable not set${NC}"
        exit 1
    fi
    
    python deploy_to_hf.py
    
    echo -e "${GREEN}✓ Deployed to HuggingFace Spaces${NC}"
}

# Main deployment logic
case "$1" in
    docker)
        build_images
        deploy_docker
        ;;
    k8s|kubernetes)
        build_images
        push_images
        deploy_k8s
        ;;
    hf|huggingface)
        deploy_hf
        ;;
    build)
        build_images
        push_images
        ;;
    *)
        echo "Usage: $0 {docker|k8s|hf|build} [environment]"
        echo ""
        echo "Commands:"
        echo "  docker       - Build and deploy to Docker Compose"
        echo "  k8s          - Build, push, and deploy to Kubernetes"
        echo "  hf           - Deploy to HuggingFace Spaces"
        echo "  build        - Build and push images only"
        echo ""
        echo "Environments (for k8s):"
        echo "  dev          - Development environment (default)"
        echo "  staging      - Staging environment"
        echo "  prod         - Production environment"
        echo ""
        echo "Environment Variables:"
        echo "  DOCKER_REGISTRY - Docker registry URL (default: your-registry)"
        echo "  VERSION         - Image version tag (default: git describe)"
        echo "  HF_TOKEN        - HuggingFace API token (required for hf)"
        exit 1
        ;;
esac

echo ""
echo -e "${GREEN}Deployment complete!${NC}"
