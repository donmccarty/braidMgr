"""
Unit tests for src/api/routes/

Tests API endpoints:
- Health check endpoint
- Root endpoint
"""

import pytest
from unittest.mock import Mock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI

from src.api.routes.health import router


class TestHealthRouter:
    """Tests for health.py router endpoints."""

    @pytest.fixture
    def app(self):
        """Create test app with health router."""
        app = FastAPI()
        app.include_router(router)
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def test_root_endpoint(self, client):
        """Root endpoint returns API info."""
        response = client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert "name" in data
        assert "braidMgr" in data["name"]
        assert "version" in data
        assert "docs" in data
        assert data["docs"] == "/docs"

    def test_health_endpoint_healthy(self, client):
        """Health endpoint returns healthy status."""
        # Mock the services registry
        with patch("src.api.routes.health.services") as mock_services:
            mock_services.health_check_all.return_value = {
                "aurora": True,
            }

            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()

            assert data["status"] == "healthy"
            assert "services" in data
            assert data["services"]["aurora"] is True

    def test_health_endpoint_with_unhealthy_service(self, client):
        """Health endpoint shows unhealthy service."""
        with patch("src.api.routes.health.services") as mock_services:
            mock_services.health_check_all.return_value = {
                "aurora": "Connection refused",
            }

            response = client.get("/health")

            assert response.status_code == 200
            data = response.json()

            # Still returns 200, but shows service error
            assert data["status"] == "healthy"
            assert data["services"]["aurora"] == "Connection refused"

    def test_health_endpoint_multiple_services(self, client):
        """Health endpoint shows all services."""
        with patch("src.api.routes.health.services") as mock_services:
            mock_services.health_check_all.return_value = {
                "aurora": True,
                "anthropic": True,
                "s3": True,
            }

            response = client.get("/health")

            data = response.json()
            assert len(data["services"]) == 3
            assert all(status is True for status in data["services"].values())


class TestHealthRouterWithMiddleware:
    """Tests for health router with middleware stack."""

    @pytest.fixture
    def app(self):
        """Create test app with middleware and health router."""
        from src.api.middleware import (
            CorrelationIdMiddleware,
            RequestLoggingMiddleware,
        )

        app = FastAPI()
        app.add_middleware(RequestLoggingMiddleware)
        app.add_middleware(CorrelationIdMiddleware)
        app.include_router(router)
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def test_health_has_correlation_id(self, client):
        """Health response has correlation ID header."""
        with patch("src.api.routes.health.services") as mock_services:
            mock_services.health_check_all.return_value = {"aurora": True}

            response = client.get("/health")

            assert "X-Correlation-ID" in response.headers

    def test_health_with_custom_correlation_id(self, client):
        """Health endpoint respects provided correlation ID."""
        with patch("src.api.routes.health.services") as mock_services:
            mock_services.health_check_all.return_value = {"aurora": True}

            custom_id = "my-health-check-id"
            response = client.get(
                "/health",
                headers={"X-Correlation-ID": custom_id}
            )

            assert response.headers.get("X-Correlation-ID") == custom_id

    def test_root_has_correlation_id(self, client):
        """Root endpoint response has correlation ID header."""
        response = client.get("/")

        assert "X-Correlation-ID" in response.headers


class TestHealthRouterResponses:
    """Tests for health router response formats."""

    @pytest.fixture
    def app(self):
        """Create test app."""
        app = FastAPI()
        app.include_router(router)
        return app

    @pytest.fixture
    def client(self, app):
        """Create test client."""
        return TestClient(app)

    def test_root_response_format(self, client):
        """Root endpoint has expected JSON structure."""
        response = client.get("/")

        data = response.json()

        # All required fields present
        required_fields = {"name", "version", "docs"}
        assert required_fields.issubset(data.keys())

        # All values are strings
        assert all(isinstance(v, str) for v in data.values())

    def test_health_response_format(self, client):
        """Health endpoint has expected JSON structure."""
        with patch("src.api.routes.health.services") as mock_services:
            mock_services.health_check_all.return_value = {"aurora": True}

            response = client.get("/health")
            data = response.json()

            # Required fields
            assert "status" in data
            assert "services" in data

            # Types correct
            assert isinstance(data["status"], str)
            assert isinstance(data["services"], dict)

    def test_content_type_is_json(self, client):
        """Responses have JSON content type."""
        with patch("src.api.routes.health.services") as mock_services:
            mock_services.health_check_all.return_value = {}

            response = client.get("/health")
            assert "application/json" in response.headers.get("content-type", "")

            response = client.get("/")
            assert "application/json" in response.headers.get("content-type", "")
