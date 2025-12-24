# Service Architecture

*Parent: [ARCHITECTURE.md](../ARCHITECTURE.md)*

Service centralization pattern for external integrations.

**Key Concepts**:
- All external access through ServiceRegistry singleton
- Fail-fast initialization at startup
- Consistent error handling and logging
- Dependency injection for testability

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

        # Validate connections (fail fast)
        self._validate_connections()
        self._initialized = True

    @property
    def aurora(self) -> AuroraService:
        return self._aurora

    @property
    def s3(self) -> S3Service:
        return self._s3

    @property
    def claude(self) -> ClaudeService:
        return self._claude

# Singleton instance
services = ServiceRegistry()
```

---

## Service Inventory

| Service | Purpose | Methods |
|---------|---------|---------|
| AuroraService | Database operations | execute_query, execute_one, execute_returning, transaction |
| S3Service | File storage | upload, download, delete, generate_presigned_url |
| ClaudeService | AI chat | send_message, stream_response |
| AuthService | Authentication | verify_token, create_tokens, hash_password |

---

## Base Service Contract

```python
# src/services/base.py

from abc import ABC, abstractmethod
import structlog

class BaseService(ABC):
    """Abstract base for all services."""

    def __init__(self, config):
        self.config = config
        self.logger = structlog.get_logger(service=self.__class__.__name__)

    @abstractmethod
    async def health_check(self) -> bool:
        """Check service connectivity."""
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

## Aurora Service

```python
# src/services/aurora_service.py

class AuroraService(BaseService):
    """PostgreSQL database operations."""

    def __init__(self, config: DatabaseConfig):
        super().__init__(config)
        self._pools: dict[str, asyncpg.Pool] = {}

    async def initialize(self):
        """Create connection pools."""
        # Central database pool
        self._central_pool = await asyncpg.create_pool(
            dsn=self.config.central_dsn,
            min_size=2,
            max_size=10
        )

    async def get_org_pool(self, database_name: str) -> asyncpg.Pool:
        """Get or create pool for organization database."""
        if database_name not in self._pools:
            self._pools[database_name] = await asyncpg.create_pool(
                dsn=self.config.build_dsn(database_name),
                min_size=2,
                max_size=10
            )
        return self._pools[database_name]

    async def execute_query(
        self,
        pool: asyncpg.Pool,
        query: str,
        *args
    ) -> list[asyncpg.Record]:
        """Execute query and return all rows."""
        async with pool.acquire() as conn:
            return await conn.fetch(query, *args)

    async def execute_one(
        self,
        pool: asyncpg.Pool,
        query: str,
        *args
    ) -> asyncpg.Record | None:
        """Execute query and return single row."""
        async with pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    async def execute_returning(
        self,
        pool: asyncpg.Pool,
        query: str,
        *args
    ) -> asyncpg.Record:
        """Execute INSERT/UPDATE with RETURNING clause."""
        async with pool.acquire() as conn:
            return await conn.fetchrow(query, *args)

    @asynccontextmanager
    async def transaction(self, pool: asyncpg.Pool):
        """Transaction context manager."""
        async with pool.acquire() as conn:
            async with conn.transaction():
                yield conn
```

---

## S3 Service

```python
# src/services/s3_service.py

class S3Service(BaseService):
    """S3 file storage operations."""

    def __init__(self, config: S3Config):
        super().__init__(config)
        self.client = boto3.client('s3')
        self.bucket = config.bucket_name

    async def upload(
        self,
        key: str,
        data: bytes,
        content_type: str
    ) -> str:
        """Upload file and return S3 key."""
        await asyncio.to_thread(
            self.client.put_object,
            Bucket=self.bucket,
            Key=key,
            Body=data,
            ContentType=content_type
        )
        return key

    async def generate_presigned_url(
        self,
        key: str,
        expires_in: int = 3600
    ) -> str:
        """Generate signed download URL."""
        return self.client.generate_presigned_url(
            'get_object',
            Params={'Bucket': self.bucket, 'Key': key},
            ExpiresIn=expires_in
        )

    async def delete(self, key: str) -> None:
        """Delete file from S3."""
        await asyncio.to_thread(
            self.client.delete_object,
            Bucket=self.bucket,
            Key=key
        )
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
```
