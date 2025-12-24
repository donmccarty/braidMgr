"""
Configuration settings loader for braidMgr.

Loads configuration from config.yaml with environment variable substitution.
Single source of truth for all application settings.

Usage:
    from src.config import get_config, AppConfig

    config = get_config()
    print(config.database.host)
"""

import os
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml


# =============================================================================
# CONFIG DATA CLASSES
# =============================================================================
# Each dataclass maps to a section in config.yaml.
# Nested structures use nested dataclasses.
# =============================================================================


@dataclass
class DatabasePoolConfig:
    """
    Connection pool settings for PostgreSQL.

    Attributes:
        min_connections: Minimum connections to keep open in pool
        max_connections: Maximum connections allowed in pool
        connection_timeout: Query timeout in seconds
    """

    min_connections: int = 2
    max_connections: int = 10
    connection_timeout: int = 30


@dataclass
class DatabaseConfig:
    """
    PostgreSQL/Aurora database connection configuration.

    Attributes:
        host: Database server hostname
        port: PostgreSQL port
        name: Database name
        user: Database username
        password: Database password
        pool: Connection pool settings
    """

    host: str = "localhost"
    port: int = 5432
    name: str = "braidmgr_dev"
    user: str = "postgres"
    password: str = "postgres"
    pool: DatabasePoolConfig = field(default_factory=DatabasePoolConfig)


@dataclass
class APIConfig:
    """
    REST API server configuration.

    Attributes:
        host: Bind address (0.0.0.0 for all interfaces)
        port: Server port
        cors_origins: Comma-separated CORS allowed origins
    """

    host: str = "0.0.0.0"
    port: int = 8000
    cors_origins: str = "http://localhost:5173,http://localhost:3000"


@dataclass
class GoogleOAuthConfig:
    """
    Google OAuth 2.0 configuration.

    Attributes:
        client_id: Google OAuth client ID
        client_secret: Google OAuth client secret
        redirect_uri: Callback URL for OAuth flow
    """

    client_id: str = ""
    client_secret: str = ""
    redirect_uri: str = "http://localhost:8000/auth/oauth/google/callback"


@dataclass
class MicrosoftOAuthConfig:
    """
    Microsoft Azure AD OAuth configuration.

    Attributes:
        client_id: Microsoft OAuth client ID
        client_secret: Microsoft OAuth client secret
        tenant_id: Azure AD tenant (use 'common' for multi-tenant)
        redirect_uri: Callback URL for OAuth flow
    """

    client_id: str = ""
    client_secret: str = ""
    tenant_id: str = "common"
    redirect_uri: str = "http://localhost:8000/auth/oauth/microsoft/callback"


@dataclass
class OAuthConfig:
    """
    OAuth providers configuration.

    Attributes:
        google: Google OAuth settings
        microsoft: Microsoft OAuth settings
    """

    google: GoogleOAuthConfig = field(default_factory=GoogleOAuthConfig)
    microsoft: MicrosoftOAuthConfig = field(default_factory=MicrosoftOAuthConfig)


@dataclass
class AuthConfig:
    """
    Authentication configuration including JWT, passwords, and OAuth.

    Attributes:
        jwt_secret: Secret key for JWT signing
        jwt_algorithm: JWT signing algorithm
        access_token_expiry_minutes: Access token expiry in minutes
        refresh_token_expiry_days: Refresh token expiry in days
        bcrypt_rounds: bcrypt cost factor for password hashing
        min_password_length: Minimum required password length
        reset_token_expiry_hours: Password reset token expiry
        max_login_attempts: Failed attempts before lockout
        lockout_duration_minutes: Lockout duration after max attempts
        oauth: OAuth provider settings
    """

    jwt_secret: str = "dev-secret-change-in-production"
    jwt_algorithm: str = "HS256"
    access_token_expiry_minutes: int = 15
    refresh_token_expiry_days: int = 7
    bcrypt_rounds: int = 12
    min_password_length: int = 8
    reset_token_expiry_hours: int = 1
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 30
    oauth: OAuthConfig = field(default_factory=OAuthConfig)


@dataclass
class LoggingConfig:
    """
    Logging configuration.

    Attributes:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format: Output format (json, console, auto)
    """

    level: str = "INFO"
    format: str = "auto"


@dataclass
class DebugConfig:
    """
    Debug settings for development.

    Attributes:
        enabled: Enable debug mode
        sql_echo: Echo SQL queries to console
    """

    enabled: bool = False
    sql_echo: bool = False


