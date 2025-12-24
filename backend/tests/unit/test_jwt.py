"""
Unit tests for src/utils/jwt.py

Tests JWT token creation and validation:
- Access token creation with claims
- Token decoding and validation
- Token expiry handling
- Error handling for invalid tokens
"""

import pytest
from datetime import datetime, timedelta, timezone
from unittest.mock import patch, MagicMock
from jose import jwt

from src.utils.jwt import (
    create_access_token,
    decode_access_token,
    get_token_expiry,
    is_token_expired,
    get_token_user_id,
)
from src.utils.exceptions import AuthenticationError


class TestCreateAccessToken:
    """Tests for access token creation."""

    def test_creates_valid_jwt(self):
        """Token is a valid JWT with three parts."""
        token = create_access_token(
            user_id="test-uuid",
            email="test@example.com",
            name="Test User",
        )
        parts = token.split(".")
        assert len(parts) == 3

    def test_includes_required_claims(self):
        """Token includes sub, email, name, exp, iat, jti claims."""
        token = create_access_token(
            user_id="test-uuid",
            email="test@example.com",
            name="Test User",
        )
        payload = decode_access_token(token)

        assert payload["sub"] == "test-uuid"
        assert payload["email"] == "test@example.com"
        assert payload["name"] == "Test User"
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload

    def test_includes_optional_org_claims(self):
        """Token includes org_id and org_role when provided."""
        token = create_access_token(
            user_id="test-uuid",
            email="test@example.com",
            name="Test User",
            org_id="org-uuid",
            org_role="admin",
        )
        payload = decode_access_token(token)

        assert payload["org_id"] == "org-uuid"
        assert payload["org_role"] == "admin"

    def test_excludes_org_claims_when_not_provided(self):
        """Token omits org_id and org_role when not provided."""
        token = create_access_token(
            user_id="test-uuid",
            email="test@example.com",
            name="Test User",
        )
        payload = decode_access_token(token)

        assert "org_id" not in payload
        assert "org_role" not in payload

    def test_custom_expiry_delta(self):
        """Token respects custom expiry delta."""
        custom_delta = timedelta(hours=2)
        token = create_access_token(
            user_id="test-uuid",
            email="test@example.com",
            name="Test User",
            expires_delta=custom_delta,
        )
        payload = decode_access_token(token)

        # Expiry should be approximately 2 hours from now
        exp_time = datetime.fromtimestamp(payload["exp"], tz=timezone.utc)
        expected = datetime.now(timezone.utc) + custom_delta
        assert abs((exp_time - expected).total_seconds()) < 5

    def test_unique_jti_per_token(self):
        """Each token has a unique jti claim."""
        token1 = create_access_token(
            user_id="test-uuid",
            email="test@example.com",
            name="Test User",
        )
        token2 = create_access_token(
            user_id="test-uuid",
            email="test@example.com",
            name="Test User",
        )

        payload1 = decode_access_token(token1)
        payload2 = decode_access_token(token2)

        assert payload1["jti"] != payload2["jti"]


