# Sequence 4: Views

*Parent: [USER_STORIES.md](../USER_STORIES.md)*

UI views matching v1 functionality.

**Depends on**: Sequence 3
**Stories**: 8
**Priority**: MVP

---

## S4-001: Dashboard View

**Story**: As a user, I want a dashboard overview, so that I can see project health at a glance.

**Acceptance Criteria**:
- Summary cards (Critical, Warning, Active, Completed, Total)
- Counts accurate and update on data changes
- Clickable cards navigate to filtered list
- Budget status indicator displayed
- Loads within 1 second

**Traces**: PAR-005

---

## S4-002: All Items View

**Story**: As a user, I want a tabular list of all items, so that I can browse and manage them.

**Acceptance Criteria**:
- Table with columns per PAR-006
- Sortable columns (click header)
- Filter controls (type, workstream, status, search)
- Double-click opens edit dialog
- Responsive on tablet/mobile

**Traces**: PAR-006, WEB-002

---

## S4-003: Active Items View

**Story**: As a user, I want to see only active items grouped by severity, so that I can focus on what needs attention.

**Acceptance Criteria**:
- Excludes completed items
- Groups by severity (Critical, Warning, Active)
- Collapsible group cards
- Color-coded by severity
- Double-click opens edit dialog

**Traces**: PAR-007

---

## S4-004: Timeline View

**Story**: As a user, I want a Gantt-style timeline, so that I can visualize item schedules.

**Acceptance Criteria**:
- Items plotted by start/finish dates
- Color-coded by indicator status
- Today line visible
- Hover shows item details
- Scroll/zoom controls

**Traces**: PAR-008

---

## S4-005: Chronology View

**Story**: As a user, I want a monthly timeline, so that I can see items by month.

**Acceptance Criteria**:
- Items grouped by month
- Collapsible month sections
- Current month highlighted
- Items sorted by date within month

**Traces**: PAR-009

---

## S4-006: Help View

**Story**: As a user, I want in-app help, so that I can learn how to use the application.

**Acceptance Criteria**:
- Documentation displayed in app
- Keyboard shortcuts listed
- Searchable or indexed
- Contact/feedback link

**Traces**: PAR-017

---

## S4-007: Edit Item Dialog

**Story**: As a user, I want a modal dialog for editing items, so that I can update item details.

**Acceptance Criteria**:
- All fields editable per PAR-012
- Date pickers for date fields
- Slider or numeric for percent complete
- Save and Cancel buttons
- Validation errors displayed

**Traces**: PAR-012

---

## S4-008: Onboarding & Contextual Help

**Story**: As a new user, I want guided onboarding and contextual help, so that I can learn the app quickly without reading documentation.

**Acceptance Criteria**:
- First-time user tour (3-5 key features)
- Tooltips on complex fields (hover for explanation)
- Empty state guidance ("No items yet - click here to add your first")
- Keyboard shortcut hints in menus
- Skip/dismiss option for experienced users
- Tour can be restarted from Help menu

**Traces**: PAR-017
