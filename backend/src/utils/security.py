"""
Security utilities for braidMgr authentication.

Provides password hashing with bcrypt and secure token generation.

Usage:
    from src.utils.security import (
        hash_password,
        verify_password,
        generate_secure_token,
        validate_password_strength,
    )

    # Hash a password for storage
    hashed = hash_password("user_password")

    # Verify password on login
    is_valid = verify_password("user_password", hashed)

    # Generate secure random token for refresh/reset
    token = generate_secure_token()
"""

import re
import secrets
from typing import Optional, Tuple

from passlib.context import CryptContext

from src.config import get_config
from src.utils.logging import get_logger

logger = get_logger(__name__)

# =============================================================================
# PASSWORD HASHING
# =============================================================================
# Uses bcrypt via passlib for secure password hashing.
# Cost factor is configurable via auth.bcrypt_rounds (default 12).
# =============================================================================

# Passlib context for bcrypt - lazy initialization to allow config loading
_pwd_context: Optional[CryptContext] = None


def _get_pwd_context() -> CryptContext:
    """
    Get or create the password hashing context.

    Uses bcrypt with configurable rounds from auth config.
    Lazy initialization ensures config is loaded first.

    Returns:
        CryptContext configured for bcrypt
    """
    global _pwd_context
    if _pwd_context is None:
        config = get_config()
        rounds = config.application.auth.bcrypt_rounds
        _pwd_context = CryptContext(
            schemes=["bcrypt"],
            deprecated="auto",
            bcrypt__rounds=rounds,
        )
    return _pwd_context


def hash_password(password: str) -> str:
    """
    Hash a password using bcrypt.

    Args:
        password: Plain text password to hash

    Returns:
        Bcrypt hash string (includes salt and algorithm info)

    Example:
        >>> hashed = hash_password("mypassword123")
        >>> hashed.startswith("$2b$")
        True
    """
    context = _get_pwd_context()
    return context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against its hash.

    Uses constant-time comparison to prevent timing attacks.

    Args:
        plain_password: Password to verify
        hashed_password: Stored bcrypt hash

    Returns:
        True if password matches, False otherwise
    """
    context = _get_pwd_context()
    try:
        return context.verify(plain_password, hashed_password)
    except Exception as e:
        # Log but don't expose details - could be invalid hash format
        logger.warning("password_verification_error", error=str(e))
        return False


# =============================================================================
# PASSWORD VALIDATION
# =============================================================================
# Validates password strength requirements:
# - Minimum length (configurable, default 8)
# - At least one uppercase letter
# - At least one lowercase letter
# - At least one digit
# =============================================================================


def validate_password_strength(password: str) -> Tuple[bool, Optional[str]]:
    """
    Validate password meets strength requirements.

    Requirements:
        - Minimum length (from config, default 8)
        - At least one uppercase letter
        - At least one lowercase letter
        - At least one digit

    Args:
        password: Password to validate

    Returns:
        Tuple of (is_valid, error_message).
        If valid, error_message is None.
        If invalid, error_message describes the issue.

    Example:
        >>> is_valid, error = validate_password_strength("weak")
        >>> is_valid
        False
        >>> "8 characters" in error
        True
    """
    config = get_config()
    min_length = config.application.auth.min_password_length

    if len(password) < min_length:
        return False, f"Password must be at least {min_length} characters"

    if not re.search(r"[A-Z]", password):
        return False, "Password must contain at least one uppercase letter"

    if not re.search(r"[a-z]", password):
        return False, "Password must contain at least one lowercase letter"

    if not re.search(r"\d", password):
        return False, "Password must contain at least one digit"

    return True, None


# =============================================================================
# TOKEN GENERATION
# =============================================================================
# Secure random token generation for:
# - Refresh tokens (opaque, stored hashed)
# - Password reset tokens
# - Email verification tokens
# =============================================================================

# Token length in bytes (32 bytes = 256 bits)
TOKEN_BYTES = 32


def generate_secure_token() -> str:
    """
    Generate a cryptographically secure random token.

    Uses secrets.token_urlsafe for URL-safe base64 encoding.
    32 bytes provides 256 bits of entropy.

    Returns:
        URL-safe random string (43 characters)

    Example:
        >>> token = generate_secure_token()
        >>> len(token)
        43
    """
    return secrets.token_urlsafe(TOKEN_BYTES)


def generate_token_hash(token: str) -> str:
    """
    Hash a token for secure storage.

    Tokens should be hashed before storing in database.
    Uses bcrypt for consistency with password hashing.

    Args:
        token: Plain token to hash

    Returns:
        Bcrypt hash of the token
    """
    context = _get_pwd_context()
    return context.hash(token)


def verify_token_hash(token: str, token_hash: str) -> bool:
    """
    Verify a token against its stored hash.

    Args:
        token: Plain token to verify
        token_hash: Stored bcrypt hash

    Returns:
        True if token matches, False otherwise
    """
    context = _get_pwd_context()
    try:
        return context.verify(token, token_hash)
    except Exception as e:
        logger.warning("token_verification_error", error=str(e))
        return False


# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================


def reset_pwd_context() -> None:
    """
    Reset the password context (for testing).

    Allows tests to reinitialize with different config.
    """
    global _pwd_context
    _pwd_context = None
