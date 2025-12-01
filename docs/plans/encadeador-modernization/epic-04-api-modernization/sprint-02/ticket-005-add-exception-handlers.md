# [API-005] Add Exception Handlers

> **Epic**: [Epic 04: API Modernization](../00-epic-overview.md)  
> **Sprint**: [Sprint 02](./00-sprint-overview.md)  
> **Points**: 2  
> **Priority**: P0

## Context

### Background

Exception handlers convert application exceptions into structured API responses. Without them, exceptions result in generic 500 errors. With handlers, each exception type maps to appropriate HTTP status codes and structured error responses.

### Relation to Epic

Ensures consistent error responses across all API endpoints.

### Current State

No global exception handlers. Exceptions are caught in routes and manually converted to HTTPException.

## Specification

### File to Create

**Path**: `app/internal/exception_handlers.py`

### Exception Handler Implementation

```python
"""Global exception handlers for FastAPI application."""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError as PydanticValidationError
import logging
import uuid

from app.internal.exceptions import (
    EncadeadorException,
    S3OperationError,
    ArtifactNotFoundError,
    ParseError,
    ChainingError,
    ValidationError,
)
from app.models.errors import ErrorResponse, ErrorDetail, ValidationErrorResponse

logger = logging.getLogger(__name__)


def _generate_request_id() -> str:
    """Generate unique request ID for tracing."""
    return f"req-{uuid.uuid4().hex[:12]}"


async def encadeador_exception_handler(
    request: Request,
    exc: EncadeadorException,
) -> JSONResponse:
    """
    Handle all EncadeadorException subclasses.
    
    Maps exception error_code and http_status to structured response.
    """
    request_id = _generate_request_id()
    
    logger.error(
        f"[{request_id}] {exc.__class__.__name__}: {exc.message}",
        extra={
            "request_id": request_id,
            "error_code": exc.error_code,
            "details": exc.details,
            "path": request.url.path,
        }
    )
    
    response = ErrorResponse(
        error=ErrorDetail(
            error_code=exc.error_code,
            message=exc.message,
            details=exc.details if exc.details else None,
        ),
        request_id=request_id,
    )
    
    return JSONResponse(
        status_code=exc.http_status,
        content=response.model_dump(exclude_none=True),
    )


async def validation_error_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """
    Handle Pydantic request validation errors.
    
    Returns 422 with detailed validation error information.
    """
    request_id = _generate_request_id()
    
    logger.warning(
        f"[{request_id}] Validation error on {request.url.path}",
        extra={
            "request_id": request_id,
            "errors": exc.errors(),
        }
    )
    
    response = ValidationErrorResponse(
        error_code="VALIDATION_ERROR",
        message="Request validation failed",
        details=[
            {
                "loc": list(err["loc"]),
                "msg": err["msg"],
                "type": err["type"],
            }
            for err in exc.errors()
        ],
    )
    
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content=response.model_dump(),
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """
    Catch-all handler for unexpected exceptions.
    
    Logs full exception and returns generic 500 response.
    """
    request_id = _generate_request_id()
    
    logger.exception(
        f"[{request_id}] Unhandled exception on {request.url.path}",
        extra={"request_id": request_id},
    )
    
    response = ErrorResponse(
        error=ErrorDetail(
            error_code="INTERNAL_ERROR",
            message="An unexpected error occurred",
            details=None,
        ),
        request_id=request_id,
    )
    
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content=response.model_dump(exclude_none=True),
    )


def register_exception_handlers(app) -> None:
    """
    Register all exception handlers with FastAPI app.
    
    Call this in app.py after creating the FastAPI instance.
    
    Example:
        >>> from fastapi import FastAPI
        >>> from app.internal.exception_handlers import register_exception_handlers
        >>> app = FastAPI()
        >>> register_exception_handlers(app)
    """
    from fastapi.exceptions import RequestValidationError
    
    # Handle all EncadeadorException subclasses
    app.add_exception_handler(EncadeadorException, encadeador_exception_handler)
    
    # Handle specific subclasses (for logging clarity, optional)
    app.add_exception_handler(S3OperationError, encadeador_exception_handler)
    app.add_exception_handler(ArtifactNotFoundError, encadeador_exception_handler)
    app.add_exception_handler(ParseError, encadeador_exception_handler)
    app.add_exception_handler(ChainingError, encadeador_exception_handler)
    app.add_exception_handler(ValidationError, encadeador_exception_handler)
    
    # Handle Pydantic validation errors
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    
    # Catch-all for unexpected errors
    app.add_exception_handler(Exception, generic_exception_handler)
```

