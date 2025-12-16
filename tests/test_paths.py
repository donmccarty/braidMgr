"""
Unit tests for platform-aware path handling.

Tests the paths module which provides cross-platform data directory locations.
"""

import pytest
import sys
from pathlib import Path
from unittest.mock import patch

from src.core.paths import (
    APP_NAME,
    get_app_data_dir,
    get_default_project_dir,
    ensure_app_directories,
    is_first_run,
    get_project_data_path,
)


class TestAppName:
    """Tests for app identity constants."""

    def test_app_name_defined(self):
        """APP_NAME is defined."""
        assert APP_NAME == "BRAID Manager"


class TestGetAppDataDir:
    """Tests for get_app_data_dir function."""

    def test_returns_path(self):
        """Returns a Path object."""
        result = get_app_data_dir()
        assert isinstance(result, Path)

    def test_path_ends_with_app_name(self):
        """Path ends with app name."""
        result = get_app_data_dir()
        assert result.name == APP_NAME

    @patch('sys.platform', 'darwin')
    def test_macos_path(self):
        """macOS uses ~/Library/Application Support."""
        result = get_app_data_dir()
        assert "Library" in str(result)
        assert "Application Support" in str(result)

    @patch('sys.platform', 'win32')
    @patch.dict('os.environ', {'APPDATA': 'C:\\Users\\Test\\AppData\\Roaming'})
    def test_windows_path_with_appdata(self):
        """Windows uses APPDATA environment variable."""
        result = get_app_data_dir()
        assert "AppData" in str(result) or "Roaming" in str(result)

    @patch('sys.platform', 'linux')
    def test_linux_path(self):
        """Linux uses ~/.local/share."""
        result = get_app_data_dir()
        assert ".local" in str(result)
        assert "share" in str(result)


class TestGetDefaultProjectDir:
    """Tests for get_default_project_dir function."""

    def test_returns_path(self):
        """Returns a Path object."""
        result = get_default_project_dir()
        assert isinstance(result, Path)

    def test_path_structure(self):
        """Path is inside app data dir under projects/default."""
        result = get_default_project_dir()
        assert result.name == "default"
        assert result.parent.name == "projects"


class TestEnsureAppDirectories:
    """Tests for ensure_app_directories function."""

    def test_returns_path(self, tmp_path, monkeypatch):
        """Returns the app data directory path."""
        # Mock get_app_data_dir to use temp directory
        test_dir = tmp_path / "BRAID Manager"
        monkeypatch.setattr('src.core.paths.get_app_data_dir', lambda: test_dir)

        result = ensure_app_directories()
        assert result == test_dir

    def test_creates_directories(self, tmp_path, monkeypatch):
        """Creates app directory and subdirectories."""
        test_dir = tmp_path / "BRAID Manager"
        monkeypatch.setattr('src.core.paths.get_app_data_dir', lambda: test_dir)

        ensure_app_directories()

        assert test_dir.exists()
        assert (test_dir / "projects").exists()
        assert (test_dir / "projects" / "default").exists()

    def test_idempotent(self, tmp_path, monkeypatch):
        """Can be called multiple times safely."""
        test_dir = tmp_path / "BRAID Manager"
        monkeypatch.setattr('src.core.paths.get_app_data_dir', lambda: test_dir)

        # Call twice
        ensure_app_directories()
        ensure_app_directories()

        assert test_dir.exists()


class TestIsFirstRun:
    """Tests for is_first_run function."""

    def test_first_run_when_no_dir(self, tmp_path, monkeypatch):
        """Returns True when app data dir doesn't exist."""
        test_dir = tmp_path / "nonexistent" / "BRAID Manager"
        monkeypatch.setattr('src.core.paths.get_app_data_dir', lambda: test_dir)

        assert is_first_run() is True

    def test_not_first_run_when_dir_exists(self, tmp_path, monkeypatch):
        """Returns False when app data dir exists."""
        test_dir = tmp_path / "BRAID Manager"
        test_dir.mkdir(parents=True)
        monkeypatch.setattr('src.core.paths.get_app_data_dir', lambda: test_dir)

        assert is_first_run() is False


class TestGetProjectDataPath:
    """Tests for get_project_data_path function."""

    def test_returns_default_project_dir(self):
        """Currently returns the default project directory."""
        result = get_project_data_path()
        expected = get_default_project_dir()
        assert result == expected
