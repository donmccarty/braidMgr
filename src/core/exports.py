"""
Export functionality for RAID Manager.
Generates reports in various formats (Markdown, CSV).
"""

import csv
from datetime import date
from pathlib import Path
from typing import Optional
from io import StringIO

from .models import Item, ProjectData
from .indicators import INDICATOR_ORDER, get_indicator_config
from .budget import CalculatedBudget, format_currency, format_currency_full


class Exporter:
    """Exports RAID data to various formats"""

    def __init__(self, project_data: ProjectData, budget: Optional[CalculatedBudget] = None):
        self.data = project_data
        self.budget = budget

    # -------------------------------------------------------------------------
    # Markdown Exports
    # -------------------------------------------------------------------------

    def to_markdown_active(self) -> str:
        """Generate markdown report of active items (for Teams posting)"""
        lines = []
        today = date.today()

        lines.append(f"# {self.data.metadata.project_name} - Active Items")
        lines.append(f"*Generated: {today.strftime('%Y-%m-%d')}*\n")

        # Group by severity
        critical = []
        warning = []
        active = []

        for item in self.data.items:
            if item.is_complete or item.draft:
                continue
            config = get_indicator_config(item.indicator)
            if config:
                if config.severity == 'critical':
                    critical.append(item)
                elif config.severity == 'warning':
                    warning.append(item)
                elif config.severity in ('active', 'upcoming'):
                    active.append(item)

        if critical:
            lines.append("## 🔴 Critical\n")
            for item in critical:
                lines.append(self._format_item_md(item))

        if warning:
            lines.append("\n## 🟡 Warning\n")
            for item in warning:
                lines.append(self._format_item_md(item))

        if active:
            lines.append("\n## 🔵 Active\n")
            for item in active:
                lines.append(self._format_item_md(item))

        return '\n'.join(lines)

    def to_markdown_summary(self) -> str:
        """Generate markdown summary report"""
        lines = []
        today = date.today()

        lines.append(f"# {self.data.metadata.project_name} - Summary")
        lines.append(f"*Generated: {today.strftime('%Y-%m-%d')}*\n")

        # Count by indicator
        counts: dict[str, int] = {}
        for item in self.data.items:
            key = item.indicator or "No Indicator"
            counts[key] = counts.get(key, 0) + 1

        lines.append("## Status Summary\n")
        lines.append("| Indicator | Count |")
        lines.append("|-----------|-------|")

        for indicator in INDICATOR_ORDER:
            if indicator in counts:
                lines.append(f"| {indicator} | {counts[indicator]} |")

        if "No Indicator" in counts:
            lines.append(f"| No Indicator | {counts['No Indicator']} |")

        lines.append(f"\n**Total Items:** {len(self.data.items)}")

        # Budget summary if available
        if self.budget:
            m = self.budget.metrics
            lines.append("\n## Budget Summary\n")
            lines.append(f"- **Budget Total:** {format_currency_full(m.budget_total)}")
            lines.append(f"- **Burn to Date:** {format_currency_full(m.burn_to_date)} ({m.burn_pct}%)")
            lines.append(f"- **Weekly Average:** {format_currency_full(m.wkly_avg_burn)}")
            lines.append(f"- **Projected Remaining:** {format_currency_full(m.remaining_burn)}")
            lines.append(f"- **Budget Remaining:** {format_currency_full(m.budget_remaining)}")
            lines.append(f"- **Status:** {m.budget_status_icon}")

        return '\n'.join(lines)

    def to_markdown_table(self, items: Optional[list[Item]] = None) -> str:
        """Generate markdown table of items"""
        if items is None:
            items = self.data.items

        lines = []
        lines.append("| # | Type | Title | Assigned | Status | % |")
        lines.append("|---|------|-------|----------|--------|---|")

        for item in items:
            indicator = item.indicator or "-"
            lines.append(
                f"| {item.item_num} | {item.type} | {item.title[:50]} | "
                f"{item.assigned_to or '-'} | {indicator} | {item.percent_complete}% |"
            )

        return '\n'.join(lines)

    def _format_item_md(self, item: Item) -> str:
        """Format a single item for markdown"""
        parts = [f"- **#{item.item_num}** {item.title}"]

        details = []
        if item.assigned_to:
            details.append(f"Assigned: {item.assigned_to}")
        if item.finish:
            details.append(f"Due: {item.finish.strftime('%m/%d')}")
        if item.percent_complete:
            details.append(f"{item.percent_complete}%")

        if details:
            parts.append(f"  - {' | '.join(details)}")

        return '\n'.join(parts)

    # -------------------------------------------------------------------------
    # CSV Exports
    # -------------------------------------------------------------------------

    def to_csv(self, items: Optional[list[Item]] = None) -> str:
        """Export items to CSV string"""
        if items is None:
            items = self.data.items

        output = StringIO()
        writer = csv.writer(output)

        # Header
        writer.writerow([
            'Item #', 'Type', 'Workstream', 'Title', 'Description',
            'Assigned To', 'Start', 'Finish', 'Deadline',
            '% Complete', 'Indicator', 'Priority', 'Draft', 'Client Visible'
        ])

        # Data rows
        for item in items:
            writer.writerow([
                item.item_num,
                item.type,
                item.workstream or '',
                item.title,
                item.description or '',
                item.assigned_to or '',
                item.start.strftime('%Y-%m-%d') if item.start else '',
                item.finish.strftime('%Y-%m-%d') if item.finish else '',
                item.deadline.strftime('%Y-%m-%d') if item.deadline else '',
                item.percent_complete,
                item.indicator or '',
                item.priority or '',
                'Yes' if item.draft else 'No',
                'Yes' if item.client_visible else 'No'
            ])

        return output.getvalue()

    def save_csv(self, filepath: Path, items: Optional[list[Item]] = None) -> None:
        """Save items to CSV file"""
        content = self.to_csv(items)
        with open(filepath, 'w', encoding='utf-8', newline='') as f:
            f.write(content)

    def save_markdown(self, filepath: Path, content: str) -> None:
        """Save markdown content to file"""
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)

    # -------------------------------------------------------------------------
    # Filtered Exports
    # -------------------------------------------------------------------------

    def get_open_items(self) -> list[Item]:
        """Get all non-completed items"""
        return [i for i in self.data.items if i.is_open]

    def get_critical_items(self) -> list[Item]:
        """Get items with critical status"""
        return [i for i in self.data.items if i.is_critical]

    def get_items_by_assignee(self, assignee: str) -> list[Item]:
        """Get items for a specific assignee"""
        return [i for i in self.data.items if i.assigned_to == assignee]

    def get_items_by_type(self, item_type: str) -> list[Item]:
        """Get items of a specific type"""
        return [i for i in self.data.items if i.type == item_type]

    def get_items_by_workstream(self, workstream: str) -> list[Item]:
        """Get items in a specific workstream"""
        return [i for i in self.data.items if i.workstream == workstream]
