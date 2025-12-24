"""
Domain models for braidMgr.

Contains dataclasses representing business entities.
"""

from src.domain.auth import (
    User,
    TokenPayload,
    RefreshToken,
    PasswordResetToken,
    LoginAttempt,
    OAuthAccount,
    OAuthProvider,
    OrgRole,
    ProjectRole,
    AuthResult,
    CurrentUser,
)

__all__ = [
    # Auth entities
    "User",
    "TokenPayload",
    "RefreshToken",
    "PasswordResetToken",
    "LoginAttempt",
    "OAuthAccount",
    "OAuthProvider",
    # Role enums
    "OrgRole",
    "ProjectRole",
    # Results
    "AuthResult",
    "CurrentUser",
]
