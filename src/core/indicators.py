"""
Indicator calculation logic for RAID Manager.
Determines the status indicator for each item based on dates and progress.
"""

from datetime import date, timedelta
from typing import Optional
from dataclasses import dataclass

from .models import Item


@dataclass
class IndicatorConfig:
    """Configuration for a single indicator"""
    name: str
    severity: str  # 'critical', 'warning', 'active', 'upcoming', 'completed', 'done'
    icon: str
    color: str
    bg_color: str
    description: str


# Indicator configuration - matches the JavaScript indicatorConfig
INDICATOR_CONFIG = {
    "Beyond Deadline!!!": IndicatorConfig(
        name="Beyond Deadline!!!",
        severity="critical",
        icon="⛔",
        color="#fff",
        bg_color="#dc3545",
        description="Deadline has passed"
    ),
    "Late Finish!!": IndicatorConfig(
        name="Late Finish!!",
        severity="critical",
        icon="🔴",
        color="#fff",
        bg_color="#dc3545",
        description="Finish date passed, not complete"
    ),
    "Late Start!!": IndicatorConfig(
        name="Late Start!!",
        severity="critical",
        icon="⏰",
        color="#fff",
        bg_color="#dc3545",
        description="Start date passed, not started"
    ),
    "Trending Late!": IndicatorConfig(
        name="Trending Late!",
        severity="warning",
        icon="⚠️",
        color="#000",
        bg_color="#ffc107",
        description="May not finish on time based on progress"
    ),
    "Finishing Soon!": IndicatorConfig(
        name="Finishing Soon!",
        severity="active",
        icon="🏁",
        color="#fff",
        bg_color="#0d6efd",
        description="Finish date within 2 weeks"
    ),
    "Starting Soon!": IndicatorConfig(
        name="Starting Soon!",
        severity="upcoming",
        icon="🚀",
        color="#fff",
        bg_color="#6f42c1",
        description="Start date within 2 weeks"
    ),
    "In Progress": IndicatorConfig(
        name="In Progress",
        severity="active",
        icon="🔄",
        color="#fff",
        bg_color="#0d6efd",
        description="Work has started"
    ),
    "Not Started": IndicatorConfig(
        name="Not Started",
        severity="upcoming",
        icon="⏳",
        color="#fff",
        bg_color="#6c757d",
        description="Not yet begun"
    ),
    "Completed Recently": IndicatorConfig(
        name="Completed Recently",
        severity="completed",
        icon="✅",
        color="#fff",
        bg_color="#198754",
        description="Completed within last 2 weeks"
    ),
    "Completed": IndicatorConfig(
        name="Completed",
        severity="done",
        icon="✓",
        color="#fff",
        bg_color="#6c757d",
        description="Work is done"
    ),
}

# Severity ordering for sorting
SEVERITY_ORDER = ['critical', 'warning', 'active', 'upcoming', 'completed', 'done']

# Indicator ordering for display
INDICATOR_ORDER = [
    "Beyond Deadline!!!",
    "Late Finish!!",
    "Late Start!!",
    "Trending Late!",
    "Finishing Soon!",
    "Starting Soon!",
    "In Progress",
    "Completed Recently",
    "Completed",
    "Not Started",
]


def networkdays(start_date: date, end_date: date) -> int:
    """Calculate business days between two dates (inclusive)."""
    if not start_date or not end_date:
        return 0
    days = 0
    current = start_date
    while current <= end_date:
        if current.weekday() < 5:  # Monday = 0, Friday = 4
            days += 1
        current += timedelta(days=1)
    return days


def calculate_indicator(item: Item, today: Optional[date] = None) -> Optional[str]:
    """
    Calculate the indicator for a single item based on precedence rules.

    Precedence (highest to lowest):
    1. Completed Recently (100% and finished within 2 weeks)
    2. Completed (100%)
    3. Beyond Deadline!!! (deadline passed)
    4. Late Finish!! (finish date passed, not complete)
    5. Late Start!! (start date passed, not started)
    6. Trending Late! (remaining work > remaining time)
    7. Finishing Soon! (finish within 2 weeks)
    8. Starting Soon! (start within 2 weeks, not started)
    9. In Progress (started but not complete)
    10. Not Started (default for items with no dates)
    """
    if today is None:
        today = date.today()

    # Draft items get no indicator
    if item.draft:
        return None

    percent = item.percent_complete or 0
    start = item.start
    finish = item.finish
    deadline = item.deadline
    duration = item.duration

    soon_window = timedelta(days=14)

    # 1. Completed Recently
    if percent == 100 and finish and finish >= today - soon_window:
        return "Completed Recently"

    # 2. Completed
    if percent == 100:
        return "Completed"

    # 3. Beyond Deadline!!!
    if deadline and deadline < today:
        return "Beyond Deadline!!!"

    # 4. Late Finish!!
    if finish and finish < today and percent < 100:
        return "Late Finish!!"

    # 5. Late Start!!
    if start and start < today and percent == 0:
        return "Late Start!!"

    # 6. Trending Late!
    if start and finish and duration:
        remaining_days = (finish - today).days
        remaining_work = (1 - percent / 100) * duration
        if remaining_work > remaining_days:
            return "Trending Late!"

    # 7. Finishing Soon!
    if finish and finish <= today + soon_window and percent < 100:
        return "Finishing Soon!"

    # 8. Starting Soon!
    if percent == 0 and start and start <= today + soon_window and start >= today:
        return "Starting Soon!"

    # 9. In Progress
    if percent > 0 and percent < 100:
        return "In Progress"

    # 10. Default - Not Started (for items with dates but 0%)
    if start or finish:
        return "Not Started"

    return None


def update_all_indicators(items: list[Item], today: Optional[date] = None) -> dict[str, int]:
    """
    Update indicators for all items in place.
    Returns a count of each indicator type.
    """
    if today is None:
        today = date.today()

    counts: dict[str, int] = {}

    for item in items:
        indicator = calculate_indicator(item, today)
        item.indicator = indicator

        key = indicator or "No Indicator"
        counts[key] = counts.get(key, 0) + 1

    return counts


def get_indicator_config(indicator: Optional[str]) -> Optional[IndicatorConfig]:
    """Get the configuration for an indicator"""
    if indicator is None:
        return None
    return INDICATOR_CONFIG.get(indicator)


def sort_by_severity(items: list[Item]) -> list[Item]:
    """Sort items by indicator severity (most critical first)"""
    def severity_key(item: Item) -> tuple[int, str]:
        config = get_indicator_config(item.indicator)
        if config is None:
            return (len(SEVERITY_ORDER), item.title or '')
        try:
            severity_idx = SEVERITY_ORDER.index(config.severity)
        except ValueError:
            severity_idx = len(SEVERITY_ORDER)
        return (severity_idx, item.title or '')

    return sorted(items, key=severity_key)
