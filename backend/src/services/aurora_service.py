"""
Aurora PostgreSQL service for transactional database access.

All database queries for braidMgr data go through this service:
- Projects, items, workstreams
- User roles, permissions
- Audit logs, chat sessions

Local development uses Docker PostgreSQL.
Production uses AWS RDS PostgreSQL or Aurora.

Uses asyncpg for async database access per the async-first architecture.

Database Error Mapping:
| PostgreSQL Error          | Application Error        |
|---------------------------|--------------------------|
| UniqueViolationError      | ConflictError (409)      |
| ForeignKeyViolationError  | ValidationError (400)    |
| CheckViolationError       | ValidationError (400)    |
| PostgresConnectionError   | ServiceUnavailableError  |

Usage:
    from src.services import services

    # Simple query
    results = await services.aurora.execute_query(
        "SELECT * FROM items WHERE project_id = $1",
        project_id
    )

    # Insert with returning
    new_item = await services.aurora.execute_returning(
        "INSERT INTO items (project_id, title) VALUES ($1, $2) RETURNING *",
        project_id, "New Item"
    )

    # Transaction context
    async with services.aurora.transaction() as conn:
        await conn.execute("UPDATE items SET status = $1 WHERE id = $2", "done", item_id)
        await conn.execute("INSERT INTO audit_log (...) VALUES (...)")
"""

import asyncio
from contextlib import asynccontextmanager
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, AsyncGenerator

import asyncpg
from asyncpg import Pool, Connection
import structlog

from src.services.base_service import BaseService
from src.utils.exceptions import (
    ConflictError,
    ValidationError,
    DatabaseError,
    ServiceUnavailableError,
)


@dataclass
class AuroraConfig:
    """
    Aurora PostgreSQL connection configuration.

    All values loaded from config.yaml, never hardcoded.

    Attributes:
        host: Database server hostname
        port: PostgreSQL port
        name: Database name
        user: Database username
        password: Database password
        min_connections: Minimum pool connections
        max_connections: Maximum pool connections
        connection_timeout: Query timeout in seconds
    """

    host: str = "localhost"
    port: int = 5432
    name: str = "braidmgr_dev"
    user: str = "postgres"
    password: str = "postgres"
    min_connections: int = 2
    max_connections: int = 10
    connection_timeout: int = 30


