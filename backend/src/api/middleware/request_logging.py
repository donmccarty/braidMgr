"""
Request logging middleware for audit and debugging.

Logs request start with method, path, query params,
and request completion with status code and duration.

Usage:
    # In main.py
    from src.api.middleware.request_logging import RequestLoggingMiddleware
    app.add_middleware(RequestLoggingMiddleware)
"""

import time
from typing import Set

import structlog
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response


logger = structlog.get_logger()


# Paths to exclude from logging (health checks, metrics, etc.)
EXCLUDED_PATHS: Set[str] = {
    "/health",
    "/healthz",
    "/ready",
    "/metrics",
    "/favicon.ico",
}


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware that logs all HTTP requests for audit and debugging.

    Logs include:
    - request_started: method, path, query params (at request start)
    - request_completed: method, path, status code, duration (at request end)

    The correlation ID is automatically included via structlog contextvars
    (set by CorrelationIdMiddleware which should run first).

    Sensitive paths like /health are excluded to reduce log volume.
    """

    async def dispatch(
        self,
        request: Request,
        call_next: RequestResponseEndpoint,
    ) -> Response:
        # Skip logging for health checks and similar
        if request.url.path in EXCLUDED_PATHS:
            return await call_next(request)

        # Record start time for duration calculation
        start_time = time.perf_counter()

        # Extract request info (safe fields only - no body, no auth headers)
        method = request.method
        path = request.url.path
        query = str(request.query_params) if request.query_params else ""
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("User-Agent", "unknown")[:100]  # Truncate

        # Log request start
        logger.info(
            "request_started",
            method=method,
            path=path,
            query=query,
            client_ip=client_ip,
            user_agent=user_agent,
        )

        # Process the request
        response = await call_next(request)

        # Calculate duration
        duration_ms = (time.perf_counter() - start_time) * 1000

        # Log request completion
        log_method = self._get_log_method(response.status_code)
        log_method(
            "request_completed",
            method=method,
            path=path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )

        return response

    def _get_client_ip(self, request: Request) -> str:
        """
        Get client IP, preferring X-Forwarded-For for load balancer scenarios.

        In production behind ALB, the real client IP is in X-Forwarded-For.
        """
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # X-Forwarded-For can be comma-separated; first is original client
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _get_log_method(self, status_code: int):
        """
        Get appropriate log level based on response status code.

        - 5xx: error (server errors - investigate)
        - 4xx: warning (client errors - may indicate issues)
        - 2xx/3xx: info (success)
        """
        if status_code >= 500:
            return logger.error
        elif status_code >= 400:
            return logger.warning
        return logger.info
