"""
Unit tests for YAML persistence layer.

Tests the YamlStore class which handles loading and saving RAID logs and Budget files.
Uses temporary files to avoid external dependencies.
"""

import pytest
from pathlib import Path
from datetime import date, datetime

from src.core.yaml_store import (
    YamlStore,
    _parse_date,
    _format_date,
)
from src.core.models import (
    Item,
    ProjectData,
    ProjectMetadata,
    BudgetData,
    BudgetMetadata,
    RateCardEntry,
    TimesheetEntry,
    BudgetLedgerEntry,
)


class TestParseDateHelper:
    """Tests for _parse_date helper function."""

    def test_parse_none(self):
        """None input returns None."""
        assert _parse_date(None) is None

    def test_parse_date_object(self):
        """date object returns same date."""
        d = date(2024, 12, 15)
        assert _parse_date(d) == d

    def test_parse_datetime_object(self):
        """datetime object is accepted (datetime is subclass of date)."""
        dt = datetime(2024, 12, 15, 10, 30, 0)
        # Note: datetime is a subclass of date, so isinstance(dt, date) is True
        # The function returns it as-is, which works since datetime can be used as date
        result = _parse_date(dt)
        assert result.year == 2024
        assert result.month == 12
        assert result.day == 15

    def test_parse_string_iso_format(self):
        """ISO format string parses correctly."""
        assert _parse_date("2024-12-15") == date(2024, 12, 15)

    def test_parse_invalid_string(self):
        """Invalid string returns None."""
        assert _parse_date("not-a-date") is None

    def test_parse_other_types(self):
        """Other types return None."""
        assert _parse_date(12345) is None
        assert _parse_date([2024, 12, 15]) is None


class TestFormatDateHelper:
    """Tests for _format_date helper function."""

    def test_format_none(self):
        """None input returns None."""
        assert _format_date(None) is None

    def test_format_date(self):
        """date formats as ISO string."""
        d = date(2024, 12, 15)
        assert _format_date(d) == "2024-12-15"


class TestYamlStoreInit:
    """Tests for YamlStore initialization."""

    def test_default_data_dir(self):
        """Default data_dir is current directory."""
        store = YamlStore()
        assert store.data_dir == Path('.')

    def test_custom_data_dir(self, tmp_path):
        """Can specify custom data_dir."""
        store = YamlStore(data_dir=tmp_path)
        assert store.data_dir == tmp_path


