# API Middleware Patterns

*Parent: [PATTERNS.md](../PATTERNS.md)*

FastAPI middleware for error handling and request logging.

**Key Concepts**:
- Error handler converts AppError to JSON response
- Request logging tracks duration and status
- Middleware order matters (correlation first, then logging, then auth)

---

## Error Handler Middleware

```python
# src/api/middleware/error_handler.py
from fastapi import Request
from fastapi.responses import JSONResponse
from src.utils.exceptions import AppError
import structlog

logger = structlog.get_logger()

async def app_error_handler(request: Request, exc: AppError) -> JSONResponse:
    """Convert application errors to consistent JSON responses."""
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": exc.error_code,
            "message": exc.message,
            "details": exc.details,
            "correlation_id": getattr(request.state, "correlation_id", None),
        }
    )

async def unhandled_error_handler(request: Request, exc: Exception) -> JSONResponse:
    """Catch-all for unexpected errors."""
    correlation_id = getattr(request.state, "correlation_id", "unknown")
    logger.exception(
        "unhandled_error",
        correlation_id=correlation_id,
        path=request.url.path,
    )
    return JSONResponse(
        status_code=500,
        content={
            "error": "INTERNAL_ERROR",
            "message": "An unexpected error occurred",
            "correlation_id": correlation_id,
        }
    )
```

---

## Request Logging Middleware

```python
# src/api/middleware/request_logging.py
import time
import structlog
from starlette.middleware.base import BaseHTTPMiddleware

logger = structlog.get_logger()

class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        start_time = time.perf_counter()

        logger.info(
            "request_started",
            method=request.method,
            path=request.url.path,
            query=str(request.query_params),
        )

        response = await call_next(request)

        duration_ms = (time.perf_counter() - start_time) * 1000
        logger.info(
            "request_completed",
            method=request.method,
            path=request.url.path,
            status_code=response.status_code,
            duration_ms=round(duration_ms, 2),
        )

        return response
```

---

## Middleware Registration Order

Order matters - register in this sequence:

```python
# src/api/main.py
from fastapi import FastAPI
from src.api.middleware.correlation import CorrelationIdMiddleware
from src.api.middleware.request_logging import RequestLoggingMiddleware
from src.api.middleware.error_handler import app_error_handler, unhandled_error_handler
from src.utils.exceptions import AppError

app = FastAPI()

# 1. Correlation ID (first - sets context for all others)
app.add_middleware(CorrelationIdMiddleware)

# 2. Request logging (after correlation so ID is available)
app.add_middleware(RequestLoggingMiddleware)

# 3. Exception handlers (catch errors from routes)
app.add_exception_handler(AppError, app_error_handler)
app.add_exception_handler(Exception, unhandled_error_handler)
```

---

## Middleware Flow

```
Request
  │
  ▼
CorrelationIdMiddleware  ──→ Sets X-Correlation-ID
  │
  ▼
RequestLoggingMiddleware ──→ Logs request_started
  │
  ▼
Route Handler            ──→ Business logic
  │
  ▼ (if error)
Exception Handler        ──→ AppError → JSON response
  │
  ▼
RequestLoggingMiddleware ──→ Logs request_completed
  │
  ▼
Response
```
