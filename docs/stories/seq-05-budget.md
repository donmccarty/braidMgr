# Sequence 5: Budget

*Parent: [USER_STORIES.md](../USER_STORIES.md)*

Budget tracking and visualization.

**Depends on**: Sequence 3
**Stories**: 4
**Priority**: MVP

---

## S5-001: Budget Data Model

**Story**: As a developer, I want an optimized budget schema, so that budget data is flexible and complete.

**Acceptance Criteria**:
- Rate card table (resource, role, rate, dates)
- Timesheet/actuals table
- Budget allocation by workstream/phase
- Variance tracking (planned vs actual)
- Schema documented in DATA_MODEL.md

**Traces**: PAR-011

---

## S5-002: Budget View

**Story**: As a user, I want to see budget metrics, so that I can track financial health.

**Acceptance Criteria**:
- Metric cards per PAR-010
- Progress bar for burn percentage
- Status indicator (over/under/within 15%)
- Loads within 1 second

**Traces**: PAR-010

---

## S5-003: Weekly Burn Chart

**Story**: As a user, I want a weekly burn chart, so that I can see spend trends.

**Acceptance Criteria**:
- Bar chart showing weekly costs
- Cumulative line optional
- Interactive (hover shows values)
- Responsive sizing

**Traces**: PAR-010

---

## S5-004: Resource Breakdown

**Story**: As a user, I want a resource cost breakdown, so that I can see who is consuming budget.

**Acceptance Criteria**:
- Table with resource, hours, cost
- Sorted by cost descending
- Percentage of total column
- Exportable to CSV

**Traces**: PAR-010
