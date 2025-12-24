"""
Utility modules for braidMgr backend.

Exports:
    Exceptions: AppError, ValidationError, NotFoundError, etc.
    Logging: setup_logging, get_logger, sanitize_for_logging
    Security: hash_password, verify_password, validate_password_strength
    JWT: create_access_token, decode_access_token
"""

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
from src.utils.logging import setup_logging, get_logger, sanitize_for_logging
from src.utils.security import (
    hash_password,
    verify_password,
    validate_password_strength,
    generate_secure_token,
    generate_token_hash,
    verify_token_hash,
)
from src.utils.jwt import (
    create_access_token,
    decode_access_token,
    get_token_expiry,
    is_token_expired,
)

__all__ = [
    # Exceptions
    "AppError",
    "ValidationError",
    "AuthenticationError",
    "AuthorizationError",
    "NotFoundError",
    "ConflictError",
    "WorkflowError",
    "RateLimitError",
    "ConfigurationError",
    "DatabaseError",
    "ExternalServiceError",
    "ServiceUnavailableError",
    # Logging
    "setup_logging",
    "get_logger",
    "sanitize_for_logging",
    # Security
    "hash_password",
    "verify_password",
    "validate_password_strength",
    "generate_secure_token",
    "generate_token_hash",
    "verify_token_hash",
    # JWT
    "create_access_token",
    "decode_access_token",
    "get_token_expiry",
    "is_token_expired",
]
