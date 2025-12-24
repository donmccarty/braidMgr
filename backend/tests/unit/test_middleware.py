"""
Unit tests for src/api/middleware/

Tests middleware components:
- CorrelationIdMiddleware
- RequestLoggingMiddleware
- Error handlers
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
import uuid

from starlette.requests import Request
from starlette.responses import Response
from starlette.testclient import TestClient
from fastapi import FastAPI

from src.api.middleware.correlation import (
    CorrelationIdMiddleware,
    get_correlation_id,
    correlation_id_var,
)
from src.api.middleware.request_logging import (
    RequestLoggingMiddleware,
    EXCLUDED_PATHS,
)
from src.api.middleware.error_handler import (
    app_error_handler,
    unhandled_error_handler,
    _get_correlation_id,
)
from src.utils.exceptions import (
    AppError,
    ValidationError,
    NotFoundError,
    AuthenticationError,
)


class TestCorrelationIdMiddleware:
    """Tests for CorrelationIdMiddleware."""

    @pytest.fixture
    def app(self):
        """Create test app with middleware."""
        app = FastAPI()
        app.add_middleware(CorrelationIdMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"correlation_id": get_correlation_id()}

        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def test_generates_correlation_id(self, client):
        """Generates UUID correlation ID when not provided."""
        response = client.get("/test")
        assert response.status_code == 200

        # Response should have correlation ID header
        correlation_id = response.headers.get("X-Correlation-ID")
        assert correlation_id is not None

        # Should be a valid UUID
        uuid.UUID(correlation_id)

    def test_uses_provided_correlation_id(self, client):
        """Uses correlation ID from request header."""
        custom_id = "my-custom-correlation-id"
        response = client.get(
            "/test",
            headers={"X-Correlation-ID": custom_id}
        )

        assert response.status_code == 200
        assert response.headers.get("X-Correlation-ID") == custom_id

    def test_correlation_id_accessible_in_handler(self, client):
        """Correlation ID is accessible via get_correlation_id()."""
        custom_id = "test-id-123"
        response = client.get(
            "/test",
            headers={"X-Correlation-ID": custom_id}
        )

        # Endpoint returns the correlation ID it sees
        data = response.json()
        assert data["correlation_id"] == custom_id

    def test_get_correlation_id_outside_request(self):
        """get_correlation_id() returns None outside request context."""
        # Clear the context var
        correlation_id_var.set("")
        result = get_correlation_id()
        assert result is None


class TestRequestLoggingMiddleware:
    """Tests for RequestLoggingMiddleware."""

    @pytest.fixture
    def app(self):
        """Create test app with middleware."""
        app = FastAPI()
        app.add_middleware(RequestLoggingMiddleware)

        @app.get("/test")
        async def test_endpoint():
            return {"status": "ok"}

        @app.get("/health")
        async def health_endpoint():
            return {"status": "healthy"}

        @app.get("/error")
        async def error_endpoint():
            raise ValueError("Test error")

        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app, raise_server_exceptions=False)

    def test_logs_successful_request(self, client, caplog):
        """Logs start and completion for successful requests."""
        with patch("src.api.middleware.request_logging.logger") as mock_logger:
            response = client.get("/test")
            assert response.status_code == 200

            # Should have logged request_started and request_completed
            call_events = [call[0][0] for call in mock_logger.info.call_args_list]
            assert "request_started" in call_events
            assert "request_completed" in call_events

    def test_excludes_health_endpoints(self, client):
        """Health check paths are not logged."""
        with patch("src.api.middleware.request_logging.logger") as mock_logger:
            response = client.get("/health")
            assert response.status_code == 200

            # Should NOT have logged anything
            assert mock_logger.info.call_count == 0

    def test_excluded_paths(self):
        """EXCLUDED_PATHS contains expected paths."""
        assert "/health" in EXCLUDED_PATHS
        assert "/healthz" in EXCLUDED_PATHS
        assert "/ready" in EXCLUDED_PATHS
        assert "/metrics" in EXCLUDED_PATHS
        assert "/favicon.ico" in EXCLUDED_PATHS


class TestAppErrorHandler:
    """Tests for app_error_handler."""

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        request = Mock(spec=Request)
        request.url.path = "/test"
        request.method = "GET"
        request.state.correlation_id = "test-correlation-id"
        return request

    @pytest.mark.asyncio
    async def test_handles_validation_error(self, mock_request):
        """Converts ValidationError to 400 response."""
        error = ValidationError("Invalid input", field="email")

        response = await app_error_handler(mock_request, error)

        assert response.status_code == 400
        body = response.body.decode()
        assert "VALIDATION_ERROR" in body
        assert "Invalid input" in body

    @pytest.mark.asyncio
    async def test_handles_not_found_error(self, mock_request):
        """Converts NotFoundError to 404 response."""
        error = NotFoundError("Project", "abc-123")

        response = await app_error_handler(mock_request, error)

        assert response.status_code == 404
        body = response.body.decode()
        assert "NOT_FOUND" in body

    @pytest.mark.asyncio
    async def test_handles_authentication_error(self, mock_request):
        """Converts AuthenticationError to 401 response."""
        error = AuthenticationError("Invalid token")

        response = await app_error_handler(mock_request, error)

        assert response.status_code == 401
        body = response.body.decode()
        assert "AUTHENTICATION_ERROR" in body

    @pytest.mark.asyncio
    async def test_includes_correlation_id(self, mock_request):
        """Response includes correlation ID."""
        error = ValidationError("Test error")

        response = await app_error_handler(mock_request, error)

        import json
        body = json.loads(response.body.decode())
        assert body["correlation_id"] == "test-correlation-id"

    @pytest.mark.asyncio
    async def test_includes_error_details(self, mock_request):
        """Response includes error details."""
        error = ValidationError("Invalid value", field="count", value=42)

        response = await app_error_handler(mock_request, error)

        import json
        body = json.loads(response.body.decode())
        assert body["details"]["field"] == "count"


class TestUnhandledErrorHandler:
    """Tests for unhandled_error_handler."""

    @pytest.fixture
    def mock_request(self):
        """Create mock request."""
        request = Mock(spec=Request)
        request.url.path = "/test"
        request.method = "POST"
        request.query_params = {}
        request.state.correlation_id = "error-correlation-id"
        return request

    @pytest.mark.asyncio
    async def test_returns_500(self, mock_request):
        """Unhandled errors return 500 status."""
        error = ValueError("Unexpected error")

        response = await unhandled_error_handler(mock_request, error)

        assert response.status_code == 500

    @pytest.mark.asyncio
    async def test_generic_message(self, mock_request):
        """Response has generic message (no internal details)."""
        error = ValueError("Database connection failed: password123")

        response = await unhandled_error_handler(mock_request, error)

        body = response.body.decode()
        # Should NOT contain internal details
        assert "password123" not in body
        assert "Database connection" not in body
        # Should have generic message
        assert "unexpected error" in body.lower()

    @pytest.mark.asyncio
    async def test_includes_correlation_id(self, mock_request):
        """Response includes correlation ID for tracing."""
        error = RuntimeError("Crash")

        response = await unhandled_error_handler(mock_request, error)

        import json
        body = json.loads(response.body.decode())
        assert body["correlation_id"] == "error-correlation-id"

    @pytest.mark.asyncio
    async def test_error_code_is_internal(self, mock_request):
        """Error code is INTERNAL_ERROR."""
        error = Exception("Any error")

        response = await unhandled_error_handler(mock_request, error)

        import json
        body = json.loads(response.body.decode())
        assert body["error"] == "INTERNAL_ERROR"


class TestGetCorrelationId:
    """Tests for _get_correlation_id helper."""

    def test_returns_correlation_id_from_state(self):
        """Returns correlation ID from request.state."""
        request = Mock()
        request.state.correlation_id = "test-id"

        result = _get_correlation_id(request)
        assert result == "test-id"

    def test_returns_unknown_when_missing(self):
        """Returns 'unknown' when correlation ID not set."""
        # Create a Mock with state attribute, but state has no correlation_id
        mock_state = Mock(spec=[])  # state with no attributes
        request = Mock()
        request.state = mock_state

        result = _get_correlation_id(request)
        assert result == "unknown"


class TestMiddlewareIntegration:
    """Integration tests for middleware stack."""

    @pytest.fixture
    def app(self):
        """Create app with full middleware stack."""
        app = FastAPI()

        # Add middleware in correct order (reverse of execution order)
        app.add_middleware(RequestLoggingMiddleware)
        app.add_middleware(CorrelationIdMiddleware)

        # Add error handlers
        from src.utils.exceptions import AppError
        app.add_exception_handler(AppError, app_error_handler)
        app.add_exception_handler(Exception, unhandled_error_handler)

        @app.get("/success")
        async def success():
            return {"status": "ok", "correlation_id": get_correlation_id()}

        @app.get("/validation-error")
        async def validation_error():
            raise ValidationError("Bad input", field="test")

        @app.get("/crash")
        async def crash():
            raise RuntimeError("Boom!")

        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app, raise_server_exceptions=False)

    def test_successful_request_flow(self, client):
        """Successful request has correlation ID throughout."""
        response = client.get("/success")

        assert response.status_code == 200
        data = response.json()

        # Correlation ID in response body matches header
        header_id = response.headers.get("X-Correlation-ID")
        assert data["correlation_id"] == header_id

    def test_app_error_has_correlation_id(self, client):
        """App errors include correlation ID in response."""
        response = client.get("/validation-error")

        assert response.status_code == 400
        data = response.json()

        # Error response has correlation ID
        assert "correlation_id" in data
        # And it matches response header
        assert data["correlation_id"] == response.headers.get("X-Correlation-ID")

    def test_unhandled_error_has_correlation_id(self, client):
        """Unhandled errors include correlation ID in response."""
        response = client.get("/crash")

        assert response.status_code == 500
        data = response.json()

        # Error response has correlation ID
        assert "correlation_id" in data
        # Generic message, not internal details
        assert "unexpected error" in data["message"].lower()
