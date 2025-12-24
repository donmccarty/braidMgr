# Budget Entities

*Parent: [DATA_MODEL.md](../DATA_MODEL.md)*

Budget tracking entities for project financial management.

**Key Concepts**:
- Rate cards define billing rates by resource, role, and geography
- Budget allocations define planned budgets by workstream/phase
- Timesheet entries track actual time and cost
- Variance analysis compares allocated vs actual spend
- Budget tracking is per-project (not cross-org)

---

## RATE_CARD

Resource billing rates.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| organization_id | UUID | FK(ORGANIZATION), NOT NULL | Parent organization |
| resource_name | VARCHAR(255) | NOT NULL | Resource/person name |
| role | VARCHAR(100) | NULL | Role/title |
| geography | VARCHAR(100) | NULL | Location/geography |
| hourly_rate | DECIMAL(10,2) | NOT NULL | Hourly billing rate |
| effective_from | DATE | NOT NULL | Rate effective start |
| effective_to | DATE | NULL | Rate effective end (null = current) |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |

**Indexes**:
- `idx_rate_card_org` on organization_id
- `idx_rate_card_resource` on resource_name

**Design Notes**:
- Rate cards are org-level (shared across projects in the org)
- `effective_to` NULL means the rate is currently active
- Historical rates preserved for accurate cost calculations
- Rate lookup: match resource_name, then apply rate effective on timesheet date

---

## BUDGET_ALLOCATION

Budget allocated to project workstreams/phases.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| project_id | UUID | FK(PROJECT), NOT NULL | Parent project |
| workstream_id | UUID | FK(WORKSTREAM), NULL | Workstream (optional) |
| amount | DECIMAL(12,2) | NOT NULL | Allocated amount |
| period_start | DATE | NULL | Period start |
| period_end | DATE | NULL | Period end |
| notes | TEXT | NULL | Allocation notes |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |

**Indexes**:
- `idx_budget_allocation_project` on project_id

**Design Notes**:
- Allocations can be project-wide (workstream_id NULL) or per-workstream
- Optional date range for time-phased budgeting
- Multiple allocations can exist per project/workstream
- Total budget = SUM of all allocations for project

---

## TIMESHEET_ENTRY

Actual time/cost entries.

| Attribute | Type | Constraints | Description |
|-----------|------|-------------|-------------|
| id | UUID | PK | Unique identifier |
| project_id | UUID | FK(PROJECT), NOT NULL | Parent project |
| rate_card_id | UUID | FK(RATE_CARD), NULL | Rate card used |
| week_ending | DATE | NOT NULL | Week ending date |
| resource_name | VARCHAR(255) | NOT NULL | Resource name |
| hours | DECIMAL(6,2) | NOT NULL | Hours worked |
| rate | DECIMAL(10,2) | NOT NULL | Hourly rate applied |
| cost | DECIMAL(12,2) | NOT NULL | Total cost (hours * rate) |
| complete_week | BOOLEAN | DEFAULT true | Full week of data |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |

**Indexes**:
- `idx_timesheet_project` on project_id
- `idx_timesheet_week` on week_ending
- `idx_timesheet_resource` on resource_name

**Design Notes**:
- `rate_card_id` links to RATE_CARD for traceability
- `rate` is denormalized for historical accuracy (rate may change)
- `cost` is pre-calculated (hours * rate) for query performance
- `complete_week` FALSE indicates partial week data (e.g., mid-project start)
- Week ending date is typically a Friday

---

## Budget Calculations

### Total Budget
```sql
SELECT SUM(amount) as total_budget
FROM budget_allocation
WHERE project_id = :project_id
```

### Actual Spend
```sql
SELECT SUM(cost) as actual_spend
FROM timesheet_entry
WHERE project_id = :project_id
```

### Burn Rate (Weekly)
```sql
SELECT week_ending, SUM(cost) as weekly_cost
FROM timesheet_entry
WHERE project_id = :project_id
GROUP BY week_ending
ORDER BY week_ending
```

### Remaining Budget
```sql
-- Total Budget - Actual Spend = Remaining
-- Also calculate: Remaining / Average Weekly Burn = Weeks Remaining
```

---

## Entity Relationships

```
ORGANIZATION ──1:M──→ RATE_CARD
                          │
                          └──1:M── TIMESHEET_ENTRY ←──M:1── PROJECT
                                                              │
                                                              └──1:M──→ BUDGET_ALLOCATION
```
