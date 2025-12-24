# Feature Parity Requirements (PAR)

*Parent: [REQUIREMENTS.md](../REQUIREMENTS.md)*

These document the current v1 functionality. All must be preserved in v1.5 for regression testing.

---

## PAR-001: Item Types

**Title**: Support 7 BRAID item types

**Description**: The system shall support the following item types:
- Budget
- Risk
- Action Item
- Issue
- Decision
- Deliverable
- Plan Item

**Acceptance Criteria**:
- All 7 item types can be created
- Items display with type-appropriate styling
- Filtering by type works correctly

**Priority**: MVP

---

## PAR-002: Item Fields

**Title**: Support all item data fields

**Description**: Each item shall have the following fields:
- item_num (unique within project)
- type (one of 7 types)
- title (required)
- workstream (optional)
- description (optional, multi-line)
- assigned_to (optional)
- dep_item_num (list of dependent item numbers)
- start date (optional)
- finish date (optional)
- duration (optional, in days)
- deadline (optional)
- draft (boolean, excludes from views if true)
- client_visible (boolean)
- percent_complete (0-100)
- rpt_out (list of report codes)
- created_date
- last_updated
- notes (multi-line with dated entries)
- indicator (calculated status)
- priority (optional)
- budget_amount (for Budget type items)

**Acceptance Criteria**:
- All fields can be edited via item dialog
- Fields persist correctly through save/load cycles
- Empty optional fields handled gracefully

**Priority**: MVP

---

## PAR-003: Status Indicators

**Title**: Automatic status indicator calculation

**Description**: The system shall automatically calculate status indicators based on dates and progress:

| Indicator | Severity | Condition |
|-----------|----------|-----------|
| Beyond Deadline!!! | critical | Deadline has passed |
| Late Finish!! | critical | Finish date passed, not 100% complete |
| Late Start!! | critical | Start date passed, 0% complete |
| Trending Late! | warning | Remaining work > remaining time |
| Finishing Soon! | active | Finish within 2 weeks, not complete |
| Starting Soon! | upcoming | Start within 2 weeks, not started |
| In Progress | active | Between 1-99% complete |
| Not Started | upcoming | Has dates, 0% complete |
| Completed Recently | completed | 100% and finished within 2 weeks |
| Completed | done | 100% complete |

**Acceptance Criteria**:
- Indicators calculate correctly per precedence rules
- Draft items receive no indicator
- Indicators update when dates/progress change
- Batch update available via "Update Indicators" action

**Priority**: MVP

---

## PAR-004: Project Metadata

**Title**: Project-level metadata storage

**Description**: Each project shall store metadata:
- project_name (required)
- client_name (optional)
- next_item_num (auto-increment counter)
- last_updated (timestamp)
- project_start date
- project_end date
- indicators_updated (timestamp of last recalculation)
- workstreams (list of strings)

**Acceptance Criteria**:
- Metadata displays in appropriate views
- Workstream list populates filter dropdowns
- next_item_num increments when items created

**Priority**: MVP

---

## PAR-005: Dashboard View

**Title**: Summary dashboard with statistics

**Description**: Dashboard view shall display:
- Summary cards showing counts by severity:
  - Critical items count
  - Warning items count
  - Active items count
  - Completed items count
  - Total items count
- Budget status indicator (if budget data loaded)
- Health score or velocity metrics
- Clickable cards to navigate to filtered views

**Acceptance Criteria**:
- All counts accurate and update on data changes
- Clicking a card navigates to filtered All Items view
- Budget status reflects current calculations
- Dashboard loads within 1 second

**Priority**: MVP

---

## PAR-006: All Items View

**Title**: Tabular view of all items with filtering

**Description**: All Items view shall display:
- Table with columns: #, Type, Workstream, Title, Assignee, Indicator, Deadline
- Filter controls:
  - Type dropdown (all types + "All")
  - Workstream dropdown (all workstreams + "All")
  - Status/Indicator dropdown
  - Search text box
- Sortable columns (click header to sort)
- Double-click row opens Edit dialog

**Acceptance Criteria**:
- All items display in table
- Filters combine correctly (AND logic)
- Search filters on title and description
- Sorting works for all columns
- Column widths reasonable for content

**Priority**: MVP

---

## PAR-007: Active Items View

**Title**: Grouped view of non-completed items

**Description**: Active Items view shall display:
- Only non-completed items (excludes Completed, Completed Recently)
- Grouped by severity (Critical, Warning, Active, etc.)
- Collapsible group cards
- Color-coded by severity
- Double-click item opens Edit dialog

**Acceptance Criteria**:
- Completed items not shown
- Groups display in severity order
- Group cards show item count
- Items within groups sorted by deadline

**Priority**: MVP

---

## PAR-008: Timeline View

**Title**: Gantt-style timeline visualization

