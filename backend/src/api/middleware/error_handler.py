"""
Error handler middleware for consistent JSON error responses.

Converts AppError exceptions to JSON with correlation ID,
catches unhandled exceptions with logging,
and never exposes internal details to clients.

Usage:
    # In main.py
    from src.api.middleware.error_handler import (
        app_error_handler,
        unhandled_error_handler,
    )
    from src.utils.exceptions import AppError

    app.add_exception_handler(AppError, app_error_handler)
    app.add_exception_handler(Exception, unhandled_error_handler)
"""

from typing import Optional

import structlog
from fastapi import Request
from fastapi.responses import JSONResponse

from src.utils.exceptions import AppError


logger = structlog.get_logger()


async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """
    Convert application errors to consistent JSON responses.

    All AppError subclasses (NotFoundError, ValidationError, etc.) are
    converted to a standard JSON format including the correlation ID
    for tracing.

    Response format:
    {
        "error": "ERROR_CODE",
        "message": "Human readable message",
        "details": { ... },
        "correlation_id": "uuid"
    }

    Args:
        request: The FastAPI request object.
        exc: The AppError exception that was raised.

    Returns:
        JSONResponse with appropriate status code and error details.
    """
    correlation_id = _get_correlation_id(request)

    # Log the error with context
    logger.warning(
        "application_error",
        error_code=exc.error_code,
        status_code=exc.status_code,
        message=exc.message,
        details=exc.details,
        path=request.url.path,
        method=request.method,
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "correlation_id": correlation_id,
        },
    )


async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all handler for unexpected errors.

    Logs the full exception with stack trace for debugging, but returns
    a generic error message to the client to avoid exposing internals.

    IMPORTANT: This handler should rarely be triggered. Unexpected exceptions
    indicate bugs that should be fixed. Monitor logs for these.

    Args:
        request: The FastAPI request object.
        exc: The unexpected exception.

    Returns:
        JSONResponse with 500 status and generic error message.
    """
    correlation_id = _get_correlation_id(request)

    # Log full exception with stack trace for debugging
    logger.exception(
        "unhandled_error",
        error_type=type(exc).__name__,
        error_message=str(exc),
        path=request.url.path,
        method=request.method,
        query_params=str(request.query_params),
    )

    # Return generic message - never expose internal details
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred. Please try again later.",
            "details": {},
            "correlation_id": correlation_id,
        },
    )


def _get_correlation_id(request: Request) -> Optional[str]:
    """
    Get correlation ID from request state.

    The CorrelationIdMiddleware sets this on request.state.
    Returns "unknown" if middleware hasn't run (shouldn't happen).
    """
    return getattr(request.state, "correlation_id", "unknown")
