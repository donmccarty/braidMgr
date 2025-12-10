#!/usr/bin/env python3
"""
RAID Manager CLI - Command-line interface for RAID log management.

Usage:
    raid-cli update [--file FILE]           Update indicators for all items
    raid-cli export [--format FORMAT] [--filter FILTER] [--file FILE]
    raid-cli summary [--file FILE]          Show project summary
    raid-cli list [--open] [--type TYPE] [--assigned PERSON] [--file FILE]
    raid-cli budget [--file FILE]           Show budget summary

Examples:
    raid-cli update
    raid-cli export --format md --filter active
    raid-cli list --open --assigned "Don McCarty"
    raid-cli budget
"""

import argparse
import sys
from datetime import date
from pathlib import Path
from typing import Optional

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.yaml_store import YamlStore
from src.core.indicators import update_all_indicators, INDICATOR_ORDER
from src.core.budget import BudgetCalculator, format_currency_full
from src.core.budget_import import import_openair_csv
from src.core.exports import Exporter


def find_data_dir() -> Path:
    """Find the data directory"""
    candidates = [
        Path('project_viewer/data'),
        Path('data'),
        Path('.')
    ]
    for candidate in candidates:
        if candidate.exists():
            raid_files = list(candidate.glob('RAID-Log-*.yaml')) + list(candidate.glob('BRAID-Log-*.yaml'))
            if raid_files:
                return candidate
    return Path('.')


def find_raid_file(data_dir: Path, specified: Optional[str] = None) -> Optional[Path]:
    """Find the RAID log file"""
    if specified:
        return Path(specified)

    files = list(data_dir.glob('RAID-Log-*.yaml')) + list(data_dir.glob('BRAID-Log-*.yaml'))
    return files[0] if files else None


def find_budget_file(data_dir: Path, specified: Optional[str] = None) -> Optional[Path]:
    """Find the Budget file"""
    if specified:
        return Path(specified)

    files = list(data_dir.glob('Budget-*.yaml'))
    return files[0] if files else None


def cmd_update(args):
    """Update indicators for all items"""
    data_dir = find_data_dir()
    raid_file = find_raid_file(data_dir, args.file)

    if not raid_file or not raid_file.exists():
        print("Error: No RAID log file found")
        return 1

    store = YamlStore(data_dir)
    project_data = store.load_raid_log(raid_file)

    today = date.today()
    counts = update_all_indicators(project_data.items, today)

    # Update metadata
    project_data.metadata.indicators_updated = today
    project_data.metadata.last_updated = today

    # Save back
    store.save_raid_log(raid_file, project_data)

    # Output summary
    print(f"# RAID Log Indicators Updated\n")
    print(f"Updated: {today.isoformat()}")
    print(f"File: {raid_file}\n")
    print("## Summary\n")
    print("| Indicator | Count |")
    print("|-----------|-------|")

    for indicator in INDICATOR_ORDER:
        if indicator in counts:
            print(f"| {indicator} | {counts[indicator]} |")

    if "No Indicator" in counts:
        print(f"| No Indicator | {counts['No Indicator']} |")

    print(f"\nTotal items updated: {len(project_data.items)}")
    return 0


def cmd_export(args):
    """Export items to various formats"""
    data_dir = find_data_dir()
    raid_file = find_raid_file(data_dir, args.file)

    if not raid_file or not raid_file.exists():
        print("Error: No RAID log file found")
        return 1

    store = YamlStore(data_dir)
    project_data = store.load_raid_log(raid_file)

    # Load budget if available
    budget = None
    budget_file = find_budget_file(data_dir)
    if budget_file and budget_file.exists():
        budget_data = store.load_budget(budget_file)
        calc = BudgetCalculator(budget_data)
        budget = calc.calculate()

    exporter = Exporter(project_data, budget)

    # Determine which items to export
    items = project_data.items
    if args.filter == 'active':
        items = [i for i in items if i.is_open and not i.draft]
    elif args.filter == 'critical':
        items = [i for i in items if i.is_critical]
    elif args.filter == 'open':
        items = [i for i in items if i.is_open]

    # Generate output
    if args.format == 'csv':
        output = exporter.to_csv(items)
    elif args.format == 'md' or args.format == 'markdown':
        if args.filter == 'active':
            output = exporter.to_markdown_active()
        else:
            output = exporter.to_markdown_table(items)
    else:
        output = exporter.to_markdown_table(items)

    # Output or save
    if args.output:
        output_path = Path(args.output)
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"Exported to: {output_path}")
    else:
        print(output)

    return 0


