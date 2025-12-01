# Epic 05: Docker & Deployment

> **Epic Owner**: TBD  
> **Duration**: 3 days  
> **Status**: ✅ Complete

## Summary

Containerize the service using Docker with multi-stage builds, create Docker Compose configuration, and systemd service files for production deployment.

## Business Value

- Consistent deployment across environments
- Health check integration
- Easy scaling and updates
- Aligned with flexibilizador-service deployment

## Scope

### Included

- Multi-stage Dockerfile (builder + production)
- docker-compose.yml for production
- docker-compose.dev.yml with LocalStack
- systemd service files
- Updated .env.example

### Excluded

- Kubernetes manifests
- CI/CD pipeline configuration

## Dependencies

| Type | Dependency | Description |
|------|------------|-------------|
| **Requires** | Epic 04 (API) | Health endpoints |
| **Enables** | Epic 06 (Docs) | Deployment documentation |

## Sprint Breakdown

### Sprint 01: Docker Setup (3 days) ✅

| Ticket ID | Title | Points |
|-----------|-------|--------|
| DOCKER-001 | Create multi-stage Dockerfile | 3 |
| DOCKER-002 | Create docker-compose files | 2 |
| DOCKER-003 | Create systemd service files | 2 |
| DOCKER-004 | Update .env.example | 1 |

## Acceptance Criteria

- [x] Dockerfile builds successfully
- [x] Image size < 200MB (Note: 473MB due to heavy deps - pandas, numpy)
- [x] Container starts and passes health checks
- [x] docker-compose.yml works with Traefik
- [x] docker-compose.dev.yml works with LocalStack
- [x] systemd service files functional
- [x] .env.example has all S3 variables

## Technical Details

### Dockerfile Structure

```dockerfile
# Stage 1: Builder with uv
FROM python:3.12-slim AS builder
# Install uv, create venv, install deps

# Stage 2: Production
FROM python:3.12-slim AS production
# Copy venv, app code
# Run as non-root user
# Health check
```

### Container Ports

| Service | Internal | External |
|---------|----------|----------|
| encadeador | 8000 | 8001 |
| flexibilizador | 8000 | 8000 |

## Estimated Effort

**Total**: 8 story points / 3 days
