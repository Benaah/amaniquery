# Build and Deploy Script for AmaniQuery (PowerShell)
# Usage: .\build_and_deploy.ps1 [docker|k8s|hf] [environment]

param(
    [Parameter(Mandatory=$true)]
    [ValidateSet('docker', 'k8s', 'kubernetes', 'hf', 'huggingface', 'build')]
    [string]$Command,
    
    [Parameter(Mandatory=$false)]
    [ValidateSet('dev', 'staging', 'prod')]
    [string]$Environment = 'dev'
)

# Configuration
$REGISTRY = if ($env:DOCKER_REGISTRY) { $env:DOCKER_REGISTRY } else { "your-registry" }
$VERSION = if ($env:VERSION) { $env:VERSION } else { 
    try { git describe --tags --always --dirty } catch { "latest" }
}

Write-Host "AmaniQuery Build and Deploy" -ForegroundColor Green
Write-Host "==============================" -ForegroundColor Green
Write-Host "Version: $VERSION"
Write-Host "Environment: $Environment"
Write-Host ""

function Build-Images {
    Write-Host "Building Docker images..." -ForegroundColor Yellow
    
    # Build API
    Write-Host "Building API image..."
    docker build -t "${REGISTRY}/amaniquery-api:${VERSION}" `
        -t "${REGISTRY}/amaniquery-api:latest" `
        -f Dockerfile .
    
    # Build Frontend
    Write-Host "Building Frontend image..."
    docker build -t "${REGISTRY}/amaniquery-frontend:${VERSION}" `
        -t "${REGISTRY}/amaniquery-frontend:latest" `
        -f frontend/Dockerfile ./frontend
    
    Write-Host "✓ Images built successfully" -ForegroundColor Green
}

function Push-Images {
    Write-Host "Pushing images to registry..." -ForegroundColor Yellow
    
    docker push "${REGISTRY}/amaniquery-api:${VERSION}"
    docker push "${REGISTRY}/amaniquery-api:latest"
    docker push "${REGISTRY}/amaniquery-frontend:${VERSION}"
    docker push "${REGISTRY}/amaniquery-frontend:latest"
    
    Write-Host "✓ Images pushed successfully" -ForegroundColor Green
}

function Deploy-Docker {
    Write-Host "Deploying with Docker Compose..." -ForegroundColor Yellow
    
    docker-compose --profile full down
    docker-compose --profile full up -d
    
    Write-Host "✓ Deployed to Docker Compose" -ForegroundColor Green
    Write-Host "Frontend: http://localhost:3000"
    Write-Host "API: http://localhost:8000"
    Write-Host "API Docs: http://localhost:8000/docs"
}

function Deploy-K8s {
    Write-Host "Deploying to Kubernetes ($Environment)..." -ForegroundColor Yellow
    
    # Update image tags in kustomization
    Push-Location "k8s/overlays/$Environment"
    kustomize edit set image `
        "amaniquery-api=${REGISTRY}/amaniquery-api:${VERSION}" `
        "amaniquery-frontend=${REGISTRY}/amaniquery-frontend:${VERSION}"
    Pop-Location
    
    # Apply to cluster
    kubectl apply -k "k8s/overlays/$Environment"
    
    # Wait for rollout
    Write-Host "Waiting for rollout to complete..."
    kubectl rollout status deployment/api -n amaniquery
    kubectl rollout status deployment/frontend -n amaniquery
    
    Write-Host "✓ Deployed to Kubernetes" -ForegroundColor Green
    
    # Show status
    kubectl get pods -n amaniquery
    kubectl get ingress -n amaniquery
}

function Deploy-HF {
    Write-Host "Deploying to HuggingFace Spaces..." -ForegroundColor Yellow
    
    if (-not $env:HF_TOKEN) {
        Write-Host "Error: HF_TOKEN environment variable not set" -ForegroundColor Red
        exit 1
    }
    
    python deploy_to_hf.py
    
    Write-Host "✓ Deployed to HuggingFace Spaces" -ForegroundColor Green
}

# Main deployment logic
switch ($Command) {
    'docker' {
        Build-Images
        Deploy-Docker
    }
    { $_ -in 'k8s', 'kubernetes' } {
        Build-Images
        Push-Images
        Deploy-K8s
    }
    { $_ -in 'hf', 'huggingface' } {
        Deploy-HF
    }
    'build' {
        Build-Images
        Push-Images
    }
}

Write-Host ""
Write-Host "Deployment complete!" -ForegroundColor Green
