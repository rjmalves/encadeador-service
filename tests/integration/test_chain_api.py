"""Integration tests for the chain API endpoint."""

import tempfile
import zipfile
from pathlib import Path

import boto3
import pytest
from fastapi.testclient import TestClient
from moto import mock_aws

from app.adapters.s3_repository import reset_s3_repository
from app.app import make_app


@pytest.fixture
def client():
    """Create test client."""
    # Reset S3 repository to ensure clean state
    reset_s3_repository()
    app = make_app(root_path="/")
    return TestClient(app, raise_server_exceptions=False)


@pytest.fixture
def temp_dir():
    """Create temporary directory."""
    with tempfile.TemporaryDirectory() as td:
        yield Path(td)


def create_mock_deck_zip(path: Path, program: str = "DECOMP") -> Path:
    """Create a mock deck zip file for testing."""
    zip_path = path / "deck_processado.zip"

    with zipfile.ZipFile(zip_path, "w") as zf:
        if program == "DECOMP":
            zf.writestr("caso.dat", "rv0\n")
            zf.writestr("dadger.rv0", "DECOMP test content\n")
            zf.writestr("dadgnl.rv0", "GNL test content\n")
        else:  # NEWAVE
            zf.writestr("caso.dat", "rv0\n")
            zf.writestr("dger.dat", "NEWAVE test content\n")

    return zip_path


def create_mock_outputs(bucket: str, execution_hash: str, s3_client):
    """Create mock output files in S3."""
    # Create caso.dat
    s3_client.put_object(
        Bucket=bucket,
        Key=f"artifacts/{execution_hash}/saidas/caso.dat",
        Body=b"rv0\n",
    )
    # Create relato file
    s3_client.put_object(
        Bucket=bucket,
        Key=f"artifacts/{execution_hash}/saidas/relato.rv0",
        Body=b"RELATO content for testing\n",
    )
    # Create relgnl file
    s3_client.put_object(
        Bucket=bucket,
        Key=f"artifacts/{execution_hash}/saidas/relgnl.rv0",
        Body=b"RELGNL content for testing\n",
    )


class TestChainAPIValidation:
    """Tests for request validation."""

    def test_missing_sources_returns_422(self, client):
        """Test that missing sources field returns 422."""
        response = client.post(
            "/chain/",
            json={
                "destination": {
                    "program": "DECOMP",
                    "bucket": "test",
                    "execution_hash": "abc",
                },
                "variable": "VARM",
            },
        )
        assert response.status_code == 422

    def test_missing_destination_returns_422(self, client):
        """Test that missing destination field returns 422."""
        response = client.post(
            "/chain/",
            json={
                "sources": [
                    {
                        "program": "DECOMP",
                        "bucket": "test",
                        "execution_hash": "abc",
                    }
                ],
                "variable": "VARM",
            },
        )
        assert response.status_code == 422

    def test_invalid_program_returns_422(self, client):
        """Test that invalid program returns 422."""
        response = client.post(
            "/chain/",
            json={
                "sources": [
                    {
                        "program": "INVALID",
                        "bucket": "test",
                        "execution_hash": "abc",
                    }
                ],
                "destination": {
                    "program": "DECOMP",
                    "bucket": "test",
                    "execution_hash": "def",
                },
                "variable": "VARM",
            },
        )
        assert response.status_code == 422

    def test_invalid_variable_returns_422(self, client):
        """Test that invalid variable returns 422."""
        response = client.post(
            "/chain/",
            json={
                "sources": [
                    {
                        "program": "DECOMP",
                        "bucket": "test",
                        "execution_hash": "abc",
                    }
                ],
                "destination": {
                    "program": "DECOMP",
                    "bucket": "test",
                    "execution_hash": "def",
                },
                "variable": "INVALID_VAR",
            },
        )
        assert response.status_code == 422

    def test_empty_sources_returns_422(self, client):
        """Test that empty sources list returns 422."""
        response = client.post(
            "/chain/",
            json={
                "sources": [],
                "destination": {
                    "program": "DECOMP",
                    "bucket": "test",
                    "execution_hash": "def",
                },
                "variable": "VARM",
            },
        )
        assert response.status_code == 422


class TestChainAPIErrors:
    """Tests for error responses."""

    @mock_aws
    def test_artifact_not_found_returns_404(self, client):
        """Test that missing S3 artifact returns 404."""
        # Setup: Create bucket but no artifacts
        s3 = boto3.client("s3", region_name="us-east-1")
        s3.create_bucket(Bucket="decomp-bucket")

        # Reset repository to pick up mocked S3
        reset_s3_repository()

        response = client.post(
            "/chain/",
            json={
                "sources": [
                    {
                        "program": "DECOMP",
                        "bucket": "decomp-bucket",
                        "execution_hash": "nonexistent",
                    }
                ],
                "destination": {
                    "program": "DECOMP",
                    "bucket": "decomp-bucket",
                    "execution_hash": "dest123",
                },
                "variable": "VARM",
            },
        )

        # Should return 404 for missing artifact
        assert response.status_code == 404
        data = response.json()
        assert "error" in data
        assert data["error"]["error_code"] == "ARTIFACT_NOT_FOUND"

    def test_error_response_includes_request_id(self, client):
        """Test that error responses include request_id."""
        response = client.post("/chain/", json={})
        data = response.json()

        # Validation errors should have request_id
        assert "request_id" in data


class TestChainAPILegacyMode:
    """Tests for legacy (base62 ID) mode."""

    def test_legacy_mode_request_accepted(self, client):
        """Test that legacy mode requests are accepted by validation."""
        # Legacy mode may fail due to filesystem access, but should pass validation
        response = client.post(
            "/chain/",
            json={
                "sources": [{"program": "DECOMP", "id": "2cA3xY"}],
                "destination": {"program": "DECOMP", "id": "4dB5zW"},
                "variable": "VARM",
            },
        )

        # Should not be validation error (422)
        # May be 404/500 due to missing filesystem paths
        assert response.status_code != 422


class TestHealthEndpoints:
    """Tests for health check endpoints."""

    def test_health_returns_200(self, client):
        """Test main health endpoint."""
        response = client.get("/health/")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"

    def test_liveness_returns_200(self, client):
        """Test liveness probe."""
        response = client.get("/health/live")
        assert response.status_code == 200
        assert response.json()["alive"] is True

    def test_readiness_checks_dependencies(self, client):
        """Test readiness probe includes checks."""
        response = client.get("/health/ready")
        # May be 200 or 503 depending on environment
        data = response.json()
        assert "ready" in data
        assert "checks" in data


class TestExceptionHandlers:
    """Tests for exception handlers."""

    def test_validation_error_format(self, client):
        """Test that validation errors have correct format."""
        response = client.post("/chain/", json={})
        assert response.status_code == 422

        data = response.json()
        assert "error_code" in data
        assert data["error_code"] == "VALIDATION_ERROR"
        assert "message" in data
        assert "details" in data
        assert "request_id" in data

    def test_validation_error_details_have_location(self, client):
        """Test that validation error details include field location."""
        response = client.post(
            "/chain/",
            json={
                "sources": [
                    {
                        "program": "DECOMP",
                        "bucket": "test",
                        "execution_hash": "abc",
                    }
                ],
                # Missing destination
                "variable": "VARM",
            },
        )
        assert response.status_code == 422

        data = response.json()
        assert len(data["details"]) > 0
        assert "loc" in data["details"][0]
        assert "msg" in data["details"][0]
