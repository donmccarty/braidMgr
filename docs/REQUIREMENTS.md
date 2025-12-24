# braidMgr Requirements

*Last updated: 2024-12-24*

This document defines requirements for braidMgr v1.5 and v2.

---

## Requirement Categories

| Category | Description | Count | Document |
|----------|-------------|-------|----------|
| **PAR** | v1 Parity (features to maintain) | 18 | [feature-parity.md](requirements/feature-parity.md) |
| **WEB** | Web Platform (v1.5 PWA) | 8 | [web-platform.md](requirements/web-platform.md) |
| **ENT** | Enterprise (v2 multi-tenant) | 9 | [enterprise.md](requirements/enterprise.md) |

---

## Requirement Format

Each requirement includes:
- **ID**: Unique identifier (PAR-001, WEB-001, ENT-001)
- **Title**: Brief description
- **Description**: Detailed requirement
- **Acceptance Criteria**: Testable conditions
- **Priority**: MVP or Post-MVP

---

## Summary

| Category | Count | MVP | Post-MVP |
|----------|-------|-----|----------|
| PAR (Parity) | 18 | 18 | 0 |
| WEB (Web Platform) | 8 | 8 | 0 |
| ENT (Enterprise) | 9 | 5 | 4 |
| **Total** | **35** | **31** | **4** |

---

## Quick Reference

### PAR: Feature Parity (18 requirements)
- PAR-001 to PAR-004: Core data (item types, fields, indicators, metadata)
- PAR-005 to PAR-010: Views (dashboard, items, active, timeline, chronology, budget)
- PAR-011 to PAR-013: Data (budget model, edit dialog, YAML persistence)
- PAR-014 to PAR-018: Features (exports, filtering, help, update indicators)

### WEB: Web Platform (8 requirements)
- WEB-001 to WEB-002: PWA and responsive design
- WEB-003 to WEB-005: Tech stack (React, FastAPI, PostgreSQL)
- WEB-006 to WEB-008: Infrastructure (auth, error handling, loading states)

### ENT: Enterprise (9 requirements)
- ENT-001 to ENT-004: Core (multi-tenancy, roles, portfolios, AI chat)
- ENT-005 to ENT-009: Extended (attachments, SSO, search, audit, collaboration)

---

## Traceability

All requirements are traced to:
- User stories in [USER_STORIES.md](USER_STORIES.md)
- Implementation sequences in [stories/](stories/)
- Test cases in tests/

See [USER_STORIES.md](USER_STORIES.md) for story-to-requirement mapping.
