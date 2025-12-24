"""
Password reset token repository for database operations.

Handles CRUD operations for the password_reset_tokens table.

Usage:
    from src.repositories.password_reset_repository import PasswordResetRepository
    from src.services import services

    repo = PasswordResetRepository(services.aurora)
    token = await repo.create(user_id, token_hash, expires_at)
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from src.domain.auth import PasswordResetToken
from src.services.aurora_service import AuroraService
from src.utils.logging import get_logger

logger = get_logger(__name__)


class PasswordResetRepository:
    """
    Repository for password reset token database operations.

    Reset tokens are stored with hashed values for security.
    Each token can only be used once.
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

    async def get_by_id(self, token_id: UUID) -> Optional[PasswordResetToken]:
        """
        Get password reset token by ID.

        Args:
            token_id: Token UUID

        Returns:
            PasswordResetToken if found, None otherwise
        """
        row = await self._aurora.fetch_one(
            """
            SELECT id, user_id, token_hash, expires_at, used_at, created_at
            FROM password_reset_tokens
            WHERE id = $1
            """,
            token_id,
        )
        return self._row_to_token(row) if row else None

    async def get_valid_for_user(self, user_id: UUID) -> Optional[PasswordResetToken]:
        """
        Get most recent valid (unused, non-expired) token for a user.

        Args:
            user_id: User UUID

        Returns:
            Most recent valid PasswordResetToken or None
        """
        row = await self._aurora.fetch_one(
            """
            SELECT id, user_id, token_hash, expires_at, used_at, created_at
            FROM password_reset_tokens
            WHERE user_id = $1
              AND used_at IS NULL
              AND expires_at > $2
            ORDER BY created_at DESC
            LIMIT 1
            """,
            user_id,
            datetime.now(timezone.utc),
        )
        return self._row_to_token(row) if row else None

    # =========================================================================
    # WRITE OPERATIONS
    # =========================================================================

    async def create(
        self,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
    ) -> PasswordResetToken:
        """
        Create a new password reset token.

        Args:
            user_id: User UUID
            token_hash: Bcrypt hash of token value
            expires_at: Token expiry timestamp

        Returns:
            Created PasswordResetToken
        """
        row = await self._aurora.fetch_one(
            """
            INSERT INTO password_reset_tokens (user_id, token_hash, expires_at)
            VALUES ($1, $2, $3)
            RETURNING id, user_id, token_hash, expires_at, used_at, created_at
            """,
            user_id,
            token_hash,
            expires_at,
        )

        token = self._row_to_token(row)
        logger.info("password_reset_token_created", user_id=str(user_id))
        return token

    async def mark_used(self, token_id: UUID) -> bool:
        """
        Mark a password reset token as used.

        Args:
            token_id: Token UUID

        Returns:
            True if marked, False if not found or already used
        """
        result = await self._aurora.execute(
            """
            UPDATE password_reset_tokens
            SET used_at = $1
            WHERE id = $2 AND used_at IS NULL
            """,
            datetime.now(timezone.utc),
            token_id,
        )
        marked = result == "UPDATE 1"
        if marked:
            logger.info("password_reset_token_used", token_id=str(token_id))
        return marked

    async def invalidate_all_for_user(self, user_id: UUID) -> int:
        """
        Invalidate all unused tokens for a user.

        Called when a new reset is requested or password is changed.

        Args:
            user_id: User UUID

        Returns:
            Number of tokens invalidated
        """
        result = await self._aurora.execute(
            """
            UPDATE password_reset_tokens
            SET used_at = $1
            WHERE user_id = $2 AND used_at IS NULL
            """,
            datetime.now(timezone.utc),
            user_id,
        )
        count = int(result.split()[1]) if result.startswith("UPDATE") else 0
        if count > 0:
            logger.debug(
                "password_reset_tokens_invalidated",
                user_id=str(user_id),
                count=count,
            )
        return count

    async def cleanup_expired(self, older_than_days: int = 7) -> int:
        """
        Delete expired tokens older than specified days.

        Housekeeping to keep table size manageable.

        Args:
            older_than_days: Delete tokens expired more than this many days ago

        Returns:
            Number of tokens deleted
        """
        from datetime import timedelta

        cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)

        result = await self._aurora.execute(
            """
            DELETE FROM password_reset_tokens
            WHERE expires_at < $1
            """,
            cutoff,
        )
        count = int(result.split()[1]) if result.startswith("DELETE") else 0
        if count > 0:
            logger.info("password_reset_tokens_cleaned", count=count)
        return count

    # =========================================================================
    # HELPERS
    # =========================================================================

    @staticmethod
    def _row_to_token(row) -> Optional[PasswordResetToken]:
        """
        Convert database row to PasswordResetToken domain object.

        Args:
            row: asyncpg Record

        Returns:
            PasswordResetToken instance or None
        """
        if row is None:
            return None

        return PasswordResetToken(
            id=row["id"],
            user_id=row["user_id"],
            token_hash=row["token_hash"],
            expires_at=row["expires_at"],
            used_at=row["used_at"],
            created_at=row["created_at"],
        )
