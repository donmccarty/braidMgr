# Database Architecture

*Parent: [ARCHITECTURE.md](../ARCHITECTURE.md)*

Multi-tenant database strategy and connection management.

**Key Concepts**:
- Database-per-organization isolation
- Central auth database + per-org data databases
- Connection routing based on JWT context
- Pool management per database

---

## Multi-Tenancy Strategy

**Strategy**: Database-per-organization

```
Central Database: braidmgr_central
├── users
├── organizations
├── user_org_memberships
└── audit_log (auth events)

Org Database: braidmgr_org_{slug}
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
└── audit_log (data events)
```

---

## Why Database-per-Org?

| Benefit | Description |
|---------|-------------|
| Complete isolation | No risk of cross-tenant data leaks |
| Per-org backup/restore | Independent backup schedules per org |
| Performance isolation | One org's load doesn't affect others |
| Compliance-friendly | Supports data residency requirements |
| Easy org deletion | DROP DATABASE fully removes org |
| Schema flexibility | Custom indexes per org if needed |

**Tradeoffs**:
- More databases to manage
- Connection pool overhead
- Cross-org queries impossible (by design)

---

## Connection Routing

### Request Flow

1. Request arrives with org context from:
   - JWT `org_id` claim (after authentication)
   - Subdomain (e.g., `acme.braidmgr.com`)

2. Lookup org's `database_name` from central database

3. Get or create connection pool for that database

4. Execute all queries within org database context

### Code Pattern

```python
async def get_org_connection(org_id: UUID) -> asyncpg.Pool:
    """Get database connection pool for organization."""
    # Get org record from central DB
    org = await services.aurora.execute_one(
        services.aurora.central_pool,
        "SELECT database_name FROM organizations WHERE id = $1",
        org_id
    )
    if not org:
        raise NotFoundError("Organization not found")

    # Get or create pool for org database
    return await services.aurora.get_org_pool(org['database_name'])


# Usage in route handler
@router.get("/projects/{project_id}")
async def get_project(
    project_id: UUID,
    current_user: User = Depends(get_current_user)
):
    # Routing happens automatically based on user's org_id
    pool = await get_org_connection(current_user.org_id)

    project = await services.aurora.execute_one(
        pool,
        "SELECT * FROM projects WHERE id = $1",
        project_id
    )
    return ProjectResponse.from_record(project)
```

---

## Connection Pooling

### Pool Configuration

| Setting | Value | Description |
|---------|-------|-------------|
| min_size | 2 | Minimum connections per database |
| max_size | 10 | Maximum connections per database |
| max_idle_time | 300 | Seconds before idle connection closed |
| command_timeout | 60 | Query timeout in seconds |

### Pool Management

```python
class AuroraService:
    def __init__(self):
        self._pools: dict[str, asyncpg.Pool] = {}
        self._pool_lock = asyncio.Lock()

    async def get_org_pool(self, database_name: str) -> asyncpg.Pool:
        """Get or create pool for organization database."""
        if database_name in self._pools:
            return self._pools[database_name]

        async with self._pool_lock:
            # Double-check after acquiring lock
            if database_name in self._pools:
                return self._pools[database_name]

            pool = await asyncpg.create_pool(
                dsn=self._build_dsn(database_name),
                min_size=2,
                max_size=10,
                max_inactive_connection_lifetime=300
            )
            self._pools[database_name] = pool
            return pool
```

---

## Key Indexes

Performance-critical indexes (defined in DATA_MODEL.md):

| Index | Table | Columns | Purpose |
|-------|-------|---------|---------|
| idx_item_project | items | project_id | Item queries by project |
| idx_item_indicator | items | indicator | Dashboard status counts |
| idx_item_assigned | items | assigned_to | Items by assignee view |
| idx_item_deleted | items | deleted_at | Exclude soft-deleted |
| idx_timesheet_week | timesheet_entries | week_ending | Budget calculations |
| idx_chat_session_user | chat_sessions | user_id | User's chat history |

---

## Migrations

Using Alembic for schema versioning:

```bash
# Create new migration
alembic revision --autogenerate -m "add item priority"

# Apply to central database
alembic upgrade head

# Apply to all org databases
python scripts/migrate_all_orgs.py
```

### Multi-Database Migration Strategy

1. Apply migration to staging org database first
2. Validate with integration tests
3. Apply to central database
4. Apply to all org databases (parallel with concurrency limit)
5. Verify migration success per org
