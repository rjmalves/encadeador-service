"""Unit tests for exception handlers."""

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.internal.exception_handlers import register_exception_handlers
from app.internal.exceptions import (
    ArtifactNotFoundError,
    ChainingError,
    EncadeadorException,
    ParseError,
    S3OperationError,
    ValidationError,
)


@pytest.fixture
def app():
    """Create a test app with exception handlers."""
    app = FastAPI()
    register_exception_handlers(app)

    @app.get("/test/encadeador-exception")
    def raise_encadeador_exception():
        raise EncadeadorException("Test error", {"key": "value"})

    @app.get("/test/artifact-not-found")
    def raise_artifact_not_found():
        raise ArtifactNotFoundError(
            "Object not found",
            {"bucket": "test-bucket", "key": "path/to/file"},
        )

    @app.get("/test/s3-error")
    def raise_s3_error():
        raise S3OperationError("Upload failed", {"bucket": "test", "key": "file"})

    @app.get("/test/parse-error")
    def raise_parse_error():
        raise ParseError("Invalid file format", {"file": "dadger.rv0"})

    @app.get("/test/chaining-error")
    def raise_chaining_error():
        raise ChainingError("Chaining failed", {"variable": "VARM"})

    @app.get("/test/validation-error")
    def raise_validation_error():
        raise ValidationError("Invalid hash", {"hash": "invalid!"})

    @app.get("/test/generic-exception")
    def raise_generic_exception():
        raise RuntimeError("Something went wrong")

    return app


@pytest.fixture
def client(app):
    """Create test client."""
    return TestClient(app, raise_server_exceptions=False)


class TestEncadeadorExceptionHandler:
    """Tests for EncadeadorException handler."""

    def test_returns_correct_status_code(self, client):
        """Test that base exception returns 500."""
        response = client.get("/test/encadeador-exception")
        assert response.status_code == 500

    def test_returns_structured_response(self, client):
        """Test response structure."""
        response = client.get("/test/encadeador-exception")
        data = response.json()

        assert "error" in data
        assert "error_code" in data["error"]
        assert "message" in data["error"]
        assert "request_id" in data

    def test_includes_details_when_present(self, client):
        """Test that details are included in response."""
        response = client.get("/test/encadeador-exception")
        data = response.json()

        assert data["error"]["details"] == {"key": "value"}


class TestArtifactNotFoundHandler:
    """Tests for ArtifactNotFoundError handler."""

    def test_returns_404(self, client):
        """Test that artifact not found returns 404."""
        response = client.get("/test/artifact-not-found")
        assert response.status_code == 404

    def test_returns_correct_error_code(self, client):
        """Test error code."""
        response = client.get("/test/artifact-not-found")
        data = response.json()
        assert data["error"]["error_code"] == "ARTIFACT_NOT_FOUND"

    def test_includes_bucket_and_key_in_details(self, client):
        """Test that bucket and key are in details."""
        response = client.get("/test/artifact-not-found")
        data = response.json()

        assert data["error"]["details"]["bucket"] == "test-bucket"
        assert data["error"]["details"]["key"] == "path/to/file"


class TestS3OperationErrorHandler:
    """Tests for S3OperationError handler."""

    def test_returns_500(self, client):
        """Test that S3 error returns 500."""
        response = client.get("/test/s3-error")
        assert response.status_code == 500

    def test_returns_correct_error_code(self, client):
        """Test error code."""
        response = client.get("/test/s3-error")
        data = response.json()
        assert data["error"]["error_code"] == "S3_ERROR"


class TestParseErrorHandler:
    """Tests for ParseError handler."""

    def test_returns_422(self, client):
        """Test that parse error returns 422."""
        response = client.get("/test/parse-error")
        assert response.status_code == 422

    def test_returns_correct_error_code(self, client):
        """Test error code."""
        response = client.get("/test/parse-error")
        data = response.json()
        assert data["error"]["error_code"] == "PARSE_ERROR"


class TestChainingErrorHandler:
    """Tests for ChainingError handler."""

    def test_returns_500(self, client):
        """Test that chaining error returns 500."""
        response = client.get("/test/chaining-error")
        assert response.status_code == 500

    def test_returns_correct_error_code(self, client):
        """Test error code."""
        response = client.get("/test/chaining-error")
        data = response.json()
        assert data["error"]["error_code"] == "CHAINING_ERROR"


class TestValidationErrorHandler:
    """Tests for ValidationError handler."""

    def test_returns_400(self, client):
        """Test that validation error returns 400."""
        response = client.get("/test/validation-error")
        assert response.status_code == 400

    def test_returns_correct_error_code(self, client):
        """Test error code."""
        response = client.get("/test/validation-error")
        data = response.json()
        assert data["error"]["error_code"] == "INVALID_REQUEST"


class TestGenericExceptionHandler:
    """Tests for generic exception handler."""

    def test_returns_500(self, client):
        """Test that generic exception returns 500."""
        response = client.get("/test/generic-exception")
        assert response.status_code == 500

    def test_returns_generic_error_code(self, client):
        """Test error code is INTERNAL_ERROR."""
        response = client.get("/test/generic-exception")
        data = response.json()
        assert data["error"]["error_code"] == "INTERNAL_ERROR"

    def test_does_not_leak_stack_trace(self, client):
        """Test that no stack trace is in response."""
        response = client.get("/test/generic-exception")
        data = response.json()

        # Should not contain "RuntimeError" or traceback info
        response_str = str(data)
        assert "traceback" not in response_str.lower()
        assert "RuntimeError" not in response_str

    def test_has_generic_message(self, client):
        """Test that message is generic."""
        response = client.get("/test/generic-exception")
        data = response.json()
        assert data["error"]["message"] == "An unexpected error occurred"


class TestRequestIdGeneration:
    """Tests for request ID in responses."""

    def test_all_errors_have_request_id(self, client):
        """Test that all error responses include request_id."""
        endpoints = [
            "/test/encadeador-exception",
            "/test/artifact-not-found",
            "/test/s3-error",
            "/test/parse-error",
            "/test/chaining-error",
            "/test/validation-error",
            "/test/generic-exception",
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            data = response.json()
            assert "request_id" in data, f"Missing request_id in {endpoint}"
            assert data["request_id"].startswith("req-"), (
                f"Invalid request_id format in {endpoint}"
            )

    def test_request_ids_are_unique(self, client):
        """Test that each request gets unique ID."""
        request_ids = set()

        for _ in range(5):
            response = client.get("/test/encadeador-exception")
            data = response.json()
            request_ids.add(data["request_id"])

        assert len(request_ids) == 5, "Request IDs should be unique"
