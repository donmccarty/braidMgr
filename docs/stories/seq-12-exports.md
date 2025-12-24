# Sequence 12: Exports

*Parent: [USER_STORIES.md](../USER_STORIES.md)*

Export functionality for sharing project data outside the application. Supports Markdown for reports and CSV for data analysis.

**Depends on**: Sequences 4 (Views), 5 (Budget)
**Stories**: 3
**Priority**: MVP

**Key Concepts**:
- Exports respect current filter state
- Markdown for human-readable reports
- CSV for Excel/data analysis
- Include generation timestamp

---

## S12-001: Markdown Export

**Story**: As a user, I want to export to Markdown, so that I can share reports.

**Acceptance Criteria**:
- Active items report (grouped by severity)
- Summary report (counts and budget)
- Table format option
- Download as .md file

**Traces**: PAR-014

---

## S12-002: CSV Export

**Story**: As a user, I want to export to CSV, so that I can analyze in Excel.

**Acceptance Criteria**:
- All columns exported
- Dates formatted correctly (YYYY-MM-DD)
- Special characters escaped properly
- Download as .csv file

**Traces**: PAR-015

---

## S12-003: Filtered Export

**Story**: As a user, I want to export filtered results, so that I get only what I need.

**Acceptance Criteria**:
- Export current filter state
- By type, assignee, workstream, status
- Export open items only option
- Export critical items only option

**Traces**: PAR-014, PAR-015, PAR-016
