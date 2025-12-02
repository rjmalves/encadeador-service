"""Tests for health endpoints."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.app import make_app


@pytest.fixture
def app():
    """Create test application."""
    return make_app()


@pytest.fixture
async def client(app):
    """Create async test client."""
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
    ) as client:
        yield client


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    @pytest.mark.asyncio
    async def test_health_returns_200(self, client):
        """Test main health endpoint returns 200."""
        response = await client.get("/health/")

        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert "timestamp" in data

    @pytest.mark.asyncio
    async def test_health_without_trailing_slash(self, client):
        """Test health endpoint works without trailing slash."""
        response = await client.get("/health")

        # FastAPI should redirect or handle
        assert response.status_code in [200, 307]

    @pytest.mark.asyncio
    async def test_liveness_returns_200(self, client):
        """Test liveness probe returns 200."""
        response = await client.get("/health/live")

        assert response.status_code == 200
        data = response.json()
        assert data["alive"] is True

    @pytest.mark.asyncio
    async def test_readiness_checks_dependencies(self, client):
        """Test readiness probe returns dependency checks."""
        response = await client.get("/health/ready")

        # May be 200 or 503 depending on environment
        data = response.json()
        assert "ready" in data
        assert "checks" in data
        assert "temp_dir" in data["checks"]
        assert "s3" in data["checks"]

    @pytest.mark.asyncio
    async def test_readiness_returns_503_when_deps_fail(self, client, monkeypatch):
        """Test readiness returns 503 when dependencies fail."""
        # Mock _check_temp_dir to return False
        from app.routers import health

        monkeypatch.setattr(health, "_check_temp_dir", lambda: False)

        response = await client.get("/health/ready")

        assert response.status_code == 503
        data = response.json()
        assert data["ready"] is False


class TestHealthModels:
    """Tests for health response models."""

    def test_health_status_model(self):
        """Test HealthStatus model."""
        from app.routers.health import HealthStatus

        status = HealthStatus(
            status="healthy",
            version="2.0.0",
            timestamp="2024-12-01T12:00:00Z",
        )

        assert status.status == "healthy"
        assert status.version == "2.0.0"
        assert status.timestamp == "2024-12-01T12:00:00Z"
        assert status.details is None

    def test_liveness_status_model(self):
        """Test LivenessStatus model."""
        from app.routers.health import LivenessStatus

        status = LivenessStatus(alive=True)
        assert status.alive is True

    def test_readiness_status_model(self):
        """Test ReadinessStatus model."""
        from app.routers.health import ReadinessStatus

        status = ReadinessStatus(
            ready=True,
            checks={"temp_dir": True, "s3": True},
        )

        assert status.ready is True
        assert status.checks["temp_dir"] is True
        assert status.checks["s3"] is True
