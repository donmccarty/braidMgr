"""
Pytest configuration and shared fixtures for BRAID Manager tests.

# =============================================================================
# Testing Approach
# =============================================================================
#
# Unit Tests (test_*.py):
#   - Test core business logic in isolation
#   - Use pytest fixtures for test data (no external file dependencies)
#   - Tests are deterministic with fixed dates
#
# Test Coverage:
#   - test_indicators.py: Indicator calculation logic (most critical)
#   - test_models.py: Data model creation and properties
#   - test_paths.py: Platform-aware path handling
#   - test_templates.py: New project creation
#   - test_yaml_store.py: YAML persistence (save/load roundtrip)
#   - test_budget.py: Budget calculations, metrics, and status
#   - test_exports.py: Markdown and CSV export functionality
#
# Integration Tests (integration_*.py):
#   - Test with real YAML files from project_viewer/data/
#   - Not run by default pytest discovery (different naming pattern)
#   - Run manually: python tests/integration_test_core.py
#
# Running Tests:
#   cd raid_manager
#   .venv/bin/python -m pytest tests/ -v      # All unit tests
#   .venv/bin/python -m pytest tests/ -v -k "indicators"  # Specific module
#
# =============================================================================
"""

import sys
from pathlib import Path
from datetime import date, timedelta

import pytest

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.core.models import Item, ProjectData, ProjectMetadata


# =============================================================================
# Date Fixtures - Fixed dates for deterministic testing
# =============================================================================

@pytest.fixture
def today():
    """Fixed 'today' date for deterministic tests."""
    return date(2024, 12, 15)


@pytest.fixture
def two_weeks_ago(today):
    """Date 14 days before 'today'."""
    return today - timedelta(days=14)


@pytest.fixture
def one_week_ago(today):
    """Date 7 days before 'today'."""
    return today - timedelta(days=7)


@pytest.fixture
def one_week_ahead(today):
    """Date 7 days after 'today'."""
    return today + timedelta(days=7)


@pytest.fixture
def three_weeks_ahead(today):
    """Date 21 days after 'today'."""
    return today + timedelta(days=21)


# =============================================================================
# Item Factory Fixture
# =============================================================================

@pytest.fixture
def make_item():
    """Factory fixture to create test items with defaults."""
    def _make_item(
        item_num=1,
        type="Action Item",
        title="Test Item",
        percent_complete=0,
        start=None,
        finish=None,
        deadline=None,
        duration=None,
        draft=False,
        **kwargs
    ):
        return Item(
            item_num=item_num,
            type=type,
            title=title,
            percent_complete=percent_complete,
            start=start,
            finish=finish,
            deadline=deadline,
            duration=duration,
            draft=draft,
            **kwargs
        )
    return _make_item


# =============================================================================
# Sample Project Data
# =============================================================================

@pytest.fixture
def sample_metadata():
    """Sample project metadata."""
    return ProjectMetadata(
        project_name="Test Project",
        client_name="Test Client",
        next_item_num=10,
        workstreams=["Development", "Testing", "General"]
    )


@pytest.fixture
def sample_items(make_item, today, one_week_ago, one_week_ahead):
    """Sample set of items with various states."""
    return [
        make_item(item_num=1, title="Completed task", percent_complete=100,
                  start=one_week_ago, finish=today, type="Action Item"),
        make_item(item_num=2, title="In progress task", percent_complete=50,
                  start=one_week_ago, finish=one_week_ahead, type="Action Item"),
        make_item(item_num=3, title="Not started task", percent_complete=0,
                  start=today, finish=one_week_ahead, type="Risk"),
        make_item(item_num=4, title="Late task", percent_complete=25,
                  start=one_week_ago, finish=one_week_ago, type="Issue"),
        make_item(item_num=5, title="Draft item", percent_complete=0, draft=True,
                  type="Decision"),
    ]


@pytest.fixture
def sample_project(sample_metadata, sample_items):
    """Sample project with metadata and items."""
    return ProjectData(metadata=sample_metadata, items=sample_items)
