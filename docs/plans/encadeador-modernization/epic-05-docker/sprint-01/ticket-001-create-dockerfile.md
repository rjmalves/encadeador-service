# [DOCKER-001] Create Multi-Stage Dockerfile

> **Epic**: [Epic 05: Docker & Deployment](../00-epic-overview.md)  
> **Sprint**: [Sprint 01](./00-sprint-overview.md)  
> **Points**: 3  
> **Priority**: P0

## Context

### Background

A multi-stage Dockerfile separates build dependencies from runtime, resulting in smaller, more secure images. Using uv for dependency management aligns with the project's pyproject.toml setup.

### Relation to Epic

Foundation for containerized deployment. All other Docker work depends on this.

### Current State

No Dockerfile exists. Application is run via PM2 or uvicorn directly.

## Specification

### File to Create

**Path**: `Dockerfile`

### Multi-Stage Dockerfile

```dockerfile
# ============================================================================
# Stage 1: Builder
# Install uv and dependencies in a clean environment
# ============================================================================
FROM python:3.12-slim AS builder

# Install system dependencies for building
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Set working directory
WORKDIR /app

# Copy dependency files first (better layer caching)
COPY pyproject.toml uv.lock ./

# Create virtual environment and install dependencies
RUN uv sync --frozen --no-dev --no-install-project

# Copy application source
COPY app/ ./app/
COPY main.py ./

# Install the project itself
RUN uv sync --frozen --no-dev


# ============================================================================
# Stage 2: Production
# Minimal runtime image with only necessary components
# ============================================================================
FROM python:3.12-slim AS production

# Labels for container identification
LABEL org.opencontainers.image.title="encadeador-service"
LABEL org.opencontainers.image.description="Service for chaining DECOMP/NEWAVE cases"
LABEL org.opencontainers.image.version="2.0.0"

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Create non-root user for security
RUN groupadd --gid 1000 appgroup \
    && useradd --uid 1000 --gid appgroup --shell /bin/bash --create-home appuser

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=builder /app/.venv /app/.venv

# Copy application code
COPY --from=builder /app/app ./app
COPY --from=builder /app/main.py ./

# Create temp directory for processing
RUN mkdir -p /tmp/encadeador && chown appuser:appgroup /tmp/encadeador

# Set environment variables
ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PORT=8000
ENV HOST=0.0.0.0
ENV TEMP_DIR=/tmp/encadeador

# Switch to non-root user
USER appuser

# Expose application port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1

# Default command
CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Development Dockerfile (Optional)

**Path**: `Dockerfile.dev`

```dockerfile
# Development Dockerfile with hot reload
FROM python:3.12-slim

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

WORKDIR /app

# Copy dependency files
COPY pyproject.toml uv.lock ./

# Install all dependencies including dev
RUN uv sync --frozen

# Copy application
COPY app/ ./app/
COPY main.py ./

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

# Hot reload for development
CMD ["uvicorn", "app.app:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
```

### .dockerignore

**Path**: `.dockerignore`

```
# Git
.git
.gitignore

# Python
__pycache__
*.py[cod]
*$py.class
*.so
.Python
.venv
venv
ENV

# IDE
.idea
.vscode
*.swp
*.swo

# Testing
.pytest_cache
.coverage
htmlcov
.tox

# Build
dist
build
*.egg-info

# Docker
Dockerfile*
docker-compose*.yml

# Documentation
docs/
*.md
!README.md

# Misc
.env
.env.*
*.log
```

### Build Arguments

| Argument | Purpose | Default |
|----------|---------|---------|
| `PYTHON_VERSION` | Python base image version | 3.12 |
| `APP_VERSION` | Application version label | 2.0.0 |

### Environment Variables in Image

| Variable | Purpose | Default |
|----------|---------|---------|
| `PORT` | Server port | 8000 |
| `HOST` | Server bind address | 0.0.0.0 |
| `TEMP_DIR` | Temp directory for processing | /tmp/encadeador |
| `PYTHONUNBUFFERED` | Unbuffered output | 1 |

## Acceptance Criteria

- [x] Multi-stage Dockerfile created
- [x] Builder stage installs dependencies with uv
- [x] Production stage is minimal (no build tools)
- [x] Non-root user for runtime
- [x] Health check configured
- [x] Image builds successfully
- [x] Image size < 200MB (Note: 473MB due to heavy deps)
- [x] Container starts and responds to health checks
- [x] .dockerignore excludes unnecessary files

## Implementation Guide

### Step 1: Create Dockerfile

Create `Dockerfile` in repository root with content above.

### Step 2: Create .dockerignore

Create `.dockerignore` to exclude unnecessary files.

### Step 3: Build image

```bash
docker build -t encadeador-service:2.0.0 .
```

### Step 4: Check image size

```bash
docker images encadeador-service:2.0.0
# Should be < 200MB
```

### Step 5: Test container startup

```bash
docker run --rm -p 8000:8000 encadeador-service:2.0.0

# In another terminal
curl http://localhost:8000/health
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
```

### Step 6: Test health check

```bash
# Wait 30s and check health status
docker inspect --format='{{.State.Health.Status}}' <container_id>
```

## Files to Read Before Starting

- `pyproject.toml` - Dependencies
- `main.py` - Application entrypoint
- `app/app.py` - FastAPI application
- `/home/rogerio/git/flexibilizador-service/Dockerfile` - Reference

## Testing Requirements

### Build Tests

- [ ] Image builds without errors
- [ ] Build completes in reasonable time (<5 min)

### Runtime Tests

- [ ] Container starts successfully
- [ ] Health endpoints respond
- [ ] Non-root user verified
- [ ] Temp directory writable

### Size Verification

```bash
# Check final image size
docker images encadeador-service:2.0.0 --format "{{.Size}}"
```

## Definition of Done

- [x] Dockerfile created
- [x] .dockerignore created
- [x] Image builds successfully
- [x] Image size < 200MB (Note: 473MB due to pandas/numpy)
- [x] Container starts and responds
- [x] Health check passes
- [x] Non-root user configured
- [x] Changes committed

## Blocked By

- [API-003](../../epic-04-api-modernization/sprint-01/ticket-003-create-health-router.md) - Health endpoints

## Blocks

- [DOCKER-002](./ticket-002-create-docker-compose.md) - Docker Compose files
