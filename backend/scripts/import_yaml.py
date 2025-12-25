#!/usr/bin/env python3
"""
YAML Import Script for braidMgr v1 to v2 Migration.

One-time migration script to import existing RAID-Log and Budget YAML files
into the v2 PostgreSQL database.

Usage:
    # Import a RAID log file:
    python scripts/import_yaml.py raid /path/to/RAID-Log-ProjectName.yaml

    # Import a Budget file:
    python scripts/import_yaml.py budget /path/to/Budget-ProjectName.yaml

    # Import with custom organization name:
    python scripts/import_yaml.py raid /path/to/file.yaml --org "My Company"

    # Dry run (validate without importing):
    python scripts/import_yaml.py raid /path/to/file.yaml --dry-run

Requirements:
    - Database must be running and accessible
    - config.yaml must be configured with database connection
    - Run from backend directory with virtual environment activated

Notes:
    - Creates a default organization if none exists
    - Creates a migration user for imported data
    - Parses dated notes from v1 format (e.g., "2024-12-15: Note content")
    - Generates UUIDs for all imported entities
    - Reports validation errors without stopping import
"""

import argparse
import asyncio
import re
import sys
from dataclasses import dataclass, field
from datetime import date, datetime
from decimal import Decimal
from pathlib import Path
from typing import Optional
from uuid import UUID, uuid4

import yaml

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_config
from src.domain.core import ItemType, Indicator
from src.domain.auth import ProjectRole
from src.services import services
from src.services.project_service import ProjectService
from src.services.item_service import ItemService
from src.services.workstream_service import WorkstreamService
from src.repositories.user_repository import UserRepository
from src.repositories.user_project_role_repository import UserProjectRoleRepository
from src.utils.logging import setup_logging, get_logger


# =============================================================================
# DATA CLASSES FOR PARSED YAML
# =============================================================================


@dataclass
class ParsedNote:
    """A parsed note with date and content."""
    note_date: date
    content: str


@dataclass
class ParsedItem:
    """A parsed item from v1 YAML."""
    item_num: int
    type: str
    title: str
    description: Optional[str] = None
    workstream: Optional[str] = None
    assigned_to: Optional[str] = None
    start_date: Optional[date] = None
    finish_date: Optional[date] = None
    duration_days: Optional[int] = None
    deadline: Optional[date] = None
    draft: bool = False
    client_visible: bool = True
    percent_complete: int = 0
    indicator: Optional[str] = None
    priority: Optional[str] = None
    rpt_out: Optional[list[str]] = None
    budget_amount: Optional[Decimal] = None
    notes: list[ParsedNote] = field(default_factory=list)
    dep_item_nums: list[int] = field(default_factory=list)


@dataclass
class ParsedProject:
    """A parsed project from v1 YAML."""
    name: str
    client_name: Optional[str] = None
    project_start: Optional[date] = None
    project_end: Optional[date] = None
    next_item_num: int = 1
    workstreams: list[str] = field(default_factory=list)
    items: list[ParsedItem] = field(default_factory=list)


@dataclass
class ImportResult:
    """Result of an import operation."""
    success: bool
    project_id: Optional[UUID] = None
    items_imported: int = 0
    items_failed: int = 0
    notes_imported: int = 0
    workstreams_created: int = 0
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)


# =============================================================================
# YAML PARSING
# =============================================================================


def parse_date(value: any) -> Optional[date]:
    """
    Parse a date from various formats.

    Handles:
    - date objects (passthrough)
    - datetime objects (extract date)
    - strings in formats: YYYY-MM-DD, MM/DD/YYYY, etc.
    - None/empty values

    Args:
        value: The value to parse.

    Returns:
        Parsed date or None if unparseable.
    """
    if value is None:
        return None

    if isinstance(value, date):
        return value

    if isinstance(value, datetime):
        return value.date()

    if isinstance(value, str):
        value = value.strip()
        if not value:
            return None

        # Try various formats
        formats = [
            "%Y-%m-%d",      # 2024-12-15
            "%m/%d/%Y",      # 12/15/2024
            "%d/%m/%Y",      # 15/12/2024
            "%Y/%m/%d",      # 2024/12/15
            "%B %d, %Y",     # December 15, 2024
            "%b %d, %Y",     # Dec 15, 2024
        ]

        for fmt in formats:
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                continue

        return None

    return None


