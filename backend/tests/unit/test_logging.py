"""
Unit tests for src/utils/logging.py

Tests the structured logging configuration:
- setup_logging() configuration
- get_logger() returns bound loggers
- sanitize_for_logging() masks sensitive data
"""

import pytest
import structlog

from src.utils.logging import setup_logging, get_logger, sanitize_for_logging


class TestSetupLogging:
    """Tests for setup_logging() function."""

    def test_setup_logging_development(self):
        """Setup for development environment completes without error."""
        # Should not raise
        setup_logging(environment="development", log_level="DEBUG")

    def test_setup_logging_production(self):
        """Setup for production environment completes without error."""
        setup_logging(environment="production", log_level="INFO")

    def test_setup_logging_with_json_output(self):
        """Can explicitly request JSON output."""
        setup_logging(environment="development", json_output=True)

    def test_setup_logging_with_console_output(self):
        """Can explicitly request console output."""
        setup_logging(environment="production", json_output=False)

    def test_invalid_log_level_defaults_to_info(self):
        """Invalid log level falls back to INFO."""
        # Should not raise, defaults to INFO
        setup_logging(log_level="INVALID_LEVEL")


class TestGetLogger:
    """Tests for get_logger() function."""

    def setup_method(self):
        """Configure logging before each test."""
        setup_logging(environment="development", log_level="DEBUG")

    def test_get_logger_returns_bound_logger(self):
        """get_logger returns a structlog BoundLogger."""
        logger = get_logger()
        assert logger is not None
        # Should be callable with standard methods
        assert hasattr(logger, "info")
        assert hasattr(logger, "debug")
        assert hasattr(logger, "warning")
        assert hasattr(logger, "error")

    def test_get_logger_with_name(self):
        """Can get a named logger."""
        logger = get_logger("test.module")
        assert logger is not None

    def test_logger_can_bind_context(self):
        """Logger can bind additional context."""
        logger = get_logger()
        bound = logger.bind(request_id="123", user_id="456")
        assert bound is not None

    def test_multiple_loggers_are_independent(self):
        """Multiple logger instances don't interfere."""
        logger1 = get_logger("module1")
        logger2 = get_logger("module2")
        # Both should work independently
        assert logger1 is not None
        assert logger2 is not None


class TestSanitizeForLogging:
    """Tests for sanitize_for_logging() function."""

    def test_empty_dict(self):
        """Empty dict returns empty dict."""
        result = sanitize_for_logging({})
        assert result == {}

    def test_non_sensitive_data_unchanged(self):
        """Non-sensitive data passes through unchanged."""
        data = {"name": "John", "count": 42, "active": True}
        result = sanitize_for_logging(data)
        assert result == data

    def test_password_redacted(self):
        """Password field is redacted."""
        data = {"username": "john", "password": "secret123"}
        result = sanitize_for_logging(data)
        assert result["username"] == "john"
        assert result["password"] == "***REDACTED***"

    def test_password_hash_redacted(self):
        """Password hash field is redacted."""
        data = {"password_hash": "$2b$12$..."}
        result = sanitize_for_logging(data)
        assert result["password_hash"] == "***REDACTED***"

    def test_token_redacted(self):
        """Token fields are redacted."""
        data = {"token": "abc123", "access_token": "xyz789", "refresh_token": "def456"}
        result = sanitize_for_logging(data)
        assert result["token"] == "***REDACTED***"
        assert result["access_token"] == "***REDACTED***"
        assert result["refresh_token"] == "***REDACTED***"

    def test_api_key_redacted(self):
        """API key field is redacted."""
        data = {"api_key": "sk-1234567890"}
        result = sanitize_for_logging(data)
        assert result["api_key"] == "***REDACTED***"

    def test_secret_redacted(self):
        """Secret field is redacted."""
        data = {"secret": "super_secret_value", "jwt_secret": "jwt-secret-key"}
        result = sanitize_for_logging(data)
        assert result["secret"] == "***REDACTED***"
        assert result["jwt_secret"] == "***REDACTED***"

    def test_email_partially_masked(self):
        """Email is partially masked (last 4 chars visible)."""
        data = {"email": "user@example.com"}
        result = sanitize_for_logging(data)
        assert result["email"] == "***.com"

    def test_phone_partially_masked(self):
        """Phone is partially masked (last 4 chars visible)."""
        data = {"phone": "+1-555-123-4567"}
        result = sanitize_for_logging(data)
        assert result["phone"] == "***4567"

    def test_short_values_not_masked(self):
        """Short values (<=4 chars) for partial mask fields are not masked."""
        data = {"phone": "1234"}
        result = sanitize_for_logging(data)
        # Too short to mask meaningfully
        assert result["phone"] == "1234"

    def test_nested_dict_sanitized(self):
        """Nested dictionaries are recursively sanitized."""
        data = {
            "user": {
                "name": "John",
                "password": "secret",
            }
        }
        result = sanitize_for_logging(data)
        assert result["user"]["name"] == "John"
        assert result["user"]["password"] == "***REDACTED***"

    def test_list_of_dicts_sanitized(self):
        """Lists containing dicts are recursively sanitized."""
        data = {
            "users": [
                {"name": "John", "password": "secret1"},
                {"name": "Jane", "password": "secret2"},
            ]
        }
        result = sanitize_for_logging(data)
        assert result["users"][0]["password"] == "***REDACTED***"
        assert result["users"][1]["password"] == "***REDACTED***"
        assert result["users"][0]["name"] == "John"
        assert result["users"][1]["name"] == "Jane"

    def test_list_of_primitives_unchanged(self):
        """Lists of primitives pass through unchanged."""
        data = {"tags": ["tag1", "tag2", "tag3"]}
        result = sanitize_for_logging(data)
        assert result["tags"] == ["tag1", "tag2", "tag3"]

    def test_case_insensitive_matching(self):
        """Field matching is case-insensitive."""
        data = {"PASSWORD": "secret", "Token": "abc", "API_KEY": "key123"}
        result = sanitize_for_logging(data)
        assert result["PASSWORD"] == "***REDACTED***"
        assert result["Token"] == "***REDACTED***"
        assert result["API_KEY"] == "***REDACTED***"

    def test_deeply_nested_structure(self):
        """Deep nesting is handled correctly."""
        data = {
            "level1": {
                "level2": {
                    "level3": {
                        "password": "deep_secret"
                    }
                }
            }
        }
        result = sanitize_for_logging(data)
        assert result["level1"]["level2"]["level3"]["password"] == "***REDACTED***"

    def test_mixed_content(self):
        """Mixed sensitive and non-sensitive content handled correctly."""
        data = {
            "name": "Test User",
            "email": "test@example.com",
            "password": "secret123",
            "settings": {
                "theme": "dark",
                "api_key": "key-abc-123",
            },
            "roles": ["admin", "user"],
        }
        result = sanitize_for_logging(data)

        assert result["name"] == "Test User"
        assert result["email"] == "***.com"
        assert result["password"] == "***REDACTED***"
        assert result["settings"]["theme"] == "dark"
        assert result["settings"]["api_key"] == "***REDACTED***"
        assert result["roles"] == ["admin", "user"]
