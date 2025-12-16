"""
Unit tests for export functionality.

Tests the Exporter class which generates Markdown and CSV reports.
"""

import pytest
import csv
from io import StringIO
from datetime import date

from src.core.exports import Exporter
from src.core.models import Item, ProjectData, ProjectMetadata
from src.core.budget import CalculatedBudget, BudgetMetrics


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def sample_project_for_export():
    """Project with items in various states for export testing."""
    items = [
        Item(item_num=1, type="Risk", title="Critical Risk",
             workstream="Development", assigned_to="Alice",
             percent_complete=0, indicator="Beyond Deadline!!!",
             start=date(2024, 12, 1), finish=date(2024, 12, 10),
             deadline=date(2024, 12, 8)),
        Item(item_num=2, type="Action Item", title="Late Task",
             workstream="Testing", assigned_to="Bob",
             percent_complete=50, indicator="Late Finish!!",
             start=date(2024, 12, 1), finish=date(2024, 12, 10)),
        Item(item_num=3, type="Issue", title="Warning Issue",
             workstream="Development", assigned_to="Alice",
             percent_complete=25, indicator="Trending Late!",
             start=date(2024, 12, 1), finish=date(2024, 12, 20)),
        Item(item_num=4, type="Action Item", title="Active Task",
             workstream="General", assigned_to="Carol",
             percent_complete=60, indicator="In Progress",
             start=date(2024, 12, 1), finish=date(2024, 12, 25)),
        Item(item_num=5, type="Decision", title="Completed Decision",
             workstream="General", assigned_to="Dave",
             percent_complete=100, indicator="Completed",
             start=date(2024, 11, 1), finish=date(2024, 11, 15)),
        Item(item_num=6, type="Deliverable", title="Draft Deliverable",
             workstream="Development", draft=True,
             percent_complete=0, indicator=None),
    ]

    return ProjectData(
        metadata=ProjectMetadata(
            project_name="Test Export Project",
            client_name="Export Client",
            workstreams=["Development", "Testing", "General"]
        ),
        items=items
    )


@pytest.fixture
def sample_budget_metrics():
    """Sample budget metrics for export testing."""
    return CalculatedBudget(
        metrics=BudgetMetrics(
            budget_total=100000.0,
            burn_to_date=45000.0,
            burn_pct=45.0,
            wkly_avg_burn=5000.0,
            remaining_burn=30000.0,
            budget_remaining=25000.0,
            budget_status="under budget",
            budget_status_icon="🟢 under budget"
        )
    )


# =============================================================================
# Exporter Initialization Tests
# =============================================================================

class TestExporterInit:
    """Tests for Exporter initialization."""

    def test_init_with_project_only(self, sample_project_for_export):
        """Can create exporter with just project data."""
        exporter = Exporter(sample_project_for_export)
        assert exporter.data == sample_project_for_export
        assert exporter.budget is None

    def test_init_with_budget(self, sample_project_for_export, sample_budget_metrics):
        """Can create exporter with project and budget."""
        exporter = Exporter(sample_project_for_export, sample_budget_metrics)
        assert exporter.budget == sample_budget_metrics


# =============================================================================
# Markdown Active Items Export Tests
# =============================================================================

class TestMarkdownActiveExport:
    """Tests for active items markdown export."""

    def test_contains_project_name(self, sample_project_for_export):
        """Export contains project name."""
        exporter = Exporter(sample_project_for_export)
        md = exporter.to_markdown_active()

        assert "Test Export Project" in md

    def test_contains_critical_section(self, sample_project_for_export):
        """Export has critical section with critical items."""
        exporter = Exporter(sample_project_for_export)
        md = exporter.to_markdown_active()

        assert "🔴 Critical" in md
        assert "Critical Risk" in md
        assert "Late Task" in md

    def test_contains_warning_section(self, sample_project_for_export):
        """Export has warning section with warning items."""
        exporter = Exporter(sample_project_for_export)
        md = exporter.to_markdown_active()

        assert "🟡 Warning" in md
        assert "Warning Issue" in md

    def test_contains_active_section(self, sample_project_for_export):
        """Export has active section with in-progress items."""
        exporter = Exporter(sample_project_for_export)
        md = exporter.to_markdown_active()

        assert "🔵 Active" in md
        assert "Active Task" in md

    def test_excludes_completed_items(self, sample_project_for_export):
        """Completed items not in active export."""
        exporter = Exporter(sample_project_for_export)
        md = exporter.to_markdown_active()

        assert "Completed Decision" not in md

    def test_excludes_draft_items(self, sample_project_for_export):
        """Draft items not in active export."""
        exporter = Exporter(sample_project_for_export)
        md = exporter.to_markdown_active()

        assert "Draft Deliverable" not in md

    def test_includes_item_details(self, sample_project_for_export):
        """Item entries include relevant details."""
        exporter = Exporter(sample_project_for_export)
        md = exporter.to_markdown_active()

        # Should have item numbers
        assert "#1" in md
        assert "#4" in md

        # Should have assignees
        assert "Alice" in md
        assert "Carol" in md


