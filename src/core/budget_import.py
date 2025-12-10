"""
Budget import functionality for RAID Manager.
Imports timesheet data from OpenAir CSV exports.
"""

import csv
from datetime import datetime, date
from pathlib import Path
from typing import Optional
from dataclasses import dataclass

from .models import BudgetData, TimesheetEntry, RateCardEntry


@dataclass
class ImportResult:
    """Result of a budget import operation"""
    success: bool
    entries_imported: int
    entries_skipped: int  # Zero-hour entries
    weeks_with_data: int
    resources_found: list[str]
    resources_missing_rate: list[str]  # Resources not in rate card
    total_hours: float
    total_cost: float
    message: str


def parse_openair_csv(filepath: Path) -> list[dict]:
    """
    Parse OpenAir CSV export file.

    Expected columns:
    - Date: week ending date (MM/DD/YYYY)
    - User: resource name (Last, First)
    - Client: client name
    - Project: project name
    - Task: task type
    - All hours: hours for that week
    """
    rows = []

    with open(filepath, 'r', encoding='utf-8-sig') as f:  # utf-8-sig handles BOM
        reader = csv.DictReader(f)

        for row in reader:
            # Parse date - OpenAir uses MM/DD/YYYY
            date_str = row.get('Date', '').strip()
            try:
                week_ending = datetime.strptime(date_str, '%m/%d/%Y').date()
            except ValueError:
                continue  # Skip rows with invalid dates

            # Parse hours
            hours_str = row.get('All hours', '0').strip()
            try:
                hours = float(hours_str)
            except ValueError:
                hours = 0.0

            rows.append({
                'week_ending': week_ending,
                'resource': row.get('User', '').strip(),
                'client': row.get('Client', '').strip(),
                'project': row.get('Project', '').strip(),
                'task': row.get('Task', '').strip(),
                'hours': hours
            })

    return rows


def get_rate_for_resource(resource_name: str, rate_card: list[RateCardEntry]) -> Optional[float]:
    """Look up the rate for a resource from the rate card"""
    for entry in rate_card:
        if entry.name == resource_name:
            return entry.rate
    return None


def import_openair_csv(
    csv_path: Path,
    budget_data: BudgetData,
    project_end_date: Optional[date] = None
) -> ImportResult:
    """
    Import timesheet data from OpenAir CSV into budget data.

    Args:
        csv_path: Path to the OpenAir CSV export
        budget_data: Existing budget data (rate card will be used for lookups)
        project_end_date: Optional cutoff date - weeks after this are marked incomplete

    Returns:
        ImportResult with details of the import
    """
    # Parse the CSV
    rows = parse_openair_csv(csv_path)

    if not rows:
        return ImportResult(
            success=False,
            entries_imported=0,
            entries_skipped=0,
            weeks_with_data=0,
            resources_found=[],
            resources_missing_rate=[],
            total_hours=0,
            total_cost=0,
            message="No valid rows found in CSV"
        )

    # Build new timesheet entries
    new_entries: list[TimesheetEntry] = []
    skipped = 0
    missing_rates: set[str] = set()
    resources_found: set[str] = set()

    # Determine the latest week with any hours to mark complete_week
    today = date.today()

    # Find the Saturday of the current week (for complete_week logic)
    # A week is "complete" if its week_ending date is before the current week's Saturday
    days_until_saturday = (5 - today.weekday()) % 7
    if days_until_saturday == 0 and today.weekday() != 5:
        days_until_saturday = 7
    current_week_saturday = today + __import__('datetime').timedelta(days=days_until_saturday)

    for row in rows:
        # Skip zero-hour entries
        if row['hours'] == 0:
            skipped += 1
            continue

        resource = row['resource']
        resources_found.add(resource)

        # Look up rate
        rate = get_rate_for_resource(resource, budget_data.rate_card)
        if rate is None:
            missing_rates.add(resource)
            continue  # Skip entries without rates

        # Calculate cost
        cost = round(row['hours'] * rate, 2)

        # Determine if week is complete
        # Week is complete if its ending date is before today's week
        complete_week = row['week_ending'] < current_week_saturday

        # If project_end_date provided, also check against that
        if project_end_date and row['week_ending'] > project_end_date:
            complete_week = False

        new_entries.append(TimesheetEntry(
            week_ending=row['week_ending'],
            resource=resource,
            hours=row['hours'],
            rate=rate,
            cost=cost,
            complete_week=complete_week
        ))

    if not new_entries:
        return ImportResult(
            success=False,
            entries_imported=0,
            entries_skipped=skipped,
            weeks_with_data=0,
            resources_found=sorted(resources_found),
            resources_missing_rate=sorted(missing_rates),
            total_hours=0,
            total_cost=0,
            message=f"No entries to import. Missing rates for: {', '.join(sorted(missing_rates))}" if missing_rates else "No entries with hours > 0"
        )

    # Sort entries by week_ending, then resource
    new_entries.sort(key=lambda e: (e.week_ending, e.resource))

    # Calculate totals
    total_hours = sum(e.hours for e in new_entries)
    total_cost = sum(e.cost for e in new_entries)
    weeks_with_data = len(set(e.week_ending for e in new_entries))

    # Replace timesheet data
    budget_data.timesheet_data = new_entries

    # Update metadata
    budget_data.metadata.last_updated = today

    return ImportResult(
        success=True,
        entries_imported=len(new_entries),
        entries_skipped=skipped,
        weeks_with_data=weeks_with_data,
        resources_found=sorted(resources_found),
        resources_missing_rate=sorted(missing_rates),
        total_hours=total_hours,
        total_cost=total_cost,
        message=f"Imported {len(new_entries)} entries across {weeks_with_data} weeks"
    )
