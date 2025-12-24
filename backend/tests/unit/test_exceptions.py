"""
Unit tests for src/utils/exceptions.py

Tests the custom exception hierarchy:
- AppError base class
- All 4xx client errors
- All 5xx server errors
- to_dict() serialization
"""

import pytest
from src.utils.exceptions import (
    AppError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    NotFoundError,
    ConflictError,
    WorkflowError,
    RateLimitError,
    ConfigurationError,
    DatabaseError,
    ExternalServiceError,
    ServiceUnavailableError,
)


class TestAppError:
    """Tests for the base AppError class."""

    def test_default_values(self):
        """AppError has correct default status code and error code."""
        error = AppError("Something went wrong")
        assert error.status_code == 500
        assert error.error_code == "INTERNAL_ERROR"
        assert error.message == "Something went wrong"
        assert error.details == {}

    def test_custom_error_code(self):
        """Can override error_code at instantiation."""
        error = AppError("Custom error", error_code="CUSTOM_CODE")
        assert error.error_code == "CUSTOM_CODE"

    def test_with_details(self):
        """Details are stored and accessible."""
        error = AppError("Error with context", details={"key": "value"})
        assert error.details == {"key": "value"}

    def test_to_dict(self):
        """to_dict() returns correct structure for API responses."""
        error = AppError("Test message", details={"field": "test"})
        result = error.to_dict()

        assert result == {
            "error": "INTERNAL_ERROR",
            "message": "Test message",
            "details": {"field": "test"},
        }

    def test_exception_inheritance(self):
        """AppError is a proper Exception subclass."""
        error = AppError("Test")
        assert isinstance(error, Exception)
        assert str(error) == "Test"


class TestValidationError:
    """Tests for ValidationError (400)."""

    def test_status_code(self):
        """ValidationError has 400 status code."""
        error = ValidationError("Invalid input")
        assert error.status_code == 400
        assert error.error_code == "VALIDATION_ERROR"

    def test_with_field(self):
        """Field name is included in details."""
        error = ValidationError("Invalid email", field="email")
        assert error.details["field"] == "email"

    def test_with_value(self):
        """Value is included in details."""
        error = ValidationError("Invalid value", field="count", value=42)
        assert error.details["value"] == 42

    def test_value_truncation(self):
        """Long values are truncated to 50 chars."""
        long_value = "x" * 100
        error = ValidationError("Too long", value=long_value)
        assert len(error.details["value"]) == 50

    def test_inherits_from_app_error(self):
        """ValidationError is an AppError subclass."""
        error = ValidationError("Test")
        assert isinstance(error, AppError)


class TestAuthenticationError:
    """Tests for AuthenticationError (401)."""

    def test_status_code(self):
        """AuthenticationError has 401 status code."""
        error = AuthenticationError("Invalid token")
        assert error.status_code == 401
        assert error.error_code == "AUTHENTICATION_ERROR"


class TestAuthorizationError:
    """Tests for AuthorizationError (403)."""

    def test_status_code(self):
        """AuthorizationError has 403 status code."""
        error = AuthorizationError()
        assert error.status_code == 403
        assert error.error_code == "AUTHORIZATION_ERROR"

    def test_default_message(self):
        """Has default permission denied message."""
        error = AuthorizationError()
        assert "permission" in error.message.lower()

    def test_with_required_permission(self):
        """Required permission is included in details."""
        error = AuthorizationError(required_permission="admin:write")
        assert error.details["required_permission"] == "admin:write"


class TestNotFoundError:
    """Tests for NotFoundError (404)."""

    def test_status_code(self):
        """NotFoundError has 404 status code."""
        error = NotFoundError("Project", "abc-123")
        assert error.status_code == 404
        assert error.error_code == "NOT_FOUND"

    def test_message_format(self):
        """Message includes resource type and ID."""
        error = NotFoundError("Item", 42)
        assert "Item" in error.message
        assert "42" in error.message

    def test_details_include_resource_info(self):
        """Details include resource_type and resource_id."""
        error = NotFoundError("User", "user-uuid")
        assert error.details["resource_type"] == "User"
        assert error.details["resource_id"] == "user-uuid"


