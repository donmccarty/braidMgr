# Sequence 3: Core Data

*Parent: [USER_STORIES.md](../USER_STORIES.md)*

RAID item and project data management.

**Depends on**: Sequences 1, 2
**Stories**: 8
**Priority**: MVP

---

## S3-001: Project CRUD

**Story**: As a project manager, I want to create and manage projects, so that I can organize my RAID items.

**Acceptance Criteria**:
- Create project (name, client, dates, workstreams)
- Edit project metadata
- Delete project (soft delete with confirmation)
- List projects for current user
- Project assigned to organization

**Traces**: PAR-004, WEB-005

---

## S3-002: Item CRUD

**Story**: As a team member, I want to create and edit RAID items, so that I can track project work.

**Acceptance Criteria**:
- Create item with all fields from PAR-002
- Edit item via modal dialog
- Delete item (soft delete)
- Item number auto-assigned
- created_date and last_updated tracked

**Traces**: PAR-002, PAR-012

---

## S3-003: Item Types

**Story**: As a team member, I want to categorize items by type, so that I can distinguish risks from actions.

**Acceptance Criteria**:
- All 7 item types available in dropdown
- Type-specific styling/colors
- Filter by type in list view
- Type stored and persisted correctly

**Traces**: PAR-001

---

## S3-004: Indicator Calculation

**Story**: As a user, I want status indicators calculated automatically, so that I can see item health at a glance.

**Acceptance Criteria**:
- All 10 indicators calculate per PAR-003 rules
- Indicators update on item save
- Batch update action available
- Draft items excluded from indicators
- Severity ordering correct

**Traces**: PAR-003, PAR-018

---

## S3-005: Workstream Management

**Story**: As a project manager, I want to define workstreams, so that I can organize items by area.

**Acceptance Criteria**:
- Add/remove workstreams in project settings
- Workstream dropdown populated from project
- Items can be assigned to workstream
- Workstream filter in list view

**Traces**: PAR-004, PAR-016

---

## S3-006: Item Filtering

**Story**: As a user, I want to filter items by various criteria, so that I can find what I need.

**Acceptance Criteria**:
- Filter by type, workstream, assignee, status
- Search by title and description
- Filters combine with AND logic
- Clear all filters option
- Filter state persists in session

**Traces**: PAR-016

---

## S3-007: YAML Import

**Story**: As an admin (Don), I want to import existing YAML files, so that v1 data is migrated.

**Acceptance Criteria**:
- Import RAID-Log-*.yaml files
- Import Budget-*.yaml files
- Data maps to new schema correctly
- Validation errors reported clearly
- One-time migration script (not user-facing)

**Traces**: PAR-013

---

## S3-008: Data Validation

**Story**: As a user, I want form validation, so that I enter valid data.

**Acceptance Criteria**:
- Required fields validated (title)
- Date format validation
- Percent complete 0-100
- Field-level error messages
- Submit blocked until valid

**Traces**: PAR-002, WEB-007
