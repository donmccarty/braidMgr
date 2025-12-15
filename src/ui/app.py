#!/usr/bin/env python3
"""
RAID Manager Desktop Application
Main application window with navigation sidebar and view panels.
Styled to match the HTML project viewer.
"""

import customtkinter as ctk
from pathlib import Path
import sys

# Add parent to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.core.yaml_store import YamlStore
from src.core.indicators import update_all_indicators, INDICATOR_ORDER, get_indicator_config
from src.core.budget import BudgetCalculator
from src.core.models import ProjectData, BudgetData

# Colors matching HTML version
SIDEBAR_BG = "#1a1a2e"  # Dark blue gradient start
SIDEBAR_BG_DARK = "#16213e"  # Dark blue gradient end
ACCENT_COLOR = "#4dabf7"  # Blue accent for active items
CONTENT_BG = "#f5f5f5"  # Light gray background
CONTENT_BG_DARK = "#1e1e1e"  # Dark mode content

# Sidebar colors (replacing rgba with hex approximations)
SEPARATOR_COLOR = "#333344"  # rgba(255,255,255,0.1) on dark bg
TEXT_DIM = "#b3b3b3"  # rgba(255,255,255,0.7)
TEXT_DIMMER = "#666666"  # rgba(255,255,255,0.4)
HOVER_BG = "#2a2a3e"  # rgba(255,255,255,0.1) hover
ACTIVE_BG = "#3a3a4e"  # rgba(255,255,255,0.15) active

# Set appearance - follow system setting
ctk.set_appearance_mode("system")  # Respect system dark/light mode
ctk.set_default_color_theme("blue")


