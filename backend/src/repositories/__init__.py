"""
Repository layer for braidMgr.

Provides database access for domain entities.
All repositories require an AuroraService instance.

Usage:
    from src.repositories import UserRepository
    from src.services import services

    repo = UserRepository(services.aurora)
    user = await repo.get_by_email("user@example.com")
"""

from src.repositories.user_repository import UserRepository
from src.repositories.refresh_token_repository import RefreshTokenRepository
from src.repositories.password_reset_repository import PasswordResetRepository
from src.repositories.login_attempt_repository import LoginAttemptRepository
from src.repositories.oauth_account_repository import OAuthAccountRepository

__all__ = [
    "UserRepository",
    "RefreshTokenRepository",
    "PasswordResetRepository",
    "LoginAttemptRepository",
    "OAuthAccountRepository",
]