def parse_notes(notes_value: any) -> list[ParsedNote]:
    """
    Parse notes from v1 format.

    v1 notes are typically multi-line strings with date prefixes:
        2024-12-15: This is a note from December 15
        2024-12-10: Earlier note content

    Args:
        notes_value: The notes field value (string or list).

    Returns:
        List of ParsedNote objects.
    """
    if not notes_value:
        return []

    # Handle list of notes (some v1 files use this)
    if isinstance(notes_value, list):
        result = []
        for note in notes_value:
            if isinstance(note, dict):
                # Format: {date: "2024-12-15", content: "..."}
                note_date = parse_date(note.get("date"))
                content = note.get("content", "").strip()
                if note_date and content:
                    result.append(ParsedNote(note_date=note_date, content=content))
            elif isinstance(note, str):
                # Try to parse as "date: content"
                parsed = _parse_single_note(note)
                if parsed:
                    result.append(parsed)
        return result

    # Handle multi-line string
    if isinstance(notes_value, str):
        result = []
        lines = notes_value.strip().split("\n")

        current_note = None
        for line in lines:
            parsed = _parse_single_note(line)
            if parsed:
                if current_note:
                    result.append(current_note)
                current_note = parsed
            elif current_note and line.strip():
                # Continuation of previous note
                current_note.content += "\n" + line.strip()

        if current_note:
            result.append(current_note)

        return result

    return []


def _parse_single_note(line: str) -> Optional[ParsedNote]:
    """
    Parse a single note line with date prefix.

    Format: "2024-12-15: Note content here"

    Args:
        line: A single note line.

    Returns:
        ParsedNote if successfully parsed, None otherwise.
    """
    if not line:
        return None

    line = line.strip()
    if not line:
        return None

    # Match date prefix pattern: YYYY-MM-DD: or MM/DD/YYYY:
    match = re.match(r'^(\d{4}-\d{2}-\d{2}|\d{1,2}/\d{1,2}/\d{4}):\s*(.+)$', line)
    if match:
        date_str = match.group(1)
        content = match.group(2).strip()
        note_date = parse_date(date_str)
        if note_date and content:
            return ParsedNote(note_date=note_date, content=content)

    return None


def map_item_type(v1_type: str) -> Optional[ItemType]:
    """
    Map v1 item type string to v2 ItemType enum.

    Args:
        v1_type: The v1 type string.

    Returns:
        ItemType enum value or None if unknown.
    """
    # Normalize: lowercase, remove spaces/underscores
    normalized = v1_type.lower().replace(" ", "").replace("_", "").replace("-", "")

    mapping = {
        "budget": ItemType.BUDGET,
        "risk": ItemType.RISK,
        "actionitem": ItemType.ACTION_ITEM,
        "action": ItemType.ACTION_ITEM,
        "issue": ItemType.ISSUE,
        "decision": ItemType.DECISION,
        "deliverable": ItemType.DELIVERABLE,
        "planitem": ItemType.PLAN_ITEM,
        "plan": ItemType.PLAN_ITEM,
        "milestone": ItemType.PLAN_ITEM,
    }

    return mapping.get(normalized)


