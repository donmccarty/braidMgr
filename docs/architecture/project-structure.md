# Project Structure

*Parent: [ARCHITECTURE.md](../ARCHITECTURE.md)*

Directory layout and file organization for braidMgr v2.

**Key Concepts**:
- Monorepo with backend/ and frontend/ directories
- Layered backend architecture (API → Core → Services → Repositories)
- Feature-based frontend organization
- Documentation alongside code

---

## Top-Level Structure

```
braidMgr/
├── docs/                          # Documentation
│   ├── REQUIREMENTS.md
│   ├── USER_STORIES.md
│   ├── DATA_MODEL.md
│   ├── ARCHITECTURE.md
│   ├── PATTERNS.md
│   ├── PROCESS_FLOWS.md
│   ├── STATUS.yaml
│   ├── backlog.md
│   └── implementation/
│       └── SEQUENCE_NN.md
│
├── backend/                       # FastAPI backend
├── frontend/                      # React frontend
│
├── docker-compose.yml             # Local development
├── Dockerfile.backend
├── Dockerfile.frontend
└── config.yaml                    # Configuration
```

---

## Backend Structure

```
backend/
├── src/
│   ├── api/                       # API layer (HTTP handling)
│   │   ├── __init__.py
│   │   ├── main.py                # FastAPI app, startup
│   │   ├── middleware/            # Request processing
│   │   │   ├── auth.py            # JWT validation
│   │   │   ├── correlation.py     # Request ID tracking
│   │   │   ├── error_handler.py   # Exception → response
│   │   │   └── request_logging.py # Structured logging
│   │   ├── routes/                # Endpoint handlers
│   │   │   ├── auth.py            # Login, register, refresh
│   │   │   ├── projects.py        # Project CRUD
│   │   │   ├── items.py           # Item CRUD
│   │   │   ├── budget.py          # Budget operations
│   │   │   └── chat.py            # AI chat endpoints
│   │   └── schemas/               # Pydantic request/response
│   │       ├── auth.py
│   │       ├── project.py
│   │       ├── item.py
│   │       └── chat.py
│   │
│   ├── core/                      # Business logic (no I/O)
│   │   ├── __init__.py
│   │   ├── indicators.py          # Status calculation
│   │   ├── budget.py              # Budget calculations
│   │   └── permissions.py         # RBAC logic
│   │
│   ├── domain/                    # Domain entities
│   │   ├── __init__.py
│   │   ├── user.py
│   │   ├── project.py
│   │   ├── item.py
│   │   └── chat.py
│   │
│   ├── repositories/              # Data access layer
│   │   ├── __init__.py
│   │   ├── base.py                # BaseRepository
│   │   ├── user_repository.py
│   │   ├── project_repository.py
│   │   └── item_repository.py
│   │
│   ├── services/                  # External integrations
│   │   ├── __init__.py            # ServiceRegistry
│   │   ├── base.py                # BaseService
│   │   ├── aurora_service.py      # Database
│   │   ├── s3_service.py          # File storage
│   │   └── claude_service.py      # AI chat
│   │
│   └── utils/                     # Utilities
│       ├── __init__.py
│       ├── config.py              # Configuration loading
│       ├── exceptions.py          # Custom exceptions
│       └── logging.py             # Logging setup
│
├── tests/
│   ├── conftest.py                # Shared fixtures
│   ├── unit/                      # Unit tests (80%)
│   ├── integration/               # Integration tests (15%)
│   └── e2e/                       # End-to-end tests (5%)
│
├── alembic/                       # Database migrations
│   ├── versions/
│   └── env.py
│
├── pyproject.toml
└── requirements.txt
```

**Layer responsibilities**:
- **api/**: HTTP concerns only (routing, serialization, auth middleware)
- **core/**: Pure business logic, no external dependencies, fully testable
- **domain/**: Entity definitions with validation
- **repositories/**: Database operations, SQL queries
- **services/**: External service wrappers (database, S3, Claude)

---

## Frontend Structure

```
frontend/
├── src/
│   ├── components/                # Reusable components
│   │   ├── ui/                    # shadcn/ui primitives
│   │   │   ├── button.tsx
│   │   │   ├── card.tsx
│   │   │   ├── dialog.tsx
│   │   │   └── ...
│   │   ├── layout/                # Layout components
│   │   │   ├── Sidebar.tsx
│   │   │   ├── Header.tsx
│   │   │   └── MainLayout.tsx
│   │   └── features/              # Feature-specific
│   │       ├── items/
│   │       │   ├── ItemTable.tsx
│   │       │   ├── ItemCard.tsx
│   │       │   └── EditItemDialog.tsx
│   │       ├── budget/
│   │       │   ├── BudgetMetrics.tsx
│   │       │   └── BurnChart.tsx
│   │       └── chat/
│   │           ├── ChatPanel.tsx
│   │           └── MessageList.tsx
│   │
│   ├── pages/                     # Page components
│   │   ├── Dashboard.tsx
│   │   ├── Items.tsx
│   │   ├── Timeline.tsx
│   │   ├── Budget.tsx
│   │   └── Chat.tsx
│   │
│   ├── hooks/                     # Custom hooks
│   │   ├── useAuth.ts
│   │   ├── useProjects.ts
│   │   └── useItems.ts
│   │
│   ├── lib/                       # Utilities
│   │   ├── api.ts                 # API client
│   │   ├── auth.ts                # Auth utilities
│   │   └── utils.ts
│   │
│   ├── stores/                    # Zustand stores
│   │   └── uiStore.ts             # UI state (sidebar, etc.)
│   │
│   ├── types/                     # TypeScript types
│   │   ├── api.ts                 # API types
│   │   ├── project.ts
│   │   └── item.ts
│   │
│   ├── App.tsx                    # Root component
│   └── main.tsx                   # Entry point
│
├── public/                        # Static assets
├── index.html
├── package.json
├── tailwind.config.js
├── tsconfig.json
└── vite.config.ts
```

**Component organization**:
- **ui/**: Reusable primitives (shadcn/ui components)
- **layout/**: App shell components (header, sidebar)
- **features/**: Domain-specific components grouped by feature
- **pages/**: Top-level page components for routing
