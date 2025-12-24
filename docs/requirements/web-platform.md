# Web Platform Requirements (WEB)

*Parent: [REQUIREMENTS.md](../REQUIREMENTS.md)*

These define the v1.5 web conversion requirements.

---

## WEB-001: Progressive Web App

**Title**: PWA with offline support

**Description**: Application shall be a Progressive Web App:
- Installable on desktop and mobile
- Service worker for offline capability
- App manifest with icons
- Works when network unavailable

**Acceptance Criteria**:
- Passes Lighthouse PWA audit
- Install prompt appears on supported browsers
- Basic functionality works offline
- Syncs when connection restored

**Priority**: MVP

---

## WEB-002: Responsive Design

**Title**: Responsive layout for all screen sizes

**Description**: Application shall adapt to:
- Desktop (1200px+)
- Tablet (768px - 1199px)
- Mobile (< 768px)

**Acceptance Criteria**:
- All views usable on all screen sizes
- Navigation adapts (sidebar collapses on mobile)
- Touch-friendly controls on mobile
- Tables scroll horizontally on narrow screens

**Priority**: MVP

---

## WEB-003: React Frontend

**Title**: React-based single-page application

**Description**: Frontend shall use:
- React 18 with TypeScript
- Vite build tool
- Tailwind CSS for styling
- shadcn/ui component library

**Acceptance Criteria**:
- Application builds without errors
- TypeScript strict mode enabled
- Component tests pass
- Build optimized for production

**Priority**: MVP

---

## WEB-004: FastAPI Backend

**Title**: Python FastAPI REST API

**Description**: Backend shall provide:
- RESTful API endpoints for all operations
- JSON request/response format
- JWT authentication
- Pydantic request validation

**Acceptance Criteria**:
- OpenAPI spec generated automatically
- All endpoints return consistent response format
- 400/401/403/404/500 errors handled properly
- Request validation with clear error messages

**Priority**: MVP

---

## WEB-005: PostgreSQL Database

**Title**: PostgreSQL for data persistence

**Description**: Application shall use:
- PostgreSQL for relational data storage
- Alembic for schema migrations
- Async database access (asyncpg)

**Acceptance Criteria**:
- Schema matches logical data model
- Migrations versioned and reversible
- Connection pooling configured
- Indexes on frequently queried columns

**Priority**: MVP

---

## WEB-006: Authentication

**Title**: User authentication

**Description**: Application shall support:
- Email/password registration and login
- OAuth (Google, Microsoft)
- JWT access tokens (short-lived)
- Refresh tokens (longer-lived)
- Password reset flow

**Acceptance Criteria**:
- Users can register with email
- OAuth login works for both providers
- Tokens refresh automatically
- Invalid tokens return 401
- Password reset email sends correctly

**Priority**: MVP

---

## WEB-007: API Error Handling

**Title**: Consistent API error responses

**Description**: All API errors shall return:
- Appropriate HTTP status code
- JSON body with: error code, message, details, correlation_id

**Acceptance Criteria**:
- 400: Validation errors with field-level details
- 401: Authentication required
- 403: Permission denied
- 404: Resource not found
- 500: Internal error (no sensitive details)

**Priority**: MVP

---

## WEB-008: Loading States

**Title**: Visual feedback during async operations

**Description**: Application shall show:
- Loading spinners during data fetch
- Skeleton screens for initial load
- Button loading states during submit
- Toast notifications for success/error

**Acceptance Criteria**:
- No blank screens during loading
- User knows when operation is in progress
- Errors display user-friendly messages
- Success confirmations appear briefly

**Priority**: MVP
