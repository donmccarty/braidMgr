# Repository Pattern

*Parent: [PATTERNS.md](../PATTERNS.md)*

Base repository with common CRUD operations.

**Key Concepts**:
- Generic base class for all repositories
- Soft delete support (deleted_at timestamp)
- Structured logging for all operations
- Error handling with context

---

## Base Repository

```python
# src/repositories/base.py
from typing import TypeVar, Generic, Optional, List
from uuid import UUID
from abc import abstractmethod
import structlog
from src.utils.exceptions import DatabaseError, NotFoundError

T = TypeVar('T')

class BaseRepository(Generic[T]):
    """Base repository with common CRUD operations."""

    def __init__(self, aurora_service, table_name: str):
        self._aurora = aurora_service
        self._table_name = table_name
        self._logger = structlog.get_logger().bind(
            repository=self.__class__.__name__
        )

    async def find_by_id(self, pool, id: UUID) -> Optional[T]:
        """Find entity by ID."""
        log = self._logger.bind(id=str(id))

        try:
            query = f"""
                SELECT * FROM {self._table_name}
                WHERE id = $1 AND deleted_at IS NULL
            """
            row = await self._aurora.execute_one(pool, query, id)

            if row:
                log.debug("entity_found")
                return self._row_to_entity(row)
            else:
                log.debug("entity_not_found")
                return None

        except Exception as e:
            log.error("find_by_id_failed", error=str(e))
            raise DatabaseError(
                f"Failed to find {self._table_name}",
                operation="find_by_id",
                table=self._table_name,
            )

    async def find_all(
        self,
        pool,
        limit: int = 100,
        offset: int = 0
    ) -> List[T]:
        """Find all entities with pagination."""
        query = f"""
            SELECT * FROM {self._table_name}
            WHERE deleted_at IS NULL
            ORDER BY created_at DESC
            LIMIT $1 OFFSET $2
        """
        rows = await self._aurora.execute_query(pool, query, limit, offset)
        return [self._row_to_entity(row) for row in rows]

    async def count(self, pool) -> int:
        """Count all non-deleted entities."""
        query = f"""
            SELECT COUNT(*) FROM {self._table_name}
            WHERE deleted_at IS NULL
        """
        result = await self._aurora.execute_one(pool, query)
        return result['count']

    async def soft_delete(self, pool, id: UUID) -> bool:
        """Soft delete by setting deleted_at."""
        query = f"""
            UPDATE {self._table_name}
            SET deleted_at = NOW(), updated_at = NOW()
            WHERE id = $1 AND deleted_at IS NULL
            RETURNING id
        """
        result = await self._aurora.execute_one(pool, query, id)
        return result is not None

    async def exists(self, pool, id: UUID) -> bool:
        """Check if entity exists."""
        query = f"""
            SELECT 1 FROM {self._table_name}
            WHERE id = $1 AND deleted_at IS NULL
        """
        result = await self._aurora.execute_one(pool, query, id)
        return result is not None

    @abstractmethod
    def _row_to_entity(self, row: dict) -> T:
        """Convert database row to entity."""
        pass
```

---

## Example Repository Implementation

```python
# src/repositories/item_repository.py
from uuid import UUID
from typing import List, Optional
from src.repositories.base import BaseRepository
from src.domain.item import Item

class ItemRepository(BaseRepository[Item]):

    def __init__(self, aurora_service):
        super().__init__(aurora_service, "items")

    async def find_by_project(
        self,
        pool,
        project_id: UUID,
        type_filter: Optional[str] = None
    ) -> List[Item]:
        """Find items by project with optional type filter."""
        if type_filter:
            query = """
                SELECT * FROM items
                WHERE project_id = $1
                  AND type = $2
                  AND deleted_at IS NULL
                ORDER BY item_num
            """
            rows = await self._aurora.execute_query(
                pool, query, project_id, type_filter
            )
        else:
            query = """
                SELECT * FROM items
                WHERE project_id = $1 AND deleted_at IS NULL
                ORDER BY item_num
            """
            rows = await self._aurora.execute_query(pool, query, project_id)

        return [self._row_to_entity(row) for row in rows]

    async def find_by_item_num(
        self,
        pool,
        project_id: UUID,
        item_num: int
    ) -> Optional[Item]:
        """Find item by project and item number."""
        query = """
            SELECT * FROM items
            WHERE project_id = $1
              AND item_num = $2
              AND deleted_at IS NULL
        """
        row = await self._aurora.execute_one(pool, query, project_id, item_num)
        return self._row_to_entity(row) if row else None

    async def create(self, pool, item: Item) -> Item:
        """Create new item."""
        query = """
            INSERT INTO items (
                id, project_id, item_num, type, title, description,
                workstream_id, assigned_to, start_date, finish_date,
                deadline, percent_complete, indicator, created_at, updated_at
            ) VALUES (
                $1, $2, $3, $4, $5, $6, $7, $8, $9, $10, $11, $12, $13,
                NOW(), NOW()
            )
            RETURNING *
        """
        row = await self._aurora.execute_returning(
            pool, query,
            item.id, item.project_id, item.item_num, item.type,
            item.title, item.description, item.workstream_id,
            item.assigned_to, item.start_date, item.finish_date,
            item.deadline, item.percent_complete, item.indicator
        )
        return self._row_to_entity(row)

    def _row_to_entity(self, row: dict) -> Item:
        """Convert database row to Item entity."""
        return Item(
            id=row['id'],
            project_id=row['project_id'],
            item_num=row['item_num'],
            type=row['type'],
            title=row['title'],
            description=row['description'],
            workstream_id=row['workstream_id'],
            assigned_to=row['assigned_to'],
            start_date=row['start_date'],
            finish_date=row['finish_date'],
            deadline=row['deadline'],
            percent_complete=row['percent_complete'],
            indicator=row['indicator'],
            created_at=row['created_at'],
            updated_at=row['updated_at'],
        )
```
