# braidMgr Implementation Patterns

*Last updated: 2024-12-24*

This document contains code patterns and templates that MUST be applied when implementing features. Patterns are carried forward into implementation sequence docs.

---

## Child Documents

| Document | Description |
|----------|-------------|
| [error-handling.md](patterns/error-handling.md) | Exception hierarchy, error logging, database error mapping |
| [logging.md](patterns/logging.md) | Structured logging, correlation IDs, log levels |
| [middleware.md](patterns/middleware.md) | Error handler, request logging middleware |
| [service-patterns.md](patterns/service-patterns.md) | ServiceRegistry, BaseService contract |
| [repository-patterns.md](patterns/repository-patterns.md) | BaseRepository with CRUD operations |
| [testing.md](patterns/testing.md) | Test structure, fixtures, unit/integration templates |
| [async-patterns.md](patterns/async-patterns.md) | Parallel operations, transaction boundaries |
| [validation-patterns.md](patterns/validation-patterns.md) | Pydantic request/response schemas |
| [react-patterns.md](patterns/react-patterns.md) | React Query hooks, component structure |

---

## Pattern Summary

### Backend Patterns

| Pattern | Purpose | Key Points |
|---------|---------|------------|
| Exception Hierarchy | Consistent error handling | AppError base class, never raw HTTPException |
| Error Logging | Debuggable failures | Always log context before raising |
| Correlation ID | Request tracing | Flows through all logs |
| Service Registry | Centralized access | Single place for all external services |
| Base Repository | Data access | Soft delete, error handling, logging |
| Transactions | Data integrity | Side effects after commit |

### Frontend Patterns

| Pattern | Purpose | Key Points |
|---------|---------|------------|
| React Query | Server state | Caching, background refetch |
| Zustand | UI state | No boilerplate, simple API |
| shadcn/ui | Components | Accessible, customizable |
| TypeScript | Type safety | Strict mode, no any |

---

## Quick Reference

### Exception Classes

| Exception | HTTP | Use When |
|-----------|------|----------|
| ValidationError | 400 | Input fails validation |
| AuthenticationError | 401 | Not authenticated |
| AuthorizationError | 403 | No permission |
| NotFoundError | 404 | Resource not found |
| ConflictError | 409 | Duplicate or state conflict |
| WorkflowError | 422 | Invalid state transition |
| DatabaseError | 500 | Database operation failed |
| ExternalServiceError | 502 | External API failed |
| ServiceUnavailableError | 503 | Service temporarily down |

### Test Distribution

| Type | Target | Scope |
|------|--------|-------|
| Unit | 80% | Mocked dependencies, pure logic |
| Integration | 15% | Real database, mocked external |
| E2E | 5% | Full HTTP stack |

---

## Checklist

Before marking any feature complete, verify:

- [ ] All database operations wrapped in try/catch
- [ ] Errors logged with context (operation, parameters, error type)
- [ ] Custom exceptions used (not raw HTTPException)
- [ ] Correlation ID flows through all logs
- [ ] No PII in log messages
- [ ] Unit tests exist for business logic
- [ ] Integration tests exist for repositories
- [ ] Pydantic schemas validate all inputs
- [ ] API returns consistent error format