class RAIDManagerApp(ctk.CTk):
    """Main application window"""

    def __init__(self):
        super().__init__()

        # Window setup
        self.title("BRAID Log - MLMIC Claim Report Migration")
        self.geometry("1400x900")
        self.minsize(1000, 700)

        # Data
        self.project_data: ProjectData = None
        self.budget_data: BudgetData = None
        self.calculated_budget = None
        self.data_dir: Path = None

        # Configure grid
        self.grid_columnconfigure(0, weight=0, minsize=220)  # Sidebar fixed width
        self.grid_columnconfigure(1, weight=1)  # Content expands
        self.grid_rowconfigure(0, weight=1)

        # Create sidebar
        self._create_sidebar()

        # Create main content area
        self.content_frame = ctk.CTkFrame(self, corner_radius=0, fg_color=CONTENT_BG_DARK)
        self.content_frame.grid(row=0, column=1, sticky="nsew")
        self.content_frame.grid_columnconfigure(0, weight=1)
        self.content_frame.grid_rowconfigure(0, weight=1)

        # View frames (lazy loaded)
        self.views = {}
        self.current_view = None

        # Try to load data
        self._find_and_load_data()

        # Show dashboard by default
        self.show_view("dashboard")

    def _create_sidebar(self):
        """Create the navigation sidebar matching HTML design"""
        self.sidebar = ctk.CTkFrame(self, width=220, corner_radius=0, fg_color=SIDEBAR_BG)
        self.sidebar.grid(row=0, column=0, sticky="nsew")
        self.sidebar.grid_propagate(False)
        self.sidebar.grid_columnconfigure(0, weight=1)

        # Header with title
        header_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent", height=60)
        header_frame.grid(row=0, column=0, sticky="ew", padx=0, pady=0)
        header_frame.grid_propagate(False)
        header_frame.grid_columnconfigure(0, weight=1)

        self.logo_label = ctk.CTkLabel(
            header_frame,
            text="BRAID Log",
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color="white"
        )
        self.logo_label.grid(row=0, column=0, padx=16, pady=16, sticky="w")

        # Separator line
        sep = ctk.CTkFrame(self.sidebar, height=1, fg_color=SEPARATOR_COLOR)
        sep.grid(row=1, column=0, sticky="ew")

        # Navigation label
        nav_label = ctk.CTkLabel(
            self.sidebar,
            text="NAVIGATION",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=TEXT_DIMMER
        )
        nav_label.grid(row=2, column=0, padx=16, pady=(12, 4), sticky="w")

        # Navigation section
        nav_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        nav_frame.grid(row=3, column=0, sticky="nsew", pady=0)
        nav_frame.grid_columnconfigure(0, weight=1)
        self.sidebar.grid_rowconfigure(3, weight=1)

        # Navigation items with icons (using Unicode symbols)
        self.nav_buttons = {}
        nav_items = [
            ("dashboard", "📊", "Dashboard"),
            ("items", "📋", "Items"),
            ("budget", "💰", "Budget"),
        ]

        for i, (view_id, icon, label) in enumerate(nav_items):
            btn_frame = ctk.CTkFrame(nav_frame, fg_color="transparent", height=40)
            btn_frame.grid(row=i, column=0, sticky="ew", padx=0, pady=1)
            btn_frame.pack_propagate(False)
            btn_frame.grid_columnconfigure(1, weight=1)

            # Active indicator (left border)
            indicator = ctk.CTkFrame(btn_frame, width=4, fg_color="transparent")
            indicator.grid(row=0, column=0, sticky="ns")

            # Button content - more visible text color
            btn = ctk.CTkButton(
                btn_frame,
                text=f"  {icon}  {label}",
                command=lambda v=view_id: self.show_view(v),
                fg_color="transparent",
                text_color="#cccccc",  # Brighter text
                hover_color=HOVER_BG,
                anchor="w",
                font=ctk.CTkFont(size=14),
                height=40,
                corner_radius=0
            )
            btn.grid(row=0, column=1, sticky="ew")

            self.nav_buttons[view_id] = {"button": btn, "indicator": indicator, "frame": btn_frame}

        # Actions section at bottom
        actions_frame = ctk.CTkFrame(self.sidebar, fg_color="transparent")
        actions_frame.grid(row=4, column=0, sticky="sew", pady=8)
        actions_frame.grid_columnconfigure(0, weight=1)

        # Separator
        sep2 = ctk.CTkFrame(actions_frame, height=1, fg_color=SEPARATOR_COLOR)
        sep2.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        actions_label = ctk.CTkLabel(
            actions_frame,
            text="ACTIONS",
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=TEXT_DIMMER
        )
        actions_label.grid(row=1, column=0, padx=16, pady=(4, 8), sticky="w")

        self.update_btn = ctk.CTkButton(
            actions_frame,
            text="  🔄  Update Indicators",
            command=self._update_indicators,
            fg_color="transparent",
            text_color=TEXT_DIM,
            hover_color=HOVER_BG,
            anchor="w",
            font=ctk.CTkFont(size=13),
            height=36,
            corner_radius=0
        )
        self.update_btn.grid(row=2, column=0, sticky="ew")

        self.reload_btn = ctk.CTkButton(
            actions_frame,
            text="  ↻  Reload Data",
            command=self._reload_data,
            fg_color="transparent",
            text_color=TEXT_DIM,
            hover_color=HOVER_BG,
            anchor="w",
            font=ctk.CTkFont(size=13),
            height=36,
            corner_radius=0
        )
        self.reload_btn.grid(row=3, column=0, sticky="ew")

        # Status at very bottom
        self.status_label = ctk.CTkLabel(
            actions_frame,
            text="No data loaded",
            font=ctk.CTkFont(size=11),
            text_color=TEXT_DIMMER
        )
        self.status_label.grid(row=4, column=0, padx=16, pady=(16, 8), sticky="w")

    def _find_and_load_data(self):
        """Find and load RAID and Budget data"""
        candidates = [
            Path(__file__).parent.parent.parent.parent / 'data',
            Path.cwd() / 'data',
            Path.cwd(),
        ]

        for candidate in candidates:
            if candidate.exists():
                raid_files = list(candidate.glob('RAID-Log-*.yaml')) + list(candidate.glob('BRAID-Log-*.yaml'))
                if raid_files:
                    self.data_dir = candidate
                    break

        if not self.data_dir:
            self.status_label.configure(text="No data found")
            return

        self._load_data()

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
            self.status_label.configure(text=f"{item_count} items ({open_count} open)")

    def _reload_data(self):
        """Reload data from files"""
        self._load_data()
        if self.current_view:
            self.show_view(self.current_view, force_refresh=True)

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

        self.show_view(self.current_view, force_refresh=True)

    def show_view(self, view_id: str, force_refresh: bool = False):
        """Show a view by ID"""
        # Update nav button styles
        for vid, nav in self.nav_buttons.items():
            if vid == view_id:
                nav["button"].configure(
                    fg_color=ACTIVE_BG,
                    text_color="white"
                )
                nav["indicator"].configure(fg_color=ACCENT_COLOR)
            else:
                nav["button"].configure(
                    fg_color="transparent",
                    text_color=TEXT_DIM
                )
                nav["indicator"].configure(fg_color="transparent")

        # Create or get view
        if view_id not in self.views or force_refresh:
            if view_id in self.views:
                self.views[view_id].destroy()

            if view_id == "dashboard":
                from src.ui.views.dashboard import DashboardView
                self.views[view_id] = DashboardView(
                    self.content_frame,
                    self.project_data,
                    self.calculated_budget
                )
            elif view_id == "items":
                from src.ui.views.items import ItemsView
                self.views[view_id] = ItemsView(
                    self.content_frame,
                    self.project_data
                )
            elif view_id == "budget":
                from src.ui.views.budget import BudgetView
                self.views[view_id] = BudgetView(
                    self.content_frame,
                    self.calculated_budget
                )

        # Hide all views
        for vid, view in self.views.items():
            view.grid_forget()

        # Show selected view
        if view_id in self.views:
            self.views[view_id].grid(row=0, column=0, sticky="nsew", padx=20, pady=20)

        self.current_view = view_id


def main():
    app = RAIDManagerApp()
    app.lift()
    app.attributes('-topmost', True)
    app.after(100, lambda: app.attributes('-topmost', False))
    app.focus_force()
    app.mainloop()


if __name__ == "__main__":
    main()
