# braidMgr User Stories

*Last updated: 2024-12-24*

This document organizes braidMgr implementation into user stories, sequenced by dependencies. Stories trace to requirements in [REQUIREMENTS.md](REQUIREMENTS.md).

---

## Story Format

Each story includes:
- **ID**: Unique identifier (S1-001 = Sequence 1, Story 001)
- **Title**: Brief description
- **Story**: As a [role], I want [goal], so that [benefit]
- **Acceptance Criteria**: Testable conditions
- **Traces**: Requirement IDs from REQUIREMENTS.md

---

## Sequence Overview

### v1.5 - Web Conversion (Sequences 1-6)

| Seq | Name | Stories | Dependencies | Priority | Document |
|-----|------|---------|--------------|----------|----------|
| 1 | Foundation | 8 | None | MVP | [seq-01-foundation.md](stories/seq-01-foundation.md) |
| 2 | Authentication | 6 | Seq 1 | MVP | [seq-02-authentication.md](stories/seq-02-authentication.md) |
| 3 | Core Data | 8 | Seq 1, 2 | MVP | [seq-03-core-data.md](stories/seq-03-core-data.md) |
| 4 | Views | 8 | Seq 3 | MVP | [seq-04-views.md](stories/seq-04-views.md) |
| 5 | Budget | 4 | Seq 3 | MVP | [seq-05-budget.md](stories/seq-05-budget.md) |
| 6 | PWA | 3 | Seq 4, 5 | MVP | [seq-06-pwa.md](stories/seq-06-pwa.md) |

### v2.0 - Enterprise Features (Sequences 7-14)

| Seq | Name | Stories | Dependencies | Priority | Document |
|-----|------|---------|--------------|----------|----------|
| 7 | Multi-User | 6 | Seq 2 | MVP | [seq-07-multi-user.md](stories/seq-07-multi-user.md) |
| 8 | Multi-Org | 4 | Seq 7 | MVP | [seq-08-multi-org.md](stories/seq-08-multi-org.md) |
| 9 | Portfolios | 3 | Seq 7, 8 | MVP | [seq-09-portfolios.md](stories/seq-09-portfolios.md) |
| 10 | AI Chat | 5 | Seq 3, 7 | MVP | [seq-10-ai-chat.md](stories/seq-10-ai-chat.md) |
| 11 | Attachments | 3 | Seq 3, 8 | Post-MVP | [seq-11-attachments.md](stories/seq-11-attachments.md) |
| 12 | Exports | 3 | Seq 4, 5 | MVP | [seq-12-exports.md](stories/seq-12-exports.md) |
| 13 | SSO | 2 | Seq 7, 8 | Post-MVP | [seq-13-sso.md](stories/seq-13-sso.md) |
| 14 | Global Search | 2 | Seq 3, 11 | Post-MVP | [seq-14-global-search.md](stories/seq-14-global-search.md) |

---

## Dependency Graph

```
Sequence 1 (Foundation)
    │
    ├──→ Sequence 2 (Auth)
    │         │
    │         ├──→ Sequence 7 (Multi-User)
    │         │         │
    │         │         ├──→ Sequence 8 (Multi-Org)
    │         │         │         │
    │         │         │         ├──→ Sequence 9 (Portfolios)
    │         │         │         │
    │         │         │         └──→ Sequence 11 (Attachments) ──→ Sequence 14 (Search)
    │         │         │
    │         │         └──→ Sequence 13 (SSO)
    │         │
    │         └──→ Sequence 3 (Core Data)
    │                   │
    │                   ├──→ Sequence 4 (Views) ──→ Sequence 6 (PWA)
    │                   │         │
    │                   │         └──→ Sequence 12 (Exports)
    │                   │
    │                   ├──→ Sequence 5 (Budget)
    │                   │
    │                   └──→ Sequence 10 (AI Chat)
```

---

## Story Count Summary

| Sequence | Name | Stories | Priority |
|----------|------|---------|----------|
| 1 | Foundation | 8 | MVP |
| 2 | Authentication | 6 | MVP |
| 3 | Core Data | 8 | MVP |
| 4 | Views | 8 | MVP |
| 5 | Budget | 4 | MVP |
| 6 | PWA | 3 | MVP |
| 7 | Multi-User | 6 | MVP |
| 8 | Multi-Org | 4 | MVP |
| 9 | Portfolios | 3 | MVP |
| 10 | AI Chat | 5 | MVP |
| 11 | Attachments | 3 | Post-MVP |
| 12 | Exports | 3 | MVP |
| 13 | SSO | 2 | Post-MVP |
| 14 | Global Search | 2 | Post-MVP |
| **Total** | | **65** | **57 MVP** |

---

## Requirements Coverage

All requirements from [REQUIREMENTS.md](REQUIREMENTS.md) are traced:
- **PAR (18)**: Covered in Sequences 3, 4, 5, 12
- **WEB (8)**: Covered in Sequences 1, 2, 4, 6
- **ENT (9)**: Covered in Sequences 7, 8, 9, 10, 11, 13, 14

Coverage: 100%
