"""Initial schema for braidMgr v1.5

Revision ID: 001
Revises:
Create Date: 2024-12-24

Creates all tables from DATA_MODEL.md for single-tenant v1.5:
- Enum types (item_type, indicator, org_role, project_role, chat_role)
- Core entities (users, organizations, projects, portfolios)
- Item entities (items, workstreams, notes, dependencies, attachments)
- Budget entities (rate_cards, budget_allocations, timesheet_entries)
- Access entities (user_org_memberships, user_project_roles)
- Chat entities (chat_sessions, chat_messages)
- System entities (audit_log)
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# Revision identifiers
revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # =========================================================================
    # ENUM TYPES
    # =========================================================================

    # Item type enum - the seven RAID+ item types
    op.execute("""
        CREATE TYPE item_type_enum AS ENUM (
            'Budget',
            'Risk',
            'Action Item',
            'Issue',
            'Decision',
            'Deliverable',
            'Plan Item'
        )
    """)

    # Indicator enum - calculated status indicators
    op.execute("""
        CREATE TYPE indicator_enum AS ENUM (
            'Beyond Deadline!!!',
            'Late Finish!!',
            'Late Start!!',
            'Trending Late!',
            'Finishing Soon!',
            'Starting Soon!',
            'In Progress',
            'Not Started',
            'Completed Recently',
            'Completed'
        )
    """)

    # Organization role enum
    op.execute("""
        CREATE TYPE org_role_enum AS ENUM (
            'owner',
            'admin',
            'member'
        )
    """)

    # Project role enum
    op.execute("""
        CREATE TYPE project_role_enum AS ENUM (
            'admin',
            'project_manager',
            'team_member',
            'viewer'
        )
    """)

    # Chat message role enum
    op.execute("""
        CREATE TYPE chat_role_enum AS ENUM (
            'user',
            'assistant',
            'system'
        )
    """)

    # =========================================================================
    # CORE ENTITIES
    # =========================================================================

    # Users table (central database in multi-tenant)
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("email", sa.String(255), nullable=False, unique=True),
        sa.Column("password_hash", sa.String(255), nullable=True),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("avatar_url", sa.String(500), nullable=True),
        sa.Column("email_verified", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_users_email", "users", ["email"])
    op.create_index("idx_users_deleted_at", "users", ["deleted_at"])

    # Organizations table (central database in multi-tenant)
    op.create_table(
        "organizations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("slug", sa.String(100), nullable=False, unique=True),
        sa.Column("settings", postgresql.JSONB, nullable=True, server_default="{}"),
        sa.Column("database_name", sa.String(100), nullable=True, unique=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_organizations_slug", "organizations", ["slug"])
    op.create_index("idx_organizations_deleted_at", "organizations", ["deleted_at"])

    # User-Organization membership (central database in multi-tenant)
    op.create_table(
        "user_org_memberships",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("org_role", postgresql.ENUM("owner", "admin", "member", name="org_role_enum", create_type=False), nullable=False, server_default="member"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_user_org_memberships_user_id", "user_org_memberships", ["user_id"])
    op.create_index("idx_user_org_memberships_org_id", "user_org_memberships", ["organization_id"])
    op.create_unique_constraint("uq_user_org_membership", "user_org_memberships", ["user_id", "organization_id"])

    # Projects table (per-org database in multi-tenant)
    op.create_table(
        "projects",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("client_name", sa.String(255), nullable=True),
        sa.Column("project_start", sa.Date, nullable=True),
        sa.Column("project_end", sa.Date, nullable=True),
        sa.Column("next_item_num", sa.Integer, nullable=False, server_default="1"),
        sa.Column("indicators_updated", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_projects_org_id", "projects", ["organization_id"])
    op.create_index("idx_projects_deleted_at", "projects", ["deleted_at"])

    # Portfolios table
    op.create_table(
        "portfolios",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_portfolios_org_id", "portfolios", ["organization_id"])

    # Portfolio-Project junction table (M:N)
    op.create_table(
        "portfolio_projects",
        sa.Column("portfolio_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("portfolios.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
    )

    # =========================================================================
    # ITEM ENTITIES
    # =========================================================================

    # Workstreams table
    op.create_table(
        "workstreams",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("sort_order", sa.Integer, nullable=False, server_default="0"),
    )
    op.create_index("idx_workstreams_project_id", "workstreams", ["project_id"])

    # Items table (RAID log entries)
    op.create_table(
        "items",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("item_num", sa.Integer, nullable=False),
        sa.Column("type", postgresql.ENUM("Budget", "Risk", "Action Item", "Issue", "Decision", "Deliverable", "Plan Item", name="item_type_enum", create_type=False), nullable=False),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("description", sa.Text, nullable=True),
        sa.Column("workstream_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workstreams.id", ondelete="SET NULL"), nullable=True),
        sa.Column("assigned_to", sa.String(255), nullable=True),
        sa.Column("start_date", sa.Date, nullable=True),
        sa.Column("finish_date", sa.Date, nullable=True),
        sa.Column("duration_days", sa.Integer, nullable=True),
        sa.Column("deadline", sa.Date, nullable=True),
        sa.Column("draft", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("client_visible", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("percent_complete", sa.Integer, nullable=False, server_default="0"),
        sa.Column("indicator", postgresql.ENUM("Beyond Deadline!!!", "Late Finish!!", "Late Start!!", "Trending Late!", "Finishing Soon!", "Starting Soon!", "In Progress", "Not Started", "Completed Recently", "Completed", name="indicator_enum", create_type=False), nullable=True),
        sa.Column("priority", sa.String(50), nullable=True),
        sa.Column("rpt_out", postgresql.ARRAY(sa.String(50)), nullable=True),
        sa.Column("budget_amount", sa.Numeric(12, 2), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index("idx_items_project_id", "items", ["project_id"])
    op.create_index("idx_items_item_num", "items", ["project_id", "item_num"])
    op.create_index("idx_items_type", "items", ["type"])
    op.create_index("idx_items_indicator", "items", ["indicator"])
    op.create_index("idx_items_assigned_to", "items", ["assigned_to"])
    op.create_index("idx_items_deleted_at", "items", ["deleted_at"])
    op.create_unique_constraint("uq_item_num_per_project", "items", ["project_id", "item_num"])

    # Item notes table
    op.create_table(
        "item_notes",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("note_date", sa.Date, nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("created_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_item_notes_item_id", "item_notes", ["item_id"])
    op.create_index("idx_item_notes_date", "item_notes", ["note_date"])

    # Item dependencies table (predecessor links)
    op.create_table(
        "item_dependencies",
        sa.Column("item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("items.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("depends_on_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("items.id", ondelete="CASCADE"), primary_key=True),
    )

    # Attachments table
    op.create_table(
        "attachments",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("item_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("items.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(255), nullable=False),
        sa.Column("content_type", sa.String(100), nullable=True),
        sa.Column("size_bytes", sa.Integer, nullable=True),
        sa.Column("s3_key", sa.String(500), nullable=False),
        sa.Column("uploaded_by", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_attachments_item_id", "attachments", ["item_id"])

    # =========================================================================
    # ACCESS ENTITIES
    # =========================================================================

    # User-Project roles table (RBAC)
    op.create_table(
        "user_project_roles",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", postgresql.ENUM("admin", "project_manager", "team_member", "viewer", name="project_role_enum", create_type=False), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_user_project_roles_user_id", "user_project_roles", ["user_id"])
    op.create_index("idx_user_project_roles_project_id", "user_project_roles", ["project_id"])
    op.create_unique_constraint("uq_user_project_role", "user_project_roles", ["user_id", "project_id"])

    # =========================================================================
    # BUDGET ENTITIES
    # =========================================================================

    # Rate cards table
    op.create_table(
        "rate_cards",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False),
        sa.Column("resource_name", sa.String(255), nullable=False),
        sa.Column("role", sa.String(100), nullable=True),
        sa.Column("geography", sa.String(100), nullable=True),
        sa.Column("hourly_rate", sa.Numeric(10, 2), nullable=False),
        sa.Column("effective_from", sa.Date, nullable=True),
        sa.Column("effective_to", sa.Date, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_rate_cards_org_id", "rate_cards", ["organization_id"])

    # Budget allocations table
    op.create_table(
        "budget_allocations",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("workstream_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workstreams.id", ondelete="SET NULL"), nullable=True),
        sa.Column("amount", sa.Numeric(12, 2), nullable=False),
        sa.Column("period_start", sa.Date, nullable=True),
        sa.Column("period_end", sa.Date, nullable=True),
        sa.Column("notes", sa.Text, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_budget_allocations_project_id", "budget_allocations", ["project_id"])

    # Timesheet entries table
    op.create_table(
        "timesheet_entries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=False),
        sa.Column("rate_card_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("rate_cards.id", ondelete="SET NULL"), nullable=True),
        sa.Column("week_ending", sa.Date, nullable=False),
        sa.Column("resource_name", sa.String(255), nullable=False),
        sa.Column("hours", sa.Numeric(6, 2), nullable=False),
        sa.Column("rate", sa.Numeric(10, 2), nullable=False),
        sa.Column("cost", sa.Numeric(12, 2), nullable=False),
        sa.Column("complete_week", sa.Boolean, nullable=False, server_default="false"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_timesheet_entries_project_id", "timesheet_entries", ["project_id"])
    op.create_index("idx_timesheet_entries_week_ending", "timesheet_entries", ["week_ending"])

    # =========================================================================
    # CHAT ENTITIES
    # =========================================================================

    # Chat sessions table
    op.create_table(
        "chat_sessions",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("project_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("projects.id", ondelete="CASCADE"), nullable=True),
        sa.Column("title", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_chat_sessions_user_id", "chat_sessions", ["user_id"])
    op.create_index("idx_chat_sessions_project_id", "chat_sessions", ["project_id"])

    # Chat messages table
    op.create_table(
        "chat_messages",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("session_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("chat_sessions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("role", postgresql.ENUM("user", "assistant", "system", name="chat_role_enum", create_type=False), nullable=False),
        sa.Column("content", sa.Text, nullable=False),
        sa.Column("context_refs", postgresql.JSONB, nullable=True),
        sa.Column("token_count", sa.Integer, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_chat_messages_session_id", "chat_messages", ["session_id"])

    # =========================================================================
    # SYSTEM ENTITIES
    # =========================================================================

    # Audit log table (immutable)
    op.create_table(
        "audit_log",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("action", sa.String(100), nullable=False),
        sa.Column("entity_type", sa.String(100), nullable=False),
        sa.Column("entity_id", postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column("before_state", postgresql.JSONB, nullable=True),
        sa.Column("after_state", postgresql.JSONB, nullable=True),
        sa.Column("correlation_id", sa.String(100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False, server_default=sa.text("now()")),
    )
    op.create_index("idx_audit_log_user_id", "audit_log", ["user_id"])
    op.create_index("idx_audit_log_entity", "audit_log", ["entity_type", "entity_id"])
    op.create_index("idx_audit_log_created_at", "audit_log", ["created_at"])
    op.create_index("idx_audit_log_correlation_id", "audit_log", ["correlation_id"])


def downgrade() -> None:
    # Drop tables in reverse order (respecting foreign keys)
    op.drop_table("audit_log")
    op.drop_table("chat_messages")
    op.drop_table("chat_sessions")
    op.drop_table("timesheet_entries")
    op.drop_table("budget_allocations")
    op.drop_table("rate_cards")
    op.drop_table("user_project_roles")
    op.drop_table("attachments")
    op.drop_table("item_dependencies")
    op.drop_table("item_notes")
    op.drop_table("items")
    op.drop_table("workstreams")
    op.drop_table("portfolio_projects")
    op.drop_table("portfolios")
    op.drop_table("projects")
    op.drop_table("user_org_memberships")
    op.drop_table("organizations")
    op.drop_table("users")

    # Drop enum types
    op.execute("DROP TYPE chat_role_enum")
    op.execute("DROP TYPE project_role_enum")
    op.execute("DROP TYPE org_role_enum")
    op.execute("DROP TYPE indicator_enum")
    op.execute("DROP TYPE item_type_enum")