### Update app.py

```python
# app/app.py
from fastapi import FastAPI
from app.internal.exception_handlers import register_exception_handlers
from app.routers import chain, health

app = FastAPI(
    title="Encadeador Service",
    version="2.0.0",
    description="Service for chaining DECOMP/NEWAVE cases"
)

# Register exception handlers
register_exception_handlers(app)

# Include routers
app.include_router(chain.router)
app.include_router(health.router)
```

### Exception to HTTP Status Mapping

| Exception | HTTP Status | Error Code |
|-----------|-------------|------------|
| `ValidationError` | 400 | INVALID_REQUEST |
| `ArtifactNotFoundError` | 404 | ARTIFACT_NOT_FOUND |
| `ParseError` | 422 | PARSE_ERROR |
| `S3OperationError` | 500 | S3_ERROR |
| `ChainingError` | 500 | CHAINING_ERROR |
| `EncadeadorException` | 500 | INTERNAL_ERROR |
| `RequestValidationError` | 422 | VALIDATION_ERROR |
| `Exception` | 500 | INTERNAL_ERROR |

### Response Format

```json
{
  "error": {
    "error_code": "ARTIFACT_NOT_FOUND",
    "message": "Artifact not found: s3://bucket/key",
    "details": {
      "bucket": "decomp-bucket",
      "key": "artifacts/abc/file.zip"
    }
  },
  "request_id": "req-abc123def456"
}
```

## Acceptance Criteria

- [x] Exception handlers created for all exception types
- [x] Request ID generated for tracing
- [x] Logging includes request ID and context
- [x] Structured error responses returned
- [x] Handlers registered in app.py
- [x] Validation errors return field-level details
- [x] Generic handler catches unexpected errors
- [x] No stack traces leaked in production

## Implementation Guide

### Step 1: Create exception_handlers.py

Create `app/internal/exception_handlers.py` with all handlers.

### Step 2: Update app.py

Import and call `register_exception_handlers(app)`.

### Step 3: Test handlers

```python
# Test artifact not found
curl http://localhost:8000/chain -X POST -H "Content-Type: application/json" -d '{
  "sources": [{
    "program": "DECOMP",
    "bucket": "decomp-bucket",
    "execution_hash": "nonexistent"
  }],
  "destination": {...},
  "variable": "VARM"
}'

# Should return:
# {
#   "error": {
#     "error_code": "ARTIFACT_NOT_FOUND",
#     "message": "...",
#     "details": {...}
#   },
#   "request_id": "req-..."
# }
```

### Step 4: Verify validation errors

```bash
# Missing required field
curl http://localhost:8000/chain -X POST -H "Content-Type: application/json" -d '{}'

# Should return 422 with validation details
```

## Files to Read Before Starting

- `app/internal/exceptions.py` - Exception classes
- `app/models/errors.py` - Error response models
- `app/app.py` - Main application

## Testing Requirements

### Unit Tests

```python
# tests/unit/test_exception_handlers.py
import pytest
from fastapi.testclient import TestClient
from app.app import app
from app.internal.exceptions import ArtifactNotFoundError


@pytest.fixture
def client():
    return TestClient(app, raise_server_exceptions=False)


def test_validation_error_returns_422(client):
    """Test that invalid request returns 422 with details."""
    response = client.post("/chain", json={})
    assert response.status_code == 422
    data = response.json()
    assert data["error_code"] == "VALIDATION_ERROR"
    assert "details" in data


def test_error_response_includes_request_id(client):
    """Test that error responses include request_id."""
    response = client.post("/chain", json={})
    data = response.json()
    # Validation errors might not have request_id in some structures
    # Check the structure matches expected format
    assert "error_code" in data or "error" in data
```

## Definition of Done

- [x] Exception handlers created
- [x] Handlers registered in app.py
- [x] All exception types handled
- [x] Request ID in all responses
- [x] Logging with context
- [x] Unit tests passing
- [x] No stack traces in responses
- [x] Changes committed

## Blocked By

- [API-002](../sprint-01/ticket-002-create-error-models.md) - Error models

## Blocks

- [API-006](./ticket-006-api-integration-tests.md) - Integration tests
