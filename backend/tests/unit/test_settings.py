"""
Unit tests for src/config/settings.py

Tests configuration loading:
- Environment variable substitution
- Dataclass conversion
- Default values
- get_config() singleton
"""

import os
import pytest
from pathlib import Path
from unittest.mock import patch
import tempfile

from src.config.settings import (
    load_config,
    get_config,
    AppConfig,
    DatabaseConfig,
    DatabasePoolConfig,
    ApplicationConfig,
    APIConfig,
    AuthConfig,
    LoggingConfig,
    _substitute_env_vars,
    _substitute_dict,
)


class TestEnvVarSubstitution:
    """Tests for environment variable substitution."""

    def test_no_substitution_needed(self):
        """Plain strings pass through unchanged."""
        result = _substitute_env_vars("hello world")
        assert result == "hello world"

    def test_simple_substitution(self):
        """${VAR} is substituted from environment."""
        with patch.dict(os.environ, {"TEST_VAR": "test_value"}):
            result = _substitute_env_vars("${TEST_VAR}")
            assert result == "test_value"

    def test_missing_var_returns_empty(self):
        """Missing env var returns empty string."""
        # Ensure var doesn't exist
        os.environ.pop("NONEXISTENT_VAR", None)
        result = _substitute_env_vars("${NONEXISTENT_VAR}")
        assert result == ""

    def test_default_value_used(self):
        """${VAR:-default} uses default when var missing."""
        os.environ.pop("MISSING_VAR", None)
        result = _substitute_env_vars("${MISSING_VAR:-default_value}")
        assert result == "default_value"

    def test_default_value_ignored_when_var_set(self):
        """${VAR:-default} uses var value when set."""
        with patch.dict(os.environ, {"SET_VAR": "actual_value"}):
            result = _substitute_env_vars("${SET_VAR:-default_value}")
            assert result == "actual_value"

    def test_multiple_substitutions(self):
        """Multiple vars in one string are all substituted."""
        with patch.dict(os.environ, {"VAR1": "one", "VAR2": "two"}):
            result = _substitute_env_vars("${VAR1}-${VAR2}")
            assert result == "one-two"

    def test_non_string_passthrough(self):
        """Non-string values pass through unchanged."""
        assert _substitute_env_vars(42) == 42
        assert _substitute_env_vars(True) is True
        assert _substitute_env_vars(None) is None

    def test_dict_substitution(self):
        """_substitute_dict recursively substitutes in dicts."""
        with patch.dict(os.environ, {"DB_HOST": "localhost", "DB_PORT": "5432"}):
            data = {
                "host": "${DB_HOST}",
                "port": "${DB_PORT:-5433}",
            }
            result = _substitute_dict(data)
            assert result["host"] == "localhost"
            assert result["port"] == "5432"

    def test_nested_dict_substitution(self):
        """Nested dicts are recursively substituted."""
        with patch.dict(os.environ, {"INNER_VAL": "nested"}):
            data = {
                "outer": {
                    "inner": "${INNER_VAL}"
                }
            }
            result = _substitute_dict(data)
            assert result["outer"]["inner"] == "nested"


class TestDataclassDefaults:
    """Tests for dataclass default values."""

    def test_database_pool_defaults(self):
        """DatabasePoolConfig has sensible defaults."""
        config = DatabasePoolConfig()
        assert config.min_connections == 2
        assert config.max_connections == 10
        assert config.connection_timeout == 30

    def test_database_config_defaults(self):
        """DatabaseConfig has sensible defaults."""
        config = DatabaseConfig()
        assert config.host == "localhost"
        assert config.port == 5432
        assert config.name == "braidmgr_dev"
        assert config.user == "postgres"
        assert config.password == "postgres"
        assert isinstance(config.pool, DatabasePoolConfig)

    def test_api_config_defaults(self):
        """APIConfig has sensible defaults."""
        config = APIConfig()
        assert config.host == "0.0.0.0"
        assert config.port == 8000
        assert "localhost" in config.cors_origins

    def test_auth_config_defaults(self):
        """AuthConfig has sensible defaults."""
        config = AuthConfig()
        assert config.jwt_algorithm == "HS256"
        assert config.access_token_expiry_minutes == 15
        assert config.refresh_token_expiry_days == 7
        assert config.bcrypt_rounds == 12
        assert config.min_password_length == 8
        assert "dev" in config.jwt_secret  # Should be dev secret

    def test_logging_config_defaults(self):
        """LoggingConfig has sensible defaults."""
        config = LoggingConfig()
        assert config.level == "INFO"
        assert config.format == "auto"

    def test_app_config_defaults(self):
        """AppConfig has sensible defaults."""
        config = AppConfig()
        assert config.environment == "development"
        assert isinstance(config.database, DatabaseConfig)
        assert isinstance(config.application, ApplicationConfig)


