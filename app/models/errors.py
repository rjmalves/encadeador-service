"""Structured error response models for the API."""

from enum import Enum
from typing import Any

from pydantic import BaseModel, Field


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
        examples=["ARTIFACT_NOT_FOUND", "VALIDATION_ERROR", "CHAINING_ERROR"],
    )
    message: str = Field(
        ...,
        description="Human-readable error message",
        examples=["Artifact not found in S3"],
    )
    details: dict[str, Any] | None = Field(
        None,
        description="Additional context about the error",
        examples=[{"bucket": "decomp-bucket", "key": "missing/file.zip"}],
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

    error: ErrorDetail = Field(..., description="Error details")
    request_id: str | None = Field(
        None,
        description="Request ID for tracing",
        examples=["req-abc123"],
    )

    model_config = {
        "json_schema_extra": {
            "examples": [
                {
                    "error": {
                        "error_code": "ARTIFACT_NOT_FOUND",
                        "message": "Artifact not found: s3://decomp-bucket/path/to/file",
                        "details": {"bucket": "decomp-bucket", "key": "path/to/file"},
                    },
                    "request_id": "req-abc123",
                },
                {
                    "error": {
                        "error_code": "VALIDATION_ERROR",
                        "message": "Invalid execution hash format",
                        "details": {
                            "field": "execution_hash",
                            "value": "invalid!@#",
                            "expected": "alphanumeric",
                        },
                    },
                    "request_id": "req-def456",
                },
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
        ..., description="Location of the error in the request"
    )
    msg: str = Field(..., description="Error message")
    type: str = Field(..., description="Error type")


class ValidationErrorResponse(BaseModel):
    """
    Response for request validation errors (422).

    Used when Pydantic validation fails.
    """

    error_code: str = Field(
        default="VALIDATION_ERROR", description="Error code for validation errors"
    )
    message: str = Field(
        default="Request validation failed", description="General error message"
    )
    details: list[ValidationErrorDetail] = Field(
        ..., description="List of validation errors"
    )
