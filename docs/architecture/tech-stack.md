# Technology Stack

*Parent: [ARCHITECTURE.md](../ARCHITECTURE.md)*

Complete technology inventory for braidMgr v2.

**Key Concepts**:
- React + Vite frontend with TypeScript
- FastAPI + Python backend with async patterns
- Aurora PostgreSQL with database-per-org isolation
- AWS cloud infrastructure

---

## Frontend

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Framework | React | 18.x | UI components |
| Build | Vite | 5.x | Fast bundler, HMR |
| Language | TypeScript | 5.x | Type safety |
| Styling | Tailwind CSS | 3.x | Utility-first CSS |
| Components | shadcn/ui | latest | Accessible components |
| State | React Query | 5.x | Server state management |
| State (UI) | Zustand | 4.x | Client state |
| PWA | vite-plugin-pwa | 0.x | Service worker, manifest |
| Testing | Vitest | 1.x | Unit tests |
| Testing | Playwright | 1.x | E2E tests |
| Linting | ESLint | 8.x | Code quality |
| Formatting | Prettier | 3.x | Code formatting |

**Why these choices**:
- **React 18**: Concurrent features, suspense boundaries
- **Vite**: Sub-second HMR, native ESM
- **shadcn/ui**: Accessible, unstyled primitives with Tailwind
- **React Query**: Excellent caching, background refetch, optimistic updates
- **Zustand**: Minimal boilerplate, no context providers needed

---

## Backend

| Component | Technology | Version | Purpose |
|-----------|------------|---------|---------|
| Framework | FastAPI | 0.110+ | Async web framework |
| Language | Python | 3.11+ | Runtime |
| Validation | Pydantic | 2.x | Request/response validation |
| ORM | None | - | Raw SQL with asyncpg |
| Database | asyncpg | 0.29+ | Async PostgreSQL driver |
| Auth | python-jose | 3.x | JWT handling |
| Auth | passlib | 1.7+ | Password hashing |
| Logging | structlog | 24.x | Structured logging |
| Testing | pytest | 8.x | Test framework |
| Testing | pytest-asyncio | 0.23+ | Async test support |
| HTTP Client | httpx | 0.27+ | Async HTTP client |

**Why these choices**:
- **FastAPI**: Native async, auto-generated OpenAPI docs, Pydantic integration
- **No ORM**: Full control over queries, better performance, explicit SQL
- **asyncpg**: Fastest Python PostgreSQL driver, native async
- **Pydantic v2**: 10x faster validation, better error messages

---

## Database

| Component | Technology | Purpose |
|-----------|------------|---------|
| Database | Aurora PostgreSQL 15 | Primary data store |
| Migration | Alembic | Schema versioning |
| Pooling | Aurora connection pooling | Connection management |

**Why Aurora**:
- Managed PostgreSQL (reduced ops burden)
- Auto-scaling read replicas
- Point-in-time recovery
- Database cloning for staging

---

## Cloud Services (AWS)

| Service | Purpose |
|---------|---------|
| ECS Fargate | Container hosting |
| Aurora PostgreSQL | Database |
| S3 | File storage |
| CloudFront | CDN, API gateway |
| Secrets Manager | Credentials storage |
| CloudWatch | Logging, metrics |
| ECR | Container registry |

**Cost optimization**:
- Fargate Spot for non-critical workloads
- Aurora Serverless v2 for variable load
- S3 Intelligent-Tiering for attachments

---

## External Services

| Service | Purpose |
|---------|---------|
| Claude API (Anthropic) | AI chat capabilities |
| Cloudflare | DNS, WAF, static hosting |

**Claude model**: claude-sonnet-4-20250514 (balanced capability and cost)