def parse_raid_yaml(file_path: Path) -> tuple[Optional[ParsedProject], list[str]]:
    """
    Parse a RAID-Log YAML file.

    Args:
        file_path: Path to the YAML file.

    Returns:
        Tuple of (ParsedProject or None, list of error messages).
    """
    errors = []

    try:
        with open(file_path, "r") as f:
            data = yaml.safe_load(f)
    except yaml.YAMLError as e:
        return None, [f"YAML parse error: {e}"]
    except FileNotFoundError:
        return None, [f"File not found: {file_path}"]
    except Exception as e:
        return None, [f"Error reading file: {e}"]

    if not data:
        return None, ["Empty YAML file"]

    # Parse metadata
    metadata = data.get("metadata", data)  # Some files have metadata at root

    project = ParsedProject(
        name=metadata.get("project_name", file_path.stem),
        client_name=metadata.get("client_name") or metadata.get("client"),
        project_start=parse_date(metadata.get("project_start")),
        project_end=parse_date(metadata.get("project_end")),
        next_item_num=metadata.get("next_item_num", 1),
        workstreams=metadata.get("workstreams", []),
    )

    # Parse items
    items_data = data.get("items", [])
    for i, item_data in enumerate(items_data):
        try:
            # Get item type
            v1_type = item_data.get("type", "")
            item_type = map_item_type(v1_type)
            if not item_type:
                errors.append(f"Item {i+1}: Unknown type '{v1_type}'")
                continue

            # Get title (required)
            title = item_data.get("title", "").strip()
            if not title:
                errors.append(f"Item {i+1}: Missing title")
                continue

            # Parse percent complete
            pct = item_data.get("percent_complete", 0)
            if isinstance(pct, str):
                pct = int(pct.replace("%", "").strip() or 0)
            pct = max(0, min(100, int(pct)))

            # Parse rpt_out
            rpt_out = item_data.get("rpt_out")
            if isinstance(rpt_out, str):
                rpt_out = [x.strip() for x in rpt_out.split(",") if x.strip()]

            # Parse dependencies
            deps = item_data.get("dep_item_num", [])
            if isinstance(deps, int):
                deps = [deps]
            elif isinstance(deps, str):
                deps = [int(x.strip()) for x in deps.split(",") if x.strip().isdigit()]

            # Create parsed item
            parsed_item = ParsedItem(
                item_num=item_data.get("item_num", i + 1),
                type=item_type.value,
                title=title,
                description=item_data.get("description"),
                workstream=item_data.get("workstream"),
                assigned_to=item_data.get("assigned_to"),
                start_date=parse_date(item_data.get("start") or item_data.get("start_date")),
                finish_date=parse_date(item_data.get("finish") or item_data.get("finish_date")),
                duration_days=item_data.get("duration") or item_data.get("duration_days"),
                deadline=parse_date(item_data.get("deadline")),
                draft=bool(item_data.get("draft", False)),
                client_visible=bool(item_data.get("client_visible", True)),
                percent_complete=pct,
                indicator=item_data.get("indicator"),
                priority=item_data.get("priority"),
                rpt_out=rpt_out,
                budget_amount=Decimal(str(item_data["budget_amount"])) if item_data.get("budget_amount") else None,
                notes=parse_notes(item_data.get("notes")),
                dep_item_nums=deps,
            )

            project.items.append(parsed_item)

        except Exception as e:
            errors.append(f"Item {i+1}: Parse error - {e}")

    return project, errors


# =============================================================================
# DATABASE IMPORT
# =============================================================================


async def ensure_migration_user(user_repo: UserRepository) -> UUID:
    """
    Ensure a migration user exists for imported data.

    Creates a user with email 'migration@braidmgr.local' if not exists.

    Args:
        user_repo: User repository.

    Returns:
        User UUID.
    """
    email = "migration@braidmgr.local"

    user = await user_repo.get_by_email(email)
    if user:
        return user.id

    # Create migration user
    user = await user_repo.create(
        email=email,
        name="Migration Import",
        password_hash=None,  # No password - not a real login
    )

    return user.id


async def ensure_organization(org_name: str) -> UUID:
    """
    Ensure an organization exists for imported data.

    For MVP, we create a simple org record directly since org service
    doesn't exist yet.

    Args:
        org_name: Organization name.

    Returns:
        Organization UUID.
    """
    # Check if org exists
    row = await services.aurora.fetch_one(
        "SELECT id FROM organizations WHERE name = $1 AND deleted_at IS NULL",
        org_name,
    )

    if row:
        return row["id"]

    # Create org
    slug = org_name.lower().replace(" ", "-").replace("_", "-")
    row = await services.aurora.fetch_one(
        """
        INSERT INTO organizations (name, slug)
        VALUES ($1, $2)
        RETURNING id
        """,
        org_name,
        slug,
    )

    return row["id"]


