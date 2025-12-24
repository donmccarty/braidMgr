# API Design

*Parent: [ARCHITECTURE.md](../ARCHITECTURE.md)*

REST API conventions and endpoint structure.

**Key Concepts**:
- RESTful resource-based endpoints
- JWT bearer authentication
- Consistent response format
- Standard error codes

---

## Base URL Structure

```
Production:  https://api.braidmgr.com/v1
Staging:     https://api.staging.braidmgr.com/v1
Development: http://localhost:8000/v1
```

---

## Authentication

All endpoints except `/auth/*` require JWT bearer token:

```
Authorization: Bearer <access_token>
```

Access tokens expire after 15 minutes. Use refresh token to obtain new access token.

---

## Endpoint Groups

| Path | Purpose | Auth Required |
|------|---------|---------------|
| `/health` | Health check | No |
| `/auth/*` | Authentication | No |
| `/users/*` | User management | Yes |
| `/orgs/*` | Organization management | Yes |
| `/projects/*` | Project CRUD | Yes |
| `/projects/{id}/items/*` | Item CRUD | Yes |
| `/projects/{id}/budget/*` | Budget operations | Yes |
| `/chat/*` | AI chat sessions | Yes |
| `/export/*` | Export operations | Yes |

---

## Resource Endpoints

### Projects

| Method | Path | Description |
|--------|------|-------------|
| GET | /projects | List user's projects |
| POST | /projects | Create project |
| GET | /projects/{id} | Get project details |
| PUT | /projects/{id} | Update project |
| DELETE | /projects/{id} | Delete project |

### Items

| Method | Path | Description |
|--------|------|-------------|
| GET | /projects/{id}/items | List items (with filters) |
| POST | /projects/{id}/items | Create item |
| GET | /projects/{id}/items/{num} | Get item by number |
| PUT | /projects/{id}/items/{num} | Update item |
| DELETE | /projects/{id}/items/{num} | Delete item |

### Query Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| page | int | Page number (default 1) |
| per_page | int | Items per page (default 20, max 100) |
| type | string | Filter by item type |
| indicator | string | Filter by status indicator |
| assignee | string | Filter by assigned_to |
| workstream | uuid | Filter by workstream |

---

## Response Format

### Success Response

```json
{
    "data": { ... },
    "meta": {
        "page": 1,
        "per_page": 20,
        "total": 100,
        "total_pages": 5
    }
}
```

### Single Resource

```json
{
    "data": {
        "id": "uuid",
        "item_num": 42,
        "type": "Risk",
        "title": "Database migration risk",
        "indicator": "In Progress",
        "created_at": "2024-12-24T10:00:00Z",
        "updated_at": "2024-12-24T15:30:00Z"
    }
}
```

### Error Response

```json
{
    "error": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": {
        "field": "email",
        "reason": "Invalid email format"
    },
    "correlation_id": "abc-123-def"
}
```

---

## Error Codes

| Code | HTTP Status | Description |
|------|-------------|-------------|
| VALIDATION_ERROR | 400 | Invalid request data |
| AUTHENTICATION_ERROR | 401 | Missing or invalid token |
| AUTHORIZATION_ERROR | 403 | Insufficient permissions |
| NOT_FOUND | 404 | Resource not found |
| CONFLICT | 409 | Resource conflict (duplicate) |
| RATE_LIMITED | 429 | Too many requests |
| INTERNAL_ERROR | 500 | Server error |

---

## Pagination

```json
GET /projects/123/items?page=2&per_page=20

{
    "data": [...],
    "meta": {
        "page": 2,
        "per_page": 20,
        "total": 87,
        "total_pages": 5,
        "has_next": true,
        "has_prev": true
    }
}
```

---

## Rate Limiting

| Endpoint | Limit |
|----------|-------|
| /auth/* | 10 req/min |
| /chat/* | 30 req/min |
| All others | 100 req/min |

Rate limit headers:
```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 95
X-RateLimit-Reset: 1703419260
```

---

## Versioning

API version in URL path: `/v1/projects`

Breaking changes require new version. Deprecation notice 6 months before removal.
