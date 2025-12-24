# Testing Patterns

*Parent: [PATTERNS.md](../PATTERNS.md)*

Test structure, fixtures, and templates.

**Key Concepts**:
- 80/15/5 distribution: Unit/Integration/E2E
- Unit tests mock all I/O
- Integration tests use real PostgreSQL (Docker)
- AAA pattern: Arrange, Act, Assert

---

## Test Distribution

| Type | Target % | Description |
|------|----------|-------------|
| Unit | 80% | Fast, no I/O, mocked dependencies |
| Integration | 15% | Real PostgreSQL (Docker), mock external services |
| E2E | 5% | Full HTTP stack with real database |

---

## Test Directory Structure

```
tests/
├── conftest.py                    # Global fixtures
├── unit/
│   ├── test_indicators.py         # Business logic tests
│   ├── test_budget.py
│   └── middleware/
│       ├── test_auth.py
│       └── test_error_handler.py
├── integration/
│   ├── conftest.py                # DB fixtures
│   └── repositories/
│       ├── test_project_repository.py
│       └── test_item_repository.py
└── e2e/
    ├── conftest.py                # API client fixtures
    └── test_items_api.py
```

---

## Key Fixtures

```python
# tests/conftest.py
import pytest
from uuid import uuid4
from datetime import date
from unittest.mock import AsyncMock, MagicMock

@pytest.fixture
def mock_aurora():
    """Mock Aurora service for unit tests."""
    aurora = MagicMock()
    aurora.execute_query = AsyncMock(return_value=[])
    aurora.execute_one = AsyncMock(return_value=None)
    aurora.execute_returning = AsyncMock(return_value={})
    return aurora

@pytest.fixture
def sample_project_data():
    """Sample project data for tests."""
    return {
        "id": uuid4(),
        "name": "Test Project",
        "client_name": "Test Client",
        "project_start": date(2025, 1, 1),
        "project_end": date(2025, 12, 31),
    }

@pytest.fixture
def sample_item_data(sample_project_data):
    """Sample item data for tests."""
    return {
        "id": uuid4(),
        "project_id": sample_project_data["id"],
        "item_num": 1,
        "type": "Action Item",
        "title": "Test Action",
        "percent_complete": 0,
        "indicator": "Not Started",
    }
```

---

## Unit Test Template

```python
# tests/unit/test_item_repository.py
import pytest
from unittest.mock import AsyncMock
from uuid import uuid4
from src.repositories.item_repository import ItemRepository

@pytest.mark.asyncio
async def test_create_item_success(mock_aurora, sample_item_data):
    """Test successful item creation."""
    # Arrange
    mock_aurora.execute_returning.return_value = sample_item_data
    repo = ItemRepository(mock_aurora)
    mock_pool = MagicMock()

    # Act
    from src.domain.item import Item
    item = Item(**sample_item_data)
    result = await repo.create(mock_pool, item)

    # Assert
    assert result.title == sample_item_data["title"]
    assert result.item_num == 1
    mock_aurora.execute_returning.assert_called_once()


@pytest.mark.asyncio
async def test_find_by_id_not_found(mock_aurora):
    """Test find_by_id returns None for missing entity."""
    # Arrange
    mock_aurora.execute_one.return_value = None
    repo = ItemRepository(mock_aurora)
    mock_pool = MagicMock()

    # Act
    result = await repo.find_by_id(mock_pool, uuid4())

    # Assert
    assert result is None
```

---

## Integration Test Template

```python
# tests/integration/conftest.py
import pytest
import asyncpg

@pytest.fixture(scope="session")
async def test_db():
    """Create test database connection."""
    pool = await asyncpg.create_pool(
        dsn="postgresql://test:test@localhost:5433/braidmgr_test"
    )
    yield pool
    await pool.close()

@pytest.fixture(autouse=True)
async def clean_tables(test_db):
    """Clean tables before each test."""
    await test_db.execute("TRUNCATE items, projects CASCADE")
    yield
```

```python
# tests/integration/repositories/test_item_repository.py
import pytest
from uuid import uuid4
from src.repositories.item_repository import ItemRepository

@pytest.mark.asyncio
async def test_item_crud(test_db, sample_project):
    """Test complete item lifecycle."""
    repo = ItemRepository(aurora_service)  # Real Aurora service

    # Create
    item = Item(
        id=uuid4(),
        project_id=sample_project.id,
        item_num=1,
        type="Action Item",
        title="Test Item",
    )
    created = await repo.create(test_db, item)
    assert created.id is not None

    # Read
    found = await repo.find_by_id(test_db, created.id)
    assert found.title == "Test Item"

    # Update
    found.title = "Updated Title"
    updated = await repo.update(test_db, found)
    assert updated.title == "Updated Title"

    # Delete
    await repo.soft_delete(test_db, created.id)
    assert await repo.find_by_id(test_db, created.id) is None
```

---

## E2E Test Template

```python
# tests/e2e/test_items_api.py
import pytest
from httpx import AsyncClient

@pytest.fixture
async def auth_client(test_app, test_user):
    """Authenticated HTTP client."""
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        # Login and set token
        response = await client.post("/auth/login", json={
            "email": test_user.email,
            "password": "test123"
        })
        token = response.json()["access_token"]
        client.headers["Authorization"] = f"Bearer {token}"
        yield client


@pytest.mark.asyncio
async def test_create_and_get_item(auth_client, test_project):
    """Test item creation via API."""
    # Create
    response = await auth_client.post(
        f"/projects/{test_project.id}/items",
        json={"type": "Risk", "title": "Test Risk"}
    )
    assert response.status_code == 201
    item = response.json()["data"]
    assert item["title"] == "Test Risk"

    # Get
    response = await auth_client.get(
        f"/projects/{test_project.id}/items/{item['item_num']}"
    )
    assert response.status_code == 200
    assert response.json()["data"]["title"] == "Test Risk"
```

---

## Running Tests

```bash
# All tests
pytest

# Unit only (fast)
pytest tests/unit -v

# Integration (needs Docker DB)
docker-compose up -d postgres-test
pytest tests/integration -v

# With coverage
pytest --cov=src --cov-report=html
```