async def import_project(
    parsed: ParsedProject,
    org_id: UUID,
    user_id: UUID,
    dry_run: bool = False,
) -> ImportResult:
    """
    Import a parsed project into the database.

    Args:
        parsed: Parsed project data.
        org_id: Organization UUID.
        user_id: User UUID for creator.
        dry_run: If True, validate but don't import.

    Returns:
        ImportResult with statistics.
    """
    result = ImportResult(success=True)
    logger = get_logger(__name__)

    # Initialize services
    project_service = ProjectService(services.aurora)
    item_service = ItemService(services.aurora)
    workstream_service = WorkstreamService(services.aurora)
    role_repo = UserProjectRoleRepository(services.aurora)

    if dry_run:
        logger.info("dry_run_mode", project=parsed.name)
        result.workstreams_created = len(parsed.workstreams)
        result.items_imported = len(parsed.items)
        return result

    # Create project with workstreams
    project_result = await project_service.create_project(
        org_id=org_id,
        name=parsed.name,
        client_name=parsed.client_name,
        project_start=parsed.project_start,
        project_end=parsed.project_end,
        workstream_names=parsed.workstreams or None,
        created_by=user_id,
    )

    if not project_result.success:
        result.success = False
        result.errors.append(f"Failed to create project: {project_result.error}")
        return result

    project = project_result.project
    result.project_id = project.id
    result.workstreams_created = len(parsed.workstreams) if parsed.workstreams else 0

    logger.info(
        "project_created",
        project_id=str(project.id),
        name=project.name,
        workstreams=result.workstreams_created,
    )

    # Build workstream name -> ID mapping
    workstreams = await workstream_service.list_workstreams(project.id)
    ws_map = {ws.name.lower(): ws.id for ws in workstreams}

    # Track item_num -> item_id mapping for dependencies
    item_num_map: dict[int, UUID] = {}

    # Import items
    for parsed_item in parsed.items:
        try:
            # Map item type
            item_type = map_item_type(parsed_item.type)
            if not item_type:
                result.errors.append(f"Item {parsed_item.item_num}: Invalid type '{parsed_item.type}'")
                result.items_failed += 1
                continue

            # Lookup workstream
            workstream_id = None
            if parsed_item.workstream:
                workstream_id = ws_map.get(parsed_item.workstream.lower())
                if not workstream_id:
                    result.warnings.append(
                        f"Item {parsed_item.item_num}: Workstream '{parsed_item.workstream}' not found"
                    )

            # Create item
            item_result = await item_service.create_item(
                project_id=project.id,
                item_type=item_type,
                title=parsed_item.title,
                description=parsed_item.description,
                workstream_id=workstream_id,
                assigned_to=parsed_item.assigned_to,
                start_date=parsed_item.start_date,
                finish_date=parsed_item.finish_date,
                duration_days=parsed_item.duration_days,
                deadline=parsed_item.deadline,
                draft=parsed_item.draft,
                client_visible=parsed_item.client_visible,
                percent_complete=parsed_item.percent_complete,
                priority=parsed_item.priority,
                rpt_out=parsed_item.rpt_out,
                budget_amount=parsed_item.budget_amount,
            )

            if not item_result.success:
                result.errors.append(
                    f"Item {parsed_item.item_num}: {item_result.error}"
                )
                result.items_failed += 1
                continue

            item = item_result.item
            item_num_map[parsed_item.item_num] = item.id
            result.items_imported += 1

            # Import notes
            for note in parsed_item.notes:
                try:
                    await services.aurora.execute(
                        """
                        INSERT INTO item_notes (item_id, note_date, content, created_by)
                        VALUES ($1, $2, $3, $4)
                        """,
                        item.id,
                        note.note_date,
                        note.content,
                        user_id,
                    )
                    result.notes_imported += 1
                except Exception as e:
                    result.warnings.append(
                        f"Item {parsed_item.item_num} note: {e}"
                    )

        except Exception as e:
            result.errors.append(f"Item {parsed_item.item_num}: {e}")
            result.items_failed += 1

    # Import dependencies (second pass after all items created)
    for parsed_item in parsed.items:
        if not parsed_item.dep_item_nums:
            continue

        item_id = item_num_map.get(parsed_item.item_num)
        if not item_id:
            continue

        for dep_num in parsed_item.dep_item_nums:
            dep_id = item_num_map.get(dep_num)
            if dep_id:
                try:
                    await services.aurora.execute(
                        """
                        INSERT INTO item_dependencies (item_id, depends_on_id)
                        VALUES ($1, $2)
                        ON CONFLICT DO NOTHING
                        """,
                        item_id,
                        dep_id,
                    )
                except Exception as e:
                    result.warnings.append(
                        f"Item {parsed_item.item_num} dependency on {dep_num}: {e}"
                    )
            else:
                result.warnings.append(
                    f"Item {parsed_item.item_num}: Dependency {dep_num} not found"
                )

    # Update next_item_num if needed
    if parsed.next_item_num > project.next_item_num:
        await services.aurora.execute(
            """
            UPDATE projects SET next_item_num = $1 WHERE id = $2
            """,
            parsed.next_item_num,
            project.id,
        )

    logger.info(
        "import_complete",
        project_id=str(project.id),
        items_imported=result.items_imported,
        items_failed=result.items_failed,
        notes_imported=result.notes_imported,
    )

    return result


