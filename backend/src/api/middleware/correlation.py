"""
Correlation ID middleware for request tracing.

Generates or extracts correlation ID from X-Correlation-ID header,
binds to structlog contextvars for all subsequent logs,
and returns correlation ID in response header.

Usage:
    # In main.py
    from src.api.middleware.correlation import CorrelationIdMiddleware
    app.add_middleware(CorrelationIdMiddleware)

    # In any handler or service
    import structlog
    logger = structlog.get_logger()
    logger.info("operation")  # Automatically includes correlation_id
"""

import uuid
from contextvars import ContextVar
from typing import Optional

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


# ContextVar for correlation ID - accessible from anywhere in the async context
correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")


class CorrelationIdMiddleware(BaseHTTPMiddleware):
    """
    Middleware that ensures every request has a correlation ID for tracing.

    The correlation ID is:
    1. Read from X-Correlation-ID header if provided (allows tracing across services)
    2. Generated as UUID4 if not provided
    3. Bound to structlog context for automatic inclusion in all logs
    4. Stored on request.state for access in error handlers
    5. Returned in X-Correlation-ID response header

    This enables end-to-end request tracing across logs, services, and error reports.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        # Get correlation ID from header or generate new one
        correlation_id = request.headers.get("X-Correlation-ID", str(uuid.uuid4()))

        # Store in context var for access anywhere in async context
        correlation_id_var.set(correlation_id)

        # Bind to structlog context - all subsequent logs include correlation_id
        structlog.contextvars.clear_contextvars()
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

        # Store on request state for error handlers that may not use structlog
        request.state.correlation_id = correlation_id

        # Process the request
        response = await call_next(request)

        # Add correlation ID to response headers for client tracing
        response.headers["X-Correlation-ID"] = correlation_id

        return response


def get_correlation_id() -> Optional[str]:
    """
    Get the current correlation ID from context.

    Returns:
        The correlation ID for the current request, or None if not in request context.

    Example:
        from src.api.middleware.correlation import get_correlation_id

        correlation_id = get_correlation_id()
        external_api.call(headers={"X-Correlation-ID": correlation_id})
    """
    cid = correlation_id_var.get()
    return cid if cid else None