class TestDecodeAccessToken:
    """Tests for access token decoding."""

    def test_decodes_valid_token(self):
        """Valid token is decoded successfully."""
        token = create_access_token(
            user_id="test-uuid",
            email="test@example.com",
            name="Test User",
        )
        payload = decode_access_token(token)

        assert isinstance(payload, dict)
        assert payload["sub"] == "test-uuid"

    def test_raises_on_expired_token(self):
        """Expired token raises AuthenticationError."""
        token = create_access_token(
            user_id="test-uuid",
            email="test@example.com",
            name="Test User",
            expires_delta=timedelta(seconds=-1),  # Already expired
        )

        with pytest.raises(AuthenticationError) as exc_info:
            decode_access_token(token)
        assert "expired" in str(exc_info.value).lower()

    def test_raises_on_invalid_signature(self):
        """Token with invalid signature raises AuthenticationError."""
        # Create a token with wrong secret
        payload = {
            "sub": "test-uuid",
            "email": "test@example.com",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(payload, "wrong-secret", algorithm="HS256")

        with pytest.raises(AuthenticationError):
            decode_access_token(token)

    def test_raises_on_malformed_token(self):
        """Malformed token raises AuthenticationError."""
        with pytest.raises(AuthenticationError):
            decode_access_token("not.a.valid.token")

    def test_raises_on_missing_required_claims(self):
        """Token missing required claims raises AuthenticationError."""
        from src.config import get_config
        config = get_config()
        secret = config.application.auth.jwt_secret

        # Create token without email claim
        payload = {
            "sub": "test-uuid",
            "exp": datetime.now(timezone.utc) + timedelta(hours=1),
        }
        token = jwt.encode(payload, secret, algorithm="HS256")

        with pytest.raises(AuthenticationError) as exc_info:
            decode_access_token(token)
        assert "email" in str(exc_info.value)


class TestGetTokenExpiry:
    """Tests for token expiry extraction."""

    def test_extracts_expiry_from_valid_token(self):
        """Extracts expiry datetime from valid token."""
        token = create_access_token(
            user_id="test-uuid",
            email="test@example.com",
            name="Test User",
        )
        expiry = get_token_expiry(token)

        assert isinstance(expiry, datetime)
        assert expiry > datetime.now(timezone.utc)

    def test_returns_none_for_invalid_token(self):
        """Returns None for malformed token."""
        expiry = get_token_expiry("invalid-token")
        assert expiry is None

    def test_returns_none_for_token_without_exp(self):
        """Returns None if token has no exp claim."""
        from src.config import get_config
        config = get_config()
        secret = config.application.auth.jwt_secret

        # Create token without exp claim
        payload = {"sub": "test"}
        token = jwt.encode(payload, secret, algorithm="HS256")

        expiry = get_token_expiry(token)
        assert expiry is None


class TestIsTokenExpired:
    """Tests for token expiry checking."""

    def test_valid_token_not_expired(self):
        """Valid token is not expired."""
        token = create_access_token(
            user_id="test-uuid",
            email="test@example.com",
            name="Test User",
        )
        assert is_token_expired(token) is False

    def test_expired_token_is_expired(self):
        """Expired token returns True."""
        token = create_access_token(
            user_id="test-uuid",
            email="test@example.com",
            name="Test User",
            expires_delta=timedelta(seconds=-1),
        )
        assert is_token_expired(token) is True

    def test_token_within_margin_is_expired(self):
        """Token expiring within margin is considered expired."""
        token = create_access_token(
            user_id="test-uuid",
            email="test@example.com",
            name="Test User",
            expires_delta=timedelta(seconds=30),
        )
        # With 60 second margin, token expiring in 30s is "expired"
        assert is_token_expired(token, margin_seconds=60) is True

    def test_invalid_token_is_expired(self):
        """Invalid token returns True (safe default)."""
        assert is_token_expired("invalid-token") is True


class TestGetTokenUserId:
    """Tests for extracting user ID from token."""

    def test_extracts_user_id(self):
        """Extracts user_id (sub claim) from valid token."""
        token = create_access_token(
            user_id="my-user-uuid",
            email="test@example.com",
            name="Test User",
        )
        user_id = get_token_user_id(token)
        assert user_id == "my-user-uuid"

    def test_returns_none_for_invalid_token(self):
        """Returns None for malformed token."""
        user_id = get_token_user_id("invalid-token")
        assert user_id is None

    def test_returns_none_for_token_without_sub(self):
        """Returns None if token has no sub claim."""
        from src.config import get_config
        config = get_config()
        secret = config.application.auth.jwt_secret

        payload = {"email": "test@example.com"}
        token = jwt.encode(payload, secret, algorithm="HS256")

        user_id = get_token_user_id(token)
        assert user_id is None
