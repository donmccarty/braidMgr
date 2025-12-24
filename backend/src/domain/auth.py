"""
Authentication domain models for braidMgr.

Contains dataclasses representing authentication-related entities:
- User: Core user entity
- TokenPayload: JWT token claims
- RefreshToken: Refresh token entity
- PasswordResetToken: Password reset token entity
- LoginAttempt: Failed login tracking for rate limiting
- OAuthAccount: Linked OAuth provider accounts

Usage:
    from src.domain.auth import User, TokenPayload, OrgRole, ProjectRole
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import UUID


# =============================================================================
# ENUMS
# =============================================================================
# Role enums matching database enum types from migration 001.
# =============================================================================


class OrgRole(str, Enum):
    """
    Organization-level roles.

    Matches org_role_enum in PostgreSQL.
    """

    OWNER = "owner"  # Full control, billing, can delete org
    ADMIN = "admin"  # Manage users, projects, settings
    MEMBER = "member"  # Access assigned projects only


class ProjectRole(str, Enum):
    """
    Project-level roles.

    Matches project_role_enum in PostgreSQL.
    """

    ADMIN = "admin"  # Full project control, delete project
    PROJECT_MANAGER = "project_manager"  # Manage items, workstreams, budget
    TEAM_MEMBER = "team_member"  # Create/update items
    VIEWER = "viewer"  # Read-only access


# =============================================================================
# USER ENTITY
# =============================================================================


@dataclass
class User:
    """
    Core user entity.

    Represents a user account in the system.
    Maps to the 'users' table in PostgreSQL.

    Attributes:
        id: Unique user identifier
        email: User email (unique, used for login)
        name: Display name
        password_hash: Bcrypt hash of password (None for OAuth-only users)
        avatar_url: Profile picture URL
        email_verified: Whether email has been verified
        created_at: Account creation timestamp
        updated_at: Last update timestamp
        deleted_at: Soft delete timestamp (None if active)
    """

    id: UUID
    email: str
    name: str
    password_hash: Optional[str] = None
    avatar_url: Optional[str] = None
    email_verified: bool = False
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    deleted_at: Optional[datetime] = None

    @property
    def is_active(self) -> bool:
        """User is active (not soft-deleted)."""
        return self.deleted_at is None

    @property
    def has_password(self) -> bool:
        """User has a password set (vs OAuth-only)."""
        return self.password_hash is not None


# =============================================================================
# TOKEN ENTITIES
# =============================================================================


@dataclass
class TokenPayload:
    """
    JWT access token payload.

    Represents the claims embedded in a JWT access token.

    Attributes:
        sub: Subject (user ID)
        email: User email
        name: User display name
        org_id: Current organization ID
        org_role: Role in current organization
        exp: Token expiry timestamp
        iat: Token issued at timestamp
        jti: Unique token identifier
    """

    sub: str  # User ID
    email: str
    name: str
    exp: datetime
    iat: datetime
    jti: str
    org_id: Optional[str] = None
    org_role: Optional[str] = None

    @property
    def user_id(self) -> str:
        """Alias for sub claim."""
        return self.sub


@dataclass
class RefreshToken:
    """
    Refresh token entity.

    Stored in database with hashed token value.
    Used to issue new access tokens without re-authentication.

    Attributes:
        id: Token record ID
        user_id: Owner user ID
        token_hash: Bcrypt hash of token value
        expires_at: Expiry timestamp
        revoked_at: Revocation timestamp (None if active)
        created_at: Creation timestamp
        user_agent: Client user agent string
        ip_address: Client IP address
    """

    id: UUID
    user_id: UUID
    token_hash: str
    expires_at: datetime
    revoked_at: Optional[datetime] = None
    created_at: Optional[datetime] = None
    user_agent: Optional[str] = None
    ip_address: Optional[str] = None

    @property
    def is_valid(self) -> bool:
        """Token is not revoked and not expired."""
        if self.revoked_at is not None:
            return False
        return datetime.utcnow() < self.expires_at


@dataclass
class PasswordResetToken:
    """
    Password reset token entity.

    Stored in database with hashed token value.
    Sent via email to allow password reset.

    Attributes:
        id: Token record ID
        user_id: Target user ID
        token_hash: Bcrypt hash of token value
        expires_at: Expiry timestamp
        used_at: Usage timestamp (None if unused)
        created_at: Creation timestamp
    """

    id: UUID
    user_id: UUID
    token_hash: str
    expires_at: datetime
    used_at: Optional[datetime] = None
    created_at: Optional[datetime] = None

    @property
    def is_valid(self) -> bool:
        """Token is not used and not expired."""
        if self.used_at is not None:
            return False
        return datetime.utcnow() < self.expires_at


# =============================================================================
# LOGIN TRACKING
# =============================================================================


@dataclass
class LoginAttempt:
    """
    Login attempt record for rate limiting.

    Tracks failed login attempts to detect brute force attacks.

    Attributes:
        id: Record ID
        email: Attempted email address
        success: Whether login succeeded
        ip_address: Client IP address
        user_agent: Client user agent
        created_at: Attempt timestamp
    """

    id: UUID
    email: str
    success: bool
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    created_at: Optional[datetime] = None


# =============================================================================
# OAUTH ENTITIES
# =============================================================================


class OAuthProvider(str, Enum):
    """Supported OAuth providers."""

    GOOGLE = "google"
    MICROSOFT = "microsoft"


@dataclass
class OAuthAccount:
    """
    Linked OAuth provider account.

    Links a user to an external OAuth provider account.
    Allows login via Google, Microsoft, etc.

    Attributes:
        id: Record ID
        user_id: Linked user ID
        provider: OAuth provider name
        provider_user_id: User ID from provider
        email: Email from provider
        created_at: Link creation timestamp
    """

    id: UUID
    user_id: UUID
    provider: OAuthProvider
    provider_user_id: str
    email: Optional[str] = None
    created_at: Optional[datetime] = None


# =============================================================================
# AUTHENTICATION RESULTS
# =============================================================================


@dataclass
class AuthResult:
    """
    Result of an authentication attempt.

    Returned by authentication service after login/register.

    Attributes:
        success: Whether authentication succeeded
        user: Authenticated user (if success)
        access_token: JWT access token (if success)
        refresh_token: Opaque refresh token (if success)
        error: Error message (if failure)
    """

    success: bool
    user: Optional[User] = None
    access_token: Optional[str] = None
    refresh_token: Optional[str] = None
    error: Optional[str] = None


@dataclass
class CurrentUser:
    """
    Authenticated user context for request handling.

    Populated from JWT token by auth dependency.
    Available in route handlers via Depends(get_current_user).

    Attributes:
        id: User UUID
        email: User email
        name: User display name
        org_id: Current organization UUID (if any)
        org_role: Role in current organization (if any)
    """

    id: UUID
    email: str
    name: str
    org_id: Optional[UUID] = None
    org_role: Optional[OrgRole] = None

    @classmethod
    def from_token_payload(cls, payload: TokenPayload) -> "CurrentUser":
        """
        Create CurrentUser from JWT token payload.

        Args:
            payload: Decoded JWT payload

        Returns:
            CurrentUser instance
        """
        return cls(
            id=UUID(payload.sub),
            email=payload.email,
            name=payload.name,
            org_id=UUID(payload.org_id) if payload.org_id else None,
            org_role=OrgRole(payload.org_role) if payload.org_role else None,
        )
