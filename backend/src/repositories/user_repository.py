"""
User repository for database operations.

Handles CRUD operations for the users table.

Usage:
    from src.repositories.user_repository import UserRepository
    from src.services import services

    repo = UserRepository(services.aurora)
    user = await repo.get_by_email("user@example.com")
"""

from datetime import datetime, timezone
from typing import Optional
from uuid import UUID

from src.domain.auth import User
from src.services.aurora_service import AuroraService
from src.utils.logging import get_logger

logger = get_logger(__name__)


class UserRepository:
    """
    Repository for user database operations.

    All methods use async database access via AuroraService.
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

    async def get_by_id(self, user_id: UUID) -> Optional[User]:
        """
        Get user by ID.

        Args:
            user_id: User UUID

        Returns:
            User if found, None otherwise
        """
        row = await self._aurora.fetch_one(
            """
            SELECT id, email, password_hash, name, avatar_url,
                   email_verified, created_at, updated_at, deleted_at
            FROM users
            WHERE id = $1 AND deleted_at IS NULL
            """,
            user_id,
        )
        return self._row_to_user(row) if row else None

    async def get_by_email(self, email: str) -> Optional[User]:
        """
        Get user by email address.

        Args:
            email: User email (case-insensitive)

        Returns:
            User if found, None otherwise
        """
        row = await self._aurora.fetch_one(
            """
            SELECT id, email, password_hash, name, avatar_url,
                   email_verified, created_at, updated_at, deleted_at
            FROM users
            WHERE LOWER(email) = LOWER($1) AND deleted_at IS NULL
            """,
            email,
        )
        return self._row_to_user(row) if row else None

    async def email_exists(self, email: str) -> bool:
        """
        Check if email is already registered.

        Args:
            email: Email to check (case-insensitive)

        Returns:
            True if email exists
        """
        row = await self._aurora.fetch_one(
            """
            SELECT 1 FROM users
            WHERE LOWER(email) = LOWER($1) AND deleted_at IS NULL
            """,
            email,
        )
        return row is not None

    # =========================================================================
    # WRITE OPERATIONS
    # =========================================================================

    async def create(
        self,
        email: str,
        name: str,
        password_hash: Optional[str] = None,
        email_verified: bool = False,
    ) -> User:
        """
        Create a new user.

        Args:
            email: User email (must be unique)
            name: Display name
            password_hash: Bcrypt hash of password (optional for OAuth)
            email_verified: Whether email is verified

        Returns:
            Created User with generated ID

        Raises:
            ConflictError: If email already exists
        """
        row = await self._aurora.fetch_one(
            """
            INSERT INTO users (email, password_hash, name, email_verified)
            VALUES ($1, $2, $3, $4)
            RETURNING id, email, password_hash, name, avatar_url,
                      email_verified, created_at, updated_at, deleted_at
            """,
            email,
            password_hash,
            name,
            email_verified,
        )

        user = self._row_to_user(row)
        logger.info("user_created", user_id=str(user.id), email=email)
        return user

    async def update_password(self, user_id: UUID, password_hash: str) -> bool:
        """
        Update user's password hash.

        Args:
            user_id: User UUID
            password_hash: New bcrypt password hash

        Returns:
            True if updated, False if user not found
        """
        result = await self._aurora.execute(
            """
            UPDATE users
            SET password_hash = $1, updated_at = $2
            WHERE id = $3 AND deleted_at IS NULL
            """,
            password_hash,
            datetime.now(timezone.utc),
            user_id,
        )
        updated = result == "UPDATE 1"
        if updated:
            logger.info("password_updated", user_id=str(user_id))
        return updated

    async def verify_email(self, user_id: UUID) -> bool:
        """
        Mark user's email as verified.

        Args:
            user_id: User UUID

        Returns:
            True if updated, False if user not found
        """
        result = await self._aurora.execute(
            """
            UPDATE users
            SET email_verified = true, updated_at = $1
            WHERE id = $2 AND deleted_at IS NULL
            """,
            datetime.now(timezone.utc),
            user_id,
        )
        updated = result == "UPDATE 1"
        if updated:
            logger.info("email_verified", user_id=str(user_id))
        return updated

    async def update_profile(
        self,
        user_id: UUID,
        name: Optional[str] = None,
        avatar_url: Optional[str] = None,
    ) -> Optional[User]:
        """
        Update user profile fields.

        Args:
            user_id: User UUID
            name: New display name (optional)
            avatar_url: New avatar URL (optional)

        Returns:
            Updated User if found, None otherwise
        """
        # Build dynamic update
        updates = []
        params = []
        param_num = 1

        if name is not None:
            updates.append(f"name = ${param_num}")
            params.append(name)
            param_num += 1

        if avatar_url is not None:
            updates.append(f"avatar_url = ${param_num}")
            params.append(avatar_url)
            param_num += 1

        if not updates:
            return await self.get_by_id(user_id)

        updates.append(f"updated_at = ${param_num}")
        params.append(datetime.now(timezone.utc))
        param_num += 1

        params.append(user_id)

        row = await self._aurora.fetch_one(
            f"""
            UPDATE users
            SET {", ".join(updates)}
            WHERE id = ${param_num} AND deleted_at IS NULL
            RETURNING id, email, password_hash, name, avatar_url,
                      email_verified, created_at, updated_at, deleted_at
            """,
            *params,
        )

        if row:
            logger.info("user_profile_updated", user_id=str(user_id))
        return self._row_to_user(row) if row else None

    async def soft_delete(self, user_id: UUID) -> bool:
        """
        Soft delete a user.

        Args:
            user_id: User UUID

        Returns:
            True if deleted, False if user not found
        """
        result = await self._aurora.execute(
            """
            UPDATE users
            SET deleted_at = $1, updated_at = $1
            WHERE id = $2 AND deleted_at IS NULL
            """,
            datetime.now(timezone.utc),
            user_id,
        )
        deleted = result == "UPDATE 1"
        if deleted:
            logger.info("user_deleted", user_id=str(user_id))
        return deleted

    # =========================================================================
    # HELPERS
    # =========================================================================

    @staticmethod
    def _row_to_user(row) -> Optional[User]:
        """
        Convert database row to User domain object.

        Args:
            row: asyncpg Record

        Returns:
            User instance or None
        """
        if row is None:
            return None

        return User(
            id=row["id"],
            email=row["email"],
            password_hash=row["password_hash"],
            name=row["name"],
            avatar_url=row["avatar_url"],
            email_verified=row["email_verified"],
            created_at=row["created_at"],
            updated_at=row["updated_at"],
            deleted_at=row["deleted_at"],
        )
