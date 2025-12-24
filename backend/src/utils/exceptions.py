"""
Application exceptions with HTTP status code mapping.

All application exceptions inherit from AppError which provides:
- Consistent error codes for API responses
- HTTP status code mapping
- Structured details for debugging

Usage:
    from src.utils.exceptions import NotFoundError, ConflictError

    raise NotFoundError("Project", project_id)
    raise ConflictError("Item with this number already exists", field="item_num")
"""

from typing import Any, Dict, Optional


class AppError(Exception):
    """
    Base exception for all application errors.

    Attributes:
        status_code: HTTP status code for API response
        error_code: Machine-readable error code
        message: Human-readable error message
        details: Additional context for debugging
    """

    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(
        self,
        message: str,
        details: Optional[Dict[str, Any]] = None,
        error_code: Optional[str] = None,
    ):
        self.message = message
        self.details = details or {}
        if error_code:
            self.error_code = error_code
        super().__init__(message)

    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for API response."""
        return {
            "error": self.error_code,
            "message": self.message,
            "details": self.details,
        }


# =============================================================================
# CLIENT ERRORS (4xx)
# =============================================================================


class ValidationError(AppError):
    """
    Input validation failed.

    Use when request data fails validation rules.
    """

    status_code = 400
    error_code = "VALIDATION_ERROR"

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        value: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        if field:
            error_details["field"] = field
        if value is not None:
            # Sanitize - don't log sensitive or very long values
            str_value = str(value)
            error_details["value"] = str_value[:50] if len(str_value) > 50 else value
        super().__init__(message, error_details)


class AuthenticationError(AppError):
    """
    User not authenticated.

    Use when authentication is required but missing or invalid.
    """

    status_code = 401
    error_code = "AUTHENTICATION_ERROR"


class AuthorizationError(AppError):
    """
    User lacks permission for operation.

    Use when authenticated user doesn't have required permissions.
    """

    status_code = 403
    error_code = "AUTHORIZATION_ERROR"

    def __init__(
        self,
        message: str = "You do not have permission to perform this action",
        required_permission: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        if required_permission:
            error_details["required_permission"] = required_permission
        super().__init__(message, error_details)


class NotFoundError(AppError):
    """
    Resource not found.

    Use when requested resource doesn't exist or is deleted.
    """

    status_code = 404
    error_code = "NOT_FOUND"

    def __init__(
        self,
        resource_type: str,
        resource_id: Any,
        details: Optional[Dict[str, Any]] = None,
    ):
        message = f"{resource_type} not found: {resource_id}"
        error_details = details or {}
        error_details["resource_type"] = resource_type
        error_details["resource_id"] = str(resource_id)
        super().__init__(message, error_details)


class ConflictError(AppError):
    """
    Resource conflict (duplicate, state mismatch).

    Use when operation conflicts with existing data.
    """

    status_code = 409
    error_code = "CONFLICT"

    def __init__(
        self,
        message: str,
        field: Optional[str] = None,
        existing_id: Optional[Any] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        if field:
            error_details["field"] = field
        if existing_id:
            error_details["existing_id"] = str(existing_id)
        super().__init__(message, error_details)


class WorkflowError(AppError):
    """
    Invalid workflow state transition.

    Use when attempting invalid state change.
    """

    status_code = 422
    error_code = "WORKFLOW_ERROR"

    def __init__(
        self,
        message: str,
        current_state: Optional[str] = None,
        attempted_state: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        if current_state:
            error_details["current_state"] = current_state
        if attempted_state:
            error_details["attempted_state"] = attempted_state
        super().__init__(message, error_details)


class RateLimitError(AppError):
    """
    Rate limit exceeded.

    Use when client has made too many requests.
    """

    status_code = 429
    error_code = "RATE_LIMIT_EXCEEDED"

    def __init__(
        self,
        message: str = "Too many requests. Please try again later.",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        if retry_after:
            error_details["retry_after_seconds"] = retry_after
        super().__init__(message, error_details)


# =============================================================================
# SERVER ERRORS (5xx)
# =============================================================================


class ConfigurationError(AppError):
    """
    Invalid or missing configuration.

    Use when required config is missing or invalid at startup.
    """

    status_code = 500
    error_code = "CONFIGURATION_ERROR"

    def __init__(
        self,
        message: str,
        config_key: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        if config_key:
            error_details["config_key"] = config_key
        super().__init__(message, error_details)


class DatabaseError(AppError):
    """
    Database operation failed.

    Use for database-specific errors (connection, query, constraint).
    """

    status_code = 500
    error_code = "DATABASE_ERROR"

    def __init__(
        self,
        message: str,
        operation: Optional[str] = None,
        table: Optional[str] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        if operation:
            error_details["operation"] = operation
        if table:
            error_details["table"] = table
        super().__init__(message, error_details)


class ExternalServiceError(AppError):
    """
    External service call failed.

    Use when third-party API calls fail.
    """

    status_code = 502
    error_code = "EXTERNAL_SERVICE_ERROR"

    def __init__(
        self,
        service: str,
        message: str,
        upstream_status_code: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        error_details["service"] = service
        if upstream_status_code:
            error_details["upstream_status"] = upstream_status_code
        full_message = f"{service}: {message}"
        super().__init__(full_message, error_details)
        self.service = service


class ServiceUnavailableError(AppError):
    """
    Service temporarily unavailable.

    Use when service is overloaded or in maintenance.
    """

    status_code = 503
    error_code = "SERVICE_UNAVAILABLE"

    def __init__(
        self,
        message: str = "Service temporarily unavailable. Please try again later.",
        retry_after: Optional[int] = None,
        details: Optional[Dict[str, Any]] = None,
    ):
        error_details = details or {}
        if retry_after:
            error_details["retry_after_seconds"] = retry_after
        super().__init__(message, error_details)
