# braidMgr Architecture

*Last updated: 2024-12-24*

This document describes the system architecture for braidMgr v2, a multi-tenant, multi-user RAID log management application with AI chat capabilities.

---

## Child Documents

| Document | Description |
|----------|-------------|
| [tech-stack.md](architecture/tech-stack.md) | Technology inventory (React, FastAPI, Aurora, AWS) |
| [project-structure.md](architecture/project-structure.md) | Directory layout and file organization |
| [services.md](architecture/services.md) | Service centralization pattern |
| [api-design.md](architecture/api-design.md) | REST API conventions and endpoints |
| [database.md](architecture/database.md) | Multi-tenant database strategy |
| [auth-rbac.md](architecture/auth-rbac.md) | Authentication and authorization |
| [ai-integration.md](architecture/ai-integration.md) | Claude API integration |
| [frontend.md](architecture/frontend.md) | React + Vite frontend architecture |
| [deployment.md](architecture/deployment.md) | AWS infrastructure and CI/CD |

---

## Design Principles

### Service Centralization

All external service access MUST go through centralized service modules.

**Benefits**:
- Single place to modify connection logic, credentials, retry policies
- Consistent error handling and logging
- Testable via dependency injection
- Audit trail for all external calls

```python
# Correct - use service registry
from src.services import services
result = await services.aurora.execute_query(...)

# Incorrect - direct access
import asyncpg
conn = await asyncpg.connect(...)  # DON'T DO THIS
```

### Fail Fast

Validate all configuration and connections at startup. Don't wait for first request to discover problems.

### Audit Everything

All data changes logged with actor, timestamp, before/after state. No exceptions.

### Defense in Depth

- Validate at API boundary (Pydantic schemas)
- Validate at service layer (business rules)
- Validate at database (constraints)

### Clean Separation

- **Core**: Pure business logic, no I/O dependencies
- **Services**: External integrations (DB, S3, Claude)
- **API**: HTTP layer, request/response handling
- **UI**: Presentation only, no business logic

---

## System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        Cloudflare CDN                            │
│                    (Static assets, WAF)                          │
└─────────────────────────────────────────────────────────────────┘
                                │
                                ▼
┌─────────────────────────────────────────────────────────────────┐
│                         AWS CloudFront                           │
│                      (API Gateway, SSL)                          │
└─────────────────────────────────────────────────────────────────┘
                                │
                    ┌───────────┴───────────┐
                    ▼                       ▼
        ┌───────────────────┐   ┌───────────────────┐
        │   React Frontend   │   │   FastAPI Backend  │
        │   (Vite, PWA)      │   │   (ECS Fargate)    │
        └───────────────────┘   └───────────────────┘
                                        │
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
        ┌───────────────────┐ ┌───────────────────┐ ┌───────────────────┐
        │  Aurora PostgreSQL │ │    Amazon S3      │ │   Claude API      │
        │   (Multi-DB)       │ │  (Attachments)    │ │   (Anthropic)     │
        └───────────────────┘ └───────────────────┘ └───────────────────┘
```

---

## Quick Reference

### Tech Stack Summary

| Layer | Technology |
|-------|------------|
| Frontend | React 18, Vite, TypeScript, Tailwind, shadcn/ui |
| Backend | Python 3.11+, FastAPI, Pydantic v2 |
| Database | Aurora PostgreSQL 15 (database-per-org) |
| Auth | JWT tokens, OAuth (Google, Microsoft) |
| AI | Claude API (claude-sonnet-4-20250514) |
| Storage | S3 for attachments |
| Hosting | AWS (ECS Fargate, Aurora, CloudFront) |

### Key Architecture Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Multi-tenancy | Database-per-org | Complete isolation, compliance-friendly |
| ORM | None (raw SQL) | Full control, better performance |
| State management | React Query + Zustand | Server state vs UI state separation |
| AI context | Project-scoped | Focused, accurate responses |

---

## Related Documentation

| Document | Purpose |
|----------|---------|
| [REQUIREMENTS.md](REQUIREMENTS.md) | Business requirements |
| [USER_STORIES.md](USER_STORIES.md) | Implementation stories |
| [DATA_MODEL.md](DATA_MODEL.md) | Database schema |
| [PATTERNS.md](PATTERNS.md) | Code patterns |
| [PROCESS_FLOWS.md](PROCESS_FLOWS.md) | State machines |
