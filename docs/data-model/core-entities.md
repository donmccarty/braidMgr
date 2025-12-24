# Core Entities

*Parent: [DATA_MODEL.md](../DATA_MODEL.md)*

Multi-tenant foundation entities that establish the organizational hierarchy and user management structure.

**Key Concepts**:
- Database-per-organization isolation for complete data separation
- Central auth database holds users and org memberships
- Organization slug used for URL routing and database naming
- Portfolios provide flexible project grouping (not rigid PMI programs)

---

## ORGANIZATION

Represents a tenant with isolated data. Each organization has its own database.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| name | VARCHAR(255) | NOT NULL | Display name |
| slug | VARCHAR(100) | UNIQUE, NOT NULL | URL-safe identifier |
| settings | JSONB | DEFAULT '{}' | Organization settings |
| database_name | VARCHAR(100) | UNIQUE, NOT NULL | Name of isolated database |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |
| deleted_at | TIMESTAMP | NULL | Soft delete timestamp |

**Indexes**:
- `idx_organization_slug` on slug

**Design Notes**:
- The `slug` is used in URLs (e.g., `app.braidmgr.com/acme/projects`)
- The `database_name` follows pattern `braidmgr_org_{slug}`
- Settings JSONB can store org-specific configurations (SSO, theme, etc.)

---

## USER

Application user (exists in central auth database).

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| email | VARCHAR(255) | UNIQUE, NOT NULL | Email address |
| password_hash | VARCHAR(255) | NULL | Bcrypt hash (null for OAuth-only) |
| name | VARCHAR(255) | NOT NULL | Display name |
| avatar_url | VARCHAR(500) | NULL | Profile image URL |
| email_verified | BOOLEAN | DEFAULT false | Email verification status |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |
| deleted_at | TIMESTAMP | NULL | Soft delete timestamp |

**Indexes**:
- `idx_user_email` on email

**Design Notes**:
- `password_hash` is NULL for users who only authenticate via OAuth
- Users can belong to multiple organizations via USER_ORG_MEMBERSHIP
- Stored in central database, not per-org databases

---

## USER_ORG_MEMBERSHIP

Maps users to organizations with org-level role.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| user_id | UUID | FK(USER), NOT NULL | User reference |
| organization_id | UUID | FK(ORGANIZATION), NOT NULL | Organization reference |
| org_role | org_role_enum | NOT NULL | Organization-level role |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |

**Unique Constraint**: (user_id, organization_id)

**Design Notes**:
- A user can have different roles in different organizations
- `org_role` determines org-wide permissions (owner, admin, member)
- Project-level roles are handled separately by USER_PROJECT_ROLE

---

## PROJECT

A RAID log project within an organization.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| organization_id | UUID | FK(ORGANIZATION), NOT NULL | Parent organization |
| name | VARCHAR(255) | NOT NULL | Project name |
| client_name | VARCHAR(255) | NULL | Client/customer name |
| project_start | DATE | NULL | Planned start date |
| project_end | DATE | NULL | Planned end date |
| next_item_num | INTEGER | DEFAULT 1 | Auto-increment for item numbers |
| indicators_updated | TIMESTAMP | NULL | Last indicator recalculation |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |
| deleted_at | TIMESTAMP | NULL | Soft delete timestamp |

**Indexes**:
- `idx_project_organization` on organization_id
- `idx_project_deleted` on deleted_at

**Design Notes**:
- `next_item_num` auto-increments to assign unique item numbers per project
- `indicators_updated` tracks when status indicators were last recalculated
- Soft delete allows recovery and audit trail

---

## PORTFOLIO

Flexible grouping of projects.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| organization_id | UUID | FK(ORGANIZATION), NOT NULL | Parent organization |
| name | VARCHAR(255) | NOT NULL | Portfolio name |
| description | TEXT | NULL | Description |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |

**Indexes**:
- `idx_portfolio_organization` on organization_id

**Design Notes**:
- Portfolios are NOT rigid PMI program management
- Users can organize projects however they want
- A project can belong to multiple portfolios
- Cross-project dashboards aggregate data from portfolio members

---

## PORTFOLIO_PROJECT

Many-to-many relationship between portfolios and projects.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| portfolio_id | UUID | FK(PORTFOLIO), NOT NULL | Portfolio reference |
| project_id | UUID | FK(PROJECT), NOT NULL | Project reference |

**Primary Key**: (portfolio_id, project_id)

**Design Notes**:
- Pure junction table for M:N relationship
- Projects can exist without portfolio membership
- Deleting a portfolio does not delete projects

---

## Entity Relationships

```
ORGANIZATION ──1:M──→ USER_ORG_MEMBERSHIP ←──M:1── USER
      │
      ├──1:M──→ PROJECT ←──M:M──→ PORTFOLIO_PROJECT ←──M:1── PORTFOLIO
      │
      └──1:M──→ PORTFOLIO
```