class TestRaidLogOperations:
    """Tests for RAID log load/save operations."""

    def test_save_and_load_raid_log(self, tmp_path, sample_project):
        """Can save and load a RAID log."""
        store = YamlStore(data_dir=tmp_path)
        filepath = tmp_path / "RAID-Log-Test.yaml"

        # Save
        store.save_raid_log(filepath, sample_project)
        assert filepath.exists()

        # Load
        loaded = store.load_raid_log(filepath)

        assert loaded.metadata.project_name == sample_project.metadata.project_name
        assert len(loaded.items) == len(sample_project.items)

    def test_load_preserves_metadata(self, tmp_path):
        """Loaded metadata matches saved metadata."""
        store = YamlStore(data_dir=tmp_path)
        filepath = tmp_path / "RAID-Log-Test.yaml"

        original = ProjectData(
            metadata=ProjectMetadata(
                project_name="Test Project",
                client_name="Test Client",
                next_item_num=42,
                last_updated=date(2024, 12, 15),
                project_start=date(2024, 1, 1),
                project_end=date(2024, 12, 31),
                indicators_updated=date(2024, 12, 15),
                workstreams=["Dev", "QA"]
            ),
            items=[]
        )

        store.save_raid_log(filepath, original)
        loaded = store.load_raid_log(filepath)

        assert loaded.metadata.project_name == "Test Project"
        assert loaded.metadata.client_name == "Test Client"
        assert loaded.metadata.next_item_num == 42
        assert loaded.metadata.workstreams == ["Dev", "QA"]

    def test_load_preserves_item_data(self, tmp_path, make_item):
        """Loaded items have correct data."""
        store = YamlStore(data_dir=tmp_path)
        filepath = tmp_path / "RAID-Log-Test.yaml"

        original_item = make_item(
            item_num=1,
            type="Risk",
            title="Major Risk",
            workstream="Development",
            assigned_to="Alice",
            percent_complete=50,
            start=date(2024, 12, 1),
            finish=date(2024, 12, 31),
            deadline=date(2024, 12, 15),
            notes="Some notes here",
            indicator="In Progress"
        )

        original = ProjectData(
            metadata=ProjectMetadata(project_name="Test"),
            items=[original_item]
        )

        store.save_raid_log(filepath, original)
        loaded = store.load_raid_log(filepath)

        item = loaded.items[0]
        assert item.item_num == 1
        assert item.type == "Risk"
        assert item.title == "Major Risk"
        assert item.workstream == "Development"
        assert item.assigned_to == "Alice"
        assert item.percent_complete == 50
        assert item.start == date(2024, 12, 1)
        assert item.finish == date(2024, 12, 31)
        assert item.deadline == date(2024, 12, 15)
        assert item.notes == "Some notes here"
        assert item.indicator == "In Progress"

    def test_load_handles_missing_fields(self, tmp_path):
        """Load handles YAML with minimal/missing fields."""
        store = YamlStore(data_dir=tmp_path)
        filepath = tmp_path / "RAID-Log-Minimal.yaml"

        # Write minimal YAML directly
        filepath.write_text("""
metadata:
  project_name: Minimal
items:
  - item_num: 1
    title: Test
""")

        loaded = store.load_raid_log(filepath)

        assert loaded.metadata.project_name == "Minimal"
        assert loaded.metadata.next_item_num == 1  # Default
        assert len(loaded.items) == 1
        assert loaded.items[0].type == "Plan Item"  # Default

    def test_load_handles_dep_item_num_as_strings(self, tmp_path):
        """Load converts string dep_item_num to integers."""
        store = YamlStore(data_dir=tmp_path)
        filepath = tmp_path / "RAID-Log-Deps.yaml"

        filepath.write_text("""
metadata:
  project_name: Test
items:
  - item_num: 2
    title: Dependent
    dep_item_num:
      - "1"
      - "3"
""")

        loaded = store.load_raid_log(filepath)
        assert loaded.items[0].dep_item_num == [1, 3]

    def test_save_includes_optional_fields(self, tmp_path, make_item):
        """Save includes duration, priority, budget_amount when set."""
        store = YamlStore(data_dir=tmp_path)
        filepath = tmp_path / "RAID-Log-Full.yaml"

        item = make_item(
            item_num=1,
            duration=14,
            priority="High",
            budget_amount=5000.00
        )

        project = ProjectData(
            metadata=ProjectMetadata(project_name="Test"),
            items=[item]
        )

        store.save_raid_log(filepath, project)

        # Read raw to verify optional fields
        content = filepath.read_text()
        assert "duration: 14" in content
        assert "priority: High" in content
        assert "budget_amount: 5000" in content


class TestBudgetOperations:
    """Tests for Budget load/save operations."""

    def test_save_and_load_budget(self, tmp_path):
        """Can save and load a Budget file."""
        store = YamlStore(data_dir=tmp_path)
        filepath = tmp_path / "Budget-Test.yaml"

        original = BudgetData(
            metadata=BudgetMetadata(
                project_name="Test Budget",
                client="Test Client"
            ),
            rate_card=[
                RateCardEntry(name="Dev", geography="US", rate=150.0)
            ],
            budget_ledger=[
                BudgetLedgerEntry(amount=50000.0, date=date(2024, 1, 1), note="Initial")
            ],
            timesheet_data=[
                TimesheetEntry(
                    week_ending=date(2024, 12, 15),
                    resource="Alice",
                    hours=40.0,
                    rate=150.0,
                    cost=6000.0
                )
            ]
        )

        store.save_budget(filepath, original)
        assert filepath.exists()

        loaded = store.load_budget(filepath)

        assert loaded.metadata.project_name == "Test Budget"
        assert len(loaded.rate_card) == 1
        assert loaded.rate_card[0].rate == 150.0
        assert len(loaded.budget_ledger) == 1
        assert loaded.budget_ledger[0].amount == 50000.0
        assert len(loaded.timesheet_data) == 1
        assert loaded.timesheet_data[0].hours == 40.0

    def test_load_budget_handles_missing_sections(self, tmp_path):
        """Load handles Budget with missing sections."""
        store = YamlStore(data_dir=tmp_path)
        filepath = tmp_path / "Budget-Minimal.yaml"

        filepath.write_text("""
metadata:
  project_name: Minimal
""")

        loaded = store.load_budget(filepath)

        assert loaded.metadata.project_name == "Minimal"
        assert loaded.rate_card == []
        assert loaded.budget_ledger == []
        assert loaded.timesheet_data == []


