# braidMgr Backlog

*Last updated: 2024-12-24*

This document tracks technical decisions, priorities, and pending work items outside the main user story sequences.

---

## Infrastructure Tasks

### INFRA-001: MkDocs Documentation Site

**Status**: Pending
**Priority**: P1

Create a documentation site using MkDocs Material theme (similar to ali-ai-ingestion-engine).

**Tasks**:
- [ ] Create mkdocs.yml configuration
- [ ] Set up docs/ folder structure for MkDocs
- [ ] Create index.md home page
- [ ] Create navigation structure:
  - Overview (value proposition, roadmap)
  - **User Guide** (getting started, features, workflows)
  - **FAQ / Knowledge Base** (common questions, troubleshooting)
  - Architecture (system design, tech stack)
  - Data Model (entities, ERD)
  - API Reference (endpoints, schemas)
  - Development (setup, contributing)
  - Operations (deployment, troubleshooting)
- [ ] Add mermaid diagram support
- [ ] Configure search and tags plugins
- [ ] Add custom CSS for branding

**Reference**: /Users/donmccarty/ali-ai-ingestion-engine/mkdocs.yml

---

### INFRA-002: Cloudflare Pages Hosting

**Status**: Pending
**Priority**: P1
**Depends on**: INFRA-001

Deploy documentation site to Cloudflare Pages.

**Tasks**:
- [ ] Create Cloudflare Pages project
- [ ] Connect to GitHub repository
- [ ] Configure build command (mkdocs build)
- [ ] Set output directory (site/)
- [ ] Configure custom domain (optional)
- [ ] Set up automatic deployments on push to main
- [ ] Verify SSL certificate

---

### INFRA-003: GitHub Actions CI/CD

**Status**: Pending
**Priority**: P2

Set up continuous integration and deployment.

**Tasks**:
- [ ] Backend tests on PR
- [ ] Frontend tests on PR
- [ ] Linting and type checking
- [ ] Build verification
- [ ] Deploy docs on merge to main
- [ ] Deploy app on release tag

---

## Technical Decisions

### DECISION-001: Database-per-Org Multi-Tenancy

**Status**: Approved
**Date**: 2024-12-24

Use separate PostgreSQL databases per organization for complete data isolation.

**Rationale**:
- Strongest isolation (no accidental data leakage)
- Easier compliance (data residency, retention per org)
- Performance isolation (one org's load doesn't affect others)
- Simpler backup/restore per org

**Trade-offs**:
- More database connections to manage
- Cross-org queries not possible (feature, not bug)
- More complex provisioning

---

### DECISION-002: React + Vite + shadcn/ui Frontend

**Status**: Approved
**Date**: 2024-12-24

Use React 18 with Vite build tool and shadcn/ui component library.

**Rationale**:
- Claude has extensive training data on React
- Vite is modern and fast
- shadcn/ui is accessible and customizable
- TypeScript for type safety

---

### DECISION-003: FastAPI + Pydantic Backend

**Status**: Approved
**Date**: 2024-12-24

Use Python FastAPI with Pydantic v2 for validation.

**Rationale**:
- Reuse existing Python core logic from v1
- FastAPI is fast and well-documented
- Pydantic v2 is faster and more capable
- Async support with asyncpg

---

### DECISION-004: Portfolio Flexibility

**Status**: Approved
**Date**: 2024-12-24

Portfolios are flexible containers, not rigid PMI programs.

**Rationale**:
- Users organize projects however they want
- No enforced hierarchy or dependencies
- Projects can be in multiple portfolios
- Simpler to implement and use

---

### DECISION-005: AI Chat Default Scope

**Status**: Approved
**Date**: 2024-12-24

AI chat defaults to current project context, expandable by asking.

**Rationale**:
- Focused context = better responses
- RBAC enforced (only accessible data)
- User can ask "across all my projects" to expand
- Simpler initial implementation

---

### DECISION-006: Budget Data Model Redesign

**Status**: Approved
**Date**: 2024-12-24

Redesign budget schema for optimal flexibility (not v1 format).

**Rationale**:
- v1 format tied to one company's import
- New schema supports:
  - Rate cards with role/resource mapping
  - Timesheet/actuals tracking
  - Budget allocations by workstream/phase
  - Variance tracking (planned vs actual)
  - Forecasting data

---

### DECISION-007: Project Locking for Multi-User

**Status**: Pending
**Date**: 2024-12-24
**Applies to**: Sequence 7 (Multi-User)

Use pessimistic locking for project editing instead of real-time collaboration.

**Proposed Model**:
- One PM locks a project for editing (explicit checkout)
- While locked, others have read-only access
- Lock timeout (TBD: 30 min?) or manual release
- Org admins can force-unlock if needed

**Portfolio Views**:
- Read-only aggregate views (no locking needed)
- Program manager can add portfolio-level notes (separate from project data)
- Optional: "Lock for review" to freeze projects temporarily

**Rationale**:
- Simpler than real-time collaboration (no WebSockets, no conflict resolution)
- Fits traditional PM workflow (one owner at a time)
- Avoids merge conflicts entirely

**Open Questions**:
- Lock timeout duration?
- Lock at project level or workstream level?
- Portfolio notes: simple text or structured items?

---

## P0: Blocking Issues

None currently.

---

## P1: High Priority

| ID | Description | Status |
|----|-------------|--------|
| INFRA-001 | MkDocs documentation site | Pending |
| INFRA-002 | Cloudflare Pages hosting | Pending |

---

## P2: Medium Priority

| ID | Description | Status |
|----|-------------|--------|
| INFRA-003 | GitHub Actions CI/CD | Pending |

---

## P3: Low Priority

None currently.

---

## Resolved

None yet.
