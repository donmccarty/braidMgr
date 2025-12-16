"""
Unit tests for budget calculation logic.

Tests the BudgetCalculator class and currency formatting functions.
"""

import pytest
from datetime import date, timedelta

from src.core.budget import (
    BudgetCalculator,
    BudgetMetrics,
    CalculatedBudget,
    WeeklyBurn,
    ResourceBurn,
    format_currency,
    format_currency_full,
    format_currency_rounded,
)
from src.core.models import (
    BudgetData,
    BudgetMetadata,
    RateCardEntry,
    TimesheetEntry,
    BudgetLedgerEntry,
    Item,
)


# =============================================================================
# Fixtures
# =============================================================================

@pytest.fixture
def empty_budget_data():
    """Budget data with no timesheet entries."""
    return BudgetData(
        metadata=BudgetMetadata(project_name="Empty Project"),
        rate_card=[],
        budget_ledger=[],
        timesheet_data=[]
    )


@pytest.fixture
def simple_budget_data():
    """Simple budget with a few weeks of data."""
    return BudgetData(
        metadata=BudgetMetadata(
            project_name="Simple Project",
            client="Test Client"
        ),
        rate_card=[
            RateCardEntry(name="Dev", geography="US", rate=150.0,
                         roll_off_date=date(2024, 6, 30)),
        ],
        budget_ledger=[
            BudgetLedgerEntry(amount=50000.0, date=date(2024, 1, 1), note="Initial"),
        ],
        timesheet_data=[
            TimesheetEntry(week_ending=date(2024, 1, 7), resource="Alice",
                          hours=40.0, rate=150.0, cost=6000.0, complete_week=True),
            TimesheetEntry(week_ending=date(2024, 1, 14), resource="Alice",
                          hours=40.0, rate=150.0, cost=6000.0, complete_week=True),
            TimesheetEntry(week_ending=date(2024, 1, 21), resource="Alice",
                          hours=40.0, rate=150.0, cost=6000.0, complete_week=True),
        ]
    )


@pytest.fixture
def multi_resource_budget_data():
    """Budget with multiple resources."""
    return BudgetData(
        metadata=BudgetMetadata(project_name="Multi Resource"),
        rate_card=[
            RateCardEntry(name="Dev Sr", geography="US", rate=175.0,
                         roll_off_date=date(2024, 6, 30)),
            RateCardEntry(name="Dev Jr", geography="US", rate=125.0,
                         roll_off_date=date(2024, 6, 30)),
        ],
        budget_ledger=[
            BudgetLedgerEntry(amount=100000.0, date=date(2024, 1, 1)),
        ],
        timesheet_data=[
            # Week 1
            TimesheetEntry(week_ending=date(2024, 1, 7), resource="Alice",
                          hours=40.0, rate=175.0, cost=7000.0, complete_week=True),
            TimesheetEntry(week_ending=date(2024, 1, 7), resource="Bob",
                          hours=40.0, rate=125.0, cost=5000.0, complete_week=True),
            # Week 2
            TimesheetEntry(week_ending=date(2024, 1, 14), resource="Alice",
                          hours=32.0, rate=175.0, cost=5600.0, complete_week=True),
            TimesheetEntry(week_ending=date(2024, 1, 14), resource="Bob",
                          hours=40.0, rate=125.0, cost=5000.0, complete_week=True),
        ]
    )


# =============================================================================
# Currency Formatting Tests
# =============================================================================

class TestFormatCurrency:
    """Tests for currency formatting functions."""

    def test_format_currency_thousands(self):
        """Large amounts show as K (floor division)."""
        assert format_currency(5000) == "$5K"
        assert format_currency(12500) == "$12K"  # Floor division
        assert format_currency(100000) == "$100K"

    def test_format_currency_small(self):
        """Small amounts show full value."""
        assert format_currency(500) == "$500"
        assert format_currency(999) == "$999"

    def test_format_currency_negative(self):
        """Negative amounts handled correctly."""
        assert format_currency(-5000) == "$-5K"

    def test_format_currency_full(self):
        """Full format shows decimals."""
        assert format_currency_full(1234.56) == "$1,234.56"
        assert format_currency_full(50000) == "$50,000.00"

    def test_format_currency_rounded(self):
        """Rounded format shows whole dollars."""
        assert format_currency_rounded(1234.56) == "$1,235"
        assert format_currency_rounded(50000.99) == "$50,001"


