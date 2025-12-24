"""
JWT token utilities for braidMgr authentication.

Provides JWT encoding and decoding with configurable expiry.

Usage:
    from src.utils.jwt import create_access_token, decode_access_token

    # Create access token
    token = create_access_token(
        user_id="uuid",
        email="user@example.com",
        name="Jane Smith",
        org_id="org-uuid",
        org_role="admin",
    )

    # Decode and validate token
    payload = decode_access_token(token)
"""

import uuid
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, Optional

from jose import JWTError, jwt

from src.config import get_config
from src.utils.exceptions import AuthenticationError
from src.utils.logging import get_logger

logger = get_logger(__name__)


# =============================================================================
# JWT TOKEN CREATION
# =============================================================================
# Creates signed JWT tokens with configurable expiry.
# Tokens include standard claims (sub, exp, iat, jti) plus custom claims.
# =============================================================================


def create_access_token(
    user_id: str,
    email: str,
    name: str,
    org_id: Optional[str] = None,
    org_role: Optional[str] = None,
    expires_delta: Optional[timedelta] = None,
) -> str:
    """
    Create a signed JWT access token.

    Token includes user identity and organization context.
    Expiry defaults to config access_token_expiry_minutes (15 min).

    Args:
        user_id: User UUID (becomes 'sub' claim)
        email: User email address
        name: User display name
        org_id: Current organization UUID (optional)
        org_role: Role in current organization (optional)
        expires_delta: Custom expiry duration (optional)

    Returns:
        Signed JWT string

    Example:
        >>> token = create_access_token(
        ...     user_id="abc-123",
        ...     email="user@example.com",
        ...     name="Jane",
        ... )
        >>> token.count(".")
        2
    """
    config = get_config()
    auth_config = config.application.auth

    # Calculate expiry
    if expires_delta is None:
        expires_delta = timedelta(minutes=auth_config.access_token_expiry_minutes)

    now = datetime.now(timezone.utc)
    expire = now + expires_delta

    # Build token payload
    payload: Dict[str, Any] = {
        "sub": user_id,
        "email": email,
        "name": name,
        "iat": now,
        "exp": expire,
        "jti": str(uuid.uuid4()),  # Unique token ID for revocation
    }

    # Add optional organization context
    if org_id:
        payload["org_id"] = org_id
    if org_role:
        payload["org_role"] = org_role

    # Sign token
    token = jwt.encode(
        payload,
        auth_config.jwt_secret,
        algorithm=auth_config.jwt_algorithm,
    )

    logger.debug(
        "access_token_created",
        user_id=user_id,
        expires_at=expire.isoformat(),
    )

    return token


def decode_access_token(token: str) -> Dict[str, Any]:
    """
    Decode and validate a JWT access token.

    Verifies signature and expiry. Raises AuthenticationError on failure.

    Args:
        token: JWT string to decode

    Returns:
        Token payload as dictionary with claims:
        - sub: User ID
        - email: User email
        - name: User name
        - org_id: Organization ID (if present)
        - org_role: Organization role (if present)
        - exp: Expiry timestamp
        - iat: Issued at timestamp
        - jti: Token ID

    Raises:
        AuthenticationError: If token is invalid, expired, or malformed
    """
    config = get_config()
    auth_config = config.application.auth

    try:
        payload = jwt.decode(
            token,
            auth_config.jwt_secret,
            algorithms=[auth_config.jwt_algorithm],
        )

        # Validate required claims
        required_claims = ["sub", "email", "exp"]
        for claim in required_claims:
            if claim not in payload:
                raise AuthenticationError(f"Token missing required claim: {claim}")

        return payload

    except jwt.ExpiredSignatureError:
        logger.debug("token_expired")
        raise AuthenticationError("Token has expired")

    except JWTError as e:
        logger.warning("token_decode_error", error=str(e))
        raise AuthenticationError("Invalid token")


# =============================================================================
# TOKEN UTILITIES
# =============================================================================


def get_token_expiry(token: str) -> Optional[datetime]:
    """
    Get expiry time from a token without full validation.

    Useful for checking if refresh is needed.
    Does NOT verify signature - use decode_access_token for that.

    Args:
        token: JWT string

    Returns:
        Expiry datetime or None if invalid/missing
    """
    try:
        config = get_config()
        auth_config = config.application.auth
        # Decode without verification to read claims
        # Still need algorithms param for python-jose
        payload = jwt.decode(
            token,
            auth_config.jwt_secret,
            algorithms=[auth_config.jwt_algorithm],
            options={"verify_signature": False, "verify_exp": False},
        )
        exp = payload.get("exp")
        if exp:
            return datetime.fromtimestamp(exp, tz=timezone.utc)
        return None
    except Exception:
        return None


def is_token_expired(token: str, margin_seconds: int = 0) -> bool:
    """
    Check if a token is expired or about to expire.

    Args:
        token: JWT string
        margin_seconds: Consider expired if within this many seconds

    Returns:
        True if expired or within margin of expiry
    """
    expiry = get_token_expiry(token)
    if expiry is None:
        return True

    threshold = datetime.now(timezone.utc) + timedelta(seconds=margin_seconds)
    return expiry <= threshold


def get_token_user_id(token: str) -> Optional[str]:
    """
    Extract user ID from token without full validation.

    Useful for logging/correlation. Does NOT verify signature.

    Args:
        token: JWT string

    Returns:
        User ID string or None if invalid
    """
    try:
        config = get_config()
        auth_config = config.application.auth
        # Decode without verification to read claims
        # Still need algorithms param for python-jose
        payload = jwt.decode(
            token,
            auth_config.jwt_secret,
            algorithms=[auth_config.jwt_algorithm],
            options={"verify_signature": False, "verify_exp": False},
        )
        return payload.get("sub")
    except Exception:
        return None
