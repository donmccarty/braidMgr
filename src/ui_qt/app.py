#!/usr/bin/env python3
"""
RAID Manager Desktop Application - PySide6 Version
Main application window with navigation sidebar and view panels.
Styled to match the HTML project viewer.
"""

import sys
import shutil
from pathlib import Path
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
    QPushButton, QLabel, QFrame, QStackedWidget, QScrollArea,
    QSizePolicy, QGraphicsDropShadowEffect, QFileDialog, QInputDialog,
    QMessageBox
)
from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QColor, QIcon, QAction

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.yaml_store import YamlStore
from src.core.indicators import update_all_indicators
from src.core.budget import BudgetCalculator
from src.core.models import ProjectData, BudgetData
from src.core.paths import get_project_data_path, ensure_app_directories, is_first_run
from src.core.templates import create_new_project
from src.ui_qt.styles import MAIN_STYLESHEET, COLORS
from src.ui_qt.views.dashboard import DashboardView
from src.ui_qt.dialogs import EditItemDialog


class NavButton(QPushButton):
    """Custom navigation button with indicator"""

    def __init__(self, icon: str, text: str, parent=None):
        super().__init__(parent)
        self.setObjectName("nav_button")
        self.setText(f"  {icon}  {text}")
        self.setCheckable(True)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumHeight(40)


