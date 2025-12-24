# braidMgr Logical Data Model

*Last updated: 2024-12-24*

This document defines the logical data model for braidMgr v2 with multi-tenant, multi-user support.

**Key Concepts**:
- 18 entities across 5 domains
- Database-per-organization multi-tenancy
- PostgreSQL with full-text search
- Soft deletes for audit trail

---

## Child Documents

| Document | Entities | Description |
|----------|----------|-------------|
| [core-entities.md](data-model/core-entities.md) | Organization, User, User_Org_Membership, Project, Portfolio, Portfolio_Project | Multi-tenant foundation |
| [item-entities.md](data-model/item-entities.md) | Item, Workstream, Item_Note, Item_Dependency, Attachment | RAID log items |
| [budget-entities.md](data-model/budget-entities.md) | Rate_Card, Budget_Allocation, Timesheet_Entry | Financial tracking |
| [access-chat-entities.md](data-model/access-chat-entities.md) | User_Project_Role, Chat_Session, Chat_Message, Audit_Log | RBAC and AI chat |
| [enums-architecture.md](data-model/enums-architecture.md) | Enum definitions, DB architecture, v1 migration | Technical details |

---

## Entity Summary

| Entity | Domain | Description |
|--------|--------|-------------|
| Organization | Core | Tenant with isolated database |
| User | Core | Application user (central DB) |
| User_Org_Membership | Core | User-org relationship with role |
| Project | Core | RAID log project container |
| Portfolio | Core | Flexible project grouping |
| Portfolio_Project | Core | M:N portfolio-project junction |
| Item | Items | RAID log entry |
| Workstream | Items | Project work area |
| Item_Note | Items | Timestamped item notes |
| Item_Dependency | Items | Item predecessor links |
| Attachment | Items | S3-stored file reference |
| Rate_Card | Budget | Resource billing rates |
| Budget_Allocation | Budget | Planned budget amounts |
| Timesheet_Entry | Budget | Actual time/cost tracking |
| User_Project_Role | Access | Project-level RBAC |
| Chat_Session | Chat | AI conversation container |
| Chat_Message | Chat | Individual chat message |
| Audit_Log | System | Immutable change log |

---

## Entity Relationship Diagram

