"""
API middleware for braidMgr backend.

Exports:
    CorrelationIdMiddleware: Request tracing with correlation IDs
    RequestLoggingMiddleware: Request/response logging
    app_error_handler: Handler for AppError exceptions
    unhandled_error_handler: Catch-all for unexpected errors
"""

from src.api.middleware.correlation import CorrelationIdMiddleware, get_correlation_id
from src.api.middleware.request_logging import RequestLoggingMiddleware
from src.api.middleware.error_handler import app_error_handler, unhandled_error_handler

__all__ = [
    "CorrelationIdMiddleware",
    "get_correlation_id",
    "RequestLoggingMiddleware",
    "app_error_handler",
    "unhandled_error_handler",
]
