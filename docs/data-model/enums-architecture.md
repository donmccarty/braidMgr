# Enums & Database Architecture

*Parent: [DATA_MODEL.md](../DATA_MODEL.md)*

Enum type definitions and database-per-organization architecture details.

**Key Concepts**:
- PostgreSQL enum types for type safety
- Database-per-org provides complete data isolation
- Central database for auth, per-org database for project data
- Connection routing based on JWT org context

---

## Enum Definitions

### item_type_enum

Defines the seven RAID+ item types.

```sql
CREATE TYPE item_type_enum AS ENUM (
    'Budget',       -- Budget line items
    'Risk',         -- Potential problems
    'Action Item',  -- Tasks to complete
    'Issue',        -- Current problems
    'Decision',     -- Decisions made/needed
    'Deliverable',  -- Project outputs
    'Plan Item'     -- Schedule/milestone items
);
```

### indicator_enum

Calculated status indicators based on dates and completion.

```sql
CREATE TYPE indicator_enum AS ENUM (
    'Beyond Deadline!!!',   -- Past deadline, not complete
    'Late Finish!!',        -- Past finish date, not complete
    'Late Start!!',         -- Past start date, not started
    'Trending Late!',       -- Progress behind schedule
    'Finishing Soon!',      -- Within 7 days of finish
    'Starting Soon!',       -- Within 7 days of start
    'In Progress',          -- Started, on track
    'Not Started',          -- Start date in future
    'Completed Recently',   -- Completed within 7 days
    'Completed'             -- Completed
);
```

**Indicator Priority** (highest to lowest):
1. Beyond Deadline!!!
2. Late Finish!!
3. Late Start!!
4. Trending Late!
5. Finishing Soon!
6. Starting Soon!
7. In Progress
8. Not Started
9. Completed Recently
10. Completed

### org_role_enum

Organization-level roles.

```sql
CREATE TYPE org_role_enum AS ENUM (
    'owner',    -- Full org control, billing, can delete org
    'admin',    -- Manage users, projects, settings
    'member'    -- Access assigned projects only
);
```

### project_role_enum

Project-level roles for RBAC.

```sql
CREATE TYPE project_role_enum AS ENUM (
    'admin',            -- Full project control
    'project_manager',  -- Manage items, workstreams, budget
    'team_member',      -- Create/update items
    'viewer'            -- Read-only access
);
```

### chat_role_enum

Chat message roles for AI conversations.

```sql
CREATE TYPE chat_role_enum AS ENUM (
    'user',       -- User message
    'assistant',  -- Claude response
    'system'      -- System prompt/context
);
```

---

## Database Architecture

### Multi-Tenancy Strategy

braidMgr uses **database-per-organization** isolation for maximum security and flexibility.

```
Central Database (braidmgr_central)
├── users
├── organizations
├── user_org_memberships
└── audit_log (central)

Organization Database (braidmgr_org_{slug})
├── projects
├── portfolios
├── portfolio_projects
├── items
├── workstreams
├── item_notes
├── item_dependencies
├── attachments
├── user_project_roles
├── rate_cards
├── budget_allocations
├── timesheet_entries
├── chat_sessions
├── chat_messages
└── audit_log (per-org)
```

### Benefits

| Benefit | Description |
|---------|-------------|
| Complete data isolation | No risk of cross-tenant data leaks |
| Per-org backup/restore | Backup/restore individual orgs independently |
| Performance isolation | One org's load doesn't affect others |
| Compliance-friendly | Supports data residency requirements |
| Easy org deletion | Drop database to fully remove org data |

### Connection Routing

1. Request arrives with org context (from JWT `org_id` claim or subdomain)
2. Service layer looks up org's `database_name` from central DB
3. Connection pool routes to correct database
4. All queries execute within org database context

```python
# Simplified connection routing example:
async def get_org_connection(org_id: UUID) -> Connection:
    org = await central_db.get_org(org_id)
    return await get_pool(org.database_name).acquire()
```

### Connection Pooling

- Separate connection pool per organization database
- Pool settings: min=2, max=10 connections per org
- Idle connections recycled after 5 minutes
- Health checks every 30 seconds

---

## Relationship Summary

| Parent | Child | Relationship | FK Column |
|--------|-------|--------------|-----------|
| Organization | User_Org_Membership | 1:M | organization_id |
| Organization | Project | 1:M | organization_id |
| Organization | Portfolio | 1:M | organization_id |
| Organization | Rate_Card | 1:M | organization_id |
| User | User_Org_Membership | 1:M | user_id |
| User | User_Project_Role | 1:M | user_id |
| User | Chat_Session | 1:M | user_id |
| Project | Item | 1:M | project_id |
| Project | Workstream | 1:M | project_id |
| Project | Budget_Allocation | 1:M | project_id |
| Project | Timesheet_Entry | 1:M | project_id |
| Project | User_Project_Role | 1:M | project_id |
| Portfolio | Portfolio_Project | 1:M | portfolio_id |
| Project | Portfolio_Project | 1:M | project_id |
| Item | Item_Note | 1:M | item_id |
| Item | Item_Dependency | 1:M | item_id |
| Item | Attachment | 1:M | item_id |
| Chat_Session | Chat_Message | 1:M | session_id |

---

## Migration from v1

The v1 YAML format maps to v2 schema as follows:

| v1 Field | v2 Table.Column |
|----------|-----------------|
| metadata.project_name | project.name |
| metadata.client_name | project.client_name |
| metadata.project_start | project.project_start |
| metadata.project_end | project.project_end |
| metadata.next_item_num | project.next_item_num |
| metadata.workstreams | workstream.name (multiple rows) |
| items[].item_num | item.item_num |
| items[].type | item.type |
| items[].title | item.title |
| items[].description | item.description |
| items[].workstream | item.workstream_id (lookup) |
| items[].assigned_to | item.assigned_to |
| items[].start | item.start_date |
| items[].finish | item.finish_date |
| items[].deadline | item.deadline |
| items[].percent_complete | item.percent_complete |
| items[].indicator | item.indicator |
| items[].rpt_out | item.rpt_out |
| items[].notes | item_note (parsed by date prefix) |
| budget.rate_card | rate_card (multiple rows) |
| budget.timesheet_data | timesheet_entry (multiple rows) |
| budget.budget_ledger | budget_allocation (multiple rows) |

**Migration Notes**:
- Notes in v1 are prefixed with dates like "2024-12-15:" which need parsing
- Workstream names need lookup to get UUIDs
- All UUIDs are generated during migration
- v1 single-project maps to v2 with default org/user
