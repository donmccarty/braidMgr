"""
Unit tests for indicator calculation logic.

Tests the calculate_indicator function which determines status based on:
- Percent complete
- Start/finish dates
- Deadline
- Duration and remaining work
"""

import pytest
from datetime import date, timedelta

from src.core.indicators import (
    calculate_indicator,
    update_all_indicators,
    networkdays,
    get_indicator_config,
    sort_by_severity,
    INDICATOR_CONFIG,
    SEVERITY_ORDER,
)


class TestNetworkdays:
    """Tests for business day calculation."""

    def test_same_day_weekday(self):
        """Same weekday counts as 1 business day."""
        monday = date(2024, 12, 16)  # Monday
        assert networkdays(monday, monday) == 1

    def test_same_day_weekend(self):
        """Same weekend day counts as 0 business days."""
        saturday = date(2024, 12, 14)
        assert networkdays(saturday, saturday) == 0

    def test_full_week(self):
        """Monday to Friday = 5 business days."""
        monday = date(2024, 12, 16)
        friday = date(2024, 12, 20)
        assert networkdays(monday, friday) == 5

    def test_week_with_weekend(self):
        """Monday to next Monday = 6 business days (skips weekend)."""
        monday = date(2024, 12, 16)
        next_monday = date(2024, 12, 23)
        assert networkdays(monday, next_monday) == 6

    def test_none_dates(self):
        """None dates return 0."""
        assert networkdays(None, date(2024, 12, 15)) == 0
        assert networkdays(date(2024, 12, 15), None) == 0
        assert networkdays(None, None) == 0


class TestCompletedIndicators:
    """Tests for completed item indicators."""

    def test_completed_100_percent(self, make_item, today, two_weeks_ago):
        """100% complete with old finish date = Completed."""
        item = make_item(
            percent_complete=100,
            finish=two_weeks_ago - timedelta(days=1)  # More than 2 weeks ago
        )
        assert calculate_indicator(item, today) == "Completed"

    def test_completed_recently(self, make_item, today, one_week_ago):
        """100% complete with recent finish = Completed Recently."""
        item = make_item(
            percent_complete=100,
            finish=one_week_ago  # Within 2 weeks
        )
        assert calculate_indicator(item, today) == "Completed Recently"

    def test_completed_recently_same_day(self, make_item, today):
        """100% complete finishing today = Completed Recently."""
        item = make_item(percent_complete=100, finish=today)
        assert calculate_indicator(item, today) == "Completed Recently"


class TestCriticalIndicators:
    """Tests for critical (red) indicators."""

    def test_beyond_deadline(self, make_item, today, one_week_ago):
        """Past deadline with incomplete work = Beyond Deadline!!!"""
        item = make_item(
            percent_complete=50,
            deadline=one_week_ago
        )
        assert calculate_indicator(item, today) == "Beyond Deadline!!!"

    def test_late_finish(self, make_item, today, one_week_ago):
        """Past finish date, not complete = Late Finish!!"""
        item = make_item(
            percent_complete=75,
            start=one_week_ago - timedelta(days=7),
            finish=one_week_ago
        )
        assert calculate_indicator(item, today) == "Late Finish!!"

    def test_late_start(self, make_item, today, one_week_ago):
        """Past start date, 0% complete = Late Start!!"""
        item = make_item(
            percent_complete=0,
            start=one_week_ago,
            finish=today + timedelta(days=7)
        )
        assert calculate_indicator(item, today) == "Late Start!!"

    def test_deadline_takes_priority_over_late_finish(self, make_item, today, one_week_ago):
        """Beyond Deadline takes priority over Late Finish."""
        item = make_item(
            percent_complete=50,
            finish=one_week_ago,
            deadline=one_week_ago - timedelta(days=1)
        )
        assert calculate_indicator(item, today) == "Beyond Deadline!!!"


class TestWarningIndicators:
    """Tests for warning (yellow) indicators."""

    def test_trending_late(self, make_item, today, one_week_ago, one_week_ahead):
        """50% work remaining with less time remaining = Trending Late!"""
        # Started 7 days ago, finishes in 7 days (14 day duration)
        # Only 25% complete means 75% remaining work (10.5 days worth)
        # But only 7 days remain
        item = make_item(
            percent_complete=25,
            start=one_week_ago,
            finish=one_week_ahead,
            duration=14
        )
        assert calculate_indicator(item, today) == "Trending Late!"

    def test_not_trending_late_if_on_track(self, make_item, today, one_week_ago, one_week_ahead):
        """On-track progress should not show Trending Late."""
        # Started 7 days ago, finishes in 7 days (14 day duration)
        # 50% complete means 7 days of work remaining, 7 days of time remaining
        item = make_item(
            percent_complete=50,
            start=one_week_ago,
            finish=one_week_ahead,
            duration=14
        )
        # Should be In Progress or Finishing Soon, not Trending Late
        indicator = calculate_indicator(item, today)
        assert indicator != "Trending Late!"


