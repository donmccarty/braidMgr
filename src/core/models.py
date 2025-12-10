"""
Data models for RAID Manager.
These are pure dataclasses with no external dependencies.
"""

from dataclasses import dataclass, field
from datetime import date
from typing import Optional
from enum import Enum


class ItemType(Enum):
    """Valid RAID item types (BRAID = Budget, Risk, Action Item, Issue, Decision)"""
    BUDGET = "Budget"
    RISK = "Risk"
    ACTION_ITEM = "Action Item"
    ISSUE = "Issue"
    DECISION = "Decision"
    DELIVERABLE = "Deliverable"
    PLAN_ITEM = "Plan Item"


class Indicator(Enum):
    """Calculated status indicators for items"""
    BEYOND_DEADLINE = "Beyond Deadline!!!"
    LATE_FINISH = "Late Finish!!"
    LATE_START = "Late Start!!"
    TRENDING_LATE = "Trending Late!"
    FINISHING_SOON = "Finishing Soon!"
    STARTING_SOON = "Starting Soon!"
    IN_PROGRESS = "In Progress"
    NOT_STARTED = "Not Started"
    COMPLETED = "Completed"
    COMPLETED_RECENTLY = "Completed Recently"


@dataclass
class Note:
    """A timestamped note entry"""
    date: date
    text: str

    def to_string(self) -> str:
        """Format as > MM/DD/YY - text"""
        return f"> {self.date.strftime('%m/%d/%y')} - {self.text}"


@dataclass
class Item:
    """A RAID log item"""
    item_num: int
    type: str
    title: str
    workstream: Optional[str] = None
    description: Optional[str] = None
    assigned_to: Optional[str] = None
    dep_item_num: list[int] = field(default_factory=list)
    start: Optional[date] = None
    finish: Optional[date] = None
    duration: Optional[int] = None
    deadline: Optional[date] = None
    draft: bool = False
    client_visible: bool = True
    percent_complete: int = 0
    rpt_out: list[str] = field(default_factory=list)
    created_date: Optional[date] = None
    last_updated: Optional[date] = None
    notes: Optional[str] = None
    indicator: Optional[str] = None
    priority: Optional[str] = None
    budget_amount: Optional[float] = None  # For Budget type items

    @property
    def is_complete(self) -> bool:
        """Check if item is in a completed state"""
        return self.indicator in ['Completed', 'Completed Recently', 'Done', 'Closed', 'Cancelled', 'Resolved']

    @property
    def is_open(self) -> bool:
        """Check if item is still open (not complete)"""
        return not self.is_complete

    @property
    def is_active(self) -> bool:
        """Check if item is actively being worked"""
        return self.indicator in ['In Progress', 'Finishing Soon!', 'Starting Soon!']

    @property
    def is_critical(self) -> bool:
        """Check if item has critical status"""
        return self.indicator in ['Beyond Deadline!!!', 'Late Finish!!', 'Late Start!!']

    @property
    def is_warning(self) -> bool:
        """Check if item has warning status"""
        return self.indicator in ['Trending Late!']


@dataclass
class ProjectMetadata:
    """RAID log metadata"""
    project_name: str
    client_name: Optional[str] = None
    next_item_num: int = 1
    last_updated: Optional[date] = None
    project_start: Optional[date] = None
    project_end: Optional[date] = None
    indicators_updated: Optional[date] = None
    workstreams: list[str] = field(default_factory=list)


@dataclass
class RateCardEntry:
    """A resource rate card entry"""
    name: str
    geography: str
    rate: float
    roll_off_date: Optional[date] = None


@dataclass
class TimesheetEntry:
    """A timesheet data entry"""
    week_ending: date
    resource: str
    hours: float
    rate: float
    cost: float
    complete_week: bool = True


@dataclass
class BudgetLedgerEntry:
    """A budget ledger entry (additions/changes to budget)"""
    amount: float
    date: date
    note: Optional[str] = None


@dataclass
class BudgetMetadata:
    """Budget file metadata"""
    project_name: str
    client: Optional[str] = None
    associated_raid_log: Optional[str] = None
    created: Optional[date] = None
    last_updated: Optional[date] = None
    data_source: Optional[str] = None


@dataclass
class BudgetData:
    """Complete budget data structure"""
    metadata: BudgetMetadata
    rate_card: list[RateCardEntry] = field(default_factory=list)
    budget_ledger: list[BudgetLedgerEntry] = field(default_factory=list)
    timesheet_data: list[TimesheetEntry] = field(default_factory=list)


@dataclass
class ProjectData:
    """Complete RAID log data structure"""
    metadata: ProjectMetadata
    items: list[Item] = field(default_factory=list)

    def get_item(self, item_num: int) -> Optional[Item]:
        """Get item by number"""
        for item in self.items:
            if item.item_num == item_num:
                return item
        return None

    def get_open_items(self) -> list[Item]:
        """Get all non-completed items"""
        return [i for i in self.items if i.is_open]

    def get_items_by_type(self, item_type: str) -> list[Item]:
        """Get items filtered by type"""
        return [i for i in self.items if i.type == item_type]

    def get_items_by_assignee(self, assignee: str) -> list[Item]:
        """Get items assigned to a specific person"""
        return [i for i in self.items if i.assigned_to == assignee]

    def get_items_by_workstream(self, workstream: str) -> list[Item]:
        """Get items in a specific workstream"""
        return [i for i in self.items if i.workstream == workstream]
