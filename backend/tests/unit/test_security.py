"""
Unit tests for src/utils/security.py

Tests password hashing, validation, and token generation:
- bcrypt password hashing
- Password verification
- Password strength validation
- Secure token generation
- Token hash verification
"""

import pytest
from unittest.mock import patch, MagicMock

from src.utils.security import (
    hash_password,
    verify_password,
    validate_password_strength,
    generate_secure_token,
    generate_token_hash,
    verify_token_hash,
    reset_pwd_context,
)


class TestPasswordHashing:
    """Tests for password hashing functions."""

    def setup_method(self):
        """Reset password context before each test."""
        reset_pwd_context()

    def test_hash_password_returns_bcrypt_hash(self):
        """hash_password returns a valid bcrypt hash."""
        hashed = hash_password("MyPassword123")
        # bcrypt hashes start with $2b$ (or $2a$ for older versions)
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    def test_hash_password_different_each_time(self):
        """Same password produces different hashes (salted)."""
        password = "MyPassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)
        assert hash1 != hash2

    def test_hash_password_handles_unicode(self):
        """Password with unicode characters is hashed correctly."""
        password = "MyPässwörd123"
        hashed = hash_password(password)
        assert verify_password(password, hashed)

    def test_hash_password_handles_empty_string(self):
        """Empty string is hashed (validation is separate)."""
        hashed = hash_password("")
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")


class TestPasswordVerification:
    """Tests for password verification."""

    def setup_method(self):
        """Reset password context before each test."""
        reset_pwd_context()

    def test_verify_password_correct(self):
        """Correct password verifies successfully."""
        password = "MyPassword123"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        """Incorrect password fails verification."""
        hashed = hash_password("CorrectPassword1")
        assert verify_password("WrongPassword1", hashed) is False

    def test_verify_password_case_sensitive(self):
        """Password verification is case-sensitive."""
        hashed = hash_password("MyPassword123")
        assert verify_password("mypassword123", hashed) is False

    def test_verify_password_invalid_hash_format(self):
        """Invalid hash format returns False (doesn't raise)."""
        assert verify_password("password", "not-a-valid-hash") is False

    def test_verify_password_empty_password(self):
        """Empty password against non-empty hash returns False."""
        hashed = hash_password("SomePassword1")
        assert verify_password("", hashed) is False


class TestPasswordStrengthValidation:
    """Tests for password strength validation."""

    def test_valid_password(self):
        """Password meeting all requirements passes."""
        is_valid, error = validate_password_strength("MyPassword123")
        assert is_valid is True
        assert error is None

    def test_password_too_short(self):
        """Password shorter than minimum length fails."""
        is_valid, error = validate_password_strength("Ab1")
        assert is_valid is False
        assert "8 characters" in error

    def test_password_no_uppercase(self):
        """Password without uppercase letter fails."""
        is_valid, error = validate_password_strength("mypassword123")
        assert is_valid is False
        assert "uppercase" in error.lower()

    def test_password_no_lowercase(self):
        """Password without lowercase letter fails."""
        is_valid, error = validate_password_strength("MYPASSWORD123")
        assert is_valid is False
        assert "lowercase" in error.lower()

    def test_password_no_digit(self):
        """Password without digit fails."""
        is_valid, error = validate_password_strength("MyPasswordABC")
        assert is_valid is False
        assert "digit" in error.lower()

    def test_password_exactly_min_length(self):
        """Password at exactly minimum length passes if other requirements met."""
        is_valid, error = validate_password_strength("AbCd1234")
        assert is_valid is True
        assert error is None

    def test_password_with_special_characters(self):
        """Password with special characters passes."""
        is_valid, error = validate_password_strength("MyP@ssword!123")
        assert is_valid is True
        assert error is None

    def test_password_with_unicode(self):
        """Password with unicode passes if requirements met."""
        is_valid, error = validate_password_strength("MyPässwörd123")
        assert is_valid is True
        assert error is None


class TestTokenGeneration:
    """Tests for secure token generation."""

    def test_generate_secure_token_length(self):
        """Token is 43 characters (32 bytes base64url encoded)."""
        token = generate_secure_token()
        assert len(token) == 43

    def test_generate_secure_token_unique(self):
        """Each token is unique."""
        tokens = [generate_secure_token() for _ in range(100)]
        assert len(set(tokens)) == 100

    def test_generate_secure_token_url_safe(self):
        """Token contains only URL-safe characters."""
        token = generate_secure_token()
        # URL-safe base64 uses alphanumeric, dash, underscore
        for char in token:
            assert char.isalnum() or char in "-_"


class TestTokenHashing:
    """Tests for token hash generation and verification."""

    def setup_method(self):
        """Reset password context before each test."""
        reset_pwd_context()

    def test_generate_token_hash_returns_bcrypt(self):
        """Token hash is valid bcrypt format."""
        token = generate_secure_token()
        hashed = generate_token_hash(token)
        assert hashed.startswith("$2b$") or hashed.startswith("$2a$")

    def test_verify_token_hash_correct(self):
        """Correct token verifies against its hash."""
        token = generate_secure_token()
        hashed = generate_token_hash(token)
        assert verify_token_hash(token, hashed) is True

    def test_verify_token_hash_incorrect(self):
        """Different token fails verification."""
        token1 = generate_secure_token()
        token2 = generate_secure_token()
        hashed = generate_token_hash(token1)
        assert verify_token_hash(token2, hashed) is False

    def test_verify_token_hash_invalid_format(self):
        """Invalid hash format returns False."""
        token = generate_secure_token()
        assert verify_token_hash(token, "not-a-valid-hash") is False


class TestResetPwdContext:
    """Tests for password context reset."""

    def test_reset_allows_reinitialize(self):
        """After reset, context is reinitialized on next use."""
        # First use creates context
        hash1 = hash_password("test")

        # Reset clears it
        reset_pwd_context()

        # Next use creates new context
        hash2 = hash_password("test")

        # Both should be valid bcrypt hashes
        assert hash1.startswith("$2b$") or hash1.startswith("$2a$")
        assert hash2.startswith("$2b$") or hash2.startswith("$2a$")
