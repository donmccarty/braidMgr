# Sequence 1: Foundation

*Parent: [USER_STORIES.md](../USER_STORIES.md)*

Infrastructure and project scaffolding.

**Depends on**: None
**Stories**: 8
**Priority**: MVP

---

## S1-001: FastAPI Project Setup

**Story**: As a developer, I want the FastAPI backend scaffolded with proper structure, so that I can build API endpoints following established patterns.

**Acceptance Criteria**:
- Project structure created (src/api, src/services, src/repositories, src/domain)
- FastAPI app configured with CORS, middleware
- Health check endpoint /health returns status
- OpenAPI docs available at /docs
- uvicorn configured for development

**Traces**: WEB-004

---

## S1-002: React Project Setup

**Story**: As a developer, I want the React frontend scaffolded with Vite and TypeScript, so that I can build UI components.

**Acceptance Criteria**:
- Vite + React 18 + TypeScript project created
- Tailwind CSS configured
- shadcn/ui initialized with base components
- ESLint + Prettier configured
- Development server runs with hot reload

**Traces**: WEB-003, WEB-008

---

## S1-003: PostgreSQL Schema Setup

**Story**: As a developer, I want the PostgreSQL schema created with migrations, so that data can be persisted.

**Acceptance Criteria**:
- Alembic configured for migrations
- Initial migration creates all v1.5 tables
- Enum types created (item_type, indicator, role)
- Indexes on frequently queried columns
- Connection pooling configured

**Traces**: WEB-005

---

## S1-004: Service Centralization

**Story**: As a developer, I want a centralized service registry, so that all external service access goes through a single interface.

**Acceptance Criteria**:
- ServiceRegistry singleton implemented
- BaseService abstract class with logging, retry
- AuroraService (database) implemented
- Services validate connections at startup
- Health checks for all services

**Traces**: WEB-004, ENT-008

---

## S1-005: Error Handling Framework

**Story**: As a developer, I want consistent error handling, so that all errors return predictable responses.

**Acceptance Criteria**:
- Custom exception hierarchy (AppError base)
- ValidationError, NotFoundError, AuthenticationError, etc.
- Error handler middleware maps exceptions to HTTP responses
- Correlation ID included in error responses
- No sensitive data in error messages

**Traces**: WEB-007

---

## S1-006: Structured Logging

**Story**: As a developer, I want structured logging with correlation IDs, so that requests can be traced across logs.

**Acceptance Criteria**:
- structlog configured
- Correlation ID middleware adds ID to all logs
- Request logging middleware (start, complete, timing)
- Log levels by layer (API=INFO, Repository=DEBUG)
- JSON format in production, console in dev

**Traces**: ENT-008

---

## S1-007: Configuration Management

**Story**: As a developer, I want centralized configuration, so that settings are consistent and environment-aware.

**Acceptance Criteria**:
- config.yaml with all settings
- Environment variable substitution ${VAR}
- Pydantic settings for validation
- Secrets loaded from environment (not in config)
- Defaults for local development

**Traces**: WEB-004

---

## S1-008: Docker Development Environment

**Story**: As a developer, I want Docker Compose for local development, so that I can run all services locally.

**Acceptance Criteria**:
- docker-compose.yml with PostgreSQL, API, frontend
- Volume mounts for hot reload
- Environment variables configured
- Single command startup (docker compose up)
- Database initialization on first run

**Traces**: WEB-005
