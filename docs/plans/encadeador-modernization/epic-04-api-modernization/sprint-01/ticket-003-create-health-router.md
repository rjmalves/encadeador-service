# [API-003] Create Health Endpoints

> **Epic**: [Epic 04: API Modernization](../00-epic-overview.md)  
> **Sprint**: [Sprint 01](./00-sprint-overview.md)  
> **Points**: 2  
> **Priority**: P0  
> **Status**: ✅ Complete

## Context

### Background

Health endpoints enable container orchestrators (Docker, Kubernetes) to monitor service health. They also help load balancers route traffic only to healthy instances.

### Relation to Epic

Required for Docker health checks and container orchestration.

### Current State

No health endpoints exist.

## Specification

### File to Create

**Path**: `app/routers/health.py`

### Health Router Implementation

```python
"""Health check endpoints for container orchestration."""

from fastapi import APIRouter, Response, status
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/health",
    tags=["health"],
)


class HealthStatus(BaseModel):
    """
    Health check response.
    
    Example:
        >>> status = HealthStatus(
        ...     status="healthy",
        ...     version="2.0.0",
        ...     timestamp="2024-12-01T12:00:00Z"
        ... )
    """
    
    status: str = Field(
        ...,
        description="Health status: healthy, degraded, or unhealthy",
        examples=["healthy", "degraded", "unhealthy"]
    )
    version: Optional[str] = Field(
        None,
        description="Application version",
        examples=["2.0.0"]
    )
    timestamp: str = Field(
        ...,
        description="ISO 8601 timestamp",
        examples=["2024-12-01T12:00:00Z"]
    )
    details: Optional[dict] = Field(
        None,
        description="Additional health details"
    )


class LivenessStatus(BaseModel):
    """Simple liveness probe response."""
    
    alive: bool = Field(
        True,
        description="Whether the service is alive"
    )


class ReadinessStatus(BaseModel):
    """Readiness probe response with dependency checks."""
    
    ready: bool = Field(
        ...,
        description="Whether the service is ready to accept traffic"
    )
    checks: dict[str, bool] = Field(
        ...,
        description="Individual dependency check results",
        examples=[{"s3": True, "temp_dir": True}]
    )


def _get_version() -> str:
    """Get application version from pyproject.toml or environment."""
    import os
    return os.getenv("APP_VERSION", "2.0.0")


def _check_temp_dir() -> bool:
    """Check if temp directory is writable."""
    from pathlib import Path
    from app.internal.settings import Settings
    
    try:
        temp_path = Path(Settings.temp_dir)
        temp_path.mkdir(parents=True, exist_ok=True)
        test_file = temp_path / ".health_check"
        test_file.write_text("ok")
        test_file.unlink()
        return True
    except Exception as e:
        logger.warning(f"Temp directory check failed: {e}")
        return False


def _check_s3_connectivity() -> bool:
    """Check S3 connectivity (optional, non-blocking)."""
    from app.internal.settings import Settings
    
    # Skip S3 check if using filesystem mode
    if Settings.decomp_source == "FS" and Settings.newave_source == "FS":
        return True
    
    try:
        import boto3
        from botocore.exceptions import ClientError, NoCredentialsError
        
        client = boto3.client(
            "s3",
            region_name=Settings.aws_region,
            endpoint_url=Settings.s3_endpoint_url or None,
        )
        
        # Simple list buckets call to verify connectivity
        client.list_buckets()
        return True
    except (ClientError, NoCredentialsError) as e:
        logger.warning(f"S3 connectivity check failed: {e}")
        return False
    except Exception as e:
        logger.warning(f"S3 connectivity check error: {e}")
        return False


@router.get(
    "/",
    response_model=HealthStatus,
    summary="Health check",
    description="Returns overall service health status"
)
async def health() -> HealthStatus:
    """
    Main health check endpoint.
    
    Returns:
        HealthStatus with overall health information
    """
    return HealthStatus(
        status="healthy",
        version=_get_version(),
        timestamp=datetime.utcnow().isoformat() + "Z",
    )


@router.get(
    "/live",
    response_model=LivenessStatus,
    summary="Liveness probe",
    description="Returns whether the service process is alive"
)
async def liveness() -> LivenessStatus:
    """
    Kubernetes liveness probe.
    
    Used to determine if the container should be restarted.
    Always returns True if the process is running.
    
    Returns:
        LivenessStatus indicating the process is alive
    """
    return LivenessStatus(alive=True)


@router.get(
    "/ready",
    response_model=ReadinessStatus,
    summary="Readiness probe",
    description="Returns whether the service is ready to accept traffic"
)
async def readiness(response: Response) -> ReadinessStatus:
    """
    Kubernetes readiness probe.
    
    Checks dependencies before accepting traffic:
    - Temp directory is writable
    - S3 is accessible (if configured)
    
    Returns:
        ReadinessStatus with dependency check results
    """
    checks = {
        "temp_dir": _check_temp_dir(),
        "s3": _check_s3_connectivity(),
    }
    
    ready = all(checks.values())
    
    if not ready:
        response.status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    
    return ReadinessStatus(
        ready=ready,
        checks=checks,
    )
```

### Register Router

Update `app/app.py`:

```python
from app.routers import chain, health

app.include_router(chain.router)
app.include_router(health.router)  # Add this line
```

### Health Check Behavior

| Endpoint | Purpose | Response |
|----------|---------|----------|
| `GET /health` | General health | Always 200 if process running |
| `GET /health/live` | Liveness probe | Always 200 if process running |
| `GET /health/ready` | Readiness probe | 200 if dependencies OK, 503 otherwise |

### Docker Health Check Integration

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health/live || exit 1
```

## Acceptance Criteria

- [ ] `GET /health` returns overall health
- [ ] `GET /health/live` returns liveness (always 200)
- [ ] `GET /health/ready` checks dependencies
- [ ] Returns 503 if dependencies fail
- [ ] Router registered in app.py
- [ ] OpenAPI docs include health endpoints
- [ ] No external calls in liveness probe

## Implementation Guide

### Step 1: Create health router

Create `app/routers/health.py` with the implementation above.

### Step 2: Register router

Update `app/app.py` to include the health router.

### Step 3: Test endpoints manually

```bash
uv run uvicorn app.app:app --reload

# In another terminal:
curl http://localhost:8000/health
curl http://localhost:8000/health/live
curl http://localhost:8000/health/ready
```

### Step 4: Verify OpenAPI docs

Check `/docs` shows health endpoints.

## Files to Read Before Starting

- `app/app.py` - Main application
- `app/routers/chain.py` - Router pattern
- `app/internal/settings.py` - Settings class

## Testing Requirements

### Unit Tests

```python
# tests/unit/test_health.py
import pytest
from fastapi.testclient import TestClient
from app.app import app


@pytest.fixture
def client():
    return TestClient(app)


def test_health_returns_200(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "healthy"


def test_liveness_returns_200(client):
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["alive"] is True


def test_readiness_checks_dependencies(client):
    response = client.get("/health/ready")
    # May be 200 or 503 depending on environment
    assert "ready" in response.json()
    assert "checks" in response.json()
```

## Definition of Done

- [ ] Health router created
- [ ] Router registered in app.py
- [ ] All three endpoints working
- [ ] Readiness checks dependencies
- [ ] Unit tests passing
- [ ] OpenAPI docs correct
- [ ] Changes committed

## Blocked By

- None

## Blocks

- [DOCKER-001](../../epic-05-docker/sprint-01/ticket-001-create-dockerfile.md) - Health checks for container
