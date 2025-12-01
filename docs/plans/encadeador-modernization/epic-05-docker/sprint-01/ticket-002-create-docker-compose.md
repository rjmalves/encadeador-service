# [DOCKER-002] Create Docker Compose Files

> **Epic**: [Epic 05: Docker & Deployment](../00-epic-overview.md)  
> **Sprint**: [Sprint 01](./00-sprint-overview.md)  
> **Points**: 2  
> **Priority**: P0

## Context

### Background

Docker Compose files define multi-container applications. We need:
1. Production compose file with Traefik integration
2. Development compose file with LocalStack for S3 testing

### Relation to Epic

Enables local development with S3 mocking and production deployment.

### Current State

No Docker Compose files exist.

## Specification

### Production Compose File

**Path**: `docker-compose.yml`

```yaml
version: "3.9"

services:
  encadeador:
    image: encadeador-service:${APP_VERSION:-2.0.0}
    build:
      context: .
      dockerfile: Dockerfile
    container_name: encadeador-service
    restart: unless-stopped
    
    environment:
      # Application settings
      - PORT=8000
      - HOST=0.0.0.0
      - ROOT_PATH=/encadeador
      - LOG_LEVEL=${LOG_LEVEL:-INFO}
      - APP_VERSION=${APP_VERSION:-2.0.0}
      
      # S3 Configuration
      - AWS_REGION=${AWS_REGION:-us-east-1}
      - DEFAULT_DECOMP_BUCKET=${DEFAULT_DECOMP_BUCKET:-decomp-bucket}
      - DEFAULT_NEWAVE_BUCKET=${DEFAULT_NEWAVE_BUCKET:-newave-bucket}
      - DECOMP_SOURCE=S3
      - NEWAVE_SOURCE=S3
      
      # Processing
      - TEMP_DIR=/tmp/encadeador
      - MAX_TEMP_DIR_AGE_HOURS=24
    
    volumes:
      # Temp directory for processing (optional persistence)
      - encadeador-temp:/tmp/encadeador
    
    expose:
      - "8000"
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health/live"]
      interval: 30s
      timeout: 10s
      retries: 3
      start_period: 10s
    
    labels:
      # Traefik labels for reverse proxy
      - "traefik.enable=true"
      - "traefik.http.routers.encadeador.rule=PathPrefix(`/encadeador`)"
      - "traefik.http.routers.encadeador.entrypoints=web"
      - "traefik.http.services.encadeador.loadbalancer.server.port=8000"
      - "traefik.http.middlewares.encadeador-strip.stripprefix.prefixes=/encadeador"
      - "traefik.http.routers.encadeador.middlewares=encadeador-strip"
    
    networks:
      - hpc-network
    
    deploy:
      resources:
        limits:
          memory: 2G
          cpus: '2'
        reservations:
          memory: 512M
          cpus: '0.5'

volumes:
  encadeador-temp:

networks:
  hpc-network:
    external: true
```

### Development Compose File

**Path**: `docker-compose.dev.yml`

```yaml
version: "3.9"

services:
  encadeador:
    build:
      context: .
      dockerfile: Dockerfile.dev
    container_name: encadeador-dev
    
    environment:
      - PORT=8000
      - HOST=0.0.0.0
      - LOG_LEVEL=DEBUG
      - APP_VERSION=dev
      
      # S3 Configuration (LocalStack)
      - AWS_REGION=us-east-1
      - AWS_ACCESS_KEY_ID=test
      - AWS_SECRET_ACCESS_KEY=test
      - S3_ENDPOINT_URL=http://localstack:4566
      - DEFAULT_DECOMP_BUCKET=decomp-bucket
      - DEFAULT_NEWAVE_BUCKET=newave-bucket
      - DECOMP_SOURCE=S3
      - NEWAVE_SOURCE=S3
      
      # Processing
      - TEMP_DIR=/tmp/encadeador
    
    volumes:
      # Mount source for hot reload
      - ./app:/app/app:ro
      - ./main.py:/app/main.py:ro
      - encadeador-temp:/tmp/encadeador
    
    ports:
      - "8001:8000"  # Map to 8001 to avoid conflicts
    
    depends_on:
      localstack:
        condition: service_healthy
    
    networks:
      - dev-network

  localstack:
    image: localstack/localstack:3.0
    container_name: localstack
    
    environment:
      - SERVICES=s3
      - DEBUG=0
      - DATA_DIR=/var/lib/localstack/data
      - AWS_DEFAULT_REGION=us-east-1
    
    ports:
      - "4566:4566"
    
    volumes:
      - localstack-data:/var/lib/localstack
      - ./scripts/localstack-init.sh:/etc/localstack/init/ready.d/init.sh:ro
    
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:4566/_localstack/health"]
      interval: 10s
      timeout: 5s
      retries: 5
      start_period: 10s
    
    networks:
      - dev-network

volumes:
  encadeador-temp:
  localstack-data:

networks:
  dev-network:
    driver: bridge
```

