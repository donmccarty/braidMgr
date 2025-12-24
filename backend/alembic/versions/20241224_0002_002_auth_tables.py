"""Authentication tables for braidMgr

Revision ID: 002
Revises: 001
Create Date: 2024-12-24

Creates authentication-related tables:
- refresh_tokens: JWT refresh token storage
- password_reset_tokens: Password reset token storage
- oauth_accounts: OAuth provider account links
- login_attempts: Failed login tracking for rate limiting
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision: str = "002"
down_revision: Union[str, None] = "001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================================================
    # REFRESH TOKENS TABLE
    # =========================================================================
    # Stores refresh tokens with hashed values for secure session management.
    # Each token is linked to a user and can be revoked individually.
    op.create_table(
        "refresh_tokens",
        # Primary key - auto-generated UUID
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # Foreign key to users table - cascade delete when user is deleted
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Bcrypt hash of the refresh token value (never store plain tokens)
        sa.Column("token_hash", sa.String(255), nullable=False),
        # Token expiration timestamp
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        # Revocation timestamp - NULL if token is still valid
        sa.Column("revoked_at", sa.DateTime(timezone=True), nullable=True),
        # Creation timestamp
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
        # Client user agent for security tracking
        sa.Column("user_agent", sa.String(500), nullable=True),
        # Client IP address for security tracking (IPv4 or IPv6)
        sa.Column("ip_address", sa.String(45), nullable=True),
    )
    # Index for finding tokens by user
    op.create_index("idx_refresh_tokens_user_id", "refresh_tokens", ["user_id"])
    # Index for cleanup of expired tokens
    op.create_index("idx_refresh_tokens_expires_at", "refresh_tokens", ["expires_at"])

    # =========================================================================
    # PASSWORD RESET TOKENS TABLE
    # =========================================================================
    # Stores password reset tokens with hashed values.
    # Each token can only be used once and expires after 1 hour.
    op.create_table(
        "password_reset_tokens",
        # Primary key - auto-generated UUID
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # Foreign key to users table - cascade delete when user is deleted
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # Bcrypt hash of the reset token value
        sa.Column("token_hash", sa.String(255), nullable=False),
        # Token expiration timestamp (typically 1 hour)
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        # Usage timestamp - NULL if not yet used, set when password is reset
        sa.Column("used_at", sa.DateTime(timezone=True), nullable=True),
        # Creation timestamp
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    # Index for finding tokens by user
    op.create_index(
        "idx_password_reset_tokens_user_id", "password_reset_tokens", ["user_id"]
    )

    # =========================================================================
    # OAUTH ACCOUNTS TABLE
    # =========================================================================
    # Links users to external OAuth provider accounts (Google, Microsoft).
    # A user can have multiple OAuth providers linked.
    op.create_table(
        "oauth_accounts",
        # Primary key - auto-generated UUID
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # Foreign key to users table - cascade delete when user is deleted
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
        ),
        # OAuth provider name: 'google' or 'microsoft'
        sa.Column("provider", sa.String(50), nullable=False),
        # User ID from the OAuth provider (unique per provider)
        sa.Column("provider_user_id", sa.String(255), nullable=False),
        # Email address from the OAuth provider
        sa.Column("email", sa.String(255), nullable=True),
        # Creation timestamp
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    # Index for finding OAuth accounts by user
    op.create_index("idx_oauth_accounts_user_id", "oauth_accounts", ["user_id"])
    # Unique constraint: one account per provider per user
    op.create_unique_constraint(
        "uq_oauth_provider_user",
        "oauth_accounts",
        ["provider", "provider_user_id"],
    )

    # =========================================================================
    # LOGIN ATTEMPTS TABLE
    # =========================================================================
    # Tracks login attempts for rate limiting and security.
    # Failed attempts are counted to trigger account lockout.
    op.create_table(
        "login_attempts",
        # Primary key - auto-generated UUID
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            server_default=sa.text("gen_random_uuid()"),
        ),
        # Email address attempted (not a foreign key - may not exist)
        sa.Column("email", sa.String(255), nullable=False),
        # Whether the login attempt succeeded
        sa.Column("success", sa.Boolean, nullable=False),
        # Client IP address for distributed attack detection
        sa.Column("ip_address", sa.String(45), nullable=True),
        # Client user agent for bot detection
        sa.Column("user_agent", sa.String(500), nullable=True),
        # Attempt timestamp
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("now()"),
        ),
    )
    # Index for counting failed attempts by email
    op.create_index("idx_login_attempts_email", "login_attempts", ["email"])
    # Index for cleanup of old attempts
    op.create_index("idx_login_attempts_created_at", "login_attempts", ["created_at"])


def downgrade() -> None:
    # Drop tables in reverse order
    op.drop_table("login_attempts")
    op.drop_table("oauth_accounts")
    op.drop_table("password_reset_tokens")
    op.drop_table("refresh_tokens")
