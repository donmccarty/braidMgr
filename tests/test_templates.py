"""
Unit tests for project templates.

Tests the templates module which creates new project structures.
"""

import pytest
from datetime import date

from src.core.templates import (
    create_new_project,
    RAID_LOG_TEMPLATE,
)
from src.core.models import ProjectData, Item


class TestCreateNewProject:
    """Tests for create_new_project function."""

    def test_returns_project_data(self):
        """Returns a ProjectData instance."""
        result = create_new_project()
        assert isinstance(result, ProjectData)

    def test_default_project_name(self):
        """Uses default project name when not specified."""
        result = create_new_project()
        assert result.metadata.project_name == "New Project"

    def test_custom_project_name(self):
        """Uses custom project name when provided."""
        result = create_new_project(project_name="My Custom Project")
        assert result.metadata.project_name == "My Custom Project"

    def test_custom_client_name(self):
        """Uses custom client name when provided."""
        result = create_new_project(client_name="Acme Corp")
        assert result.metadata.client_name == "Acme Corp"

    def test_metadata_has_today_date(self):
        """Metadata uses today's date."""
        result = create_new_project()
        today = date.today()
        assert result.metadata.last_updated == today
        assert result.metadata.project_start == today
        assert result.metadata.indicators_updated == today

    def test_next_item_num_is_2(self):
        """next_item_num is 2 (after starter item)."""
        result = create_new_project()
        assert result.metadata.next_item_num == 2

    def test_default_workstream(self):
        """Has 'General' as default workstream."""
        result = create_new_project()
        assert "General" in result.metadata.workstreams

    def test_has_starter_item(self):
        """Creates a starter item."""
        result = create_new_project()
        assert len(result.items) == 1

    def test_starter_item_properties(self):
        """Starter item has expected properties."""
        result = create_new_project()
        item = result.items[0]

        assert item.item_num == 1
        assert item.type == "Action Item"
        assert item.title == "Set up project"
        assert item.workstream == "General"
        assert item.percent_complete == 0
        assert item.draft is False


class TestStarterItem:
    """Tests for the starter item created in new projects."""

    def test_starter_item_is_item(self):
        """Starter item is an Item instance."""
        result = create_new_project()
        assert isinstance(result.items[0], Item)

    def test_starter_item_has_today_start(self):
        """Starter item has today as start date."""
        result = create_new_project()
        item = result.items[0]
        assert item.start == date.today()

    def test_starter_item_not_draft(self):
        """Starter item is not a draft."""
        result = create_new_project()
        item = result.items[0]
        assert item.draft is False

    def test_starter_item_client_visible(self):
        """Starter item is client visible."""
        result = create_new_project()
        item = result.items[0]
        assert item.client_visible is True


class TestRaidLogTemplate:
    """Tests for RAID_LOG_TEMPLATE string."""

    def test_template_is_string(self):
        """Template is a string."""
        assert isinstance(RAID_LOG_TEMPLATE, str)

    def test_template_has_metadata(self):
        """Template contains metadata section."""
        assert "metadata:" in RAID_LOG_TEMPLATE
        assert "project_name:" in RAID_LOG_TEMPLATE

    def test_template_has_items(self):
        """Template contains items section."""
        assert "items:" in RAID_LOG_TEMPLATE

    def test_template_has_placeholder(self):
        """Template has {today} placeholder for formatting."""
        assert "{today}" in RAID_LOG_TEMPLATE
