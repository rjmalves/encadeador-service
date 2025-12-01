# [API-002] Create Structured Error Models

> **Epic**: [Epic 04: API Modernization](../00-epic-overview.md)  
> **Sprint**: [Sprint 01](./00-sprint-overview.md)  
> **Points**: 2  
> **Priority**: P0  
> **Status**: ✅ Complete

## Context

### Background

Structured error responses enable API consumers to programmatically handle errors. Instead of plain text messages, errors include machine-readable codes and structured details.

### Relation to Epic

Provides consistent error format across all API endpoints.

### Current State

Errors are raised as `HTTPException` with string `detail` messages. No consistent error codes or structure.

## Specification

### File to Create

**Path**: `app/models/errors.py`

### Error Response Models

```python
"""Structured error response models for the API."""

from pydantic import BaseModel, Field
from typing import Any, Optional


class ErrorDetail(BaseModel):
    """
    Detailed error information.
    
    Provides machine-readable error codes and structured context
    for API error responses.
    
    Example:
        >>> error = ErrorDetail(
        ...     error_code="ARTIFACT_NOT_FOUND",
        ...     message="Artifact not found in S3",
        ...     details={"bucket": "decomp-bucket", "key": "path/to/file"}
        ... )
    """
    
    error_code: str = Field(
        ...,
        description="Machine-readable error code",
        examples=["ARTIFACT_NOT_FOUND", "VALIDATION_ERROR", "CHAINING_ERROR"]
    )
    message: str = Field(
        ...,
        description="Human-readable error message",
        examples=["Artifact not found in S3"]
    )
    details: Optional[dict[str, Any]] = Field(
        None,
        description="Additional context about the error",
        examples=[{"bucket": "decomp-bucket", "key": "missing/file.zip"}]
    )


class ErrorResponse(BaseModel):
    """
    Standard API error response.
    
    Used for all 4xx and 5xx responses.
    
    Example:
        >>> response = ErrorResponse(
        ...     error=ErrorDetail(
        ...         error_code="ARTIFACT_NOT_FOUND",
        ...         message="Artifact not found"
        ...     ),
        ...     request_id="req-123"
        ... )
    """
    
    error: ErrorDetail = Field(
        ...,
        description="Error details"
    )
    request_id: Optional[str] = Field(
        None,
        description="Request ID for tracing",
        examples=["req-abc123"]
    )
    
    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "error": {
                        "error_code": "ARTIFACT_NOT_FOUND",
                        "message": "Artifact not found: s3://decomp-bucket/path/to/file",
                        "details": {
                            "bucket": "decomp-bucket",
                            "key": "path/to/file"
                        }
                    },
                    "request_id": "req-abc123"
                },
                {
                    "error": {
                        "error_code": "VALIDATION_ERROR",
                        "message": "Invalid execution hash format",
                        "details": {
                            "field": "execution_hash",
                            "value": "invalid!@#",
                            "expected": "alphanumeric"
                        }
                    },
                    "request_id": "req-def456"
                }
            ]
        }
    }


class ValidationErrorDetail(BaseModel):
    """
    Validation error detail for a specific field.
    
    Example:
        >>> detail = ValidationErrorDetail(
        ...     loc=["body", "destination", "execution_hash"],
        ...     msg="String should match pattern '^[a-zA-Z0-9_-]+$'",
        ...     type="string_pattern_mismatch"
        ... )
    """
    
    loc: list[str | int] = Field(
        ...,
        description="Location of the error in the request"
    )
    msg: str = Field(
        ...,
        description="Error message"
    )
    type: str = Field(
        ...,
        description="Error type"
    )


class ValidationErrorResponse(BaseModel):
    """
    Response for request validation errors (422).
    
    Used when Pydantic validation fails.
    """
    
    error_code: str = Field(
        default="VALIDATION_ERROR",
        description="Error code for validation errors"
    )
    message: str = Field(
        default="Request validation failed",
        description="General error message"
    )
    details: list[ValidationErrorDetail] = Field(
        ...,
        description="List of validation errors"
    )
```

### Error Codes Enum

```python
"""Enumeration of error codes for consistent API responses."""

from enum import Enum


class ErrorCode(str, Enum):
    """
    Machine-readable error codes.
    
    Use these codes in ErrorDetail.error_code for consistency.
    """
    
    # Validation errors (400)
    INVALID_REQUEST = "INVALID_REQUEST"
    INVALID_PROGRAM = "INVALID_PROGRAM"
    INVALID_VARIABLE = "INVALID_VARIABLE"
    
    # Not found errors (404)
    ARTIFACT_NOT_FOUND = "ARTIFACT_NOT_FOUND"
    CASE_NOT_FOUND = "CASE_NOT_FOUND"
    
    # Processing errors (422)
    PARSE_ERROR = "PARSE_ERROR"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    
    # Chaining errors (500)
    CHAINING_ERROR = "CHAINING_ERROR"
    
    # S3 errors (500)
    S3_ERROR = "S3_ERROR"
    S3_DOWNLOAD_ERROR = "S3_DOWNLOAD_ERROR"
    S3_UPLOAD_ERROR = "S3_UPLOAD_ERROR"
    
    # Generic errors (500)
    INTERNAL_ERROR = "INTERNAL_ERROR"
```

### Update Router Response Models

Update `app/routers/chain.py` responses:

```python
from app.models.errors import ErrorResponse

@router.post(
    "/",
    response_model=ChainingResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        404: {"model": ErrorResponse, "description": "Artifact not found"},
        422: {"model": ErrorResponse, "description": "Validation/Parse error"},
        500: {"model": ErrorResponse, "description": "Internal error"},
    }
)
async def chain(...):
    ...
```

## Acceptance Criteria

- [ ] `ErrorDetail` model created
- [ ] `ErrorResponse` model created
- [ ] `ValidationErrorResponse` model created
- [ ] `ErrorCode` enum created
- [ ] OpenAPI docs show error response schemas
- [ ] Examples in models for documentation
- [ ] Type hints on all fields

## Implementation Guide

### Step 1: Create errors.py

Create `app/models/errors.py` with all error models.

### Step 2: Update __init__.py

Export error models from `app/models/__init__.py`:

```python
from app.models.errors import ErrorDetail, ErrorResponse, ErrorCode
```

### Step 3: Add responses to router

Update router decorator with response models.

### Step 4: Verify OpenAPI docs

Check `/docs` shows error response schemas.

## Files to Read Before Starting

- `app/internal/exceptions.py` - Exception classes (align error codes)
- `app/routers/chain.py` - Router to update
- Pydantic docs on model_config

## Testing Requirements

### Unit Tests

- [ ] Test ErrorDetail serialization
- [ ] Test ErrorResponse with request_id
- [ ] Test ValidationErrorResponse structure

## Definition of Done

- [ ] Error models created
- [ ] ErrorCode enum created
- [ ] Models exported
- [ ] OpenAPI shows error schemas
- [ ] Changes committed

## Blocked By

- None

## Blocks

- [API-005](../sprint-02/ticket-005-add-exception-handlers.md) - Exception handlers use models
