# Pydantic Validation Patterns

*Parent: [PATTERNS.md](../PATTERNS.md)*

Request/response schema patterns with Pydantic v2.

**Key Concepts**:
- Separate request and response schemas
- Field validators for complex validation
- from_attributes for ORM-like behavior

---

## Request Schemas

```python
# src/api/schemas/item.py
from pydantic import BaseModel, Field, field_validator
from datetime import date
from typing import Optional
from uuid import UUID

class ItemCreate(BaseModel):
    """Request body for creating an item."""
    type: str = Field(..., description="Item type")
    title: str = Field(..., min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=10000)
    workstream_id: Optional[UUID] = None
    assigned_to: Optional[str] = Field(None, max_length=255)
    start_date: Optional[date] = None
    finish_date: Optional[date] = None
    deadline: Optional[date] = None
    percent_complete: int = Field(default=0, ge=0, le=100)

    @field_validator('type')
    @classmethod
    def validate_type(cls, v):
        allowed = ['Budget', 'Risk', 'Action Item', 'Issue',
                   'Decision', 'Deliverable', 'Plan Item']
        if v not in allowed:
            raise ValueError(f'type must be one of {allowed}')
        return v

    @field_validator('finish_date')
    @classmethod
    def validate_finish_after_start(cls, v, info):
        start = info.data.get('start_date')
        if start and v and v < start:
            raise ValueError('finish_date must be after start_date')
        return v


class ItemUpdate(BaseModel):
    """Request body for updating an item."""
    title: Optional[str] = Field(None, min_length=1, max_length=500)
    description: Optional[str] = Field(None, max_length=10000)
    assigned_to: Optional[str] = Field(None, max_length=255)
    start_date: Optional[date] = None
    finish_date: Optional[date] = None
    deadline: Optional[date] = None
    percent_complete: Optional[int] = Field(None, ge=0, le=100)
```

---

## Response Schemas

```python
from pydantic import BaseModel
from datetime import datetime
from typing import Optional
from uuid import UUID

class ItemResponse(BaseModel):
    """Item in response."""
    id: UUID
    item_num: int
    type: str
    title: str
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    indicator: Optional[str] = None
    percent_complete: int
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}

    @classmethod
    def from_entity(cls, item) -> "ItemResponse":
        """Create response from domain entity."""
        return cls(
            id=item.id,
            item_num=item.item_num,
            type=item.type,
            title=item.title,
            description=item.description,
            assigned_to=item.assigned_to,
            indicator=item.indicator,
            percent_complete=item.percent_complete,
            created_at=item.created_at,
            updated_at=item.updated_at,
        )


class ItemListResponse(BaseModel):
    """Paginated item list."""
    data: list[ItemResponse]
    meta: "PaginationMeta"


class PaginationMeta(BaseModel):
    """Pagination metadata."""
    page: int
    per_page: int
    total: int
    total_pages: int
```

---

## Common Validators

```python
from pydantic import field_validator, model_validator
import re

class UserCreate(BaseModel):
    email: str = Field(..., max_length=255)
    password: str = Field(..., min_length=8, max_length=100)
    name: str = Field(..., min_length=1, max_length=255)

    @field_validator('email')
    @classmethod
    def validate_email(cls, v):
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, v):
            raise ValueError('Invalid email format')
        return v.lower()

    @field_validator('password')
    @classmethod
    def validate_password_strength(cls, v):
        if not any(c.isupper() for c in v):
            raise ValueError('Password must contain uppercase letter')
        if not any(c.isdigit() for c in v):
            raise ValueError('Password must contain digit')
        return v


class DateRangeFilter(BaseModel):
    """Date range with validation."""
    start_date: Optional[date] = None
    end_date: Optional[date] = None

    @model_validator(mode='after')
    def validate_date_range(self):
        if self.start_date and self.end_date:
            if self.end_date < self.start_date:
                raise ValueError('end_date must be after start_date')
        return self
```

---

## Error Responses

Pydantic validation errors are automatically formatted:

```python
# src/api/middleware/error_handler.py
from pydantic import ValidationError as PydanticValidationError
from src.utils.exceptions import ValidationError

async def pydantic_error_handler(request, exc: PydanticValidationError):
    """Convert Pydantic errors to app format."""
    errors = []
    for error in exc.errors():
        errors.append({
            "field": ".".join(str(loc) for loc in error["loc"]),
            "message": error["msg"],
            "type": error["type"]
        })

    raise ValidationError(
        "Validation failed",
        errors=errors
    )
```

---

## Usage in Routes

```python
from fastapi import APIRouter
from src.api.schemas.item import ItemCreate, ItemResponse

router = APIRouter()

@router.post(
    "/projects/{project_id}/items",
    response_model=ItemResponse,
    status_code=201
)
async def create_item(
    project_id: UUID,
    data: ItemCreate,  # Validated by Pydantic
    current_user: User = Depends(get_current_user)
):
    item = await item_service.create(project_id, data)
    return ItemResponse.from_entity(item)
```