# =============================================================================
# CLI
# =============================================================================


def print_result(result: ImportResult, verbose: bool = False) -> None:
    """Print import result to console."""
    if result.success:
        print(f"\n✓ Import successful")
        if result.project_id:
            print(f"  Project ID: {result.project_id}")
    else:
        print(f"\n✗ Import failed")

    print(f"\nStatistics:")
    print(f"  Workstreams created: {result.workstreams_created}")
    print(f"  Items imported: {result.items_imported}")
    print(f"  Items failed: {result.items_failed}")
    print(f"  Notes imported: {result.notes_imported}")

    if result.errors:
        print(f"\nErrors ({len(result.errors)}):")
        for error in result.errors[:10]:  # Show first 10
            print(f"  - {error}")
        if len(result.errors) > 10:
            print(f"  ... and {len(result.errors) - 10} more")

    if verbose and result.warnings:
        print(f"\nWarnings ({len(result.warnings)}):")
        for warning in result.warnings[:10]:
            print(f"  - {warning}")
        if len(result.warnings) > 10:
            print(f"  ... and {len(result.warnings) - 10} more")


async def main_async(args: argparse.Namespace) -> int:
    """Async main function."""
    logger = get_logger(__name__)

    # Initialize services
    config = get_config()
    services.initialize(config)

    try:
        file_path = Path(args.file)

        if args.command == "raid":
            print(f"Parsing RAID log: {file_path}")
            parsed, parse_errors = parse_raid_yaml(file_path)

            if parse_errors:
                print(f"\nParse errors:")
                for error in parse_errors:
                    print(f"  - {error}")

            if not parsed:
                print("\nFailed to parse file")
                return 1

            print(f"\nParsed project: {parsed.name}")
            print(f"  Client: {parsed.client_name or 'N/A'}")
            print(f"  Dates: {parsed.project_start} to {parsed.project_end}")
            print(f"  Workstreams: {len(parsed.workstreams)}")
            print(f"  Items: {len(parsed.items)}")

            # Ensure org and user exist
            org_name = args.org or "Default Organization"
            org_id = await ensure_organization(org_name)

            user_repo = UserRepository(services.aurora)
            user_id = await ensure_migration_user(user_repo)

            print(f"\nImporting to organization: {org_name}")

            # Import
            result = await import_project(
                parsed=parsed,
                org_id=org_id,
                user_id=user_id,
                dry_run=args.dry_run,
            )

            print_result(result, verbose=args.verbose)

            return 0 if result.success else 1

        elif args.command == "budget":
            print("Budget import not yet implemented")
            print("Budget data will be imported as part of a future update")
            return 1

        else:
            print(f"Unknown command: {args.command}")
            return 1

    finally:
        await services.close_all()


def main() -> int:
    """CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Import v1 YAML files into braidMgr v2 database",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/import_yaml.py raid RAID-Log-ProjectX.yaml
  python scripts/import_yaml.py raid RAID-Log-ProjectX.yaml --org "Acme Corp"
  python scripts/import_yaml.py raid RAID-Log-ProjectX.yaml --dry-run
  python scripts/import_yaml.py budget Budget-ProjectX.yaml
        """,
    )

    parser.add_argument(
        "command",
        choices=["raid", "budget"],
        help="Type of YAML file to import",
    )

    parser.add_argument(
        "file",
        help="Path to the YAML file to import",
    )

    parser.add_argument(
        "--org",
        help="Organization name (default: 'Default Organization')",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Validate without importing",
    )

    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Show warnings and detailed output",
    )

    args = parser.parse_args()

    # Setup logging
    setup_logging(environment="development", log_level="INFO")

    # Run async main
    return asyncio.run(main_async(args))


if __name__ == "__main__":
    sys.exit(main())
