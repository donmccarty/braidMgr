"""
Pytest configuration and fixtures for braidMgr backend tests.

Usage:
    pytest                      # Run all tests
    pytest tests/unit           # Run unit tests only
    pytest -v                   # Verbose output
    pytest --cov=src            # With coverage
"""

import os
import sys
import pytest
from pathlib import Path
from typing import AsyncGenerator
from unittest.mock import patch

# Add src to path for imports
backend_path = Path(__file__).parent.parent
sys.path.insert(0, str(backend_path))

# Mark all tests as async by default
pytest_plugins = ["pytest_asyncio"]


@pytest.fixture
def anyio_backend():
    """Use asyncio backend for async tests."""
    return "asyncio"


@pytest.fixture(autouse=True)
def reset_singletons():
    """Reset singletons between tests."""
    # Reset config singleton
    import src.config.settings as settings
    settings._config = None

    # Reset service registry singleton
    from src.services import ServiceRegistry
    ServiceRegistry._instance = None
    ServiceRegistry._initialized = False

    yield


@pytest.fixture
def mock_config():
    """Create a mock AppConfig for testing."""
    from unittest.mock import Mock
    from src.config.settings import AppConfig

    config = Mock(spec=AppConfig)
    config.environment = "testing"
    config.database.host = "localhost"
    config.database.port = 5432
    config.database.name = "test_db"
    config.database.user = "test_user"
    config.database.password = "test_pass"
    config.database.pool.min_connections = 1
    config.database.pool.max_connections = 5
    config.database.pool.connection_timeout = 10
    config.application.logging.level = "DEBUG"
    config.application.api.cors_origins = "http://localhost:3000"
    return config


# =============================================================================
# LOGGING SETUP FOR TESTS
# =============================================================================
@pytest.fixture(autouse=True)
def setup_test_logging():
    """Configure logging for tests."""
    from src.utils.logging import setup_logging
    setup_logging(environment="testing", log_level="DEBUG", json_output=False)
    yield


# =============================================================================
# DATABASE FIXTURES (to be implemented for integration tests)
# =============================================================================
# Future fixtures for integration tests:
# - test_db: Create test database
# - test_pool: Connection pool for test database
# - clean_db: Reset database between tests