# =============================================================================
# Markdown Summary Export Tests
# =============================================================================

class TestMarkdownSummaryExport:
    """Tests for summary markdown export."""

    def test_contains_project_name(self, sample_project_for_export):
        """Summary contains project name."""
        exporter = Exporter(sample_project_for_export)
        md = exporter.to_markdown_summary()

        assert "Test Export Project" in md

    def test_contains_status_table(self, sample_project_for_export):
        """Summary has status indicator table."""
        exporter = Exporter(sample_project_for_export)
        md = exporter.to_markdown_summary()

        assert "| Indicator | Count |" in md

    def test_counts_indicators(self, sample_project_for_export):
        """Summary counts items by indicator."""
        exporter = Exporter(sample_project_for_export)
        md = exporter.to_markdown_summary()

        assert "Beyond Deadline!!!" in md
        assert "In Progress" in md

    def test_shows_total_items(self, sample_project_for_export):
        """Summary shows total item count."""
        exporter = Exporter(sample_project_for_export)
        md = exporter.to_markdown_summary()

        assert "Total Items" in md
        assert "6" in md

    def test_includes_budget_when_available(self, sample_project_for_export, sample_budget_metrics):
        """Summary includes budget section when budget provided."""
        exporter = Exporter(sample_project_for_export, sample_budget_metrics)
        md = exporter.to_markdown_summary()

        assert "Budget Summary" in md
        assert "$100,000.00" in md
        assert "45.0%" in md  # Formatted with one decimal place

    def test_no_budget_section_without_budget(self, sample_project_for_export):
        """Summary omits budget section when no budget."""
        exporter = Exporter(sample_project_for_export)
        md = exporter.to_markdown_summary()

        assert "Budget Summary" not in md


# =============================================================================
# Markdown Table Export Tests
# =============================================================================

class TestMarkdownTableExport:
    """Tests for markdown table export."""

    def test_has_header_row(self, sample_project_for_export):
        """Table has header row."""
        exporter = Exporter(sample_project_for_export)
        md = exporter.to_markdown_table()

        assert "| # | Type | Title |" in md

    def test_has_all_items(self, sample_project_for_export):
        """Table includes all items."""
        exporter = Exporter(sample_project_for_export)
        md = exporter.to_markdown_table()

        for item in sample_project_for_export.items:
            assert str(item.item_num) in md

    def test_can_filter_items(self, sample_project_for_export):
        """Table can use filtered item list."""
        exporter = Exporter(sample_project_for_export)
        filtered = [i for i in sample_project_for_export.items if i.type == "Action Item"]
        md = exporter.to_markdown_table(items=filtered)

        assert "Late Task" in md
        assert "Active Task" in md
        assert "Critical Risk" not in md


# =============================================================================
# CSV Export Tests
# =============================================================================

class TestCsvExport:
    """Tests for CSV export functionality."""

    def test_returns_valid_csv(self, sample_project_for_export):
        """to_csv returns valid CSV string."""
        exporter = Exporter(sample_project_for_export)
        csv_str = exporter.to_csv()

        # Should be parseable
        reader = csv.reader(StringIO(csv_str))
        rows = list(reader)

        # Header + 6 items
        assert len(rows) == 7

    def test_has_expected_columns(self, sample_project_for_export):
        """CSV has expected header columns."""
        exporter = Exporter(sample_project_for_export)
        csv_str = exporter.to_csv()

        reader = csv.reader(StringIO(csv_str))
        header = next(reader)

        assert 'Item #' in header
        assert 'Type' in header
        assert 'Title' in header
        assert 'Assigned To' in header
        assert 'Indicator' in header

    def test_includes_all_items(self, sample_project_for_export):
        """CSV includes all items."""
        exporter = Exporter(sample_project_for_export)
        csv_str = exporter.to_csv()

        reader = csv.DictReader(StringIO(csv_str))
        rows = list(reader)

        assert len(rows) == 6
        item_nums = [row['Item #'] for row in rows]
        assert '1' in item_nums
        assert '6' in item_nums

    def test_formats_dates(self, sample_project_for_export):
        """CSV formats dates as YYYY-MM-DD."""
        exporter = Exporter(sample_project_for_export)
        csv_str = exporter.to_csv()

        reader = csv.DictReader(StringIO(csv_str))
        rows = list(reader)

        first_item = rows[0]
        assert first_item['Start'] == '2024-12-01'

    def test_handles_none_values(self, sample_project_for_export):
        """CSV handles None values gracefully."""
        exporter = Exporter(sample_project_for_export)
        csv_str = exporter.to_csv()

        # Draft item has no assigned_to
        reader = csv.DictReader(StringIO(csv_str))
        draft_row = [r for r in reader if r['Item #'] == '6'][0]
        assert draft_row['Assigned To'] == ''

    def test_draft_column(self, sample_project_for_export):
        """CSV has Draft column with Yes/No."""
        exporter = Exporter(sample_project_for_export)
        csv_str = exporter.to_csv()

        reader = csv.DictReader(StringIO(csv_str))
        rows = list(reader)

        draft_row = [r for r in rows if r['Item #'] == '6'][0]
        assert draft_row['Draft'] == 'Yes'

        non_draft_row = [r for r in rows if r['Item #'] == '1'][0]
        assert non_draft_row['Draft'] == 'No'

    def test_can_filter_items(self, sample_project_for_export):
        """CSV can use filtered item list."""
        exporter = Exporter(sample_project_for_export)
        filtered = [i for i in sample_project_for_export.items if i.workstream == "Development"]
        csv_str = exporter.to_csv(items=filtered)

        reader = csv.DictReader(StringIO(csv_str))
        rows = list(reader)

        # Items 1, 3, 6 are Development
        assert len(rows) == 3


