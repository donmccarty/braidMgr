# Item CRUD Flows

*Parent: [PROCESS_FLOWS.md](../PROCESS_FLOWS.md)*

Create, read, update, delete flows for RAID items.

**Key Concepts**:
- All operations check RBAC permissions first
- Audit log entry for all data changes
- Indicator recalculated after create/update
- Item numbers auto-increment per project

---

## Create Item

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API
    participant D as Database

    U->>F: Click "Add Item"
    F->>F: Open create dialog
    U->>F: Fill form, submit
    F->>A: POST /projects/{id}/items
    A->>A: Validate request (Pydantic)
    A->>A: Check permissions (RBAC)
    A->>D: Get next_item_num
    D-->>A: next_item_num
    A->>D: INSERT item
    A->>D: UPDATE project.next_item_num
    A->>D: INSERT audit_log
    D-->>A: Created item
    A->>A: Calculate indicator
    A-->>F: Item response
    F->>F: Close dialog, refresh list
    F-->>U: Show success toast
```

---

## Update Item

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API
    participant D as Database

    U->>F: Edit item, save
    F->>A: PUT /projects/{pid}/items/{num}
    A->>A: Validate request
    A->>A: Check permissions
    A->>D: Get current item
    D-->>A: Current state
    A->>D: UPDATE item
    A->>D: INSERT audit_log (with before/after)
    D-->>A: Updated item
    A->>A: Recalculate indicator
    A-->>F: Item response
    F->>F: Update UI
    F-->>U: Show success toast
```

---

## Read Item

```mermaid
sequenceDiagram
    participant F as Frontend
    participant A as API
    participant D as Database

    F->>A: GET /projects/{pid}/items/{num}
    A->>A: Check view permissions
    A->>D: SELECT item
    D-->>A: Item record
    A->>D: SELECT item_notes
    D-->>A: Notes
    A->>D: SELECT attachments
    D-->>A: Attachments
    A-->>F: Item with notes and attachments
```

---

## Delete Item

```mermaid
sequenceDiagram
    participant U as User
    participant F as Frontend
    participant A as API
    participant D as Database

    U->>F: Click delete, confirm
    F->>A: DELETE /projects/{pid}/items/{num}
    A->>A: Check delete permissions
    A->>D: Get current item
    D-->>A: Current state
    A->>D: UPDATE item SET deleted_at = NOW()
    A->>D: INSERT audit_log
    D-->>A: Success
    A-->>F: 204 No Content
    F->>F: Remove from list
    F-->>U: Show success toast
```

---

## Item Number Assignment

```python
async def create_item(project_id: UUID, data: ItemCreate) -> Item:
    """Create item with auto-assigned number."""
    async with aurora.transaction(pool) as conn:
        # Get and increment item number atomically
        project = await conn.fetchrow("""
            UPDATE projects
            SET next_item_num = next_item_num + 1
            WHERE id = $1
            RETURNING next_item_num - 1 as item_num
        """, project_id)

        # Create item with assigned number
        item = await conn.fetchrow("""
            INSERT INTO items (id, project_id, item_num, type, title, ...)
            VALUES ($1, $2, $3, $4, $5, ...)
            RETURNING *
        """, uuid4(), project_id, project['item_num'], data.type, data.title, ...)

    return Item.from_row(item)
```

---

## Audit Log Entry

```python
async def log_change(
    conn,
    user_id: UUID,
    action: str,
    entity_type: str,
    entity_id: UUID,
    before_state: dict = None,
    after_state: dict = None
):
    """Record audit log entry."""
    await conn.execute("""
        INSERT INTO audit_log
        (id, user_id, action, entity_type, entity_id, before_state, after_state, correlation_id, created_at)
        VALUES ($1, $2, $3, $4, $5, $6, $7, $8, NOW())
    """,
        uuid4(),
        user_id,
        action,
        entity_type,
        entity_id,
        json.dumps(before_state) if before_state else None,
        json.dumps(after_state) if after_state else None,
        correlation_id_var.get()
    )
```
