"""
Authentication API schemas.

Pydantic models for auth request/response validation.

Usage:
    from src.api.schemas.auth import RegisterRequest, LoginResponse
"""

from datetime import datetime
from typing import Optional
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field, field_validator


# =============================================================================
# REQUEST SCHEMAS
# =============================================================================


class RegisterRequest(BaseModel):
    """Request schema for user registration."""

    email: EmailStr = Field(
        ...,
        description="User email address",
        examples=["user@example.com"],
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Password (min 8 chars, mixed case, number)",
        examples=["MyPassword123"],
    )
    name: str = Field(
        ...,
        min_length=1,
        max_length=255,
        description="Display name",
        examples=["Jane Smith"],
    )


class LoginRequest(BaseModel):
    """Request schema for email/password login."""

    email: EmailStr = Field(
        ...,
        description="User email address",
        examples=["user@example.com"],
    )
    password: str = Field(
        ...,
        description="User password",
        examples=["MyPassword123"],
    )


class RefreshRequest(BaseModel):
    """Request schema for token refresh."""

    # Refresh token comes from httpOnly cookie, not body
    # This schema is here for documentation purposes
    pass


class ForgotPasswordRequest(BaseModel):
    """Request schema for password reset request."""

    email: EmailStr = Field(
        ...,
        description="Email address to send reset link to",
        examples=["user@example.com"],
    )


class ResetPasswordRequest(BaseModel):
    """Request schema for password reset completion."""

    email: EmailStr = Field(
        ...,
        description="User email address",
        examples=["user@example.com"],
    )
    token: str = Field(
        ...,
        description="Password reset token from email",
    )
    new_password: str = Field(
        ...,
        min_length=8,
        description="New password (min 8 chars, mixed case, number)",
        examples=["NewPassword456"],
    )


# =============================================================================
# RESPONSE SCHEMAS
# =============================================================================


class UserResponse(BaseModel):
    """User data in responses."""

    id: UUID = Field(..., description="User UUID")
    email: str = Field(..., description="User email")
    name: str = Field(..., description="Display name")
    avatar_url: Optional[str] = Field(None, description="Profile picture URL")
    email_verified: bool = Field(..., description="Email verified status")
    created_at: datetime = Field(..., description="Account creation time")

    model_config = {"from_attributes": True}


class AuthResponse(BaseModel):
    """Response schema for successful authentication."""

    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry in seconds")
    user: UserResponse = Field(..., description="Authenticated user info")


class TokenResponse(BaseModel):
    """Response schema for token refresh."""

    access_token: str = Field(..., description="New JWT access token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(..., description="Token expiry in seconds")


class MessageResponse(BaseModel):
    """Generic message response."""

    message: str = Field(..., description="Response message")


class ErrorResponse(BaseModel):
    """Error response schema."""

    error: str = Field(..., description="Error code")
    message: str = Field(..., description="Error message")
    details: Optional[dict] = Field(None, description="Additional error details")
    correlation_id: Optional[str] = Field(None, description="Request correlation ID")


# =============================================================================
# OAUTH SCHEMAS
# =============================================================================


class OAuthStartResponse(BaseModel):
    """Response when starting OAuth flow."""

    authorization_url: str = Field(..., description="URL to redirect user to")
    state: str = Field(..., description="OAuth state parameter")


class OAuthCallbackRequest(BaseModel):
    """Request schema for OAuth callback."""

    code: str = Field(..., description="Authorization code from provider")
    state: str = Field(..., description="OAuth state parameter")


# =============================================================================
# CURRENT USER SCHEMAS
# =============================================================================


class CurrentUserResponse(BaseModel):
    """Response schema for /auth/me endpoint."""

    id: UUID = Field(..., description="User UUID")
    email: str = Field(..., description="User email")
    name: str = Field(..., description="Display name")
    avatar_url: Optional[str] = Field(None, description="Profile picture URL")
    email_verified: bool = Field(..., description="Email verified status")
    org_id: Optional[UUID] = Field(None, description="Current organization ID")
    org_role: Optional[str] = Field(None, description="Role in current organization")


class UpdateProfileRequest(BaseModel):
    """Request schema for profile updates."""

    name: Optional[str] = Field(
        None,
        min_length=1,
        max_length=255,
        description="New display name",
    )
    avatar_url: Optional[str] = Field(
        None,
        max_length=500,
        description="New avatar URL",
    )