class TestConflictError:
    """Tests for ConflictError (409)."""

    def test_status_code(self):
        """ConflictError has 409 status code."""
        error = ConflictError("Resource already exists")
        assert error.status_code == 409
        assert error.error_code == "CONFLICT"

    def test_with_field(self):
        """Field name is included in details."""
        error = ConflictError("Duplicate email", field="email")
        assert error.details["field"] == "email"

    def test_with_existing_id(self):
        """Existing ID is included in details."""
        error = ConflictError("Duplicate", existing_id="existing-uuid")
        assert error.details["existing_id"] == "existing-uuid"


class TestWorkflowError:
    """Tests for WorkflowError (422)."""

    def test_status_code(self):
        """WorkflowError has 422 status code."""
        error = WorkflowError("Invalid state transition")
        assert error.status_code == 422
        assert error.error_code == "WORKFLOW_ERROR"

    def test_with_states(self):
        """Current and attempted states are included in details."""
        error = WorkflowError(
            "Cannot transition",
            current_state="draft",
            attempted_state="completed",
        )
        assert error.details["current_state"] == "draft"
        assert error.details["attempted_state"] == "completed"


class TestRateLimitError:
    """Tests for RateLimitError (429)."""

    def test_status_code(self):
        """RateLimitError has 429 status code."""
        error = RateLimitError()
        assert error.status_code == 429
        assert error.error_code == "RATE_LIMIT_EXCEEDED"

    def test_default_message(self):
        """Has default rate limit message."""
        error = RateLimitError()
        assert "too many" in error.message.lower()

    def test_with_retry_after(self):
        """Retry-after seconds included in details."""
        error = RateLimitError(retry_after=60)
        assert error.details["retry_after_seconds"] == 60


class TestConfigurationError:
    """Tests for ConfigurationError (500)."""

    def test_status_code(self):
        """ConfigurationError has 500 status code."""
        error = ConfigurationError("Missing config")
        assert error.status_code == 500
        assert error.error_code == "CONFIGURATION_ERROR"

    def test_with_config_key(self):
        """Config key is included in details."""
        error = ConfigurationError("Missing key", config_key="database.host")
        assert error.details["config_key"] == "database.host"


class TestDatabaseError:
    """Tests for DatabaseError (500)."""

    def test_status_code(self):
        """DatabaseError has 500 status code."""
        error = DatabaseError("Query failed")
        assert error.status_code == 500
        assert error.error_code == "DATABASE_ERROR"

    def test_with_operation_and_table(self):
        """Operation and table are included in details."""
        error = DatabaseError("Insert failed", operation="insert", table="items")
        assert error.details["operation"] == "insert"
        assert error.details["table"] == "items"


class TestExternalServiceError:
    """Tests for ExternalServiceError (502)."""

    def test_status_code(self):
        """ExternalServiceError has 502 status code."""
        error = ExternalServiceError("Anthropic", "API timeout")
        assert error.status_code == 502
        assert error.error_code == "EXTERNAL_SERVICE_ERROR"

    def test_message_includes_service_name(self):
        """Message includes service name."""
        error = ExternalServiceError("Stripe", "Payment failed")
        assert "Stripe" in error.message
        assert "Payment failed" in error.message

    def test_details_include_service(self):
        """Service name is in details."""
        error = ExternalServiceError("AWS", "S3 error")
        assert error.details["service"] == "AWS"

    def test_with_upstream_status(self):
        """Upstream status code is included when provided."""
        error = ExternalServiceError("API", "Error", upstream_status_code=503)
        assert error.details["upstream_status"] == 503


class TestServiceUnavailableError:
    """Tests for ServiceUnavailableError (503)."""

    def test_status_code(self):
        """ServiceUnavailableError has 503 status code."""
        error = ServiceUnavailableError()
        assert error.status_code == 503
        assert error.error_code == "SERVICE_UNAVAILABLE"

    def test_default_message(self):
        """Has default unavailable message."""
        error = ServiceUnavailableError()
        assert "unavailable" in error.message.lower()

    def test_with_retry_after(self):
        """Retry-after seconds included in details."""
        error = ServiceUnavailableError(retry_after=300)
        assert error.details["retry_after_seconds"] == 300
