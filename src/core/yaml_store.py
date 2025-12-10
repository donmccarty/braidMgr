"""
YAML persistence layer for RAID Manager.
Handles loading and saving RAID logs and Budget files.
"""

import yaml
from pathlib import Path
from datetime import date, datetime
from typing import Optional, Any

from .models import (
    Item, ProjectData, ProjectMetadata,
    BudgetData, BudgetMetadata, RateCardEntry, TimesheetEntry, BudgetLedgerEntry
)


def _parse_date(value: Any) -> Optional[date]:
    """Parse a date from various formats"""
    if value is None:
        return None
    if isinstance(value, date):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, str):
        try:
            return datetime.strptime(value, '%Y-%m-%d').date()
        except ValueError:
            return None
    return None


def _format_date(d: Optional[date]) -> Optional[str]:
    """Format date as YAML string"""
    if d is None:
        return None
    return d.strftime('%Y-%m-%d')


class YamlStore:
    """Handles YAML file operations for RAID and Budget data"""

    def __init__(self, data_dir: Optional[Path] = None):
        self.data_dir = data_dir or Path('.')

    # -------------------------------------------------------------------------
    # RAID Log Operations
    # -------------------------------------------------------------------------

    def load_raid_log(self, filepath: Path) -> ProjectData:
        """Load a RAID log from YAML file"""
        with open(filepath, 'r', encoding='utf-8') as f:
            raw = yaml.safe_load(f)

        # Parse metadata
        meta_raw = raw.get('metadata', {})
        metadata = ProjectMetadata(
            project_name=meta_raw.get('project_name', 'Unknown Project'),
            client_name=meta_raw.get('client_name'),
            next_item_num=meta_raw.get('next_item_num', 1),
            last_updated=_parse_date(meta_raw.get('last_updated')),
            project_start=_parse_date(meta_raw.get('project_start')),
            project_end=_parse_date(meta_raw.get('project_end')),
            indicators_updated=_parse_date(meta_raw.get('indicators_updated')),
            workstreams=meta_raw.get('workstreams', [])
        )

        # Parse items
        items = []
        for item_raw in raw.get('items', []):
            # Handle dep_item_num which might be strings or ints
            deps = item_raw.get('dep_item_num', [])
            if deps is None:
                deps = []
            deps = [int(d) if isinstance(d, str) else d for d in deps]

            item = Item(
                item_num=item_raw.get('item_num', 0),
                type=item_raw.get('type', 'Plan Item'),
                title=item_raw.get('title', ''),
                workstream=item_raw.get('workstream'),
                description=item_raw.get('description'),
                assigned_to=item_raw.get('assigned_to'),
                dep_item_num=deps,
                start=_parse_date(item_raw.get('start')),
                finish=_parse_date(item_raw.get('finish')),
                duration=item_raw.get('duration'),
                deadline=_parse_date(item_raw.get('deadline')),
                draft=item_raw.get('draft', False),
                client_visible=item_raw.get('client_visible', True),
                percent_complete=item_raw.get('percent_complete', 0),
                rpt_out=item_raw.get('rpt_out', []) or [],
                created_date=_parse_date(item_raw.get('created_date')),
                last_updated=_parse_date(item_raw.get('last_updated')),
                notes=item_raw.get('notes'),
                indicator=item_raw.get('indicator'),
                priority=item_raw.get('priority'),
                budget_amount=item_raw.get('budget_amount')
            )
            items.append(item)

        return ProjectData(metadata=metadata, items=items)

    def save_raid_log(self, filepath: Path, data: ProjectData) -> None:
        """Save a RAID log to YAML file"""
        # Build metadata dict
        meta_dict = {
            'project_name': data.metadata.project_name,
            'client_name': data.metadata.client_name,
            'next_item_num': data.metadata.next_item_num,
            'last_updated': _format_date(data.metadata.last_updated),
            'project_start': _format_date(data.metadata.project_start),
            'project_end': _format_date(data.metadata.project_end),
            'indicators_updated': _format_date(data.metadata.indicators_updated),
            'workstreams': data.metadata.workstreams
        }

        # Build items list
        items_list = []
        for item in data.items:
            item_dict = {
                'item_num': item.item_num,
                'type': item.type,
                'workstream': item.workstream,
                'title': item.title,
                'description': item.description,
                'assigned_to': item.assigned_to,
                'dep_item_num': [str(d) for d in item.dep_item_num] if item.dep_item_num else [],
                'start': _format_date(item.start),
                'finish': _format_date(item.finish),
                'deadline': _format_date(item.deadline),
                'draft': item.draft,
                'client_visible': item.client_visible,
                'percent_complete': item.percent_complete,
                'rpt_out': item.rpt_out or [],
                'created_date': _format_date(item.created_date),
                'last_updated': _format_date(item.last_updated),
                'notes': item.notes,
                'indicator': item.indicator,
            }
            # Add optional fields if present
            if item.duration is not None:
                item_dict['duration'] = item.duration
            if item.priority is not None:
                item_dict['priority'] = item.priority
            if item.budget_amount is not None:
                item_dict['budget_amount'] = item.budget_amount

            items_list.append(item_dict)

        output = {
            'metadata': meta_dict,
            'items': items_list
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(output, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    # -------------------------------------------------------------------------
    # Budget Operations
    # -------------------------------------------------------------------------

    def load_budget(self, filepath: Path) -> BudgetData:
        """Load a Budget file from YAML"""
        with open(filepath, 'r', encoding='utf-8') as f:
            raw = yaml.safe_load(f)

        # Parse metadata
        meta_raw = raw.get('metadata', {})
        metadata = BudgetMetadata(
            project_name=meta_raw.get('project_name', 'Unknown Project'),
            client=meta_raw.get('client'),
            associated_raid_log=meta_raw.get('associated_raid_log'),
            created=_parse_date(meta_raw.get('created')),
            last_updated=_parse_date(meta_raw.get('last_updated')),
            data_source=meta_raw.get('data_source')
        )

        # Parse rate card
        rate_card = []
        for rc_raw in raw.get('rate_card', []):
            rate_card.append(RateCardEntry(
                name=rc_raw.get('name', ''),
                geography=rc_raw.get('geography', ''),
                rate=float(rc_raw.get('rate', 0)),
                roll_off_date=_parse_date(rc_raw.get('roll_off_date'))
            ))

        # Parse budget ledger
        budget_ledger = []
        for bl_raw in raw.get('budget_ledger', []):
            budget_ledger.append(BudgetLedgerEntry(
                amount=float(bl_raw.get('amount', 0)),
                date=_parse_date(bl_raw.get('date')) or date.today(),
                note=bl_raw.get('note')
            ))

        # Parse timesheet data
        timesheet_data = []
        for ts_raw in raw.get('timesheet_data', []):
            timesheet_data.append(TimesheetEntry(
                week_ending=_parse_date(ts_raw.get('week_ending')) or date.today(),
                resource=ts_raw.get('resource', ''),
                hours=float(ts_raw.get('hours', 0)),
                rate=float(ts_raw.get('rate', 0)),
                cost=float(ts_raw.get('cost', 0)),
                complete_week=ts_raw.get('complete_week', True)
            ))

        return BudgetData(
            metadata=metadata,
            rate_card=rate_card,
            budget_ledger=budget_ledger,
            timesheet_data=timesheet_data
        )

    def save_budget(self, filepath: Path, data: BudgetData) -> None:
        """Save a Budget file to YAML"""
        meta_dict = {
            'project_name': data.metadata.project_name,
            'client': data.metadata.client,
            'associated_raid_log': data.metadata.associated_raid_log,
            'created': _format_date(data.metadata.created),
            'last_updated': _format_date(data.metadata.last_updated),
            'data_source': data.metadata.data_source
        }

        rate_card_list = []
        for rc in data.rate_card:
            rate_card_list.append({
                'name': rc.name,
                'geography': rc.geography,
                'rate': rc.rate,
                'roll_off_date': _format_date(rc.roll_off_date)
            })

        budget_ledger_list = []
        for bl in data.budget_ledger:
            budget_ledger_list.append({
                'amount': bl.amount,
                'date': _format_date(bl.date),
                'note': bl.note
            })

        timesheet_list = []
        for ts in data.timesheet_data:
            timesheet_list.append({
                'week_ending': _format_date(ts.week_ending),
                'resource': ts.resource,
                'hours': ts.hours,
                'rate': ts.rate,
                'cost': ts.cost,
                'complete_week': ts.complete_week
            })

        output = {
            'metadata': meta_dict,
            'rate_card': rate_card_list,
            'budget_ledger': budget_ledger_list,
            'timesheet_data': timesheet_list
        }

        with open(filepath, 'w', encoding='utf-8') as f:
            yaml.dump(output, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    # -------------------------------------------------------------------------
    # Discovery
    # -------------------------------------------------------------------------

    def find_raid_logs(self) -> list[Path]:
        """Find all RAID/BRAID log files in data directory"""
        patterns = ['RAID-Log-*.yaml', 'BRAID-Log-*.yaml']
        files = []
        for pattern in patterns:
            files.extend(self.data_dir.glob(pattern))
        return sorted(files)

    def find_budget_files(self) -> list[Path]:
        """Find all Budget files in data directory"""
        return sorted(self.data_dir.glob('Budget-*.yaml'))
