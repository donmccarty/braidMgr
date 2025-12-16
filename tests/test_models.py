"""
Unit tests for data models.

Tests the Item, ProjectData, and related model classes.
"""

import pytest
from datetime import date

from src.core.models import (
    Item,
    ProjectData,
    ProjectMetadata,
    ItemType,
    Indicator,
    Note,
    BudgetData,
    BudgetMetadata,
    RateCardEntry,
    TimesheetEntry,
    BudgetLedgerEntry,
)


class TestItem:
    """Tests for Item dataclass."""

    def test_item_creation_minimal(self):
        """Item can be created with minimal required fields."""
        item = Item(item_num=1, type="Action Item", title="Test")
        assert item.item_num == 1
        assert item.type == "Action Item"
        assert item.title == "Test"
        assert item.percent_complete == 0
        assert item.draft is False

    def test_item_creation_full(self):
        """Item can be created with all fields."""
        today = date.today()
        item = Item(
            item_num=42,
            type="Risk",
            title="Major Risk",
            workstream="Development",
            description="A detailed description",
            assigned_to="Alice",
            dep_item_num=[1, 2, 3],
            start=today,
            finish=today,
            duration=5,
            deadline=today,
            draft=False,
            client_visible=True,
            percent_complete=50,
            rpt_out=["report1"],
            created_date=today,
            last_updated=today,
            notes="Some notes",
            indicator="In Progress",
            priority="High",
            budget_amount=10000.00
        )
        assert item.item_num == 42
        assert item.workstream == "Development"
        assert item.dep_item_num == [1, 2, 3]
        assert item.budget_amount == 10000.00

    def test_is_complete_with_completed_indicator(self):
        """is_complete returns True for completed indicators."""
        item = Item(item_num=1, type="Action Item", title="Test", indicator="Completed")
        assert item.is_complete is True

        item.indicator = "Completed Recently"
        assert item.is_complete is True

    def test_is_complete_with_active_indicator(self):
        """is_complete returns False for non-completed indicators."""
        item = Item(item_num=1, type="Action Item", title="Test", indicator="In Progress")
        assert item.is_complete is False

        item.indicator = "Late Finish!!"
        assert item.is_complete is False

    def test_is_open_inverse_of_complete(self):
        """is_open is inverse of is_complete."""
        item = Item(item_num=1, type="Action Item", title="Test", indicator="In Progress")
        assert item.is_open is True
        assert item.is_complete is False

        item.indicator = "Completed"
        assert item.is_open is False
        assert item.is_complete is True

    def test_is_active(self):
        """is_active returns True for active indicators."""
        active_indicators = ["In Progress", "Finishing Soon!", "Starting Soon!"]
        item = Item(item_num=1, type="Action Item", title="Test")

        for indicator in active_indicators:
            item.indicator = indicator
            assert item.is_active is True, f"Expected active for {indicator}"

        item.indicator = "Completed"
        assert item.is_active is False

    def test_is_critical(self):
        """is_critical returns True for critical indicators."""
        critical_indicators = ["Beyond Deadline!!!", "Late Finish!!", "Late Start!!"]
        item = Item(item_num=1, type="Action Item", title="Test")

        for indicator in critical_indicators:
            item.indicator = indicator
            assert item.is_critical is True, f"Expected critical for {indicator}"

        item.indicator = "In Progress"
        assert item.is_critical is False

    def test_is_warning(self):
        """is_warning returns True for warning indicators."""
        item = Item(item_num=1, type="Action Item", title="Test", indicator="Trending Late!")
        assert item.is_warning is True

        item.indicator = "In Progress"
        assert item.is_warning is False


class TestProjectMetadata:
    """Tests for ProjectMetadata dataclass."""

    def test_metadata_creation_minimal(self):
        """Metadata can be created with minimal fields."""
        meta = ProjectMetadata(project_name="Test Project")
        assert meta.project_name == "Test Project"
        assert meta.next_item_num == 1
        assert meta.workstreams == []

    def test_metadata_creation_full(self):
        """Metadata can be created with all fields."""
        today = date.today()
        meta = ProjectMetadata(
            project_name="Full Project",
            client_name="Big Client",
            next_item_num=100,
            last_updated=today,
            project_start=today,
            project_end=today,
            indicators_updated=today,
            workstreams=["Dev", "QA", "PM"]
        )
        assert meta.project_name == "Full Project"
        assert meta.workstreams == ["Dev", "QA", "PM"]


