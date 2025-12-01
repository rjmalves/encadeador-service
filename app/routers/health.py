"""Health check endpoints for container orchestration."""

import logging
import os
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Response, status
from pydantic import BaseModel, Field

from app.internal.settings import Settings

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/health",
    tags=["Health"],
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
        examples=["healthy", "degraded", "unhealthy"],
    )
    version: str | None = Field(
        None,
        description="Application version",
        examples=["2.0.0"],
    )
    timestamp: str = Field(
        ...,
        description="ISO 8601 timestamp",
        examples=["2024-12-01T12:00:00Z"],
    )
    details: dict | None = Field(None, description="Additional health details")


class LivenessStatus(BaseModel):
    """Simple liveness probe response."""

    alive: bool = Field(True, description="Whether the service is alive")


class ReadinessStatus(BaseModel):
    """Readiness probe response with dependency checks."""

    ready: bool = Field(
        ..., description="Whether the service is ready to accept traffic"
    )
    checks: dict[str, bool] = Field(
        ...,
        description="Individual dependency check results",
        examples=[{"s3": True, "temp_dir": True}],
    )


def _get_version() -> str:
    """Get application version from environment or default."""
    return os.getenv("APP_VERSION", "2.0.0")


def _check_temp_dir() -> bool:
    """Check if temp directory is writable."""
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
    description="Returns overall service health status",
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
    description="Returns whether the service process is alive",
)
async def liveness() -> LivenessStatus:
    """
    Kubernetes/Docker liveness probe.

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
    description="Returns whether the service is ready to accept traffic",
)
async def readiness(response: Response) -> ReadinessStatus:
    """
    Kubernetes/Docker readiness probe.

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