class TestDiscovery:
    """Tests for file discovery methods."""

    def test_find_raid_logs(self, tmp_path):
        """find_raid_logs finds RAID and BRAID log files."""
        store = YamlStore(data_dir=tmp_path)

        # Create test files
        (tmp_path / "RAID-Log-ProjectA.yaml").write_text("metadata: {}")
        (tmp_path / "BRAID-Log-ProjectB.yaml").write_text("metadata: {}")
        (tmp_path / "Other-File.yaml").write_text("metadata: {}")

        files = store.find_raid_logs()

        assert len(files) == 2
        names = [f.name for f in files]
        assert "RAID-Log-ProjectA.yaml" in names
        assert "BRAID-Log-ProjectB.yaml" in names
        assert "Other-File.yaml" not in names

    def test_find_budget_files(self, tmp_path):
        """find_budget_files finds Budget files."""
        store = YamlStore(data_dir=tmp_path)

        # Create test files
        (tmp_path / "Budget-ProjectA.yaml").write_text("metadata: {}")
        (tmp_path / "Budget-ProjectB.yaml").write_text("metadata: {}")
        (tmp_path / "Other-File.yaml").write_text("metadata: {}")

        files = store.find_budget_files()

        assert len(files) == 2
        names = [f.name for f in files]
        assert "Budget-ProjectA.yaml" in names
        assert "Budget-ProjectB.yaml" in names

    def test_find_no_files(self, tmp_path):
        """Discovery returns empty list when no matching files."""
        store = YamlStore(data_dir=tmp_path)

        assert store.find_raid_logs() == []
        assert store.find_budget_files() == []


class TestRoundTrip:
    """Tests that data survives a save/load cycle intact."""

    def test_full_project_roundtrip(self, tmp_path, sample_project):
        """Complete project survives roundtrip."""
        store = YamlStore(data_dir=tmp_path)
        filepath = tmp_path / "RAID-Log-Roundtrip.yaml"

        store.save_raid_log(filepath, sample_project)
        loaded = store.load_raid_log(filepath)

        assert loaded.metadata.project_name == sample_project.metadata.project_name
        assert loaded.metadata.client_name == sample_project.metadata.client_name
        assert len(loaded.items) == len(sample_project.items)

        for orig, loaded_item in zip(sample_project.items, loaded.items):
            assert loaded_item.item_num == orig.item_num
            assert loaded_item.title == orig.title
            assert loaded_item.type == orig.type

    def test_dates_survive_roundtrip(self, tmp_path, make_item):
        """Date fields survive roundtrip without loss."""
        store = YamlStore(data_dir=tmp_path)
        filepath = tmp_path / "RAID-Log-Dates.yaml"

        test_date = date(2024, 6, 15)
        item = make_item(
            item_num=1,
            start=test_date,
            finish=test_date,
            deadline=test_date,
            created_date=test_date,
            last_updated=test_date
        )

        project = ProjectData(
            metadata=ProjectMetadata(
                project_name="Test",
                last_updated=test_date,
                project_start=test_date,
                project_end=test_date,
                indicators_updated=test_date
            ),
            items=[item]
        )

        store.save_raid_log(filepath, project)
        loaded = store.load_raid_log(filepath)

        assert loaded.metadata.last_updated == test_date
        assert loaded.metadata.project_start == test_date
        assert loaded.items[0].start == test_date
        assert loaded.items[0].finish == test_date
        assert loaded.items[0].deadline == test_date
