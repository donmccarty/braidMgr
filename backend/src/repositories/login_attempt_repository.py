"""
Login attempt repository for rate limiting.

Tracks failed login attempts to detect brute force attacks.

Usage:
    from src.repositories.login_attempt_repository import LoginAttemptRepository
    from src.services import services

    repo = LoginAttemptRepository(services.aurora)
    is_locked = await repo.is_locked_out("user@example.com")
"""

from datetime import datetime, timedelta, timezone
from typing import Optional
from uuid import UUID

from src.domain.auth import LoginAttempt
from src.services.aurora_service import AuroraService
from src.config import get_config
from src.utils.logging import get_logger

logger = get_logger(__name__)


class LoginAttemptRepository:
    """
    Repository for login attempt tracking.

    Used to implement rate limiting and lockout after failed attempts.
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

    async def count_recent_failed(
        self,
        email: str,
        window_minutes: int = 15,
    ) -> int:
        """
        Count failed login attempts in recent window.

        Args:
            email: Email address (case-insensitive)
            window_minutes: Time window in minutes

        Returns:
            Number of failed attempts in window
        """
        cutoff = datetime.now(timezone.utc) - timedelta(minutes=window_minutes)

        row = await self._aurora.fetch_one(
            """
            SELECT COUNT(*) as count
            FROM login_attempts
            WHERE LOWER(email) = LOWER($1)
              AND success = false
              AND created_at > $2
            """,
            email,
            cutoff,
        )
        return row["count"] if row else 0

    async def is_locked_out(self, email: str) -> bool:
        """
        Check if email is currently locked out due to failed attempts.

        Uses config values for max_login_attempts and lockout_duration_minutes.

        Args:
            email: Email address to check

        Returns:
            True if locked out, False otherwise
        """
        config = get_config()
        auth = config.application.auth

        count = await self.count_recent_failed(
            email,
            window_minutes=auth.lockout_duration_minutes,
        )
        return count >= auth.max_login_attempts

    async def get_lockout_remaining(self, email: str) -> Optional[int]:
        """
        Get remaining lockout time in seconds.

        Args:
            email: Email address

        Returns:
            Seconds remaining in lockout, or None if not locked out
        """
        if not await self.is_locked_out(email):
            return None

        config = get_config()
        auth = config.application.auth

        # Find oldest failed attempt in window
        cutoff = datetime.now(timezone.utc) - timedelta(
            minutes=auth.lockout_duration_minutes
        )

        row = await self._aurora.fetch_one(
            """
            SELECT MIN(created_at) as oldest
            FROM login_attempts
            WHERE LOWER(email) = LOWER($1)
              AND success = false
              AND created_at > $2
            """,
            email,
            cutoff,
        )

        if row and row["oldest"]:
            unlock_time = row["oldest"] + timedelta(
                minutes=auth.lockout_duration_minutes
            )
            remaining = (unlock_time - datetime.now(timezone.utc)).total_seconds()
            return max(0, int(remaining))

        return None

    # =========================================================================
    # WRITE OPERATIONS
    # =========================================================================

    async def record_attempt(
        self,
        email: str,
        success: bool,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
    ) -> LoginAttempt:
        """
        Record a login attempt.

        Args:
            email: Email address attempted
            success: Whether login succeeded
            ip_address: Client IP address
            user_agent: Client user agent

        Returns:
            Created LoginAttempt record
        """
        row = await self._aurora.fetch_one(
            """
            INSERT INTO login_attempts (email, success, ip_address, user_agent)
            VALUES ($1, $2, $3, $4)
            RETURNING id, email, success, ip_address, user_agent, created_at
            """,
            email,
            success,
            ip_address,
            user_agent,
        )

        attempt = self._row_to_attempt(row)

        if not success:
            count = await self.count_recent_failed(email)
            logger.warning(
                "login_attempt_failed",
                email=email,
                ip_address=ip_address,
                failed_count=count,
            )
        else:
            logger.info(
                "login_attempt_success",
                email=email,
                ip_address=ip_address,
            )

        return attempt

    async def cleanup_old(self, older_than_days: int = 30) -> int:
        """
        Delete old login attempts.

        Housekeeping to keep table size manageable.

        Args:
            older_than_days: Delete attempts older than this many days

        Returns:
            Number of records deleted
        """
        cutoff = datetime.now(timezone.utc) - timedelta(days=older_than_days)

        result = await self._aurora.execute(
            """
            DELETE FROM login_attempts
            WHERE created_at < $1
            """,
            cutoff,
        )
        count = int(result.split()[1]) if result.startswith("DELETE") else 0
        if count > 0:
            logger.info("login_attempts_cleaned", count=count)
        return count

    # =========================================================================
    # HELPERS
    # =========================================================================

    @staticmethod
    def _row_to_attempt(row) -> Optional[LoginAttempt]:
        """
        Convert database row to LoginAttempt domain object.

        Args:
            row: asyncpg Record

        Returns:
            LoginAttempt instance or None
        """
        if row is None:
            return None

        return LoginAttempt(
            id=row["id"],
            email=row["email"],
            success=row["success"],
            ip_address=row["ip_address"],
            user_agent=row["user_agent"],
            created_at=row["created_at"],
        )
