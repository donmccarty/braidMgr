# Item Entities

*Parent: [DATA_MODEL.md](../DATA_MODEL.md)*

RAID log item entities that form the core project tracking functionality.

**Key Concepts**:
- Items are the fundamental unit of project tracking (Risks, Actions, Issues, Decisions, etc.)
- Each item has a unique number per project for easy reference
- Notes are timestamped and dated for chronological tracking
- Dependencies enable predecessor/successor relationships
- Attachments stored in S3 with metadata in database

---

## ITEM

A RAID log item (Risk, Action, Issue, Decision, etc.).

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| project_id | UUID | FK(PROJECT), NOT NULL | Parent project |
| item_num | INTEGER | NOT NULL | Display number (unique per project) |
| type | item_type_enum | NOT NULL | Item type |
| title | VARCHAR(500) | NOT NULL | Item title |
| description | TEXT | NULL | Detailed description |
| workstream_id | UUID | FK(WORKSTREAM), NULL | Associated workstream |
| assigned_to | VARCHAR(255) | NULL | Assignee name |
| start_date | DATE | NULL | Planned start |
| finish_date | DATE | NULL | Planned finish |
| duration_days | INTEGER | NULL | Duration in business days |
| deadline | DATE | NULL | Hard deadline |
| draft | BOOLEAN | DEFAULT false | Draft mode (hidden from views) |
| client_visible | BOOLEAN | DEFAULT true | Visible to client |
| percent_complete | INTEGER | DEFAULT 0, CHECK 0-100 | Completion percentage |
| indicator | indicator_enum | NULL | Calculated status indicator |
| priority | VARCHAR(50) | NULL | Priority level |
| rpt_out | TEXT[] | NULL | Report codes list |
| budget_amount | DECIMAL(12,2) | NULL | Budget amount (for Budget type) |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update timestamp |
| deleted_at | TIMESTAMP | NULL | Soft delete timestamp |

**Unique Constraint**: (project_id, item_num)

**Indexes**:
- `idx_item_project` on project_id
- `idx_item_type` on type
- `idx_item_indicator` on indicator
- `idx_item_assigned` on assigned_to
- `idx_item_deleted` on deleted_at

**Design Notes**:
- `item_num` is human-readable (e.g., "Item #42") and unique per project
- `indicator` is calculated based on dates and completion (see PROCESS_FLOWS.md)
- `rpt_out` contains report codes for filtered views (e.g., ["EXEC", "CLIENT"])
- `draft` items are hidden from standard views until promoted
- `budget_amount` only used when type = 'Budget'

---

## WORKSTREAM

Project workstreams for organizing items.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| project_id | UUID | FK(PROJECT), NOT NULL | Parent project |
| name | VARCHAR(255) | NOT NULL | Workstream name |
| sort_order | INTEGER | DEFAULT 0 | Display order |

**Unique Constraint**: (project_id, name)

**Design Notes**:
- Workstreams are project-specific (not shared across projects)
- Examples: "Development", "Testing", "Infrastructure", "Change Management"
- `sort_order` allows custom ordering in UI views

---

## ITEM_NOTE

Timestamped notes on items.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| item_id | UUID | FK(ITEM), NOT NULL | Parent item |
| note_date | DATE | NOT NULL | Date of note |
| content | TEXT | NOT NULL | Note content |
| created_by | UUID | FK(USER), NULL | Author |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |

**Indexes**:
- `idx_item_note_item` on item_id
- `idx_item_note_date` on note_date DESC

**Design Notes**:
- Notes are dated (not just timestamped) for reporting by date
- Multiple notes can have the same date
- `created_by` links to USER for attribution
- Notes ordered by date descending (most recent first)

---

## ITEM_DEPENDENCY

Dependencies between items.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| item_id | UUID | FK(ITEM), NOT NULL | Dependent item |
| depends_on_id | UUID | FK(ITEM), NOT NULL | Prerequisite item |

**Primary Key**: (item_id, depends_on_id)

**Design Notes**:
- Pure junction table for item predecessor/successor relationships
- `item_id` depends on `depends_on_id` (predecessor relationship)
- Used for timeline views and critical path analysis
- Circular dependencies should be prevented at application level

---

## ATTACHMENT

Files attached to items.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| item_id | UUID | FK(ITEM), NOT NULL | Parent item |
| filename | VARCHAR(255) | NOT NULL | Original filename |
| content_type | VARCHAR(100) | NOT NULL | MIME type |
| size_bytes | INTEGER | NOT NULL | File size |
| s3_key | VARCHAR(500) | NOT NULL | S3 object key |
| uploaded_by | UUID | FK(USER), NOT NULL | Uploader |
| created_at | TIMESTAMP | NOT NULL | Upload timestamp |

**Indexes**:
- `idx_attachment_item` on item_id

**Design Notes**:
- Files stored in S3, only metadata in database
- S3 key pattern: `{org_slug}/{project_id}/{item_id}/{uuid}/{filename}`
- Signed URLs used for secure access (not public URLs)
- File size limits enforced at application level (10MB per file)

---

## Entity Relationships

```
PROJECT ──1:M──→ WORKSTREAM
    │
    └──1:M──→ ITEM ──1:M──→ ITEM_NOTE
                │
                ├──1:M──→ ITEM_DEPENDENCY
                │
                └──1:M──→ ATTACHMENT
```
