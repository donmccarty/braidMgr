"""
Items View - List and filter RAID items.
Styled to match HTML project viewer.
"""

import customtkinter as ctk
from typing import Optional, List, Callable

from src.core.models import ProjectData, Item
from src.core.indicators import get_indicator_config, INDICATOR_CONFIG

# Colors
CARD_BG = "#2d2d2d"
CARD_BORDER = "#3d3d3d"
ROW_BG = "#363636"
ROW_HOVER = "#404040"
TEXT_PRIMARY = "#ffffff"
TEXT_SECONDARY = "#888888"
TEXT_MUTED = "#666666"

# Type badge colors
TYPE_COLORS = {
    "Risk": "#dc3545",
    "Issue": "#fd7e14",
    "Action Item": "#0d6efd",
    "Decision": "#6f42c1",
    "Deliverable": "#28a745",
    "Budget": "#20c997",
    "Plan Item": "#6c757d"
}


class ItemsView(ctk.CTkFrame):
    """Items list view with filtering"""

    def __init__(self, parent, project_data: Optional[ProjectData], on_item_select: Optional[Callable] = None):
        super().__init__(parent, fg_color="transparent")

        self.project_data = project_data
        self.on_item_select = on_item_select
        self.filtered_items: List[Item] = []

        # Filter state
        self.type_filter = ctk.StringVar(value="All")
        self.status_filter = ctk.StringVar(value="Open")
        self.search_var = ctk.StringVar()
        self.search_var.trace_add("write", lambda *args: self._apply_filters())

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._create_widgets()
        self._apply_filters()

    def _create_widgets(self):
        """Create view widgets"""
        # Header with title and filters
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 16))
        header_frame.grid_columnconfigure(4, weight=1)

        # Title
        title = ctk.CTkLabel(
            header_frame,
            text="RAID Items",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=TEXT_PRIMARY
        )
        title.grid(row=0, column=0, sticky="w", padx=(0, 24))

        # Filters row
        filter_frame = ctk.CTkFrame(header_frame, fg_color="transparent")
        filter_frame.grid(row=0, column=1, columnspan=4, sticky="e")

        # Type filter
        type_label = ctk.CTkLabel(filter_frame, text="Type:", text_color=TEXT_SECONDARY, font=ctk.CTkFont(size=12))
        type_label.pack(side="left", padx=(0, 4))

        types = ["All", "Risk", "Action Item", "Issue", "Decision", "Deliverable", "Plan Item"]
        type_dropdown = ctk.CTkComboBox(
            filter_frame,
            values=types,
            variable=self.type_filter,
            command=lambda _: self._apply_filters(),
            width=130,
            height=32,
            fg_color=CARD_BG,
            border_color=CARD_BORDER,
            button_color=CARD_BORDER,
            dropdown_fg_color=CARD_BG
        )
        type_dropdown.pack(side="left", padx=(0, 16))

        # Status filter
        status_label = ctk.CTkLabel(filter_frame, text="Status:", text_color=TEXT_SECONDARY, font=ctk.CTkFont(size=12))
        status_label.pack(side="left", padx=(0, 4))

        statuses = ["All", "Open", "Active", "Critical", "Warning", "Completed"]
        status_dropdown = ctk.CTkComboBox(
            filter_frame,
            values=statuses,
            variable=self.status_filter,
            command=lambda _: self._apply_filters(),
            width=120,
            height=32,
            fg_color=CARD_BG,
            border_color=CARD_BORDER,
            button_color=CARD_BORDER,
            dropdown_fg_color=CARD_BG
        )
        status_dropdown.pack(side="left", padx=(0, 16))

        # Search
        search_entry = ctk.CTkEntry(
            filter_frame,
            textvariable=self.search_var,
            placeholder_text="Search items...",
            width=200,
            height=32,
            fg_color=CARD_BG,
            border_color=CARD_BORDER
        )
        search_entry.pack(side="left")

        # Items list card
        list_card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=8)
        list_card.grid(row=1, column=0, sticky="nsew")
        list_card.grid_columnconfigure(0, weight=1)
        list_card.grid_rowconfigure(1, weight=1)

        # List header
        list_header = ctk.CTkFrame(list_card, fg_color="transparent", height=40)
        list_header.grid(row=0, column=0, sticky="ew", padx=16, pady=(12, 0))
        list_header.grid_propagate(False)
        list_header.grid_columnconfigure(2, weight=1)

        ctk.CTkLabel(list_header, text="#", width=50, anchor="w", text_color=TEXT_SECONDARY, font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=0, sticky="w")
        ctk.CTkLabel(list_header, text="Title", anchor="w", text_color=TEXT_SECONDARY, font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=2, sticky="w")
        ctk.CTkLabel(list_header, text="Type", width=100, anchor="w", text_color=TEXT_SECONDARY, font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=3, sticky="w", padx=(16, 0))
        ctk.CTkLabel(list_header, text="Assignee", width=120, anchor="w", text_color=TEXT_SECONDARY, font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=4, sticky="w", padx=(16, 0))
        ctk.CTkLabel(list_header, text="Progress", width=70, anchor="e", text_color=TEXT_SECONDARY, font=ctk.CTkFont(size=12, weight="bold")).grid(row=0, column=5, sticky="e", padx=(16, 0))

        # Separator
        sep = ctk.CTkFrame(list_card, height=1, fg_color=CARD_BORDER)
        sep.grid(row=1, column=0, sticky="ew", padx=16, pady=(8, 0))

        # Scrollable items list
        self.scroll_frame = ctk.CTkScrollableFrame(list_card, fg_color="transparent")
        self.scroll_frame.grid(row=2, column=0, sticky="nsew", padx=8, pady=8)
        self.scroll_frame.grid_columnconfigure(0, weight=1)

    def _apply_filters(self):
        """Apply current filters and update list"""
        if not self.project_data:
            self.filtered_items = []
            self._render_items()
            return

        items = self.project_data.items
        type_val = self.type_filter.get()
        status_val = self.status_filter.get()
        search_val = self.search_var.get().lower()

        # Type filter
        if type_val != "All":
            items = [i for i in items if i.type == type_val]

        # Status filter
        if status_val == "Open":
            items = [i for i in items if i.is_open]
        elif status_val == "Active":
            items = [i for i in items if i.is_active]
        elif status_val == "Critical":
            items = [i for i in items if i.is_critical]
        elif status_val == "Warning":
            items = [i for i in items if i.is_warning]
        elif status_val == "Completed":
            items = [i for i in items if i.is_complete]

        # Search filter
        if search_val:
            items = [i for i in items if
                     search_val in (i.title or "").lower() or
                     search_val in (i.assigned_to or "").lower() or
                     search_val in str(i.item_num)]

        self.filtered_items = items
        self._render_items()

    def _render_items(self):
        """Render the filtered items list"""
        # Clear existing items
        for widget in self.scroll_frame.winfo_children():
            widget.destroy()

        if not self.filtered_items:
            no_items = ctk.CTkLabel(
                self.scroll_frame,
                text="No items match the current filters",
                text_color=TEXT_MUTED,
                font=ctk.CTkFont(size=14)
            )
            no_items.pack(pady=40)
            return

        # Create item rows
        for i, item in enumerate(self.filtered_items):
            self._create_item_row(item, i)

    def _create_item_row(self, item: Item, index: int):
        """Create a row for an item"""
        # Alternate row colors
        bg_color = ROW_BG if index % 2 == 0 else CARD_BG

        row_frame = ctk.CTkFrame(self.scroll_frame, fg_color=bg_color, corner_radius=4, height=44)
        row_frame.pack(fill="x", pady=1)
        row_frame.pack_propagate(False)
        row_frame.grid_columnconfigure(2, weight=1)

        # Indicator color
        indicator = item.indicator or "Not Started"
        config = get_indicator_config(indicator)
        color = config.color if config else "#6c757d"

        # Status indicator dot
        indicator_frame = ctk.CTkFrame(row_frame, fg_color="transparent", width=40)
        indicator_frame.pack(side="left", fill="y")
        indicator_frame.pack_propagate(False)

        dot = ctk.CTkLabel(indicator_frame, text="●", text_color=color, font=ctk.CTkFont(size=12))
        dot.place(relx=0.5, rely=0.5, anchor="center")

        # Item number
        num_label = ctk.CTkLabel(
            row_frame,
            text=f"#{item.item_num}",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color=TEXT_SECONDARY,
            width=40
        )
        num_label.pack(side="left", padx=(0, 8))

        # Title (flexible width)
        title_label = ctk.CTkLabel(
            row_frame,
            text=item.title or "Untitled",
            anchor="w",
            text_color=TEXT_PRIMARY,
            font=ctk.CTkFont(size=13)
        )
        title_label.pack(side="left", fill="x", expand=True, padx=(0, 16))

        # Type badge
        type_text = item.type or "Plan Item"
        type_color = TYPE_COLORS.get(type_text, "#6c757d")

        type_badge = ctk.CTkLabel(
            row_frame,
            text=type_text,
            text_color=type_color,
            font=ctk.CTkFont(size=11),
            width=90,
            anchor="w"
        )
        type_badge.pack(side="left", padx=(0, 16))

        # Assigned to
        assignee = item.assigned_to or "Unassigned"
        assignee_label = ctk.CTkLabel(
            row_frame,
            text=assignee,
            text_color=TEXT_SECONDARY,
            font=ctk.CTkFont(size=12),
            width=110,
            anchor="w"
        )
        assignee_label.pack(side="left", padx=(0, 16))

        # Progress
        progress = item.percent_complete or 0
        progress_color = "#28a745" if progress == 100 else TEXT_SECONDARY
        progress_label = ctk.CTkLabel(
            row_frame,
            text=f"{progress}%",
            text_color=progress_color,
            font=ctk.CTkFont(size=12),
            width=50,
            anchor="e"
        )
        progress_label.pack(side="right", padx=(0, 16))

    def refresh(self, project_data: Optional[ProjectData]):
        """Refresh with new data"""
        self.project_data = project_data
        self._apply_filters()
