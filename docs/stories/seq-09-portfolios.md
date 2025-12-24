# Sequence 9: Portfolios

*Parent: [USER_STORIES.md](../USER_STORIES.md)*

Flexible project grouping into portfolios. Unlike rigid PMI program management, portfolios in braidMgr are flexible containers - projects can belong to multiple portfolios, and there's no enforced hierarchy.

**Depends on**: Sequences 7 (Multi-User), 8 (Multi-Org)
**Stories**: 3
**Priority**: MVP

**Key Concept**: Portfolios aggregate metrics from multiple projects for executive dashboards while keeping project-level detail accessible.

---

## S9-001: Portfolio CRUD

**Story**: As a user, I want to create portfolios, so that I can group related projects.

**Acceptance Criteria**:
- Create portfolio (name, description)
- Edit portfolio details
- Delete portfolio (projects remain)
- List user's portfolios

**Traces**: ENT-003

---

## S9-002: Portfolio Assignment

**Story**: As a user, I want to add projects to portfolios, so that they're organized.

**Acceptance Criteria**:
- Add project to portfolio
- Remove project from portfolio
- Project can be in multiple portfolios
- Drag-drop organization (optional)

**Traces**: ENT-003

---

## S9-003: Portfolio Dashboard

**Story**: As a user, I want a portfolio dashboard, so that I see aggregated metrics.

**Acceptance Criteria**:
- Aggregated item counts across projects
- Aggregated budget totals
- List of included projects
- Drill-down to project detail

**Traces**: ENT-003