### LocalStack Initialization Script

**Path**: `scripts/localstack-init.sh`

```bash
#!/bin/bash
# Initialize LocalStack S3 buckets for development

echo "Creating S3 buckets..."

awslocal s3 mb s3://decomp-bucket
awslocal s3 mb s3://newave-bucket

echo "S3 buckets created successfully!"

# Optional: Create test data
echo "Creating test artifacts..."

# Create a minimal test deck
mkdir -p /tmp/test-deck
echo "rv0" > /tmp/test-deck/caso.dat
echo "DECOMP test" > /tmp/test-deck/dadger.rv0

cd /tmp/test-deck
zip -r /tmp/deck_processado.zip .

awslocal s3 cp /tmp/deck_processado.zip s3://decomp-bucket/artifacts/test123/entradas/deck_processado.zip

echo "Test data created!"
```

### Combined Services Compose (Optional)

**Path**: `docker-compose.services.yml`

```yaml
# For running alongside flexibilizador-service
version: "3.9"

services:
  flexibilizador:
    image: flexibilizador-service:${FLEX_VERSION:-2.0.0}
    container_name: flexibilizador-service
    environment:
      - PORT=8000
      - S3_ENDPOINT_URL=${S3_ENDPOINT_URL:-}
      - AWS_REGION=${AWS_REGION:-us-east-1}
    expose:
      - "8000"
    networks:
      - hpc-network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.flexibilizador.rule=PathPrefix(`/flexibilizador`)"
      - "traefik.http.services.flexibilizador.loadbalancer.server.port=8000"

  encadeador:
    image: encadeador-service:${ENC_VERSION:-2.0.0}
    container_name: encadeador-service
    environment:
      - PORT=8000
      - S3_ENDPOINT_URL=${S3_ENDPOINT_URL:-}
      - AWS_REGION=${AWS_REGION:-us-east-1}
    expose:
      - "8000"
    networks:
      - hpc-network
    labels:
      - "traefik.enable=true"
      - "traefik.http.routers.encadeador.rule=PathPrefix(`/encadeador`)"
      - "traefik.http.services.encadeador.loadbalancer.server.port=8000"

networks:
  hpc-network:
    external: true
```

## Acceptance Criteria

- [x] `docker-compose.yml` created for production
- [x] `docker-compose.dev.yml` created with LocalStack
- [x] LocalStack initialization script created
- [x] Health checks configured in compose files
- [x] Traefik labels for routing
- [x] Volume mounts for persistence
- [x] Resource limits defined
- [x] Development mode has hot reload

## Implementation Guide

### Step 1: Create docker-compose.yml

Create production compose file in repository root.

### Step 2: Create docker-compose.dev.yml

Create development compose file with LocalStack.

### Step 3: Create scripts directory

```bash
mkdir -p scripts
chmod +x scripts/localstack-init.sh
```

### Step 4: Test development setup

```bash
docker compose -f docker-compose.dev.yml up --build

# Wait for healthy, then test:
curl http://localhost:8001/health
curl http://localhost:4566/_localstack/health
```

### Step 5: Test S3 connectivity

```bash
# Check LocalStack buckets
aws --endpoint-url=http://localhost:4566 s3 ls

# Should show:
# decomp-bucket
# newave-bucket
```

### Step 6: Test production setup

```bash
# Create network first
docker network create hpc-network

docker compose up --build
```

## Files to Read Before Starting

- `Dockerfile` - Container definition
- `/home/rogerio/git/flexibilizador-service/docker-compose.yml` - Reference
- LocalStack documentation

## Testing Requirements

### Development Setup

- [ ] LocalStack starts and is healthy
- [ ] Buckets created by init script
- [ ] Encadeador connects to LocalStack S3
- [ ] Hot reload works (change code, see effect)

### Production Setup

- [x] Container starts with production settings
- [x] Health check passes
- [x] Traefik labels work (if Traefik running)

## Definition of Done

- [x] docker-compose.yml created
- [x] docker-compose.dev.yml created
- [x] LocalStack init script created
- [x] Both setups tested
- [x] README updated with usage instructions
- [x] Changes committed

## Blocked By

- [DOCKER-001](./ticket-001-create-dockerfile.md) - Dockerfile

## Blocks

- [DOCKER-003](./ticket-003-create-systemd-service.md) - systemd service
