"""Global exception handlers for FastAPI application."""

import logging
import uuid

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.internal.exceptions import EncadeadorException
from app.models.errors import ErrorDetail, ErrorResponse

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
        },
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
        },
    )

    # Build validation error details
    details = [
        {
            "loc": list(err["loc"]),
            "msg": err["msg"],
            "type": err["type"],
        }
        for err in exc.errors()
    ]

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error_code": "VALIDATION_ERROR",
            "message": "Request validation failed",
            "details": details,
            "request_id": request_id,
        },
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
    # Handle all EncadeadorException subclasses
    app.add_exception_handler(EncadeadorException, encadeador_exception_handler)

    # Handle Pydantic validation errors
    app.add_exception_handler(RequestValidationError, validation_error_handler)

    # Catch-all for unexpected errors
    app.add_exception_handler(Exception, generic_exception_handler)