# =============================================================================
# CSV File Save Tests
# =============================================================================

class TestCsvFileSave:
    """Tests for saving CSV to file."""

    def test_save_creates_file(self, sample_project_for_export, tmp_path):
        """save_csv creates file at path."""
        exporter = Exporter(sample_project_for_export)
        filepath = tmp_path / "export.csv"

        exporter.save_csv(filepath)

        assert filepath.exists()

    def test_saved_file_is_valid_csv(self, sample_project_for_export, tmp_path):
        """Saved file is valid CSV."""
        exporter = Exporter(sample_project_for_export)
        filepath = tmp_path / "export.csv"

        exporter.save_csv(filepath)

        with open(filepath, 'r', encoding='utf-8') as f:
            reader = csv.reader(f)
            rows = list(reader)

        assert len(rows) == 7  # Header + 6 items


# =============================================================================
# Markdown File Save Tests
# =============================================================================

class TestMarkdownFileSave:
    """Tests for saving markdown to file."""

    def test_save_creates_file(self, sample_project_for_export, tmp_path):
        """save_markdown creates file at path."""
        exporter = Exporter(sample_project_for_export)
        filepath = tmp_path / "export.md"
        content = exporter.to_markdown_summary()

        exporter.save_markdown(filepath, content)

        assert filepath.exists()

    def test_saved_file_has_content(self, sample_project_for_export, tmp_path):
        """Saved file contains expected content."""
        exporter = Exporter(sample_project_for_export)
        filepath = tmp_path / "export.md"
        content = exporter.to_markdown_summary()

        exporter.save_markdown(filepath, content)

        saved = filepath.read_text()
        assert "Test Export Project" in saved


# =============================================================================
# Filtered Item Methods Tests
# =============================================================================

class TestFilteredItemMethods:
    """Tests for convenience filter methods."""

    def test_get_open_items(self, sample_project_for_export):
        """get_open_items returns non-completed items."""
        exporter = Exporter(sample_project_for_export)
        open_items = exporter.get_open_items()

        # Item 5 is completed, so 5 open items
        assert len(open_items) == 5
        assert all(not i.is_complete for i in open_items)

    def test_get_critical_items(self, sample_project_for_export):
        """get_critical_items returns critical status items."""
        exporter = Exporter(sample_project_for_export)
        critical = exporter.get_critical_items()

        # Items 1 and 2 are critical
        assert len(critical) == 2
        assert all(i.is_critical for i in critical)

    def test_get_items_by_assignee(self, sample_project_for_export):
        """get_items_by_assignee filters by assignee."""
        exporter = Exporter(sample_project_for_export)
        alice_items = exporter.get_items_by_assignee("Alice")

        assert len(alice_items) == 2
        assert all(i.assigned_to == "Alice" for i in alice_items)

    def test_get_items_by_type(self, sample_project_for_export):
        """get_items_by_type filters by type."""
        exporter = Exporter(sample_project_for_export)
        action_items = exporter.get_items_by_type("Action Item")

        assert len(action_items) == 2
        assert all(i.type == "Action Item" for i in action_items)

    def test_get_items_by_workstream(self, sample_project_for_export):
        """get_items_by_workstream filters by workstream."""
        exporter = Exporter(sample_project_for_export)
        dev_items = exporter.get_items_by_workstream("Development")

        assert len(dev_items) == 3
        assert all(i.workstream == "Development" for i in dev_items)