class TestLoadConfig:
    """Tests for load_config() function."""

    def test_load_config_from_file(self):
        """load_config() loads from config.yaml."""
        # This assumes config.yaml exists in project root
        config = load_config()
        assert isinstance(config, AppConfig)
        assert config.environment in ["development", "staging", "production"]

    def test_load_config_file_not_found(self):
        """load_config() raises FileNotFoundError for missing file."""
        with pytest.raises(FileNotFoundError):
            load_config(Path("/nonexistent/config.yaml"))

    def test_load_config_with_env_overrides(self):
        """Environment variables override config.yaml values."""
        with patch.dict(os.environ, {"ENVIRONMENT": "testing", "LOG_LEVEL": "DEBUG"}):
            # Force reload to pick up env vars
            import src.config.settings as settings
            settings._config = None  # Reset singleton

            config = get_config(reload=True)
            assert config.environment == "testing"
            assert config.application.logging.level == "DEBUG"


class TestGetConfig:
    """Tests for get_config() singleton."""

    def setup_method(self):
        """Reset singleton before each test."""
        import src.config.settings as settings
        settings._config = None

    def test_get_config_returns_app_config(self):
        """get_config() returns an AppConfig instance."""
        config = get_config()
        assert isinstance(config, AppConfig)

    def test_get_config_is_singleton(self):
        """get_config() returns same instance on repeated calls."""
        config1 = get_config()
        config2 = get_config()
        assert config1 is config2

    def test_get_config_reload(self):
        """get_config(reload=True) returns fresh instance."""
        config1 = get_config()
        config2 = get_config(reload=True)
        # Different instance after reload
        assert config1 is not config2

    def test_config_database_accessible(self):
        """Database config is accessible via dot notation."""
        config = get_config()
        assert hasattr(config, "database")
        assert hasattr(config.database, "host")
        assert hasattr(config.database, "pool")
        assert hasattr(config.database.pool, "min_connections")

    def test_config_application_accessible(self):
        """Application config is accessible via dot notation."""
        config = get_config()
        assert hasattr(config, "application")
        assert hasattr(config.application, "api")
        assert hasattr(config.application, "auth")
        assert hasattr(config.application, "logging")


class TestConfigIntegration:
    """Integration tests for complete config loading."""

    def test_config_matches_yaml_structure(self):
        """Loaded config matches expected structure from config.yaml."""
        config = get_config(reload=True)

        # Top-level sections
        assert hasattr(config, "environment")
        assert hasattr(config, "database")
        assert hasattr(config, "application")
        assert hasattr(config, "integrations")
        assert hasattr(config, "aws")

    def test_database_config_complete(self):
        """Database config has all expected fields."""
        config = get_config()
        db = config.database

        assert isinstance(db.host, str)
        assert isinstance(db.port, int)
        assert isinstance(db.name, str)
        assert isinstance(db.user, str)
        assert isinstance(db.password, str)
        assert isinstance(db.pool.min_connections, int)
        assert isinstance(db.pool.max_connections, int)

    def test_api_config_complete(self):
        """API config has all expected fields."""
        config = get_config()
        api = config.application.api

        assert isinstance(api.host, str)
        assert isinstance(api.port, int)
        assert isinstance(api.cors_origins, str)

    def test_auth_config_complete(self):
        """Auth config has all expected fields."""
        config = get_config()
        auth = config.application.auth

        assert isinstance(auth.jwt_secret, str)
        assert isinstance(auth.jwt_algorithm, str)
        assert isinstance(auth.access_token_expiry_minutes, int)
        assert isinstance(auth.refresh_token_expiry_days, int)
        assert isinstance(auth.bcrypt_rounds, int)
        assert isinstance(auth.min_password_length, int)