```mermaid
erDiagram
    ORGANIZATION ||--o{ USER_ORG_MEMBERSHIP : has
    ORGANIZATION ||--o{ PROJECT : contains
    ORGANIZATION ||--o{ PORTFOLIO : has

    USER ||--o{ USER_ORG_MEMBERSHIP : belongs_to
    USER ||--o{ USER_PROJECT_ROLE : has
    USER ||--o{ CHAT_SESSION : owns

    PORTFOLIO ||--o{ PORTFOLIO_PROJECT : contains
    PROJECT ||--o{ PORTFOLIO_PROJECT : belongs_to

    PROJECT ||--o{ ITEM : contains
    PROJECT ||--o{ WORKSTREAM : has
    PROJECT ||--o{ BUDGET_ALLOCATION : has
    PROJECT ||--o{ USER_PROJECT_ROLE : has

    ITEM ||--o{ ITEM_DEPENDENCY : has
    ITEM ||--o{ ITEM_NOTE : has
    ITEM ||--o{ ATTACHMENT : has

    BUDGET_ALLOCATION ||--o{ TIMESHEET_ENTRY : tracks
    RATE_CARD ||--o{ TIMESHEET_ENTRY : uses

    CHAT_SESSION ||--o{ CHAT_MESSAGE : contains

    USER {
        uuid id PK
        string email UK
        string password_hash
        string name
        string avatar_url
        boolean email_verified
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at
    }

    ORGANIZATION {
        uuid id PK
        string name
        string slug UK
        jsonb settings
        string database_name UK
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at
    }

    USER_ORG_MEMBERSHIP {
        uuid id PK
        uuid user_id FK
        uuid organization_id FK
        string org_role
        timestamp created_at
    }

    PROJECT {
        uuid id PK
        uuid organization_id FK
        string name
        string client_name
        date project_start
        date project_end
        integer next_item_num
        timestamp indicators_updated
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at
    }

    PORTFOLIO {
        uuid id PK
        uuid organization_id FK
        string name
        string description
        timestamp created_at
        timestamp updated_at
    }

    PORTFOLIO_PROJECT {
        uuid portfolio_id FK
        uuid project_id FK
    }

    ITEM {
        uuid id PK
        uuid project_id FK
        integer item_num
        string type
        string title
        string description
        uuid workstream_id FK
        string assigned_to
        date start_date
        date finish_date
        integer duration_days
        date deadline
        boolean draft
        boolean client_visible
        integer percent_complete
        string indicator
        string priority
        array rpt_out
        decimal budget_amount
        timestamp created_at
        timestamp updated_at
        timestamp deleted_at
    }

    WORKSTREAM {
        uuid id PK
        uuid project_id FK
        string name
        integer sort_order
    }

    ITEM_NOTE {
        uuid id PK
        uuid item_id FK
        date note_date
        text content
        uuid created_by FK
        timestamp created_at
    }

    ITEM_DEPENDENCY {
        uuid item_id FK
        uuid depends_on_id FK
    }

    ATTACHMENT {
        uuid id PK
        uuid item_id FK
        string filename
        string content_type
        integer size_bytes
        string s3_key
        uuid uploaded_by FK
        timestamp created_at
    }

    USER_PROJECT_ROLE {
        uuid id PK
        uuid user_id FK
        uuid project_id FK
        string role
        timestamp created_at
    }

    RATE_CARD {
        uuid id PK
        uuid organization_id FK
        string resource_name
        string role
        string geography
        decimal hourly_rate
        date effective_from
        date effective_to
        timestamp created_at
    }

    BUDGET_ALLOCATION {
        uuid id PK
        uuid project_id FK
        uuid workstream_id FK
        decimal amount
        date period_start
        date period_end
        string notes
        timestamp created_at
    }

    TIMESHEET_ENTRY {
        uuid id PK
        uuid project_id FK
        uuid rate_card_id FK
        date week_ending
        string resource_name
        decimal hours
        decimal rate
        decimal cost
        boolean complete_week
        timestamp created_at
    }

    CHAT_SESSION {
        uuid id PK
        uuid user_id FK
        uuid project_id FK
        string title
        timestamp created_at
        timestamp updated_at
    }

    CHAT_MESSAGE {
        uuid id PK
        uuid session_id FK
        string role
        text content
        jsonb context_refs
        integer token_count
        timestamp created_at
    }

    AUDIT_LOG {
        uuid id PK
        uuid user_id FK
        string action
        string entity_type
        uuid entity_id
        jsonb before_state
        jsonb after_state
        string correlation_id
        timestamp created_at
    }
```

---

## Quick Reference

### Enum Types

| Enum | Values | Used By |
|------|--------|---------|
| item_type_enum | Budget, Risk, Action Item, Issue, Decision, Deliverable, Plan Item | Item.type |
| indicator_enum | Beyond Deadline!!!, Late Finish!!, Late Start!!, Trending Late!, Finishing Soon!, Starting Soon!, In Progress, Not Started, Completed Recently, Completed | Item.indicator |
| org_role_enum | owner, admin, member | User_Org_Membership.org_role |
| project_role_enum | admin, project_manager, team_member, viewer | User_Project_Role.role |
| chat_role_enum | user, assistant, system | Chat_Message.role |

### Database Layout

```
Central Database (braidmgr_central)
├── users
├── organizations
├── user_org_memberships
└── audit_log (central)

Organization Database (braidmgr_org_{slug})
├── projects, portfolios, portfolio_projects
├── items, workstreams, item_notes, item_dependencies, attachments
├── user_project_roles
├── rate_cards, budget_allocations, timesheet_entries
├── chat_sessions, chat_messages
└── audit_log (per-org)
```
