# Access Control & AI Chat Entities

*Parent: [DATA_MODEL.md](../DATA_MODEL.md)*

Entities for role-based access control (RBAC) and AI chat functionality.

**Key Concepts**:
- Two-level RBAC: organization roles and project roles
- Project roles determine CRUD permissions on project data
- Chat sessions scope AI context to project or org level
- AI only accesses data the user has permission to view
- Audit log tracks all data changes for compliance

---

## USER_PROJECT_ROLE

User role assignment per project.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| user_id | UUID | FK(USER), NOT NULL | User reference |
| project_id | UUID | FK(PROJECT), NOT NULL | Project reference |
| role | project_role_enum | NOT NULL | Project role |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |

**Unique Constraint**: (user_id, project_id)

**Design Notes**:
- A user can have different roles on different projects
- Roles from `project_role_enum`: admin, project_manager, team_member, viewer
- Role permissions (from least to most privileged):
  - **viewer**: Read-only access to project data
  - **team_member**: Create/update items, cannot delete or manage project settings
  - **project_manager**: Full item CRUD, manage workstreams, cannot delete project
  - **admin**: Full access including project deletion and role management

---

## CHAT_SESSION

AI conversation session.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| user_id | UUID | FK(USER), NOT NULL | Session owner |
| project_id | UUID | FK(PROJECT), NULL | Context project (null = org-wide) |
| title | VARCHAR(255) | NULL | Session title (auto-generated) |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last activity |

**Indexes**:
- `idx_chat_session_user` on user_id
- `idx_chat_session_project` on project_id

**Design Notes**:
- `project_id` NULL means the session context is organization-wide
- `title` auto-generated from first user message or Claude summary
- Sessions preserved for conversation history and continuity
- User can resume previous sessions or start new ones

---

## CHAT_MESSAGE

Individual chat message.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| session_id | UUID | FK(CHAT_SESSION), NOT NULL | Parent session |
| role | chat_role_enum | NOT NULL | Message role (user/assistant) |
| content | TEXT | NOT NULL | Message content |
| context_refs | JSONB | NULL | Referenced items/data |
| token_count | INTEGER | NULL | Tokens used |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |

**Indexes**:
- `idx_chat_message_session` on session_id
- `idx_chat_message_created` on created_at

**Design Notes**:
- `role` from `chat_role_enum`: user, assistant, system
- `context_refs` stores item IDs and data snippets used in response
- Example `context_refs`:
  ```json
  {
    "items": ["uuid1", "uuid2"],
    "queries": ["open risks", "overdue actions"]
  }
  ```
- `token_count` tracks API usage for cost monitoring

---

## AUDIT_LOG

Immutable audit trail.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| user_id | UUID | FK(USER), NULL | Acting user (null = system) |
| action | VARCHAR(50) | NOT NULL | Action performed |
| entity_type | VARCHAR(50) | NOT NULL | Entity type affected |
| entity_id | UUID | NULL | Entity ID affected |
| before_state | JSONB | NULL | State before change |
| after_state | JSONB | NULL | State after change |
| correlation_id | VARCHAR(50) | NULL | Request correlation ID |
| created_at | TIMESTAMP | NOT NULL | Action timestamp |

**Indexes**:
- `idx_audit_user` on user_id
- `idx_audit_entity` on (entity_type, entity_id)
- `idx_audit_action` on action
- `idx_audit_created` on created_at

**Design Notes**:
- **This table is append-only. No updates or deletes allowed.**
- `user_id` NULL indicates system-initiated action (e.g., scheduled job)
- `action` values: CREATE, UPDATE, DELETE, LOGIN, LOGOUT, PERMISSION_CHANGE
- `before_state` and `after_state` enable diff viewing in audit UI
- `correlation_id` links multiple audit entries from single request
- Exists in both central DB (auth events) and per-org DB (data events)

---

## RBAC Permission Matrix

| Action | Viewer | Team Member | Project Manager | Admin |
|--------|--------|-------------|-----------------|-------|
| View items | Yes | Yes | Yes | Yes |
| Create items | No | Yes | Yes | Yes |
| Update items | No | Yes | Yes | Yes |
| Delete items | No | No | Yes | Yes |
| Manage workstreams | No | No | Yes | Yes |
| Manage project settings | No | No | No | Yes |
| Delete project | No | No | No | Yes |
| Assign roles | No | No | No | Yes |
| View budget | Yes | Yes | Yes | Yes |
| Edit budget | No | No | Yes | Yes |
| AI chat | Yes | Yes | Yes | Yes |

---

## Entity Relationships

```
USER ──1:M──→ USER_PROJECT_ROLE ←──M:1── PROJECT
  │
  └──1:M──→ CHAT_SESSION ──1:M──→ CHAT_MESSAGE
                │
                └──M:1── PROJECT (optional)

USER ──1:M──→ AUDIT_LOG
```
