# Logging Pattern

*Parent: [PATTERNS.md](../PATTERNS.md)*

Structured logging with correlation IDs.

**Key Concepts**:
- structlog for structured logging
- Correlation ID flows through all logs
- JSON output in production, colored console in dev
- Never log sensitive data

---

## Logging Setup

```python
# src/utils/logging.py
import logging
import structlog

def setup_logging(environment: str, log_level: str = "INFO"):
    """Configure structured logging."""

    logging.basicConfig(level=getattr(logging, log_level))

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.add_log_level,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if environment == "production":
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer(colors=True))

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level)
        ),
        context_class=dict,
        cache_logger_on_first_use=True,
    )
```

---

## Correlation ID Middleware

```python
# src/api/middleware/correlation.py
import uuid
import structlog
from contextvars import ContextVar
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

correlation_id_var: ContextVar[str] = ContextVar("correlation_id", default="")

class CorrelationIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Get from header or generate new
        correlation_id = request.headers.get(
            "X-Correlation-ID",
            str(uuid.uuid4())
        )
        correlation_id_var.set(correlation_id)

        # Bind to structlog context
        structlog.contextvars.bind_contextvars(correlation_id=correlation_id)

        # Store on request for error handlers
        request.state.correlation_id = correlation_id

        response = await call_next(request)
        response.headers["X-Correlation-ID"] = correlation_id

        return response
```

---

## Log Levels by Layer

| Layer | Default Level | What to Log |
|-------|---------------|-------------|
| API | INFO | Request received, response sent, status codes |
| Middleware | INFO | Auth success/failure, rate limit hits |
| Core | INFO | Business events, state transitions |
| Repository | DEBUG | Query execution (no sensitive data) |
| Service | DEBUG | External API calls, retries, timeouts |

---

## Sensitive Data - NEVER Log

- Passwords or password hashes
- JWT tokens or API keys
- Full credit card numbers
- Social Security Numbers
- Personal health information

---

## Logging Examples

```python
# Good: contextual, structured
logger.info(
    "item_created",
    project_id=str(project_id),
    item_num=item.item_num,
    item_type=item.type,
)

# Good: error with context
logger.error(
    "database_query_failed",
    operation="find_by_id",
    table="items",
    error_type=type(e).__name__,
)

# BAD: unstructured string
logger.info(f"Created item {item.id} in project {project_id}")

# BAD: logging sensitive data
logger.info("User login", password=user.password)
```
