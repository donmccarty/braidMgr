"""
OAuth account repository for database operations.

Handles CRUD operations for the oauth_accounts table.

Usage:
    from src.repositories.oauth_account_repository import OAuthAccountRepository
    from src.services import services

    repo = OAuthAccountRepository(services.aurora)
    account = await repo.get_by_provider("google", "provider_user_id")
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from src.domain.auth import OAuthAccount, OAuthProvider
from src.services.aurora_service import AuroraService
from src.utils.logging import get_logger

logger = get_logger(__name__)


class OAuthAccountRepository:
    """
    Repository for OAuth account database operations.

    Links users to external OAuth provider accounts.
    """

    def __init__(self, aurora: AuroraService):
        """
        Initialize repository with database service.

        Args:
            aurora: AuroraService instance for database access
        """
        self._aurora = aurora

    # =========================================================================
    # READ OPERATIONS
    # =========================================================================

    async def get_by_provider(
        self,
        provider: OAuthProvider,
        provider_user_id: str,
    ) -> Optional[OAuthAccount]:
        """
        Get OAuth account by provider and provider's user ID.

        Args:
            provider: OAuth provider (google, microsoft)
            provider_user_id: User ID from the provider

        Returns:
            OAuthAccount if found, None otherwise
        """
        row = await self._aurora.fetch_one(
            """
            SELECT id, user_id, provider, provider_user_id, email, created_at
            FROM oauth_accounts
            WHERE provider = $1 AND provider_user_id = $2
            """,
            provider.value,
            provider_user_id,
        )
        return self._row_to_account(row) if row else None

    async def get_for_user(self, user_id: UUID) -> list[OAuthAccount]:
        """
        Get all OAuth accounts linked to a user.

        Args:
            user_id: User UUID

        Returns:
            List of linked OAuthAccount objects
        """
        rows = await self._aurora.fetch_all(
            """
            SELECT id, user_id, provider, provider_user_id, email, created_at
            FROM oauth_accounts
            WHERE user_id = $1
            ORDER BY created_at
            """,
            user_id,
        )
        return [self._row_to_account(row) for row in rows]

    async def has_provider(self, user_id: UUID, provider: OAuthProvider) -> bool:
        """
        Check if user has a specific OAuth provider linked.

        Args:
            user_id: User UUID
            provider: OAuth provider to check

        Returns:
            True if provider is linked
        """
        row = await self._aurora.fetch_one(
            """
            SELECT 1 FROM oauth_accounts
            WHERE user_id = $1 AND provider = $2
            """,
            user_id,
            provider.value,
        )
        return row is not None

    # =========================================================================
    # WRITE OPERATIONS
    # =========================================================================

    async def create(
        self,
        user_id: UUID,
        provider: OAuthProvider,
        provider_user_id: str,
        email: Optional[str] = None,
    ) -> OAuthAccount:
        """
        Create a new OAuth account link.

        Args:
            user_id: User UUID to link to
            provider: OAuth provider
            provider_user_id: User ID from the provider
            email: Email from the provider

        Returns:
            Created OAuthAccount

        Raises:
            ConflictError: If provider account already linked
        """
        row = await self._aurora.fetch_one(
            """
            INSERT INTO oauth_accounts (user_id, provider, provider_user_id, email)
            VALUES ($1, $2, $3, $4)
            RETURNING id, user_id, provider, provider_user_id, email, created_at
            """,
            user_id,
            provider.value,
            provider_user_id,
            email,
        )

        account = self._row_to_account(row)
        logger.info(
            "oauth_account_linked",
            user_id=str(user_id),
            provider=provider.value,
        )
        return account

    async def delete(self, account_id: UUID) -> bool:
        """
        Delete an OAuth account link.

        Args:
            account_id: OAuth account UUID

        Returns:
            True if deleted, False if not found
        """
        result = await self._aurora.execute(
            """
            DELETE FROM oauth_accounts
            WHERE id = $1
            """,
            account_id,
        )
        deleted = result == "DELETE 1"
        if deleted:
            logger.info("oauth_account_unlinked", account_id=str(account_id))
        return deleted

    async def delete_for_user(self, user_id: UUID, provider: OAuthProvider) -> bool:
        """
        Delete OAuth link for a specific provider.

        Args:
            user_id: User UUID
            provider: OAuth provider to unlink

        Returns:
            True if deleted, False if not found
        """
        result = await self._aurora.execute(
            """
            DELETE FROM oauth_accounts
            WHERE user_id = $1 AND provider = $2
            """,
            user_id,
            provider.value,
        )
        deleted = result == "DELETE 1"
        if deleted:
            logger.info(
                "oauth_account_unlinked",
                user_id=str(user_id),
                provider=provider.value,
            )
        return deleted

    # =========================================================================
    # HELPERS
    # =========================================================================

    @staticmethod
    def _row_to_account(row) -> Optional[OAuthAccount]:
        """
        Convert database row to OAuthAccount domain object.

        Args:
            row: asyncpg Record

        Returns:
            OAuthAccount instance or None
        """
        if row is None:
            return None

        return OAuthAccount(
            id=row["id"],
            user_id=row["user_id"],
            provider=OAuthProvider(row["provider"]),
            provider_user_id=row["provider_user_id"],
            email=row["email"],
            created_at=row["created_at"],
        )