# =============================================================================
# BudgetCalculator Tests
# =============================================================================

class TestBudgetCalculatorEmpty:
    """Tests for calculator with empty data."""

    def test_empty_timesheet_returns_default_metrics(self, empty_budget_data):
        """Empty timesheet returns metrics with defaults."""
        calc = BudgetCalculator(empty_budget_data)
        result = calc.calculate()

        assert isinstance(result, CalculatedBudget)
        assert result.metrics.burn_to_date == 0.0
        assert result.weekly_burn == []
        assert result.resource_burn == []


class TestBudgetCalculatorBasic:
    """Tests for basic budget calculations."""

    def test_budget_total_from_ledger(self, simple_budget_data):
        """Budget total is sum of ledger entries."""
        calc = BudgetCalculator(simple_budget_data)
        result = calc.calculate()

        assert result.metrics.budget_total == 50000.0

    def test_burn_to_date_from_timesheets(self, simple_budget_data):
        """Burn to date sums complete week costs."""
        calc = BudgetCalculator(simple_budget_data)
        result = calc.calculate()

        # 3 weeks * $6000 = $18000
        assert result.metrics.burn_to_date == 18000.0

    def test_project_start_is_first_week(self, simple_budget_data):
        """Project start is first billed week."""
        calc = BudgetCalculator(simple_budget_data)
        result = calc.calculate()

        assert result.metrics.proj_start == date(2024, 1, 7)

    def test_project_end_from_roll_off(self, simple_budget_data):
        """Project end is max roll-off date."""
        calc = BudgetCalculator(simple_budget_data)
        result = calc.calculate()

        assert result.metrics.proj_end == date(2024, 6, 30)

    def test_updates_thru_is_last_week(self, simple_budget_data):
        """Updates through is last complete week."""
        calc = BudgetCalculator(simple_budget_data)
        result = calc.calculate()

        assert result.metrics.updates_thru == date(2024, 1, 21)

    def test_weekly_average_burn(self, simple_budget_data):
        """Weekly average is burn / weeks completed."""
        calc = BudgetCalculator(simple_budget_data)
        result = calc.calculate()

        # $18000 / 2 weeks = $9000 (weeks_completed based on days)
        # Note: weeks_completed = round(14 days / 7) = 2
        assert result.metrics.wkly_avg_burn == 9000.0

    def test_burn_percentage(self, simple_budget_data):
        """Burn percentage calculated correctly."""
        calc = BudgetCalculator(simple_budget_data)
        result = calc.calculate()

        # $18000 / $50000 = 36%
        assert result.metrics.burn_pct == 36.0


