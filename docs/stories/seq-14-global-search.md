# Sequence 14: Global Search

*Parent: [USER_STORIES.md](../USER_STORIES.md)*

Full-text search across all project data. Enables users to quickly find items, notes, and attachments by keyword.

**Depends on**: Sequences 3 (Core Data), 11 (Attachments)
**Stories**: 2
**Priority**: Post-MVP

**Key Concepts**:
- PostgreSQL full-text search
- Respects RBAC (only searches accessible data)
- Results grouped by type
- Fast response (<500ms)

---

## S14-001: Search Index

**Story**: As a developer, I want searchable content indexed, so that search is fast.

**Acceptance Criteria**:
- PostgreSQL full-text search on items
- Index on title, description, notes
- Attachment filename indexed
- Index updates on data changes

**Traces**: ENT-007

---

## S14-002: Search Interface

**Story**: As a user, I want to search across all content, so that I can find items quickly.

**Acceptance Criteria**:
- Global search bar in header
- Results grouped by type (items, attachments)
- Highlights matching text
- Click result navigates to item
- Respects RBAC permissions

**Traces**: ENT-007
