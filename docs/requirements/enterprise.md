# Enterprise Requirements (ENT)

*Parent: [REQUIREMENTS.md](../REQUIREMENTS.md)*

These define v2 multi-tenant, multi-user features.

---

## ENT-001: Organization Multi-Tenancy

**Title**: Database-per-organization isolation

**Description**: Each organization shall have:
- Separate database for complete isolation
- Organization-level settings and branding
- Admin-managed user access

**Acceptance Criteria**:
- Data never leaks between organizations
- Organization CRUD for super-admins
- Database provisioned on org creation
- Org deletion removes all data

**Priority**: MVP

---

## ENT-002: User Roles

**Title**: Role-based access control

**Description**: System shall support roles:
- **Admin**: Full access, user management
- **ProjectManager**: Create/edit projects, manage team members
- **TeamMember**: View/edit assigned items
- **Viewer**: Read-only access

**Acceptance Criteria**:
- Roles assigned per-project
- Permissions enforced on API endpoints
- UI hides/disables unauthorized actions
- Role inheritance (Admin has all PM permissions, etc.)

**Priority**: MVP

---

## ENT-003: Portfolio Grouping

**Title**: Flexible project grouping into portfolios

**Description**: Users shall be able to:
- Create portfolios as containers for projects
- Add/remove projects from portfolios
- View aggregated portfolio dashboards
- No rigid hierarchy (projects can be in multiple portfolios)

**Acceptance Criteria**:
- Portfolio CRUD operations work
- Portfolio dashboard aggregates project data
- Budget totals sum across projects
- Item counts aggregate correctly

**Priority**: MVP

---

## ENT-004: AI Chat Agent

**Title**: Natural language interface with Claude

**Description**: Users shall be able to:
- Chat with AI about project data
- Ask questions in natural language
- Get insights and summaries
- Default context: current project
- Expand scope by asking

**Acceptance Criteria**:
- Chat interface embedded in app
- Responses are contextually accurate
- AI can reference specific items by number
- Conversation history persisted
- RBAC respected (can only query accessible projects)

**Priority**: MVP

---

## ENT-005: File Attachments

**Title**: Attach files to items

**Description**: Users shall be able to:
- Upload files (images, documents) to items
- View attached files inline or download
- Delete attachments
- Storage in S3

**Acceptance Criteria**:
- Upload works for common file types
- Images display inline
- Documents downloadable
- File size limits enforced
- Virus scanning (optional, post-MVP)

**Priority**: Post-MVP

---

## ENT-006: SSO Integration

**Title**: Enterprise Single Sign-On

**Description**: Organizations shall be able to:
- Configure SAML or OIDC provider
- Auto-provision users on first login
- Enforce SSO-only authentication

**Acceptance Criteria**:
- SAML 2.0 and OIDC supported
- User attributes mapped from IdP
- Just-in-time provisioning works
- SSO can be required per-org

**Priority**: Post-MVP

---

## ENT-007: Global Search

**Title**: Full-text search across all data

**Description**: Users shall be able to:
- Search items, notes, attachments
- Filter search results
- Navigate directly to search results

**Acceptance Criteria**:
- Search returns results in < 500ms
- Highlights matching text
- Respects RBAC permissions
- Searches across accessible projects

**Priority**: Post-MVP

---

## ENT-008: Audit Logging

**Title**: Comprehensive audit trail

**Description**: System shall log:
- All data modifications (create, update, delete)
- User actions (login, logout, permission changes)
- Actor, timestamp, before/after values

**Acceptance Criteria**:
- Audit logs immutable
- Queryable by admin
- Retention policy configurable
- No PII in logs

**Priority**: MVP

---

## ENT-009: Multi-User Collaboration

**Title**: Real-time or near-real-time collaboration

**Description**: Multiple users shall be able to:
- View same project simultaneously
- See recent changes by others
- Avoid overwriting each other's edits

**Acceptance Criteria**:
- Changes visible within 30 seconds
- Edit conflicts detected and handled
- User presence indicators (optional)

**Priority**: Post-MVP