class TestUpcomingIndicators:
    """Tests for upcoming (blue/purple) indicators."""

    def test_finishing_soon(self, make_item, today, one_week_ahead):
        """Finish within 2 weeks, in progress = Finishing Soon!"""
        item = make_item(
            percent_complete=50,
            start=today - timedelta(days=7),
            finish=one_week_ahead
        )
        assert calculate_indicator(item, today) == "Finishing Soon!"

    def test_starting_soon(self, make_item, today):
        """Start within 2 weeks, 0% = Starting Soon!"""
        item = make_item(
            percent_complete=0,
            start=today + timedelta(days=5),
            finish=today + timedelta(days=20)
        )
        assert calculate_indicator(item, today) == "Starting Soon!"

    def test_starting_today(self, make_item, today):
        """Start date is today, 0% = Starting Soon! (when finish is far out)."""
        item = make_item(
            percent_complete=0,
            start=today,
            finish=today + timedelta(days=30)  # Finish far enough out that it won't trigger Finishing Soon
        )
        assert calculate_indicator(item, today) == "Starting Soon!"

    def test_starting_today_with_near_finish_shows_finishing_soon(self, make_item, today):
        """When both start and finish are within 2 weeks, Finishing Soon takes precedence."""
        item = make_item(
            percent_complete=0,
            start=today,
            finish=today + timedelta(days=14)  # Within 2 weeks
        )
        # Finishing Soon has higher priority than Starting Soon
        assert calculate_indicator(item, today) == "Finishing Soon!"


class TestActiveIndicators:
    """Tests for in-progress indicators."""

    def test_in_progress(self, make_item, today, three_weeks_ahead):
        """Started but not near finish = In Progress."""
        item = make_item(
            percent_complete=30,
            start=today - timedelta(days=7),
            finish=three_weeks_ahead
        )
        assert calculate_indicator(item, today) == "In Progress"

    def test_not_started(self, make_item, today, three_weeks_ahead):
        """Has dates but 0% = Not Started."""
        item = make_item(
            percent_complete=0,
            start=three_weeks_ahead,
            finish=three_weeks_ahead + timedelta(days=7)
        )
        assert calculate_indicator(item, today) == "Not Started"


class TestDraftItems:
    """Tests for draft item handling."""

    def test_draft_no_indicator(self, make_item, today, one_week_ago):
        """Draft items get no indicator regardless of dates."""
        item = make_item(
            percent_complete=0,
            start=one_week_ago,  # Would be Late Start
            finish=today,
            draft=True
        )
        assert calculate_indicator(item, today) is None


class TestItemWithoutDates:
    """Tests for items without dates."""

    def test_no_dates_no_indicator(self, make_item, today):
        """Item with no dates and 0% = no indicator."""
        item = make_item(percent_complete=0)
        assert calculate_indicator(item, today) is None

    def test_in_progress_no_dates(self, make_item, today):
        """Item with no dates but >0% = In Progress."""
        item = make_item(percent_complete=25)
        assert calculate_indicator(item, today) == "In Progress"


class TestUpdateAllIndicators:
    """Tests for batch indicator updates."""

    def test_updates_all_items(self, sample_items, today):
        """update_all_indicators sets indicator on each item."""
        counts = update_all_indicators(sample_items, today)

        # All items should have indicator set (or None for draft)
        for item in sample_items:
            if item.draft:
                assert item.indicator is None
            else:
                assert item.indicator is not None

    def test_returns_counts(self, sample_items, today):
        """update_all_indicators returns indicator counts."""
        counts = update_all_indicators(sample_items, today)

        assert isinstance(counts, dict)
        assert sum(counts.values()) == len(sample_items)


class TestIndicatorConfig:
    """Tests for indicator configuration."""

    def test_all_indicators_have_config(self):
        """Every indicator string has configuration."""
        indicator_names = [
            "Beyond Deadline!!!",
            "Late Finish!!",
            "Late Start!!",
            "Trending Late!",
            "Finishing Soon!",
            "Starting Soon!",
            "In Progress",
            "Not Started",
            "Completed Recently",
            "Completed",
        ]
        for name in indicator_names:
            config = get_indicator_config(name)
            assert config is not None, f"Missing config for {name}"
            assert config.name == name
            assert config.severity in SEVERITY_ORDER

    def test_get_config_none(self):
        """get_indicator_config returns None for None input."""
        assert get_indicator_config(None) is None

    def test_get_config_unknown(self):
        """get_indicator_config returns None for unknown indicator."""
        assert get_indicator_config("Unknown Indicator") is None


class TestSortBySeverity:
    """Tests for severity-based sorting."""

    def test_critical_before_warning(self, make_item, today):
        """Critical items sort before warning items."""
        critical = make_item(item_num=1, title="Critical", deadline=today - timedelta(days=1))
        warning = make_item(item_num=2, title="Warning", percent_complete=25,
                           start=today - timedelta(days=7), finish=today + timedelta(days=3), duration=10)

        update_all_indicators([critical, warning], today)
        sorted_items = sort_by_severity([warning, critical])

        assert sorted_items[0] == critical

    def test_completed_sorts_last(self, make_item, today, three_weeks_ahead):
        """Completed items sort after active items."""
        completed = make_item(item_num=1, title="Done", percent_complete=100,
                             finish=today - timedelta(days=20))
        active = make_item(item_num=2, title="Active", percent_complete=50,
                          start=today - timedelta(days=7), finish=three_weeks_ahead)

        update_all_indicators([completed, active], today)
        sorted_items = sort_by_severity([completed, active])

        assert sorted_items[0] == active
        assert sorted_items[1] == completed