class RAIDManagerApp(QMainWindow):
    """Main application window"""

    def __init__(self):
        super().__init__()

        # Data
        self.project_data: ProjectData = None
        self.budget_data: BudgetData = None
        self.calculated_budget = None
        self.data_dir: Path = None

        # Setup window
        self.setWindowTitle("BRAID Log - MLMIC Claim Report Migration")
        self.setMinimumSize(1200, 800)
        self.resize(1400, 900)

        # Apply stylesheet
        self.setStyleSheet(MAIN_STYLESHEET)

        # Create central widget
        central = QWidget()
        self.setCentralWidget(central)

        # Main layout
        main_layout = QHBoxLayout(central)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create sidebar
        self._create_sidebar(main_layout)

        # Create content area
        self._create_content_area(main_layout)

        # Create menu bar
        self._create_menu_bar()

        # Load data
        self._find_and_load_data()

        # Show dashboard
        self.show_view("dashboard")

    def _create_sidebar(self, parent_layout):
        """Create the navigation sidebar"""
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(220)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Logo
        logo = QLabel("BRAID Log")
        logo.setObjectName("sidebar_logo")
        layout.addWidget(logo)

        # Separator
        sep1 = QFrame()
        sep1.setObjectName("separator")
        sep1.setFixedHeight(1)
        layout.addWidget(sep1)

        # Navigation section label
        nav_label = QLabel("NAVIGATION")
        nav_label.setObjectName("sidebar_section_label")
        layout.addWidget(nav_label)

        # Navigation buttons
        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "📊", "Dashboard"),
            ("active", "🎯", "Active Items"),
            ("items", "📋", "All Items"),
            ("timeline", "📅", "Timeline"),
            ("chronology", "📜", "Chronology"),
            ("budget", "💰", "Budget"),
            ("help", "❓", "Help"),
        ]

        for view_id, icon, text in nav_items:
            btn = NavButton(icon, text)
            btn.clicked.connect(lambda checked, v=view_id: self.show_view(v))
            layout.addWidget(btn)
            self.nav_buttons[view_id] = btn

        # Spacer
        layout.addStretch()

        # Actions separator
        sep2 = QFrame()
        sep2.setObjectName("separator")
        sep2.setFixedHeight(1)
        layout.addWidget(sep2)

        # Actions label
        actions_label = QLabel("ACTIONS")
        actions_label.setObjectName("sidebar_section_label")
        layout.addWidget(actions_label)

        # Action buttons
        update_btn = QPushButton("  🔄  Update Indicators")
        update_btn.setObjectName("action_button")
        update_btn.setCursor(Qt.PointingHandCursor)
        update_btn.clicked.connect(self._update_indicators)
        layout.addWidget(update_btn)

        reload_btn = QPushButton("  ↻  Reload Data")
        reload_btn.setObjectName("action_button")
        reload_btn.setCursor(Qt.PointingHandCursor)
        reload_btn.clicked.connect(self._reload_data)
        layout.addWidget(reload_btn)

        # Project management separator
        sep3 = QFrame()
        sep3.setObjectName("separator")
        sep3.setFixedHeight(1)
        layout.addWidget(sep3)

        # Project label
        project_label = QLabel("PROJECT")
        project_label.setObjectName("sidebar_section_label")
        layout.addWidget(project_label)

        # New Project button
        new_btn = QPushButton("  ➕  New Project")
        new_btn.setObjectName("action_button")
        new_btn.setCursor(Qt.PointingHandCursor)
        new_btn.clicked.connect(self._new_project)
        layout.addWidget(new_btn)

        # Import BRAID button
        import_braid_btn = QPushButton("  📥  Import BRAID")
        import_braid_btn.setObjectName("action_button")
        import_braid_btn.setCursor(Qt.PointingHandCursor)
        import_braid_btn.clicked.connect(self._import_braid)
        layout.addWidget(import_braid_btn)

        # Import Budget button
        import_budget_btn = QPushButton("  📥  Import Budget")
        import_budget_btn.setObjectName("action_button")
        import_budget_btn.setCursor(Qt.PointingHandCursor)
        import_budget_btn.clicked.connect(self._import_budget)
        layout.addWidget(import_budget_btn)

        # Export button
        export_btn = QPushButton("  📤  Export")
        export_btn.setObjectName("action_button")
        export_btn.setCursor(Qt.PointingHandCursor)
        export_btn.clicked.connect(self._export_project)
        layout.addWidget(export_btn)

        # Status
        self.status_label = QLabel("No data loaded")
        self.status_label.setObjectName("status_label")
        layout.addWidget(self.status_label)

        parent_layout.addWidget(sidebar)

    def _create_content_area(self, parent_layout):
        """Create the main content area"""
        content = QFrame()
        content.setObjectName("content_area")

        layout = QVBoxLayout(content)
        layout.setContentsMargins(0, 0, 0, 0)

        # Stacked widget for views
        self.view_stack = QStackedWidget()
        layout.addWidget(self.view_stack)

        # Views dict
        self.views = {}

        parent_layout.addWidget(content, 1)

    def _create_menu_bar(self):
        """Create the application menu bar"""
        menubar = self.menuBar()

        # Help menu
        help_menu = menubar.addMenu("Help")

        # User Guide action
        user_guide_action = QAction("User Guide", self)
        user_guide_action.setShortcut("F1")
        user_guide_action.triggered.connect(lambda: self.show_view("help"))
        help_menu.addAction(user_guide_action)

        help_menu.addSeparator()

        # About action
        about_action = QAction("About BRAID Manager", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def _show_about(self):
        """Show about dialog"""
        QMessageBox.about(
            self,
            "About BRAID Manager",
            "<h2>BRAID Manager</h2>"
            "<p>Version 1.0.0</p>"
            "<p>Desktop application for managing BRAID logs:<br>"
            "<b>B</b>udget, <b>R</b>isks, <b>A</b>ction Items, <b>I</b>ssues, <b>D</b>ecisions</p>"
            "<p>Built with PySide6 (Qt for Python)</p>"
            "<p>&copy; 2024 Centric Consulting</p>"
        )

    def _find_and_load_data(self):
        """Find and load RAID and Budget data from platform-appropriate location"""
        # Priority order for finding data:
        # 1. Platform app data directory (for packaged app)
        # 2. Relative 'data' folder (for development)
        # 3. Current working directory (fallback)

        candidates = [
            get_project_data_path(),  # Platform-specific app data
            Path(__file__).parent.parent.parent.parent / 'data',  # Dev mode
            Path.cwd() / 'data',
            Path.cwd(),
        ]

        for candidate in candidates:
            if candidate.exists():
                raid_files = list(candidate.glob('RAID-Log-*.yaml')) + list(candidate.glob('BRAID-Log-*.yaml'))
                if raid_files:
                    self.data_dir = candidate
                    break

        # If no data found, set up first-run with new project
        if not self.data_dir:
            self._handle_first_run()
            return

        self._load_data()

    def _handle_first_run(self):
        """Handle first run - create app directories and starter project"""
        ensure_app_directories()
        self.data_dir = get_project_data_path()

        # Create a new starter project
        new_project = create_new_project(
            project_name="My Project",
            client_name=None
        )

        # Save the starter project
        store = YamlStore(self.data_dir)
        raid_file = self.data_dir / "BRAID-Log-MyProject.yaml"
        store.save_raid_log(raid_file, new_project)

        # Load the newly created project
        self._load_data()
        self.status_label.setText("New project created")

    def _load_data(self):
        """Load data from YAML files"""
        if not self.data_dir:
            return

        store = YamlStore(self.data_dir)

        raid_files = store.find_raid_logs()
        if raid_files:
            self.project_data = store.load_raid_log(raid_files[0])

        budget_files = store.find_budget_files()
        if budget_files:
            self.budget_data = store.load_budget(budget_files[0])
            calc = BudgetCalculator(self.budget_data)
            self.calculated_budget = calc.calculate()

        if self.project_data:
            item_count = len(self.project_data.items)
            open_count = len(self.project_data.get_open_items())
            self.status_label.setText(f"{item_count} items ({open_count} open)")
            self._update_window_title()

    def _reload_data(self):
        """Reload data from files"""
        self._load_data()
        self._refresh_current_view()

    def _update_indicators(self):
        """Update indicators and save"""
        if not self.project_data or not self.data_dir:
            return

        from datetime import date
        today = date.today()

        update_all_indicators(self.project_data.items, today)
        self.project_data.metadata.indicators_updated = today
        self.project_data.metadata.last_updated = today

        store = YamlStore(self.data_dir)
        raid_files = store.find_raid_logs()
        if raid_files:
            store.save_raid_log(raid_files[0], self.project_data)

        self._refresh_current_view()

    def _refresh_current_view(self):
        """Refresh the current view"""
        current = self.view_stack.currentWidget()
        if current and hasattr(current, 'refresh'):
            current.refresh(self.project_data, self.calculated_budget)

    def show_view(self, view_id: str):
        """Show a view by ID"""
        # Update nav button states
        for vid, btn in self.nav_buttons.items():
            btn.setChecked(vid == view_id)

        # Create view if needed
        if view_id not in self.views:
            if view_id == "dashboard":
                view = DashboardView(self.project_data, self.calculated_budget)
                # Connect dashboard navigation signal
                view.navigate_to_items.connect(self.show_items_filtered)
            elif view_id == "active":
                from src.ui_qt.views.active import ActiveItemsView
                view = ActiveItemsView(self.project_data)
            elif view_id == "items":
                from src.ui_qt.views.items import ItemsView
                view = ItemsView(self.project_data)
                view.item_clicked.connect(self._show_edit_dialog)
            elif view_id == "timeline":
                from src.ui_qt.views.timeline import TimelineView
                view = TimelineView(self.project_data)
                view.item_clicked.connect(self._show_edit_dialog)
            elif view_id == "chronology":
                from src.ui_qt.views.chronology import ChronologyView
                view = ChronologyView(self.project_data)
                view.item_clicked.connect(self._show_edit_dialog)
            elif view_id == "budget":
                from src.ui_qt.views.budget import BudgetView
                view = BudgetView(self.calculated_budget)
            elif view_id == "help":
                from src.ui_qt.views.help import HelpView
                view = HelpView()
            else:
                view = QLabel(f"View: {view_id}")

            self.views[view_id] = view
            self.view_stack.addWidget(view)

        # Show view
        self.view_stack.setCurrentWidget(self.views[view_id])

    def show_items_filtered(self, filter_type: str, filter_value: str):
        """Navigate to All Items with a filter applied"""
        self.show_view("items")
        items_view = self.views.get("items")
        if items_view and hasattr(items_view, 'apply_filter'):
            items_view.apply_filter(filter_type, filter_value)

    def _show_edit_dialog(self, item_num: int):
        """Show the edit dialog for an item"""
        if not self.project_data:
            return

        # Find the item
        item = self.project_data.get_item(item_num)
        if not item:
            return

        # Create dialog
        dialog = EditItemDialog(item, self.project_data.metadata, self)

        # Populate assignees from existing items
        assignees = set()
        for i in self.project_data.items:
            if i.assigned_to:
                assignees.add(i.assigned_to)
        dialog.populate_assignees(list(assignees))

        # Connect save signal
        dialog.item_saved.connect(self._save_item)

        # Show dialog
        dialog.exec()

    def _save_item(self, item_num: int):
        """Save item changes to YAML"""
        if not self.project_data or not self.data_dir:
            return

        # Update project metadata
        from datetime import date
        self.project_data.metadata.last_updated = date.today()

        # Save to YAML
        store = YamlStore(self.data_dir)
        raid_files = store.find_raid_logs()
        if raid_files:
            store.save_raid_log(raid_files[0], self.project_data)

        # Update status
        item_count = len(self.project_data.items)
        open_count = len(self.project_data.get_open_items())
        self.status_label.setText(f"{item_count} items ({open_count} open)")

        # Refresh current view
        self._refresh_current_view()

    # =========================================================================
    # Project Management Actions
    # =========================================================================

    def _new_project(self):
        """Create a new project, replacing the current one"""
        # Get project name from user
        name, ok = QInputDialog.getText(
            self,
            "New Project",
            "Project name:",
            text="My Project"
        )
        if not ok or not name.strip():
            return

        name = name.strip()

        # Confirm replacement
        if self.project_data:
            reply = QMessageBox.question(
                self,
                "Replace Current Project?",
                f"This will replace the current project with a new one named '{name}'.\n\n"
                "The current project will be deleted. Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        # Ensure app directories exist
        ensure_app_directories()
        self.data_dir = get_project_data_path()

        # Remove existing BRAID log files
        for f in self.data_dir.glob('BRAID-Log-*.yaml'):
            f.unlink()
        for f in self.data_dir.glob('RAID-Log-*.yaml'):
            f.unlink()

        # Create new project
        new_project = create_new_project(project_name=name)

        # Save it
        safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '-')
        store = YamlStore(self.data_dir)
        raid_file = self.data_dir / f"BRAID-Log-{safe_name}.yaml"
        store.save_raid_log(raid_file, new_project)

        # Clear views cache so they rebuild with new data
        self.views.clear()
        while self.view_stack.count():
            widget = self.view_stack.widget(0)
            self.view_stack.removeWidget(widget)

        # Reload
        self._load_data()
        self._update_window_title()
        self.show_view("dashboard")
        self.status_label.setText("New project created")

    def _import_braid(self):
        """Import a BRAID log file, replacing the current one"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import BRAID Log",
            str(Path.home()),
            "YAML Files (*.yaml *.yml);;All Files (*)"
        )
        if not file_path:
            return

        source = Path(file_path)
        if not source.exists():
            QMessageBox.warning(self, "Import Failed", "File not found.")
            return

        # Confirm replacement
        if self.project_data:
            reply = QMessageBox.question(
                self,
                "Replace Current Project?",
                f"This will replace the current project with the imported file.\n\n"
                "The current project will be deleted. Continue?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            if reply != QMessageBox.Yes:
                return

        # Ensure app directories exist
        ensure_app_directories()
        self.data_dir = get_project_data_path()

        # Remove existing BRAID log files
        for f in self.data_dir.glob('BRAID-Log-*.yaml'):
            f.unlink()
        for f in self.data_dir.glob('RAID-Log-*.yaml'):
            f.unlink()

        # Copy file to app data directory
        dest = self.data_dir / source.name
        shutil.copy2(source, dest)

        # Clear views cache
        self.views.clear()
        while self.view_stack.count():
            widget = self.view_stack.widget(0)
            self.view_stack.removeWidget(widget)

        # Reload
        self._load_data()
        self._update_window_title()
        self.show_view("dashboard")
        self.status_label.setText("BRAID log imported")

    def _import_budget(self):
        """Import a Budget file"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Import Budget",
            str(Path.home()),
            "YAML Files (*.yaml *.yml);;All Files (*)"
        )
        if not file_path:
            return

        source = Path(file_path)
        if not source.exists():
            QMessageBox.warning(self, "Import Failed", "File not found.")
            return

        # Ensure app directories exist
        ensure_app_directories()
        self.data_dir = get_project_data_path()

        # Remove existing budget files
        for f in self.data_dir.glob('Budget-*.yaml'):
            f.unlink()

        # Copy file to app data directory
        dest = self.data_dir / source.name
        shutil.copy2(source, dest)

        # Reload data
        self._load_data()
        self._refresh_current_view()
        self.status_label.setText("Budget imported")

    def _export_project(self):
        """Export project files to Downloads folder"""
        if not self.data_dir:
            QMessageBox.warning(self, "Export Failed", "No project loaded.")
            return

        downloads = Path.home() / "Downloads"
        if not downloads.exists():
            downloads.mkdir(parents=True)

        exported = []

        # Export BRAID log files
        for f in self.data_dir.glob('BRAID-Log-*.yaml'):
            dest = downloads / f.name
            shutil.copy2(f, dest)
            exported.append(f.name)

        for f in self.data_dir.glob('RAID-Log-*.yaml'):
            dest = downloads / f.name
            shutil.copy2(f, dest)
            exported.append(f.name)

        # Export budget files
        for f in self.data_dir.glob('Budget-*.yaml'):
            dest = downloads / f.name
            shutil.copy2(f, dest)
            exported.append(f.name)

        if exported:
            QMessageBox.information(
                self,
                "Export Complete",
                f"Exported to Downloads:\n\n" + "\n".join(exported)
            )
        else:
            QMessageBox.warning(self, "Export Failed", "No files to export.")

    def _update_window_title(self):
        """Update window title with project name"""
        if self.project_data and self.project_data.metadata.project_name:
            self.setWindowTitle(f"BRAID Log - {self.project_data.metadata.project_name}")
        else:
            self.setWindowTitle("BRAID Log")


def main():
    app = QApplication(sys.argv)

    # Set application properties
    app.setApplicationName("BRAID Log")
    app.setOrganizationName("Centric Consulting")

    # Create and show window
    window = RAIDManagerApp()
    window.show()

    # Bring to front
    window.raise_()
    window.activateWindow()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