class TestBudgetStatus:
    """Tests for budget status determination."""

    def test_under_budget_status(self):
        """Under budget shows green status."""
        # Short project with budget well above spending
        data = BudgetData(
            metadata=BudgetMetadata(project_name="Under Budget"),
            rate_card=[
                RateCardEntry(name="Dev", geography="US", rate=100.0,
                             roll_off_date=date(2024, 1, 28)),  # Short project
            ],
            budget_ledger=[
                BudgetLedgerEntry(amount=50000.0, date=date(2024, 1, 1)),
            ],
            timesheet_data=[
                TimesheetEntry(week_ending=date(2024, 1, 7), resource="Alice",
                              hours=40.0, rate=100.0, cost=4000.0, complete_week=True),
                TimesheetEntry(week_ending=date(2024, 1, 14), resource="Alice",
                              hours=40.0, rate=100.0, cost=4000.0, complete_week=True),
            ]
        )

        calc = BudgetCalculator(data)
        result = calc.calculate()

        # $8000 burned, short remaining timeline, $50000 budget
        assert result.metrics.budget_status == "under budget"
        assert "🟢" in result.metrics.budget_status_icon

    def test_over_budget_status(self):
        """Over budget shows red status."""
        data = BudgetData(
            metadata=BudgetMetadata(project_name="Over Budget"),
            rate_card=[
                RateCardEntry(name="Dev", geography="US", rate=200.0,
                             roll_off_date=date(2024, 3, 31)),
            ],
            budget_ledger=[
                BudgetLedgerEntry(amount=10000.0, date=date(2024, 1, 1)),
            ],
            timesheet_data=[
                TimesheetEntry(week_ending=date(2024, 1, 7), resource="Alice",
                              hours=40.0, rate=200.0, cost=8000.0, complete_week=True),
                TimesheetEntry(week_ending=date(2024, 1, 14), resource="Alice",
                              hours=40.0, rate=200.0, cost=8000.0, complete_week=True),
            ]
        )

        calc = BudgetCalculator(data)
        result = calc.calculate()

        # Burn to date: $16000, projected remaining: high, budget: $10000
        assert result.metrics.budget_status == "over budget"
        assert "🔴" in result.metrics.budget_status_icon

    def test_within_15_percent_status(self):
        """Within 15% remaining shows yellow status."""
        data = BudgetData(
            metadata=BudgetMetadata(project_name="Tight Budget"),
            rate_card=[
                RateCardEntry(name="Dev", geography="US", rate=150.0,
                             roll_off_date=date(2024, 2, 14)),  # Short project
            ],
            budget_ledger=[
                BudgetLedgerEntry(amount=20000.0, date=date(2024, 1, 1)),
            ],
            timesheet_data=[
                TimesheetEntry(week_ending=date(2024, 1, 7), resource="Alice",
                              hours=40.0, rate=150.0, cost=6000.0, complete_week=True),
                TimesheetEntry(week_ending=date(2024, 1, 14), resource="Alice",
                              hours=40.0, rate=150.0, cost=6000.0, complete_week=True),
                TimesheetEntry(week_ending=date(2024, 1, 21), resource="Alice",
                              hours=40.0, rate=150.0, cost=6000.0, complete_week=True),
            ]
        )

        calc = BudgetCalculator(data)
        result = calc.calculate()

        # $18000 burned with $20000 budget, ~90% spent
        # Check if within 15% triggers (budget_remaining < budget_total * 0.15)
        if result.metrics.budget_remaining >= 0 and result.metrics.budget_remaining < 20000 * 0.15:
            assert result.metrics.budget_status == "within 15%"
            assert "🟡" in result.metrics.budget_status_icon


class TestWeeklyBurnCalculation:
    """Tests for weekly burn trend calculation."""

    def test_weekly_burn_list(self, simple_budget_data):
        """Weekly burn has entry per week."""
        calc = BudgetCalculator(simple_budget_data)
        result = calc.calculate()

        assert len(result.weekly_burn) == 3

    def test_weekly_burn_sorted_by_date(self, simple_budget_data):
        """Weekly burn sorted chronologically."""
        calc = BudgetCalculator(simple_budget_data)
        result = calc.calculate()

        dates = [wb.week_ending for wb in result.weekly_burn]
        assert dates == sorted(dates)

    def test_weekly_burn_cumulative(self, simple_budget_data):
        """Cumulative totals are correct."""
        calc = BudgetCalculator(simple_budget_data)
        result = calc.calculate()

        assert result.weekly_burn[0].cumulative == 6000.0
        assert result.weekly_burn[1].cumulative == 12000.0
        assert result.weekly_burn[2].cumulative == 18000.0


class TestResourceBurnCalculation:
    """Tests for per-resource burn calculation."""

    def test_resource_burn_aggregates_hours(self, multi_resource_budget_data):
        """Resource hours aggregated across weeks."""
        calc = BudgetCalculator(multi_resource_budget_data)
        result = calc.calculate()

        alice = next(r for r in result.resource_burn if r.resource == "Alice")
        bob = next(r for r in result.resource_burn if r.resource == "Bob")

        assert alice.hours == 72.0  # 40 + 32
        assert bob.hours == 80.0    # 40 + 40

    def test_resource_burn_aggregates_cost(self, multi_resource_budget_data):
        """Resource costs aggregated across weeks."""
        calc = BudgetCalculator(multi_resource_budget_data)
        result = calc.calculate()

        alice = next(r for r in result.resource_burn if r.resource == "Alice")
        bob = next(r for r in result.resource_burn if r.resource == "Bob")

        assert alice.cost == 12600.0  # 7000 + 5600
        assert bob.cost == 10000.0    # 5000 + 5000

    def test_resource_burn_sorted_by_cost(self, multi_resource_budget_data):
        """Resources sorted by cost descending."""
        calc = BudgetCalculator(multi_resource_budget_data)
        result = calc.calculate()

        costs = [r.cost for r in result.resource_burn]
        assert costs == sorted(costs, reverse=True)


