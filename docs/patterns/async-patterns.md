# Async Patterns

*Parent: [PATTERNS.md](../PATTERNS.md)*

Async patterns for parallel operations and transactions.

**Key Concepts**:
- Use asyncio.gather for parallel independent operations
- Transaction boundaries for atomic multi-table operations
- Side effects (notifications) happen AFTER commit

---

## Parallel Operations

Use asyncio.gather when operations are independent:

```python
import asyncio

async def load_project_context(project_id: UUID) -> ProjectContext:
    """Load all project data in parallel."""
    project, items, budget = await asyncio.gather(
        project_repo.find_by_id(project_id),
        item_repo.find_by_project(project_id),
        budget_service.calculate(project_id),
    )
    return ProjectContext(project, items, budget)
```

**When to use parallel:**
- Loading multiple independent pieces of data
- API calls to different services
- Cache lookups and database queries together

**When NOT to use parallel:**
- Operations that depend on each other
- Operations that must be in a transaction

---

## Transaction Boundaries

Wrap related writes in a transaction:

```python
async def create_item_with_notes(data: ItemCreate) -> Item:
    """
    Transaction scope: item + initial note.
    Side effects happen AFTER commit.
    """
    async with services.aurora.transaction(pool) as conn:
        # All writes in same transaction
        item = await conn.fetchrow("""
            INSERT INTO items (id, project_id, ...) VALUES ($1, $2, ...)
            RETURNING *
        """, ...)

        if data.initial_note:
            await conn.execute("""
                INSERT INTO item_notes (id, item_id, content, ...)
                VALUES ($1, $2, $3, ...)
            """, uuid4(), item['id'], data.initial_note, ...)

    # Transaction committed - changes visible

    # Side effects after commit
    await notify_assignee(item['assigned_to'], item)

    return Item.from_row(item)
```

---

## Transaction Context Manager

```python
# src/services/aurora_service.py
from contextlib import asynccontextmanager

class AuroraService:
    @asynccontextmanager
    async def transaction(self, pool):
        """Transaction context manager with automatic rollback on error."""
        async with pool.acquire() as conn:
            async with conn.transaction():
                yield conn
                # Commits on successful exit
                # Rolls back on exception
```

---

## Parallel with Error Handling

```python
import asyncio

async def load_dashboard_data(project_id: UUID) -> DashboardData:
    """Load dashboard with graceful degradation."""
    try:
        results = await asyncio.gather(
            item_repo.get_counts(project_id),
            budget_service.get_summary(project_id),
            recent_activity_service.get(project_id),
            return_exceptions=True  # Don't fail all if one fails
        )

        item_counts, budget, activity = results

        # Check for exceptions
        if isinstance(item_counts, Exception):
            logger.error("item_counts_failed", error=str(item_counts))
            item_counts = {}

        if isinstance(budget, Exception):
            logger.error("budget_failed", error=str(budget))
            budget = None

        if isinstance(activity, Exception):
            logger.error("activity_failed", error=str(activity))
            activity = []

        return DashboardData(
            item_counts=item_counts,
            budget=budget,
            recent_activity=activity
        )
    except Exception as e:
        logger.exception("dashboard_load_failed")
        raise
```

---

## Background Tasks

For non-blocking side effects:

```python
from fastapi import BackgroundTasks

@router.post("/projects/{project_id}/items")
async def create_item(
    project_id: UUID,
    data: ItemCreate,
    background_tasks: BackgroundTasks,
    current_user: User = Depends(get_current_user)
):
    # Create item (blocking, in transaction)
    item = await item_service.create(project_id, data)

    # Add side effects to background (non-blocking)
    background_tasks.add_task(send_assignment_email, item)
    background_tasks.add_task(update_project_indicators, project_id)

    return ItemResponse.from_entity(item)
```
