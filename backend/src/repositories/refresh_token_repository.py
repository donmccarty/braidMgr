"""
Refresh token repository for database operations.

Handles CRUD operations for the refresh_tokens table.

Usage:
    from src.repositories.refresh_token_repository import RefreshTokenRepository
    from src.services import services

    repo = RefreshTokenRepository(services.aurora)
    token = await repo.create(user_id, token_hash, expires_at)
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from src.domain.auth import RefreshToken
from src.services.aurora_service import AuroraService
from src.utils.logging import get_logger

logger = get_logger(__name__)


class RefreshTokenRepository:
    """
    Repository for refresh token database operations.

    Refresh tokens are stored with hashed values for security.
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

    async def get_by_id(self, token_id: UUID) -> Optional[RefreshToken]:
        """
        Get refresh token by ID.

        Args:
            token_id: Token UUID

        Returns:
            RefreshToken if found, None otherwise
        """
        row = await self._aurora.fetch_one(
            """
            SELECT id, user_id, token_hash, expires_at, revoked_at,
                   created_at, user_agent, ip_address
            FROM refresh_tokens
            WHERE id = $1
            """,
            token_id,
        )
        return self._row_to_token(row) if row else None

    async def get_valid_tokens_for_user(self, user_id: UUID) -> list[RefreshToken]:
        """
        Get all valid (non-expired, non-revoked) tokens for a user.

        Args:
            user_id: User UUID

        Returns:
            List of valid RefreshToken objects
        """
        rows = await self._aurora.fetch_all(
            """
            SELECT id, user_id, token_hash, expires_at, revoked_at,
                   created_at, user_agent, ip_address
            FROM refresh_tokens
            WHERE user_id = $1
              AND revoked_at IS NULL
              AND expires_at > $2
            ORDER BY created_at DESC
            """,
            user_id,
            datetime.now(timezone.utc),
        )
        return [self._row_to_token(row) for row in rows]

    # =========================================================================
    # WRITE OPERATIONS
    # =========================================================================

    async def create(
        self,
        user_id: UUID,
        token_hash: str,
        expires_at: datetime,
        user_agent: Optional[str] = None,
        ip_address: Optional[str] = None,
    ) -> RefreshToken:
        """
        Create a new refresh token.

        Args:
            user_id: User UUID
            token_hash: Bcrypt hash of token value
            expires_at: Token expiry timestamp
            user_agent: Client user agent string
            ip_address: Client IP address

        Returns:
            Created RefreshToken
        """
        row = await self._aurora.fetch_one(
            """
            INSERT INTO refresh_tokens (user_id, token_hash, expires_at, user_agent, ip_address)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id, user_id, token_hash, expires_at, revoked_at,
                      created_at, user_agent, ip_address
            """,
            user_id,
            token_hash,
            expires_at,
            user_agent,
            ip_address,
        )

        token = self._row_to_token(row)
        logger.debug("refresh_token_created", user_id=str(user_id))
        return token

    async def revoke(self, token_id: UUID) -> bool:
        """
        Revoke a refresh token.

        Args:
            token_id: Token UUID

        Returns:
            True if revoked, False if not found
        """
        result = await self._aurora.execute(
            """
            UPDATE refresh_tokens
            SET revoked_at = $1
            WHERE id = $2 AND revoked_at IS NULL
            """,
            datetime.now(timezone.utc),
            token_id,
        )
        revoked = result == "UPDATE 1"
        if revoked:
            logger.debug("refresh_token_revoked", token_id=str(token_id))
        return revoked

    async def revoke_all_for_user(self, user_id: UUID) -> int:
        """
        Revoke all refresh tokens for a user.

        Used when password is changed or security event occurs.

        Args:
            user_id: User UUID

        Returns:
            Number of tokens revoked
        """
        result = await self._aurora.execute(
            """
            UPDATE refresh_tokens
            SET revoked_at = $1
            WHERE user_id = $2 AND revoked_at IS NULL
            """,
            datetime.now(timezone.utc),
            user_id,
        )
        # Parse "UPDATE N" to get count
        count = int(result.split()[1]) if result.startswith("UPDATE") else 0
        if count > 0:
            logger.info(
                "refresh_tokens_revoked_all",
                user_id=str(user_id),
                count=count,
            )
        return count

    async def cleanup_expired(self, older_than_days: int = 30) -> int:
        """
        Delete expired tokens older than specified days.

        Housekeeping to keep table size manageable.

        Args:
            older_than_days: Delete tokens expired more than this many days ago

        Returns:
            Number of tokens deleted
        """
        cutoff = datetime.now(timezone.utc)
        from datetime import timedelta

        cutoff = cutoff - timedelta(days=older_than_days)

        result = await self._aurora.execute(
            """
            DELETE FROM refresh_tokens
            WHERE expires_at < $1
            """,
            cutoff,
        )
        count = int(result.split()[1]) if result.startswith("DELETE") else 0
        if count > 0:
            logger.info("refresh_tokens_cleaned", count=count)
        return count

    # =========================================================================
    # HELPERS
    # =========================================================================

    @staticmethod
    def _row_to_token(row) -> Optional[RefreshToken]:
        """
        Convert database row to RefreshToken domain object.

        Args:
            row: asyncpg Record

        Returns:
            RefreshToken instance or None
        """
        if row is None:
            return None

        return RefreshToken(
            id=row["id"],
            user_id=row["user_id"],
            token_hash=row["token_hash"],
            expires_at=row["expires_at"],
            revoked_at=row["revoked_at"],
            created_at=row["created_at"],
            user_agent=row["user_agent"],
            ip_address=row["ip_address"],
        )