def cmd_summary(args):
    """Show project summary"""
    data_dir = find_data_dir()
    raid_file = find_raid_file(data_dir, args.file)

    if not raid_file or not raid_file.exists():
        print("Error: No RAID log file found")
        return 1

    store = YamlStore(data_dir)
    project_data = store.load_raid_log(raid_file)

    # Load budget if available
    budget = None
    budget_file = find_budget_file(data_dir)
    if budget_file and budget_file.exists():
        budget_data = store.load_budget(budget_file)
        calc = BudgetCalculator(budget_data)
        budget = calc.calculate()

    exporter = Exporter(project_data, budget)
    print(exporter.to_markdown_summary())
    return 0


def cmd_list(args):
    """List items with optional filtering"""
    data_dir = find_data_dir()
    raid_file = find_raid_file(data_dir, args.file)

    if not raid_file or not raid_file.exists():
        print("Error: No RAID log file found")
        return 1

    store = YamlStore(data_dir)
    project_data = store.load_raid_log(raid_file)

    items = project_data.items

    # Apply filters
    if args.open:
        items = [i for i in items if i.is_open]
    if args.type:
        items = [i for i in items if i.type == args.type]
    if args.assigned:
        items = [i for i in items if i.assigned_to == args.assigned]
    if args.workstream:
        items = [i for i in items if i.workstream == args.workstream]

    exporter = Exporter(project_data)
    print(exporter.to_markdown_table(items))
    print(f"\n{len(items)} items")
    return 0


def cmd_budget(args):
    """Show budget summary"""
    data_dir = find_data_dir()
    budget_file = find_budget_file(data_dir, args.file)

    if not budget_file or not budget_file.exists():
        print("Error: No Budget file found")
        return 1

    store = YamlStore(data_dir)
    budget_data = store.load_budget(budget_file)
    calc = BudgetCalculator(budget_data)
    budget = calc.calculate()

    m = budget.metrics

    print(f"# Budget Summary\n")
    print(f"**Project:** {budget_data.metadata.project_name}")
    print(f"**Client:** {budget_data.metadata.client}")
    print(f"**Data through:** {m.updates_thru}\n")

    print("## Financials\n")
    print(f"| Metric | Value |")
    print(f"|--------|-------|")
    print(f"| Budget Total | {format_currency_full(m.budget_total)} |")
    print(f"| Burn to Date | {format_currency_full(m.burn_to_date)} ({m.burn_pct}%) |")
    print(f"| Weekly Average | {format_currency_full(m.wkly_avg_burn)} |")
    print(f"| Projected Remaining | {format_currency_full(m.remaining_burn)} |")
    print(f"| Est. Total Burn | {format_currency_full(m.est_total_burn)} |")
    print(f"| Budget Remaining | {format_currency_full(m.budget_remaining)} |")
    print(f"| Status | {m.budget_status_icon} |")

    print("\n## Timeline\n")
    print(f"| Metric | Value |")
    print(f"|--------|-------|")
    print(f"| Project Start | {m.proj_start} |")
    print(f"| Project End | {m.proj_end} |")
    print(f"| Weeks Total | {m.weeks_total} |")
    print(f"| Weeks Completed | {m.weeks_completed} |")
    print(f"| Weeks Remaining | {m.weeks_remaining} |")

    print("\n## Resource Burn\n")
    print("| Resource | Hours | Cost |")
    print("|----------|-------|------|")
    for rb in budget.resource_burn[:10]:
        print(f"| {rb.resource} | {rb.hours} | {format_currency_full(rb.cost)} |")

    return 0