class TestProjectData:
    """Tests for ProjectData dataclass."""

    def test_project_data_creation(self, sample_metadata, sample_items):
        """ProjectData holds metadata and items."""
        project = ProjectData(metadata=sample_metadata, items=sample_items)
        assert project.metadata.project_name == "Test Project"
        assert len(project.items) == 5

    def test_get_item_found(self, sample_project):
        """get_item returns item when found."""
        item = sample_project.get_item(1)
        assert item is not None
        assert item.item_num == 1

    def test_get_item_not_found(self, sample_project):
        """get_item returns None when not found."""
        item = sample_project.get_item(999)
        assert item is None

    def test_get_open_items(self, sample_project):
        """get_open_items returns non-completed items."""
        # First set indicators so is_complete works
        sample_project.items[0].indicator = "Completed"  # item 1
        sample_project.items[1].indicator = "In Progress"  # item 2
        sample_project.items[2].indicator = "Not Started"  # item 3
        sample_project.items[3].indicator = "Late Finish!!"  # item 4
        sample_project.items[4].indicator = None  # draft

        open_items = sample_project.get_open_items()

        # Items 2, 3, 4 are open, item 5 (draft) is open, item 1 is completed
        assert len(open_items) == 4
        assert sample_project.items[0] not in open_items

    def test_get_items_by_type(self, sample_project):
        """get_items_by_type filters correctly."""
        action_items = sample_project.get_items_by_type("Action Item")
        assert len(action_items) == 2  # items 1 and 2

        risks = sample_project.get_items_by_type("Risk")
        assert len(risks) == 1

    def test_get_items_by_assignee(self, make_item):
        """get_items_by_assignee filters correctly."""
        items = [
            make_item(item_num=1, assigned_to="Alice"),
            make_item(item_num=2, assigned_to="Bob"),
            make_item(item_num=3, assigned_to="Alice"),
            make_item(item_num=4, assigned_to=None),
        ]
        project = ProjectData(
            metadata=ProjectMetadata(project_name="Test"),
            items=items
        )

        alice_items = project.get_items_by_assignee("Alice")
        assert len(alice_items) == 2

        bob_items = project.get_items_by_assignee("Bob")
        assert len(bob_items) == 1

    def test_get_items_by_workstream(self, make_item):
        """get_items_by_workstream filters correctly."""
        items = [
            make_item(item_num=1, workstream="Dev"),
            make_item(item_num=2, workstream="QA"),
            make_item(item_num=3, workstream="Dev"),
        ]
        project = ProjectData(
            metadata=ProjectMetadata(project_name="Test"),
            items=items
        )

        dev_items = project.get_items_by_workstream("Dev")
        assert len(dev_items) == 2


class TestNote:
    """Tests for Note dataclass."""

    def test_note_creation(self):
        """Note holds date and text."""
        note = Note(date=date(2024, 12, 15), text="Made progress on feature")
        assert note.date == date(2024, 12, 15)
        assert note.text == "Made progress on feature"

    def test_note_to_string(self):
        """to_string formats correctly."""
        note = Note(date=date(2024, 12, 15), text="Status update")
        expected = "> 12/15/24 - Status update"
        assert note.to_string() == expected


class TestItemType:
    """Tests for ItemType enum."""

    def test_item_types_exist(self):
        """All expected item types exist."""
        assert ItemType.BUDGET.value == "Budget"
        assert ItemType.RISK.value == "Risk"
        assert ItemType.ACTION_ITEM.value == "Action Item"
        assert ItemType.ISSUE.value == "Issue"
        assert ItemType.DECISION.value == "Decision"
        assert ItemType.DELIVERABLE.value == "Deliverable"
        assert ItemType.PLAN_ITEM.value == "Plan Item"


class TestIndicatorEnum:
    """Tests for Indicator enum."""

    def test_indicator_values(self):
        """Indicator enum has expected values."""
        assert Indicator.BEYOND_DEADLINE.value == "Beyond Deadline!!!"
        assert Indicator.COMPLETED.value == "Completed"
        assert Indicator.IN_PROGRESS.value == "In Progress"


class TestBudgetModels:
    """Tests for budget-related models."""

    def test_rate_card_entry(self):
        """RateCardEntry holds resource rate info."""
        entry = RateCardEntry(
            name="Senior Developer",
            geography="US",
            rate=150.00,
            roll_off_date=date(2025, 6, 30)
        )
        assert entry.name == "Senior Developer"
        assert entry.rate == 150.00

    def test_timesheet_entry(self):
        """TimesheetEntry holds time tracking data."""
        entry = TimesheetEntry(
            week_ending=date(2024, 12, 15),
            resource="Alice",
            hours=40.0,
            rate=150.00,
            cost=6000.00,
            complete_week=True
        )
        assert entry.hours == 40.0
        assert entry.cost == 6000.00

    def test_budget_ledger_entry(self):
        """BudgetLedgerEntry holds budget changes."""
        entry = BudgetLedgerEntry(
            amount=50000.00,
            date=date(2024, 1, 1),
            note="Initial budget allocation"
        )
        assert entry.amount == 50000.00

    def test_budget_data(self):
        """BudgetData aggregates budget information."""
        metadata = BudgetMetadata(project_name="Test", client="Client")
        budget = BudgetData(
            metadata=metadata,
            rate_card=[RateCardEntry(name="Dev", geography="US", rate=100)],
            budget_ledger=[BudgetLedgerEntry(amount=10000, date=date(2024, 1, 1))],
            timesheet_data=[]
        )
        assert budget.metadata.project_name == "Test"
        assert len(budget.rate_card) == 1
        assert len(budget.budget_ledger) == 1
