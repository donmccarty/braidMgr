# Error Handling Pattern

*Parent: [PATTERNS.md](../PATTERNS.md)*

Custom exception hierarchy and error handling conventions.

**Key Concepts**:
- All exceptions inherit from AppError
- Use custom exceptions instead of raw HTTPException
- Always log errors with context before raising
- Map database exceptions to app exceptions

---

## Exception Hierarchy

All exceptions inherit from AppError. Use these instead of raw HTTPException:

```python
# src/utils/exceptions.py

class AppError(Exception):
    """Base application error."""
    status_code: int = 500
    error_code: str = "INTERNAL_ERROR"

    def __init__(
        self,
        message: str,
        details: dict = None,
        **kwargs
    ):
        self.message = message
        self.details = details or {}
        self.details.update(kwargs)
        super().__init__(message)


class ValidationError(AppError):
    """400 - Input validation failed."""
    status_code = 400
    error_code = "VALIDATION_ERROR"


class AuthenticationError(AppError):
    """401 - Not authenticated."""
    status_code = 401
    error_code = "AUTHENTICATION_ERROR"


class AuthorizationError(AppError):
    """403 - No permission."""
    status_code = 403
    error_code = "AUTHORIZATION_ERROR"


class NotFoundError(AppError):
    """404 - Resource not found."""
    status_code = 404
    error_code = "NOT_FOUND"

    def __init__(self, resource: str, identifier: str):
        super().__init__(
            f"{resource} not found",
            resource=resource,
            identifier=identifier
        )


class ConflictError(AppError):
    """409 - Duplicate or state conflict."""
    status_code = 409
    error_code = "CONFLICT"


class WorkflowError(AppError):
    """422 - Invalid state transition."""
    status_code = 422
    error_code = "WORKFLOW_ERROR"


class DatabaseError(AppError):
    """500 - Database operation failed."""
    status_code = 500
    error_code = "DATABASE_ERROR"


class ExternalServiceError(AppError):
    """502 - External API failed."""
    status_code = 502
    error_code = "EXTERNAL_SERVICE_ERROR"


class ServiceUnavailableError(AppError):
    """503 - Service temporarily unavailable."""
    status_code = 503
    error_code = "SERVICE_UNAVAILABLE"
```

---

## Error Logging Pattern

**ALWAYS log errors with context before raising:**

```python
import structlog

logger = structlog.get_logger()

async def some_operation(resource_id: UUID, user_id: UUID):
    # Bind context for all logs in this operation
    log = logger.bind(resource_id=str(resource_id), user_id=str(user_id))

    try:
        result = await do_something(resource_id)
        log.info("operation_completed", result_count=len(result))
        return result
    except SpecificDatabaseError as e:
        log.error(
            "operation_failed",
            error_type=type(e).__name__,
            error_message=str(e),
            # NEVER log PII: passwords, tokens, SSN, etc.
        )
        raise DatabaseError(
            "Failed to complete operation",
            operation="some_operation",
            details={"resource_id": str(resource_id)}
        )
    except Exception as e:
        log.exception("unexpected_error")  # Includes stack trace
        raise
```

---

## Database Error Mapping

Map asyncpg exceptions to app exceptions:

```python
import asyncpg

async def execute_with_error_handling(query: str, *args):
    try:
        return await self._pool.fetch(query, *args)
    except asyncpg.UniqueViolationError as e:
        raise ConflictError(
            "Resource already exists",
            field=e.constraint_name,
        )
    except asyncpg.ForeignKeyViolationError as e:
        raise ValidationError(
            "Referenced resource not found",
            field=e.constraint_name,
        )
    except asyncpg.CheckViolationError as e:
        raise ValidationError(
            "Value out of allowed range",
            field=e.constraint_name,
        )
    except asyncpg.PostgresConnectionError as e:
        logger.critical("database_connection_failed", error=str(e))
        raise ServiceUnavailableError("Database temporarily unavailable")
```

---

## Error Response Format

All errors return consistent JSON:

```json
{
    "error": "VALIDATION_ERROR",
    "message": "Invalid input",
    "details": {
        "field": "email",
        "reason": "Invalid email format"
    },
    "correlation_id": "abc-123-def"
}
```
