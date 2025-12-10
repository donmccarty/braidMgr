#!/usr/bin/env python3
"""
Test script for RAID Manager core modules.
Validates that we can load and process existing YAML files.
"""

import sys
from pathlib import Path

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.yaml_store import YamlStore
from src.core.indicators import calculate_indicator, update_all_indicators
from src.core.budget import BudgetCalculator, format_currency_full
from src.core.exports import Exporter
from datetime import date


def test_load_raid_log():
    """Test loading the RAID log"""
    print("=" * 60)
    print("TEST: Loading RAID Log")
    print("=" * 60)

    data_dir = Path(__file__).parent.parent.parent / 'project_viewer' / 'data'
    store = YamlStore(data_dir)

    raid_files = store.find_raid_logs()
    print(f"Found {len(raid_files)} RAID log files")

    if raid_files:
        raid_file = raid_files[0]
        print(f"Loading: {raid_file.name}")

        project_data = store.load_raid_log(raid_file)

        print(f"\nProject: {project_data.metadata.project_name}")
        print(f"Client: {project_data.metadata.client_name}")
        print(f"Items: {len(project_data.items)}")
        print(f"Workstreams: {project_data.metadata.workstreams}")

        # Count by type
        types = {}
        for item in project_data.items:
            types[item.type] = types.get(item.type, 0) + 1
        print(f"\nItems by type: {types}")

        # Show first few items
        print("\nFirst 3 items:")
        for item in project_data.items[:3]:
            print(f"  #{item.item_num}: {item.title[:50]} ({item.type})")

        return project_data
    return None


def test_indicators(project_data):
    """Test indicator calculation"""
    print("\n" + "=" * 60)
    print("TEST: Indicator Calculation")
    print("=" * 60)

    today = date.today()
    counts = {}

    for item in project_data.items:
        indicator = calculate_indicator(item, today)
        key = indicator or "No Indicator"
        counts[key] = counts.get(key, 0) + 1

    print(f"\nIndicator counts:")
    for indicator, count in sorted(counts.items(), key=lambda x: -x[1]):
        print(f"  {indicator}: {count}")

    # Test open/critical methods
    open_items = project_data.get_open_items()
    print(f"\nOpen items: {len(open_items)}")

    critical = [i for i in project_data.items if i.is_critical]
    print(f"Critical items: {len(critical)}")


def test_load_budget():
    """Test loading the Budget file"""
    print("\n" + "=" * 60)
    print("TEST: Loading Budget")
    print("=" * 60)

    data_dir = Path(__file__).parent.parent.parent / 'project_viewer' / 'data'
    store = YamlStore(data_dir)

    budget_files = store.find_budget_files()
    print(f"Found {len(budget_files)} Budget files")

    if budget_files:
        budget_file = budget_files[0]
        print(f"Loading: {budget_file.name}")

        budget_data = store.load_budget(budget_file)

        print(f"\nProject: {budget_data.metadata.project_name}")
        print(f"Client: {budget_data.metadata.client}")
        print(f"Rate card entries: {len(budget_data.rate_card)}")
        print(f"Timesheet entries: {len(budget_data.timesheet_data)}")
        print(f"Budget ledger entries: {len(budget_data.budget_ledger)}")

        return budget_data
    return None


def test_budget_calculations(budget_data):
    """Test budget calculations"""
    print("\n" + "=" * 60)
    print("TEST: Budget Calculations")
    print("=" * 60)

    calc = BudgetCalculator(budget_data)
    budget = calc.calculate()

    m = budget.metrics
    print(f"\nBudget Total: {format_currency_full(m.budget_total)}")
    print(f"Burn to Date: {format_currency_full(m.burn_to_date)} ({m.burn_pct}%)")
    print(f"Weekly Average: {format_currency_full(m.wkly_avg_burn)}")
    print(f"Remaining Burn: {format_currency_full(m.remaining_burn)}")
    print(f"Budget Remaining: {format_currency_full(m.budget_remaining)}")
    print(f"Status: {m.budget_status_icon}")

    print(f"\nWeeks: {m.weeks_completed}/{m.weeks_total} ({m.weeks_remaining} remaining)")

    print(f"\nWeekly burn trend ({len(budget.weekly_burn)} weeks):")
    for wb in budget.weekly_burn[-3:]:
        print(f"  {wb.week_ending}: {format_currency_full(wb.cost)} (cumulative: {format_currency_full(wb.cumulative)})")

    print(f"\nTop 3 resource burn:")
    for rb in budget.resource_burn[:3]:
        print(f"  {rb.resource}: {rb.hours}h = {format_currency_full(rb.cost)}")

    return budget


def test_exports(project_data, budget):
    """Test export functionality"""
    print("\n" + "=" * 60)
    print("TEST: Export Functionality")
    print("=" * 60)

    exporter = Exporter(project_data, budget)

    # Test summary
    summary = exporter.to_markdown_summary()
    print("\nSummary (first 500 chars):")
    print(summary[:500])

    # Test active items
    active_md = exporter.to_markdown_active()
    print(f"\nActive items MD length: {len(active_md)} chars")

    # Test CSV
    csv_output = exporter.to_csv()
    lines = csv_output.split('\n')
    print(f"CSV output: {len(lines)} lines")


def main():
    print("RAID Manager Core Module Tests")
    print("=" * 60)

    # Test RAID log loading
    project_data = test_load_raid_log()
    if not project_data:
        print("ERROR: Could not load RAID log")
        return 1

    # Test indicators
    test_indicators(project_data)

    # Test budget loading
    budget_data = test_load_budget()
    if not budget_data:
        print("WARNING: Could not load Budget file")
        budget = None
    else:
        budget = test_budget_calculations(budget_data)

    # Test exports
    test_exports(project_data, budget)

    print("\n" + "=" * 60)
    print("ALL TESTS PASSED")
    print("=" * 60)
    return 0


if __name__ == '__main__':
    sys.exit(main())
