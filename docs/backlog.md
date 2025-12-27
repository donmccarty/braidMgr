# braidMgr Backlog

*Last updated: 2025-12-27*

This document tracks technical decisions, priorities, and pending work items outside the main user story sequences.

---

## Infrastructure Tasks

### INFRA-001: MkDocs Documentation Site

**Status**: Complete
**Priority**: P1
**Completed**: 2025-12-26

Created documentation site using MkDocs Material theme.

**Completed**:
- [x] Create mkdocs.yml configuration
- [x] Navigation structure for all existing docs
- [x] Light/dark mode toggle
- [x] Code highlighting with copy buttons
- [x] Search plugin

**To build/serve**:
```bash
/Applications/Xcode.app/Contents/Developer/usr/bin/python3 -m mkdocs serve
```

**Future enhancements** (optional):
- [ ] Add mermaid diagram support
- [ ] Create User Guide section
- [ ] Create FAQ / Knowledge Base
- [ ] Add custom CSS for branding

---

### INFRA-002: Cloudflare Pages Hosting

**Status**: Complete
**Priority**: P1
**Depends on**: INFRA-001
**Completed**: 2025-12-26

Deploy documentation site to Cloudflare Pages.

**Live URL**: https://braidmgr-docs.pages.dev/

**Completed**:
- [x] Create Cloudflare Pages project (wrangler pages project create)
- [x] Initial deployment (wrangler pages deploy site)
- [x] Create deployment guide (docs/deployment/cloudflare-pages.md)
- [x] SSL certificate (automatic)

**Pending** (optional):
- [ ] Connect to GitHub for automatic deployments
- [ ] Configure custom domain

---

### INFRA-003: GitHub Actions CI/CD

**Status**: Complete
**Priority**: P2
**Completed**: 2025-12-26

Set up continuous integration and deployment.

**Workflows Created**:
- `.github/workflows/ci.yml` - Tests, linting, type checking on PRs
- `.github/workflows/deploy-docs.yml` - Auto-deploy docs to Cloudflare Pages

**Completed**:
- [x] Backend tests on PR (pytest)
- [x] Frontend tests on PR (vitest)
- [x] Linting (ruff, eslint)
- [x] Type checking (mypy, tsc)
- [x] Build verification
- [x] Deploy docs on merge to main
- [x] E2E tests on main branch

**Required Secrets** (set in GitHub repo settings):
- `CLOUDFLARE_API_TOKEN` - API token with Pages permissions
- `CLOUDFLARE_ACCOUNT_ID` - 88e50c4ee658ed559d5153f0b2f7e77b

**Pending** (optional):
- [ ] Deploy app on release tag

---

### INFRA-004: GitHub Secrets for Docs Auto-Deploy

**Status**: Pending
**Priority**: P3

Add secrets to GitHub repo for automatic docs deployment.

**Secrets needed** (Settings → Secrets → Actions):
- `CLOUDFLARE_API_TOKEN` - API token with Pages permissions
- `CLOUDFLARE_ACCOUNT_ID` - `88e50c4ee658ed559d5153f0b2f7e77b`

**Note**: Until added, deploy docs manually with `wrangler pages deploy site --project-name braidmgr-docs`

---

### DEMO-001: Record Comprehensive Demo with Chat

**Status**: Pending
**Priority**: P2

Record new demo video showcasing all functionality including AI chat.

**Prerequisites**:
- braidMgr backend running on port 8000 (not ali-ai-acctg)
- Frontend dev server running on port 5173
- Test data loaded in database

**Demo sections** (in demo-walkthrough.spec.ts):
1. Login flow
2. Project selection
3. Dashboard overview
4. All Items view with filtering
5. Active Items (severity grouping)
6. Timeline view
7. Deliverables view
8. **AI Chat Assistant** (NEW)
   - Query data: "What items are overdue or at risk?"
   - Meeting notes to actions: paste notes, get proposed updates
9. Closing

**To run**:
```bash
cd frontend && npx playwright test --project=demo-recording --reporter=list
```

**Output**: `docs/demo/braidmgr-demo.webm`

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
| - | None | - |

---

## P2: Medium Priority

| ID | Description | Status |
|----|-------------|--------|
| DEMO-001 | Record comprehensive demo with chat | Pending |

---

## P3: Low Priority

| ID | Description | Status |
|----|-------------|--------|
| INFRA-004 | Add GitHub secrets for docs auto-deploy | Pending |

---

## Resolved

| ID | Description | Completed |
|----|-------------|-----------|
| INFRA-001 | MkDocs documentation site | 2025-12-26 |
| INFRA-002 | Cloudflare Pages hosting | 2025-12-26 |
| INFRA-003 | GitHub Actions CI/CD | 2025-12-26 |