@dataclass
class ApplicationConfig:
    """
    Application settings container.

    Attributes:
        api: REST API configuration
        auth: Authentication settings
        logging: Logging configuration
        debug: Debug settings
    """

    api: APIConfig = field(default_factory=APIConfig)
    auth: AuthConfig = field(default_factory=AuthConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    debug: DebugConfig = field(default_factory=DebugConfig)


@dataclass
class AnthropicConfig:
    """
    Anthropic Claude AI configuration.

    Attributes:
        api_key: Anthropic API key
        model: Claude model ID
    """

    api_key: str = ""
    model: str = "claude-3-5-sonnet-20241022"


@dataclass
class EmailConfig:
    """
    Email delivery configuration.

    Attributes:
        provider: Email provider (ses, sendgrid, smtp)
        from_address: From address for emails
    """

    provider: str = "ses"
    from_address: str = "noreply@braidmgr.com"


@dataclass
class IntegrationsConfig:
    """
    External service integrations.

    Attributes:
        anthropic: Claude AI settings
        email: Email delivery settings
    """

    anthropic: AnthropicConfig = field(default_factory=AnthropicConfig)
    email: EmailConfig = field(default_factory=EmailConfig)


@dataclass
class S3Config:
    """
    AWS S3 document storage configuration.

    Attributes:
        bucket_documents: Bucket for file attachments
        presigned_url_expiry: Pre-signed URL expiry in seconds
    """

    bucket_documents: str = "braidmgr-documents-dev"
    presigned_url_expiry: int = 3600


@dataclass
class AWSConfig:
    """
    AWS services configuration.

    Attributes:
        region: AWS region
        s3: S3 storage settings
    """

    region: str = "us-east-1"
    s3: S3Config = field(default_factory=S3Config)


@dataclass
class AppConfig:
    """
    Complete application configuration.

    Loaded from config.yaml with environment variable substitution.
    Access via get_config() singleton.

    Attributes:
        environment: Environment name (development, staging, production)
        database: Database connection settings
        application: Application settings
        integrations: External service settings
        aws: AWS service settings
    """

    environment: str = "development"
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    application: ApplicationConfig = field(default_factory=ApplicationConfig)
    integrations: IntegrationsConfig = field(default_factory=IntegrationsConfig)
    aws: AWSConfig = field(default_factory=AWSConfig)


# =============================================================================
# CONFIG LOADING
# =============================================================================


def _substitute_env_vars(value: Any) -> Any:
    """
    Substitute environment variables in config values.

    Supports:
        ${VAR_NAME}          - Returns empty string if not set
        ${VAR_NAME:-default} - Returns default if not set

    Args:
        value: String value potentially containing ${VAR} references

    Returns:
        String with environment variables substituted
    """
    if not isinstance(value, str):
        return value

    # Pattern: ${VAR_NAME} or ${VAR_NAME:-default}
    pattern = r"\$\{([^}]+)\}"

    def replace(match: re.Match) -> str:
        expr = match.group(1)

        # Check for default value syntax: VAR_NAME:-default
        if ":-" in expr:
            var_name, default = expr.split(":-", 1)
            return os.environ.get(var_name.strip(), default)
        else:
            var_name = expr.strip()
            env_value = os.environ.get(var_name)
            if env_value is None:
                return ""
            return env_value

    return re.sub(pattern, replace, value)


def _substitute_dict(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recursively substitute environment variables in a dictionary.

    Args:
        data: Dictionary with potential ${VAR} values

    Returns:
        Dictionary with all environment variables substituted
    """
    result = {}
    for key, value in data.items():
        if isinstance(value, dict):
            result[key] = _substitute_dict(value)
        elif isinstance(value, list):
            result[key] = [
                _substitute_env_vars(item) if isinstance(item, str) else item
                for item in value
            ]
        else:
            result[key] = _substitute_env_vars(value)
    return result


def _dict_to_dataclass(data: Dict[str, Any], cls: type) -> Any:
    """
    Convert a dictionary to a dataclass, handling nested dataclasses.

    Args:
        data: Dictionary of configuration values
        cls: Target dataclass type

    Returns:
        Dataclass instance populated from dictionary
    """
    if not data:
        return cls()

    field_types = {f.name: f.type for f in cls.__dataclass_fields__.values()}
    kwargs = {}

    for key, value in data.items():
        if key not in field_types:
            continue

        field_type = field_types[key]

        # Handle nested dataclasses
        if hasattr(field_type, "__dataclass_fields__") and isinstance(value, dict):
            kwargs[key] = _dict_to_dataclass(value, field_type)
        # Handle type conversions from string
        elif field_type == int and isinstance(value, str):
            kwargs[key] = int(value) if value else 0
        elif field_type == float and isinstance(value, str):
            kwargs[key] = float(value) if value else 0.0
        elif field_type == bool and isinstance(value, str):
            kwargs[key] = value.lower() in ("true", "1", "yes")
        else:
            kwargs[key] = value

    return cls(**kwargs)


def load_config(config_path: Optional[Path] = None) -> AppConfig:
    """
    Load configuration from config.yaml.

    Args:
        config_path: Path to config.yaml. If None, searches:
            1. PROJECT_ROOT/config.yaml (backend/../config.yaml)
            2. Current working directory

    Returns:
        AppConfig with all settings loaded and env vars substituted

    Raises:
        FileNotFoundError: If config.yaml doesn't exist
        yaml.YAMLError: If config.yaml is invalid YAML
    """
    if config_path is None:
        # Look in project root (one level up from backend/src/config/)
        project_root = Path(__file__).parent.parent.parent.parent
        config_path = project_root / "config.yaml"

        # Fallback to current directory
        if not config_path.exists():
            config_path = Path.cwd() / "config.yaml"

    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")

    with open(config_path, "r") as f:
        raw_config = yaml.safe_load(f)

    # Substitute environment variables
    config_data = _substitute_dict(raw_config)

    # Build AppConfig from substituted data
    return _dict_to_dataclass(config_data, AppConfig)


# Singleton config instance
_config: Optional[AppConfig] = None


def get_config(reload: bool = False) -> AppConfig:
    """
    Get the application configuration (singleton).

    Config is loaded once and cached. Use reload=True to force reload.

    Args:
        reload: If True, reload config from disk

    Returns:
        AppConfig instance with all settings
    """
    global _config
    if _config is None or reload:
        _config = load_config()
    return _config
