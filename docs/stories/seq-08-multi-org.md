# Sequence 8: Multi-Org

*Parent: [USER_STORIES.md](../USER_STORIES.md)*

Organization-level multi-tenancy with database-per-org isolation. This is a core v2 feature enabling braidMgr to serve multiple corporate clients with complete data separation.

**Depends on**: Sequence 7 (Multi-User)
**Stories**: 4
**Priority**: MVP

**Key Concept**: Each organization gets its own PostgreSQL database. The central database stores user accounts and org metadata; org-specific databases store all project/item data.

---

## S8-001: Organization Creation

**Story**: As a super-admin, I want to create organizations, so that tenants are isolated.

**Acceptance Criteria**:
- Create org with name, settings
- Separate database provisioned automatically
- Admin user assigned to org
- Organization-level branding (optional)

**Traces**: ENT-001

---

## S8-002: Database Isolation

**Story**: As the system, I want database-per-org isolation, so that data never leaks.

**Acceptance Criteria**:
- Connection routes to correct database based on org context
- Org ID validated on every request
- No cross-org queries possible
- Audit logging per org

**Traces**: ENT-001

---

## S8-003: Organization Settings

**Story**: As an org admin, I want to manage org settings, so that the org is configured correctly.

**Acceptance Criteria**:
- Edit org name, logo
- Manage default settings
- View org members
- Configure org-level features

**Traces**: ENT-001

---

## S8-004: Organization Member Management

**Story**: As an org admin, I want to manage org members, so that I control who has access.

**Acceptance Criteria**:
- Add/remove members
- Set org-level role
- View member list
- Deactivate members

**Traces**: ENT-001