def cmd_budget_import(args):
    """Import timesheet data from OpenAir CSV"""
    csv_path = Path(args.csv)

    if not csv_path.exists():
        print(f"Error: CSV file not found: {csv_path}")
        return 1

    data_dir = find_data_dir()
    budget_file = find_budget_file(data_dir, args.file)

    if not budget_file or not budget_file.exists():
        print("Error: No Budget file found")
        return 1

    store = YamlStore(data_dir)
    budget_data = store.load_budget(budget_file)

    print(f"# Budget Import\n")
    print(f"**CSV:** {csv_path.name}")
    print(f"**Budget File:** {budget_file.name}\n")

    # Show current rate card
    print("## Rate Card\n")
    print("| Resource | Rate | Geography |")
    print("|----------|------|-----------|")
    for rc in budget_data.rate_card:
        print(f"| {rc.name} | ${rc.rate:.2f} | {rc.geography} |")
    print()

    # Do the import
    result = import_openair_csv(csv_path, budget_data)

    if not result.success:
        print(f"**Import Failed:** {result.message}")
        if result.resources_missing_rate:
            print(f"\n**Resources missing from rate card:**")
            for r in result.resources_missing_rate:
                print(f"  - {r}")
        return 1

    # Save the updated budget data
    if not args.dry_run:
        store.save_budget(budget_file, budget_data)

    # Show results
    print("## Import Results\n")
    print(f"| Metric | Value |")
    print(f"|--------|-------|")
    print(f"| Entries Imported | {result.entries_imported} |")
    print(f"| Zero-hour Entries Skipped | {result.entries_skipped} |")
    print(f"| Weeks with Data | {result.weeks_with_data} |")
    print(f"| Total Hours | {result.total_hours:.1f} |")
    print(f"| Total Cost | {format_currency_full(result.total_cost)} |")

    print(f"\n**Resources:** {', '.join(result.resources_found)}")

    if result.resources_missing_rate:
        print(f"\n**Warning - Resources missing from rate card (skipped):**")
        for r in result.resources_missing_rate:
            print(f"  - {r}")

    if args.dry_run:
        print(f"\n**DRY RUN** - No changes saved")
    else:
        print(f"\n**Saved** to {budget_file.name}")

    return 0


def main():
    parser = argparse.ArgumentParser(
        description='RAID Manager CLI - Manage RAID logs from the command line',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    subparsers = parser.add_subparsers(dest='command', help='Available commands')

    # Update command
    update_parser = subparsers.add_parser('update', help='Update indicators for all items')
    update_parser.add_argument('--file', '-f', help='RAID log file path')

    # Export command
    export_parser = subparsers.add_parser('export', help='Export items to file')
    export_parser.add_argument('--format', choices=['md', 'markdown', 'csv'], default='md',
                               help='Output format (default: md)')
    export_parser.add_argument('--filter', choices=['all', 'active', 'critical', 'open'],
                               default='all', help='Filter items')
    export_parser.add_argument('--output', '-o', help='Output file path')
    export_parser.add_argument('--file', '-f', help='RAID log file path')

    # Summary command
    summary_parser = subparsers.add_parser('summary', help='Show project summary')
    summary_parser.add_argument('--file', '-f', help='RAID log file path')

    # List command
    list_parser = subparsers.add_parser('list', help='List items')
    list_parser.add_argument('--open', action='store_true', help='Show only open items')
    list_parser.add_argument('--type', help='Filter by item type')
    list_parser.add_argument('--assigned', help='Filter by assignee')
    list_parser.add_argument('--workstream', help='Filter by workstream')
    list_parser.add_argument('--file', '-f', help='RAID log file path')

    # Budget command
    budget_parser = subparsers.add_parser('budget', help='Show budget summary')
    budget_parser.add_argument('--file', '-f', help='Budget file path')

    # Budget import command
    import_parser = subparsers.add_parser('budget-import', help='Import timesheet from OpenAir CSV')
    import_parser.add_argument('csv', help='Path to OpenAir CSV export file')
    import_parser.add_argument('--file', '-f', help='Budget YAML file path')
    import_parser.add_argument('--dry-run', action='store_true', help='Show what would be imported without saving')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return 1

    commands = {
        'update': cmd_update,
        'export': cmd_export,
        'summary': cmd_summary,
        'list': cmd_list,
        'budget': cmd_budget,
        'budget-import': cmd_budget_import,
    }

    return commands[args.command](args)


if __name__ == '__main__':
    sys.exit(main())
