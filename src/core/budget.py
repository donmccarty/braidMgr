"""
Budget calculation logic for RAID Manager.
Handles all financial metrics, burn rates, and projections.
"""

from dataclasses import dataclass, field
from datetime import date, timedelta
from typing import Optional
from collections import defaultdict
import math

from .models import BudgetData, TimesheetEntry, RateCardEntry, Item


@dataclass
class WeeklyBurn:
    """Weekly cost summary"""
    week_ending: date
    cost: float
    cumulative: float


@dataclass
class ResourceBurn:
    """Per-resource cost summary"""
    resource: str
    hours: float
    cost: float


@dataclass
class BudgetMetrics:
    """Calculated budget metrics"""
    proj_start: Optional[date] = None
    proj_end: Optional[date] = None
    updates_thru: Optional[date] = None
    budget_total: float = 0.0
    burn_to_date: float = 0.0
    wkly_avg_burn: float = 0.0
    weeks_total: int = 0
    weeks_completed: int = 0
    weeks_remaining: int = 0
    remaining_burn: float = 0.0
    est_total_burn: float = 0.0
    budget_remaining: float = 0.0
    budget_status: str = "unknown"
    budget_status_icon: str = ""
    burn_pct: float = 0.0
    remaining_pct: float = 0.0


@dataclass
class CalculatedBudget:
    """Complete calculated budget data for display"""
    metrics: BudgetMetrics
    weekly_burn: list[WeeklyBurn] = field(default_factory=list)
    resource_burn: list[ResourceBurn] = field(default_factory=list)


class BudgetCalculator:
    """Calculates budget metrics from raw budget data"""

    def __init__(self, budget_data: BudgetData):
        self.data = budget_data

    def calculate(self) -> CalculatedBudget:
        """Calculate all budget metrics"""
        metrics = BudgetMetrics()

        # Get complete weeks only
        complete_weeks = [ts for ts in self.data.timesheet_data if ts.complete_week]

        if not complete_weeks:
            return CalculatedBudget(metrics=metrics)

        # Project start: first billed date
        all_weeks = sorted(set(ts.week_ending for ts in complete_weeks))
        metrics.proj_start = all_weeks[0] if all_weeks else None

        # Project end: max roll-off date
        roll_offs = [rc.roll_off_date for rc in self.data.rate_card if rc.roll_off_date]
        metrics.proj_end = max(roll_offs) if roll_offs else None

        # Updates through: last complete week
        metrics.updates_thru = all_weeks[-1] if all_weeks else None

        # Budget total: sum of ledger entries
        metrics.budget_total = sum(bl.amount for bl in self.data.budget_ledger)

        # Burn to date: sum of complete week costs
        metrics.burn_to_date = sum(ts.cost for ts in complete_weeks)

        # Weeks calculations
        if metrics.proj_start and metrics.proj_end:
            total_days = (metrics.proj_end - metrics.proj_start).days
            metrics.weeks_total = math.ceil(total_days / 7)

        if metrics.proj_start and metrics.updates_thru:
            completed_days = (metrics.updates_thru - metrics.proj_start).days
            metrics.weeks_completed = round(completed_days / 7)

        metrics.weeks_remaining = max(0, metrics.weeks_total - metrics.weeks_completed)

        # Weekly average burn
        if metrics.weeks_completed > 0:
            metrics.wkly_avg_burn = round(metrics.burn_to_date / metrics.weeks_completed, 2)

        # Calculate remaining burn based on rate card and remaining weeks
        # This is a projection based on average weekly burn
        metrics.remaining_burn = round(metrics.wkly_avg_burn * metrics.weeks_remaining, 2)

        # Estimated total burn
        metrics.est_total_burn = round(metrics.burn_to_date + metrics.remaining_burn, 2)

        # Budget remaining
        metrics.budget_remaining = round(metrics.budget_total - metrics.est_total_burn, 2)

        # Budget status
        if metrics.budget_remaining < 0:
            metrics.budget_status = "over budget"
            metrics.budget_status_icon = "🔴 over budget"
        elif metrics.budget_total > 0 and metrics.budget_remaining < metrics.budget_total * 0.15:
            metrics.budget_status = "within 15%"
            metrics.budget_status_icon = "🟡 within 15%"
        else:
            metrics.budget_status = "under budget"
            metrics.budget_status_icon = "🟢 under budget"

        # Percentages
        if metrics.budget_total > 0:
            metrics.burn_pct = round((metrics.burn_to_date / metrics.budget_total) * 100, 1)
            metrics.remaining_pct = round(100 - metrics.burn_pct, 1)

        # Calculate weekly burn trend
        weekly_burn = self._calculate_weekly_burn(complete_weeks)

        # Calculate resource burn
        resource_burn = self._calculate_resource_burn(complete_weeks)

        return CalculatedBudget(
            metrics=metrics,
            weekly_burn=weekly_burn,
            resource_burn=resource_burn
        )

    def _calculate_weekly_burn(self, complete_weeks: list[TimesheetEntry]) -> list[WeeklyBurn]:
        """Calculate weekly burn with cumulative totals"""
        # Group by week
        by_week: dict[date, float] = defaultdict(float)
        for ts in complete_weeks:
            by_week[ts.week_ending] += ts.cost

        # Sort and calculate cumulative
        weekly_burn = []
        cumulative = 0.0
        for week in sorted(by_week.keys()):
            cost = round(by_week[week], 2)
            cumulative = round(cumulative + cost, 2)
            weekly_burn.append(WeeklyBurn(
                week_ending=week,
                cost=cost,
                cumulative=cumulative
            ))

        return weekly_burn

    def _calculate_resource_burn(self, complete_weeks: list[TimesheetEntry]) -> list[ResourceBurn]:
        """Calculate burn by resource, sorted by cost descending"""
        by_resource: dict[str, dict] = defaultdict(lambda: {'hours': 0.0, 'cost': 0.0})

        for ts in complete_weeks:
            by_resource[ts.resource]['hours'] += ts.hours
            by_resource[ts.resource]['cost'] += ts.cost

        resource_burn = [
            ResourceBurn(
                resource=name,
                hours=round(data['hours'], 2),
                cost=round(data['cost'], 2)
            )
            for name, data in by_resource.items()
        ]

        # Sort by cost descending
        resource_burn.sort(key=lambda x: x.cost, reverse=True)

        return resource_burn

    def get_budget_from_raid_items(self, items: list[Item]) -> float:
        """Calculate total budget from Budget-type RAID items"""
        return sum(
            item.budget_amount or 0
            for item in items
            if item.type == "Budget" and item.budget_amount
        )


def format_currency(amount: float) -> str:
    """Format amount as currency string"""
    if abs(amount) >= 1000:
        return f"${amount/1000:.0f}K"
    return f"${amount:,.0f}"


def format_currency_full(amount: float) -> str:
    """Format amount as full currency string with 2 decimals"""
    return f"${amount:,.2f}"


def format_currency_rounded(amount: float) -> str:
    """Format amount as currency string rounded to whole dollars"""
    return f"${round(amount):,}"