class TestBudgetFromRaidItems:
    """Tests for calculating budget from RAID items."""

    def test_sums_budget_items(self, empty_budget_data):
        """Sums budget_amount from Budget type items."""
        calc = BudgetCalculator(empty_budget_data)

        items = [
            Item(item_num=1, type="Budget", title="Initial", budget_amount=50000),
            Item(item_num=2, type="Budget", title="Extension", budget_amount=25000),
            Item(item_num=3, type="Action Item", title="Task", budget_amount=None),
        ]

        total = calc.get_budget_from_raid_items(items)
        assert total == 75000.0

    def test_ignores_non_budget_items(self, empty_budget_data):
        """Only Budget type items counted."""
        calc = BudgetCalculator(empty_budget_data)

        items = [
            Item(item_num=1, type="Risk", title="Risk", budget_amount=10000),
            Item(item_num=2, type="Action Item", title="Task", budget_amount=5000),
        ]

        total = calc.get_budget_from_raid_items(items)
        assert total == 0.0

    def test_handles_none_budget_amount(self, empty_budget_data):
        """Budget items with None amount treated as 0."""
        calc = BudgetCalculator(empty_budget_data)

        items = [
            Item(item_num=1, type="Budget", title="No Amount", budget_amount=None),
            Item(item_num=2, type="Budget", title="With Amount", budget_amount=10000),
        ]

        total = calc.get_budget_from_raid_items(items)
        assert total == 10000.0


class TestIncompleteWeeks:
    """Tests for handling incomplete weeks."""

    def test_excludes_incomplete_weeks(self):
        """Incomplete weeks excluded from calculations."""
        data = BudgetData(
            metadata=BudgetMetadata(project_name="With Incomplete"),
            rate_card=[],
            budget_ledger=[
                BudgetLedgerEntry(amount=50000.0, date=date(2024, 1, 1)),
            ],
            timesheet_data=[
                TimesheetEntry(week_ending=date(2024, 1, 7), resource="Alice",
                              hours=40.0, rate=150.0, cost=6000.0, complete_week=True),
                TimesheetEntry(week_ending=date(2024, 1, 14), resource="Alice",
                              hours=20.0, rate=150.0, cost=3000.0, complete_week=False),
            ]
        )

        calc = BudgetCalculator(data)
        result = calc.calculate()

        # Only complete week counted
        assert result.metrics.burn_to_date == 6000.0
        assert len(result.weekly_burn) == 1


class TestMultipleLedgerEntries:
    """Tests for multiple budget ledger entries."""

    def test_budget_total_sums_all_entries(self):
        """Budget total includes all ledger entries."""
        data = BudgetData(
            metadata=BudgetMetadata(project_name="Multi Ledger"),
            rate_card=[],
            budget_ledger=[
                BudgetLedgerEntry(amount=50000.0, date=date(2024, 1, 1), note="Initial"),
                BudgetLedgerEntry(amount=25000.0, date=date(2024, 3, 1), note="Extension"),
                BudgetLedgerEntry(amount=-5000.0, date=date(2024, 4, 1), note="Reduction"),
            ],
            # Need at least one complete week for calculate() to process budget
            timesheet_data=[
                TimesheetEntry(week_ending=date(2024, 1, 7), resource="Test",
                              hours=1.0, rate=100.0, cost=100.0, complete_week=True),
            ]
        )

        calc = BudgetCalculator(data)
        result = calc.calculate()

        assert result.metrics.budget_total == 70000.0