class AuroraService(BaseService[AuroraConfig]):
    """
    Centralized Aurora PostgreSQL access.

    ALL transactional database queries go through this service.
    Manages connection pooling for efficiency under load.

    Uses asyncpg for high-performance async database access.
    """

    _pool: Optional[Pool] = None

    def _initialize(self) -> None:
        """
        Prepare connection parameters.

        Note: Actual pool creation is deferred to first use (async).
        """
        self._log = structlog.get_logger().bind(service="aurora")
        self._dsn = (
            f"postgresql://{self._config.user}:{self._config.password}"
            f"@{self._config.host}:{self._config.port}/{self._config.name}"
        )
        self._log.debug(
            "service_configured",
            host=self._config.host,
            port=self._config.port,
            database=self._config.name,
        )

    async def _ensure_pool(self) -> Pool:
        """Create connection pool on first use."""
        if self._pool is None:
            try:
                self._pool = await asyncpg.create_pool(
                    dsn=self._dsn,
                    min_size=self._config.min_connections,
                    max_size=self._config.max_connections,
                    command_timeout=self._config.connection_timeout,
                )
                self._log.info(
                    "pool_created",
                    min_size=self._config.min_connections,
                    max_size=self._config.max_connections,
                )
            except asyncpg.PostgresConnectionError as e:
                self._log.critical(
                    "pool_creation_failed",
                    error_type=type(e).__name__,
                    error_message=str(e),
                )
                raise ServiceUnavailableError("Database temporarily unavailable")
            except Exception as e:
                self._log.critical(
                    "pool_creation_failed",
                    error_type=type(e).__name__,
                    error_message=str(e),
                )
                raise
        return self._pool

    def health_check(self) -> bool:
        """
        Synchronous health check for startup validation.

        For async health checks, use health_check_async().
        Uses socket check when running in async context.
        """
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            # No running loop, create one
            return asyncio.run(self.health_check_async())

        # Running in async context - use socket check for sync health
        import socket

        sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        try:
            sock.settimeout(5)
            sock.connect((self._config.host, self._config.port))
            self._log.debug("health_check_passed", method="socket")
            return True
        except (socket.error, socket.timeout) as e:
            self._log.error(
                "health_check_failed",
                method="socket",
                error_type=type(e).__name__,
                error_message=str(e),
            )
            raise
        finally:
            sock.close()

    async def health_check_async(self) -> bool:
        """
        Async health check for runtime validation.

        Returns:
            True if database is reachable and query succeeds.
        """
        try:
            result = await self.execute_one("SELECT 1 as health")
            is_healthy = result is not None and result.get("health") == 1
            self._log.debug("health_check_passed", method="query")
            return is_healthy
        except Exception as e:
            self._log.error(
                "health_check_failed",
                method="query",
                error_type=type(e).__name__,
                error_message=str(e),
            )
            raise

    @asynccontextmanager
    async def acquire(self) -> AsyncGenerator[Connection, None]:
        """
        Acquire a connection from the pool.

        Use with 'async with' for automatic cleanup:
            async with aurora.acquire() as conn:
                await conn.execute(...)
        """
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            yield conn

    @asynccontextmanager
    async def transaction(self) -> AsyncGenerator[Connection, None]:
        """
        Acquire a connection with transaction context.

        Automatically commits on success, rolls back on exception.

            async with aurora.transaction() as conn:
                await conn.execute("UPDATE ...")
                await conn.execute("INSERT ...")
        """
        pool = await self._ensure_pool()
        async with pool.acquire() as conn:
            async with conn.transaction():
                yield conn

    async def execute_query(
        self,
        query: str,
        *args: Any,
    ) -> List[Dict[str, Any]]:
        """
        Execute a SELECT query and return results as list of dicts.

        Args:
            query: SQL query with $1, $2, etc. placeholders.
            *args: Parameter values (prevents SQL injection).

        Returns:
            List of dictionaries, one per row.

        Raises:
            DatabaseError: If query execution fails.
            ServiceUnavailableError: If database is unreachable.
        """
        pool = await self._ensure_pool()
        log = self._log.bind(operation="execute_query")
        log.debug("query_started", query=query[:100])

        try:
            rows = await pool.fetch(query, *args)
            log.debug("query_completed", row_count=len(rows))
            return [dict(row) for row in rows]
        except asyncpg.PostgresConnectionError as e:
            log.error("query_failed", error_type=type(e).__name__, error_message=str(e))
            raise ServiceUnavailableError("Database temporarily unavailable")
        except asyncpg.PostgresError as e:
            log.error("query_failed", error_type=type(e).__name__, error_message=str(e))
            raise DatabaseError("Query execution failed", operation="execute_query")

    async def execute_one(
        self,
        query: str,
        *args: Any,
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a query expecting a single row result.

        Args:
            query: SQL query with $1, $2, etc. placeholders.
            *args: Parameter values.

        Returns:
            Single row as dictionary, or None if no results.

        Raises:
            DatabaseError: If query execution fails.
            ServiceUnavailableError: If database is unreachable.
        """
        pool = await self._ensure_pool()
        log = self._log.bind(operation="execute_one")
        log.debug("query_started", query=query[:100])

        try:
            row = await pool.fetchrow(query, *args)
            log.debug("query_completed", found=row is not None)
            return dict(row) if row else None
        except asyncpg.PostgresConnectionError as e:
            log.error("query_failed", error_type=type(e).__name__, error_message=str(e))
            raise ServiceUnavailableError("Database temporarily unavailable")
        except asyncpg.PostgresError as e:
            log.error("query_failed", error_type=type(e).__name__, error_message=str(e))
            raise DatabaseError("Query execution failed", operation="execute_one")

    async def execute_write(
        self,
        query: str,
        *args: Any,
    ) -> str:
        """
        Execute INSERT/UPDATE/DELETE and return status.

        Args:
            query: SQL modification query.
            *args: Parameter values.

        Returns:
            Status string (e.g., "UPDATE 5" for 5 rows updated).

        Raises:
            ConflictError: If unique constraint violated.
            ValidationError: If foreign key or check constraint violated.
            DatabaseError: If query execution fails.
            ServiceUnavailableError: If database is unreachable.
        """
        pool = await self._ensure_pool()
        log = self._log.bind(operation="execute_write")
        log.debug("write_started", query=query[:100])

        try:
            result = await pool.execute(query, *args)
            log.debug("write_completed", result=result)
            return result
        except asyncpg.UniqueViolationError as e:
            log.warning("write_conflict", constraint=e.constraint_name)
            raise ConflictError("Resource already exists", field=e.constraint_name)
        except asyncpg.ForeignKeyViolationError as e:
            log.warning("write_validation_failed", constraint=e.constraint_name)
            raise ValidationError("Referenced resource not found", field=e.constraint_name)
        except asyncpg.CheckViolationError as e:
            log.warning("write_validation_failed", constraint=e.constraint_name)
            raise ValidationError("Value out of allowed range", field=e.constraint_name)
        except asyncpg.PostgresConnectionError as e:
            log.error("write_failed", error_type=type(e).__name__, error_message=str(e))
            raise ServiceUnavailableError("Database temporarily unavailable")
        except asyncpg.PostgresError as e:
            log.error("write_failed", error_type=type(e).__name__, error_message=str(e))
            raise DatabaseError("Write operation failed", operation="execute_write")

    async def execute_returning(
        self,
        query: str,
        *args: Any,
    ) -> Dict[str, Any]:
        """
        Execute INSERT ... RETURNING and return the inserted row.

        Args:
            query: INSERT query with RETURNING clause.
            *args: Parameter values.

        Returns:
            The inserted row as a dictionary.

        Raises:
            ConflictError: If unique constraint violated.
            ValidationError: If foreign key or check constraint violated.
            DatabaseError: If query execution fails or no row returned.
            ServiceUnavailableError: If database is unreachable.
        """
        pool = await self._ensure_pool()
        log = self._log.bind(operation="execute_returning")
        log.debug("insert_started", query=query[:100])

        try:
            row = await pool.fetchrow(query, *args)
            if row is None:
                log.error("insert_no_return", query=query[:100])
                raise DatabaseError(
                    "INSERT RETURNING did not return a row",
                    operation="execute_returning",
                )
            log.debug("insert_completed", id=str(row.get("id", "unknown")))
            return dict(row)
        except asyncpg.UniqueViolationError as e:
            log.warning("insert_conflict", constraint=e.constraint_name)
            raise ConflictError("Resource already exists", field=e.constraint_name)
        except asyncpg.ForeignKeyViolationError as e:
            log.warning("insert_validation_failed", constraint=e.constraint_name)
            raise ValidationError("Referenced resource not found", field=e.constraint_name)
        except asyncpg.CheckViolationError as e:
            log.warning("insert_validation_failed", constraint=e.constraint_name)
            raise ValidationError("Value out of allowed range", field=e.constraint_name)
        except asyncpg.PostgresConnectionError as e:
            log.error("insert_failed", error_type=type(e).__name__, error_message=str(e))
            raise ServiceUnavailableError("Database temporarily unavailable")
        except asyncpg.PostgresError as e:
            log.error("insert_failed", error_type=type(e).__name__, error_message=str(e))
            raise DatabaseError("Insert operation failed", operation="execute_returning")

    async def execute_many(
        self,
        query: str,
        args_list: List[tuple],
    ) -> None:
        """
        Execute batch insert/update for multiple rows efficiently.

        Args:
            query: SQL query with $1, $2, etc. placeholders.
            args_list: List of parameter tuples, one per row.

        Raises:
            ConflictError: If unique constraint violated.
            ValidationError: If foreign key or check constraint violated.
            DatabaseError: If query execution fails.
            ServiceUnavailableError: If database is unreachable.
        """
        pool = await self._ensure_pool()
        log = self._log.bind(operation="execute_many")
        log.debug("batch_started", query=query[:100], row_count=len(args_list))

        try:
            await pool.executemany(query, args_list)
            log.debug("batch_completed", row_count=len(args_list))
        except asyncpg.UniqueViolationError as e:
            log.warning("batch_conflict", constraint=e.constraint_name)
            raise ConflictError("Resource already exists", field=e.constraint_name)
        except asyncpg.ForeignKeyViolationError as e:
            log.warning("batch_validation_failed", constraint=e.constraint_name)
            raise ValidationError("Referenced resource not found", field=e.constraint_name)
        except asyncpg.CheckViolationError as e:
            log.warning("batch_validation_failed", constraint=e.constraint_name)
            raise ValidationError("Value out of allowed range", field=e.constraint_name)
        except asyncpg.PostgresConnectionError as e:
            log.error("batch_failed", error_type=type(e).__name__, error_message=str(e))
            raise ServiceUnavailableError("Database temporarily unavailable")
        except asyncpg.PostgresError as e:
            log.error("batch_failed", error_type=type(e).__name__, error_message=str(e))
            raise DatabaseError("Batch operation failed", operation="execute_many")

    # =========================================================================
    # REPOSITORY CONVENIENCE METHODS
    # These methods provide transaction-aware query execution for repositories.
    # =========================================================================

    async def fetch_one(
        self,
        query: str,
        *args: Any,
        tx: Optional[Connection] = None,
    ) -> Optional[Dict[str, Any]]:
        """
        Execute a query expecting a single row, with optional transaction.

        Args:
            query: SQL query with $1, $2, etc. placeholders.
            *args: Parameter values.
            tx: Optional asyncpg Connection for transaction context.

        Returns:
            Single row as dictionary, or None if no results.
        """
        if tx is not None:
            row = await tx.fetchrow(query, *args)
            return dict(row) if row else None
        else:
            return await self.execute_one(query, *args)

    async def fetch_all(
        self,
        query: str,
        *args: Any,
        tx: Optional[Connection] = None,
    ) -> List[Dict[str, Any]]:
        """
        Execute a query returning multiple rows, with optional transaction.

        Args:
            query: SQL query with $1, $2, etc. placeholders.
            *args: Parameter values.
            tx: Optional asyncpg Connection for transaction context.

        Returns:
            List of dictionaries, one per row.
        """
        if tx is not None:
            rows = await tx.fetch(query, *args)
            return [dict(row) for row in rows]
        else:
            return await self.execute_query(query, *args)

    async def close(self) -> None:
        """
        Close all connections in the pool.

        Call during application shutdown.
        """
        if self._pool is not None:
            await self._pool.close()
            self._pool = None
            self._log.info("pool_closed")
