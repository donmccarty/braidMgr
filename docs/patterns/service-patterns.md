# Service Patterns

*Parent: [PATTERNS.md](../PATTERNS.md)*

Service centralization and base service contract.

**Key Concepts**:
- All external access through ServiceRegistry singleton
- Services initialized at startup (fail fast)
- BaseService provides logging and health check contract
- Never access external services directly

---

## Service Registry

```python
# src/services/__init__.py

class ServiceRegistry:
    """Singleton registry for all external services."""

    _instance = None
    _initialized = False

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def initialize(self, config: AppConfig) -> None:
        """Initialize all services at startup."""
        if self._initialized:
            return

        self._aurora = AuroraService(config.database)
        self._s3 = S3Service(config.s3)
        self._claude = ClaudeService(config.claude)

        self._validate_connections()
        self._initialized = True

    @property
    def aurora(self) -> AuroraService:
        self._ensure_initialized()
        return self._aurora

    @property
    def s3(self) -> S3Service:
        self._ensure_initialized()
        return self._s3

    @property
    def claude(self) -> ClaudeService:
        self._ensure_initialized()
        return self._claude

    def _ensure_initialized(self) -> None:
        if not self._initialized:
            raise RuntimeError(
                "ServiceRegistry not initialized. "
                "Call services.initialize(config) at startup."
            )

    def _validate_connections(self) -> None:
        """Verify all services are reachable."""
        # Each service implements health_check()
        pass

# Singleton instance
services = ServiceRegistry()
```

---

## Base Service

```python
# src/services/base.py
from abc import ABC, abstractmethod
import structlog
import asyncio

class BaseService(ABC):
    """Base class for all services."""

    def __init__(self, config):
        self.config = config
        self.logger = structlog.get_logger().bind(service=self.__class__.__name__)

    @abstractmethod
    async def health_check(self) -> bool:
        """Check service health."""
        pass

    async def with_retry(
        self,
        operation,
        max_attempts: int = 3,
        backoff_seconds: float = 1.0
    ):
        """Execute operation with exponential backoff retry."""
        for attempt in range(max_attempts):
            try:
                return await operation()
            except Exception as e:
                if attempt == max_attempts - 1:
                    raise
                wait = backoff_seconds * (2 ** attempt)
                self.logger.warning(
                    "retry_operation",
                    attempt=attempt + 1,
                    wait_seconds=wait,
                    error=str(e)
                )
                await asyncio.sleep(wait)
```

---

## Usage Pattern

```python
# Correct - use service registry
from src.services import services

async def get_project(project_id: UUID, org_db: str):
    pool = await services.aurora.get_org_pool(org_db)
    return await services.aurora.execute_one(
        pool,
        "SELECT * FROM projects WHERE id = $1",
        project_id
    )

# Incorrect - direct access
import asyncpg
conn = await asyncpg.connect(...)  # DON'T DO THIS

import boto3
s3 = boto3.client('s3')  # DON'T DO THIS
```

---

## Startup Initialization

```python
# src/api/main.py
from fastapi import FastAPI
from src.services import services
from src.utils.config import load_config

app = FastAPI()

@app.on_event("startup")
async def startup():
    config = load_config()
    services.initialize(config)  # Fail fast if services unavailable


@app.on_event("shutdown")
async def shutdown():
    await services.aurora.close_pools()
```