**Description**: Timeline view shall display:
- Items plotted by start/finish dates on horizontal timeline
- Color-coded bars by indicator status
- Date axis with week markers
- "Today" indicator line
- Hover tooltips showing full item details
- Double-click item opens Edit dialog

**Acceptance Criteria**:
- Items with dates display as bars
- Items without dates excluded or shown separately
- Timeline scrolls/zooms appropriately
- Today line clearly visible
- Colors match indicator severity

**Priority**: MVP

---

## PAR-009: Chronology View

**Title**: Monthly timeline with collapsible sections

**Description**: Chronology view shall display:
- Items grouped by month (based on deadline/finish date)
- Collapsible month sections
- Month headers with visual grouping
- Items sorted by date within month

**Acceptance Criteria**:
- All items with dates appear in correct month
- Sections expand/collapse correctly
- Current month highlighted or expanded by default

**Priority**: MVP

---

## PAR-010: Budget View

**Title**: Budget metrics and visualization

**Description**: Budget view shall display:
- Metric cards:
  - Budget Total
  - Burn to Date
  - Average Weekly Burn
  - Budget Remaining
- Progress bar showing burn percentage
- Budget status indicator (over/under/within 15%)
- Weekly burn chart (bar chart)
- Resource breakdown table (hours, cost per resource)

**Acceptance Criteria**:
- Metrics calculate correctly from budget data
- Progress bar reflects burn_to_date / budget_total
- Status indicator updates based on projections
- Chart displays weekly burn trend
- Resource table sorted by cost descending

**Priority**: MVP

---

## PAR-011: Budget Data Model

**Title**: Budget data structure

**Description**: Budget data shall include:
- Metadata: project_name, client, associated_raid_log, created, last_updated, data_source
- Rate card: resource name, geography, hourly rate, roll_off_date
- Budget ledger: amount, date, note (additions/changes)
- Timesheet data: week_ending, resource, hours, rate, cost, complete_week flag

**Acceptance Criteria**:
- All budget fields load from YAML
- Rate card used for projections
- Only complete weeks included in calculations
- Budget ledger sums to budget total

**Priority**: MVP

---

## PAR-012: Edit Item Dialog

**Title**: Modal dialog for editing items

**Description**: Edit dialog shall allow editing:
- All item fields from PAR-002
- Date fields with date picker
- Percent complete with slider or numeric input
- Notes with multi-line text area
- Save and Cancel buttons
- Validation for required fields

**Acceptance Criteria**:
- Dialog opens with current item values
- Changes save correctly
- Cancel discards changes
- Validation errors shown clearly
- URL links in notes are clickable

**Priority**: MVP

---

## PAR-013: YAML Persistence

**Title**: Load and save data as YAML files

**Description**: System shall:
- Load project data from RAID-Log-*.yaml or BRAID-Log-*.yaml files
- Load budget data from Budget-*.yaml files
- Save changes back to source files
- Handle date parsing with fallbacks

**Acceptance Criteria**:
- Files load without data loss
- Changes persist after save
- File format matches current v1 structure
- Graceful handling of missing optional fields

**Priority**: MVP

---

## PAR-014: Export - Markdown

**Title**: Export to Markdown format

**Description**: System shall export:
- Active items report (grouped by severity)
- Summary report (counts and budget)
- Table format (all items or filtered)

**Acceptance Criteria**:
- Markdown valid and renders correctly
- Reports include generation date
- Budget summary included if available

**Priority**: MVP

---

## PAR-015: Export - CSV

**Title**: Export to CSV format

**Description**: System shall export items to CSV with columns:
- Item #, Type, Workstream, Title, Description
- Assigned To, Start, Finish, Deadline
- % Complete, Indicator, Priority, Draft, Client Visible

**Acceptance Criteria**:
- CSV imports correctly into Excel
- Dates formatted as YYYY-MM-DD
- Special characters escaped properly

**Priority**: MVP

---

## PAR-016: Filtering

**Title**: Filter items by various criteria

**Description**: System shall support filtering by:
- Type
- Workstream
- Assignee
- Status/Indicator
- Open vs Completed
- Critical items only
- Search text

**Acceptance Criteria**:
- Filters apply correctly
- Multiple filters combine with AND
- Filter state persists during session
- Clear filters option available

**Priority**: MVP

---

## PAR-017: Help View

**Title**: In-app help documentation

**Description**: Help view shall display:
- User documentation
- Keyboard shortcuts
- Feature explanations
- Contact/feedback information

**Acceptance Criteria**:
- Help content is readable and accurate
- Navigation within help content
- Searchable or indexed

**Priority**: MVP

---

## PAR-018: Update Indicators Action

**Title**: Batch recalculate all indicators

**Description**: System shall provide action to:
- Recalculate indicators for all items
- Update indicators_updated timestamp
- Save changes to file

**Acceptance Criteria**:
- All items updated in one operation
- Timestamp reflects recalculation time
- Changes visible immediately in views

**Priority**: MVP
