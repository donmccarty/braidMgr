# Authentication & Authorization

*Parent: [ARCHITECTURE.md](../ARCHITECTURE.md)*

JWT-based authentication and role-based access control.

**Key Concepts**:
- JWT access tokens (15 min) with refresh tokens (7 days)
- Two-level RBAC: organization roles and project roles
- OAuth support for Google and Microsoft
- SSO for enterprise (post-MVP)

---

## Authentication Flow

```
1. User submits credentials
   └──→ POST /auth/login (email + password)
        OR
   └──→ GET /auth/oauth/google (OAuth redirect)

2. Backend verifies credentials
   └──→ Check password hash or OAuth token

3. Backend issues tokens
   ├──→ Access token (JWT, 15 min expiry)
   └──→ Refresh token (opaque, 7 day expiry)

4. Frontend stores tokens
   └──→ Access: memory, Refresh: httpOnly cookie

5. Frontend includes access token
   └──→ Authorization: Bearer <access_token>

6. Backend validates on each request
   └──→ Verify signature, check expiry, extract claims

7. Frontend refreshes before expiry
   └──→ POST /auth/refresh (with refresh token)
```

---

## JWT Structure

```json
{
    "sub": "user-uuid",
    "email": "user@example.com",
    "name": "Jane Smith",
    "org_id": "org-uuid",
    "org_role": "admin",
    "iat": 1703419200,
    "exp": 1703420100
}
```

| Claim | Description |
|-------|-------------|
| sub | User UUID |
| email | User email |
| name | Display name |
| org_id | Current organization UUID |
| org_role | Organization-level role |
| iat | Issued at timestamp |
| exp | Expiration timestamp |

---

## Organization Roles

| Role | Description | Permissions |
|------|-------------|-------------|
| owner | Organization owner | Full control, billing, can delete org |
| admin | Administrator | Manage users, projects, settings |
| member | Standard member | Access assigned projects only |

---

## Project Roles

| Role | Description | Permissions |
|------|-------------|-------------|
| admin | Project admin | Full project control, delete project |
| project_manager | PM | Manage items, workstreams, budget, settings |
| team_member | Team member | Create/update items |
| viewer | Read-only | View items and reports |

---

## Permission Matrix

| Action | Viewer | Team Member | PM | Admin |
|--------|--------|-------------|-----|-------|
| View items | Yes | Yes | Yes | Yes |
| Create items | No | Yes | Yes | Yes |
| Update items | No | Yes | Yes | Yes |
| Delete items | No | No | Yes | Yes |
| Manage workstreams | No | No | Yes | Yes |
| Manage settings | No | No | Yes | Yes |
| Delete project | No | No | No | Yes |
| Assign roles | No | No | No | Yes |
| View budget | Yes | Yes | Yes | Yes |
| Edit budget | No | No | Yes | Yes |
| AI chat | Yes | Yes | Yes | Yes |
| Export data | Yes | Yes | Yes | Yes |

---

## Permission Check Implementation

```python
from enum import Enum
from typing import Optional

class Permission(Enum):
    VIEW_ITEMS = "view_items"
    CREATE_ITEMS = "create_items"
    UPDATE_ITEMS = "update_items"
    DELETE_ITEMS = "delete_items"
    MANAGE_WORKSTREAMS = "manage_workstreams"
    MANAGE_SETTINGS = "manage_settings"
    DELETE_PROJECT = "delete_project"
    ASSIGN_ROLES = "assign_roles"
    EDIT_BUDGET = "edit_budget"

ROLE_PERMISSIONS = {
    "viewer": {Permission.VIEW_ITEMS},
    "team_member": {
        Permission.VIEW_ITEMS,
        Permission.CREATE_ITEMS,
        Permission.UPDATE_ITEMS,
    },
    "project_manager": {
        Permission.VIEW_ITEMS,
        Permission.CREATE_ITEMS,
        Permission.UPDATE_ITEMS,
        Permission.DELETE_ITEMS,
        Permission.MANAGE_WORKSTREAMS,
        Permission.MANAGE_SETTINGS,
        Permission.EDIT_BUDGET,
    },
    "admin": set(Permission),  # All permissions
}


async def check_permission(
    user_id: UUID,
    project_id: UUID,
    permission: Permission
) -> bool:
    """Check if user has permission on project."""
    role = await get_user_project_role(user_id, project_id)
    if role is None:
        return False
    return permission in ROLE_PERMISSIONS.get(role, set())


def require_permission(permission: Permission):
    """Decorator for route handlers."""
    def decorator(func):
        async def wrapper(
            project_id: UUID,
            current_user: User = Depends(get_current_user),
            *args, **kwargs
        ):
            if not await check_permission(
                current_user.id, project_id, permission
            ):
                raise AuthorizationError("Insufficient permissions")
            return await func(project_id, current_user, *args, **kwargs)
        return wrapper
    return decorator


# Usage
@router.delete("/projects/{project_id}/items/{item_num}")
@require_permission(Permission.DELETE_ITEMS)
async def delete_item(
    project_id: UUID,
    item_num: int,
    current_user: User = Depends(get_current_user)
):
    ...
```

---

## OAuth Integration

### Supported Providers

| Provider | Scopes |
|----------|--------|
| Google | email, profile |
| Microsoft | User.Read |

### OAuth Flow

```
1. Frontend redirects to /auth/oauth/{provider}
2. Backend redirects to provider's authorization URL
3. User authenticates with provider
4. Provider redirects back with authorization code
5. Backend exchanges code for provider tokens
6. Backend creates/updates user from provider profile
7. Backend issues app JWT tokens
8. Frontend redirected to app with tokens
```

---

## Token Storage

| Token | Storage | Security |
|-------|---------|----------|
| Access token | Memory (React state) | XSS vulnerable but short-lived |
| Refresh token | httpOnly cookie | Not accessible to JS |

### Token Refresh

```typescript
// lib/api.ts
async function refreshAccessToken(): Promise<string> {
    const response = await fetch('/auth/refresh', {
        method: 'POST',
        credentials: 'include', // Send httpOnly cookie
    });

    if (!response.ok) {
        // Refresh failed, redirect to login
        window.location.href = '/login';
        throw new Error('Session expired');
    }

    const { access_token } = await response.json();
    return access_token;
}
```
