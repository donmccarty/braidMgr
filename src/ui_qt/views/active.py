"""
Active Items View - PySide6 Version
Shows only open/active items grouped by assignee or workstream.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QComboBox, QGraphicsDropShadowEffect, QPushButton
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QColor
from typing import Optional
from datetime import date

from src.core.models import ProjectData
from src.ui_qt.styles import (
    TEXT_COLOR, GROUP_HEADER_COLOR, TYPE_COLORS,
    INDICATOR_COLORS, INDICATOR_SEVERITY, STATUS_GROUPS
)


def add_shadow(widget, blur=15, offset=2, color=QColor(0, 0, 0, 25)):
    """Add drop shadow to a widget"""
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setOffset(0, offset)
    shadow.setColor(color)
    widget.setGraphicsEffect(shadow)


def hex_to_rgba(hex_color, opacity):
    """Convert hex color to rgba string for Qt stylesheets"""
    r = int(hex_color[1:3], 16)
    g = int(hex_color[3:5], 16)
    b = int(hex_color[5:7], 16)
    return f"rgba({r}, {g}, {b}, {opacity})"


class CollapsibleGroupCard(QFrame):
    """A collapsible card for a group of items"""

    def __init__(self, group_name, items, group_color=None, sort_key="deadline", parent=None):
        super().__init__(parent)
        self.group_name = group_name
        self.items = items
        self.group_color = group_color or "#1a1a2e"
        self.sort_key = sort_key
        self.is_collapsed = False
        self.max_visible = 10  # Show 10 at a time initially
        self.show_all = False

        self.setStyleSheet("QFrame { background: white; border-radius: 8px; }")
        add_shadow(self)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        self._build_header()
        self._build_content()

    def _build_header(self):
        """Build the collapsible header"""
        header = QFrame()
        # Use rgba for proper Qt stylesheet transparency
        bg_color = hex_to_rgba(self.group_color, 0.08)
        border_color = hex_to_rgba(self.group_color, 0.19)
        header.setStyleSheet(f"""
            QFrame {{
                background: {bg_color};
                border-top-left-radius: 8px;
                border-top-right-radius: 8px;
                border-bottom: 1px solid {border_color};
            }}
        """)
        header.setCursor(Qt.PointingHandCursor)
        header.mousePressEvent = lambda e: self._toggle_collapse()

        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(16, 12, 16, 12)

        # Collapse indicator
        self.collapse_btn = QLabel("▼")
        self.collapse_btn.setStyleSheet(f"font-size: 10px; color: {self.group_color}; background: transparent;")
        header_layout.addWidget(self.collapse_btn)

        # Color indicator
        color_dot = QFrame()
        color_dot.setFixedSize(12, 12)
        color_dot.setStyleSheet(f"background: {self.group_color}; border-radius: 6px;")
        header_layout.addWidget(color_dot)

        # Title
        title = QLabel(self.group_name)
        title.setStyleSheet(f"font-size: 16px; font-weight: bold; color: #1a1a2e; background: transparent;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Count badge
        count = QLabel(f"{len(self.items)}")
        count.setStyleSheet(f"""
            background: {self.group_color};
            color: white;
            padding: 2px 10px;
            border-radius: 10px;
            font-size: 12px;
            font-weight: bold;
        """)
        header_layout.addWidget(count)

        self.main_layout.addWidget(header)

    def _build_content(self):
        """Build the content area with items"""
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(16, 12, 16, 12)
        self.content_layout.setSpacing(8)

        self._populate_items()

        self.main_layout.addWidget(self.content_widget)

    def _populate_items(self):
        """Populate items in the content area"""
        # Clear existing - handle both widgets and layouts
        self._clear_layout(self.content_layout)

        # Sort items
        sorted_items = self._sort_items(self.items)

        # Determine how many to show
        visible_count = len(sorted_items) if self.show_all else min(self.max_visible, len(sorted_items))

        for item in sorted_items[:visible_count]:
            item_row = self._create_item_row(item)
            self.content_layout.addLayout(item_row)

        # Show more/less button if needed
        if len(sorted_items) > self.max_visible:
            btn_layout = QHBoxLayout()
            btn_layout.addStretch()

            if self.show_all:
                btn_text = f"Show less"
            else:
                btn_text = f"Show all {len(sorted_items)} items"

            show_btn = QPushButton(btn_text)
            show_btn.setStyleSheet("""
                QPushButton {
                    background: transparent;
                    color: #0d6efd;
                    border: none;
                    font-size: 12px;
                    padding: 4px 8px;
                }
                QPushButton:hover {
                    text-decoration: underline;
                }
            """)
            show_btn.setCursor(Qt.PointingHandCursor)
            show_btn.clicked.connect(self._toggle_show_all)
            btn_layout.addWidget(show_btn)

            btn_layout.addStretch()
            self.content_layout.addLayout(btn_layout)

    def _clear_layout(self, layout):
        """Recursively clear all items from a layout"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout(child.layout())

    def _sort_items(self, items):
        """Sort items based on current sort key"""
        if self.sort_key == "deadline":
            return sorted(items, key=lambda x: (
                x.deadline if x.deadline and not isinstance(x.deadline, str) else date.max
            ))
        elif self.sort_key == "start":
            return sorted(items, key=lambda x: (
                x.start if x.start and not isinstance(x.start, str) else date.max
            ))
        elif self.sort_key == "finish":
            return sorted(items, key=lambda x: (
                x.finish if x.finish and not isinstance(x.finish, str) else date.max
            ))
        elif self.sort_key == "priority":
            # Sort by indicator severity
            priority_order = {"Overdue": 0, "Due Soon": 1, "Active": 2, "In Progress": 2, "Upcoming": 3, "Not Started": 4, "Draft": 5}
            return sorted(items, key=lambda x: priority_order.get(x.indicator, 6))
        elif self.sort_key == "item_num":
            return sorted(items, key=lambda x: x.item_num)
        elif self.sort_key == "title":
            return sorted(items, key=lambda x: (x.title or "").lower())
        elif self.sort_key == "percent":
            return sorted(items, key=lambda x: -(x.percent_complete or 0))
        else:
            return items

    def _create_item_row(self, item):
        """Create a row for an item with consistent alignment"""
        row = QHBoxLayout()
        row.setSpacing(8)

        # Item number - fixed width
        num = QLabel(f"#{item.item_num}")
        num.setFixedWidth(45)
        num.setStyleSheet(f"font-size: 12px; color: {TEXT_COLOR}; font-weight: bold; background: transparent;")
        row.addWidget(num)

        # Type pill - fixed width, background color only, standard text
        type_text = item.type or "Plan Item"
        type_color = TYPE_COLORS.get(type_text, "#6c757d")
        type_bg = hex_to_rgba(type_color, 0.15)
        type_label = QLabel(type_text)
        type_label.setFixedWidth(85)
        type_label.setStyleSheet(f"""
            background: {type_bg};
            color: {TEXT_COLOR};
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
        """)
        row.addWidget(type_label)

        # Title - stretches to fill
        title_text = item.title or "Untitled"
        if len(title_text) > 55:
            title_text = title_text[:52] + "..."
        title = QLabel(title_text)
        title.setStyleSheet(f"font-size: 13px; color: {TEXT_COLOR}; background: transparent;")
        row.addWidget(title, 1)

        # Percent complete - fixed width, always show
        pct = item.percent_complete or 0
        pct_label = QLabel(f"{pct}%" if pct > 0 else "—")
        pct_label.setFixedWidth(40)
        pct_label.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        pct_label.setStyleSheet(f"font-size: 11px; color: {TEXT_COLOR}; background: transparent;")
        row.addWidget(pct_label)

        # Status indicator - fixed width, background color only, standard text
        indicator = item.indicator or "—"
        indicator_color = INDICATOR_COLORS.get(indicator, "#6c757d")
        indicator_bg = hex_to_rgba(indicator_color, 0.15)
        status = QLabel(indicator)
        status.setFixedWidth(115)
        status.setStyleSheet(f"""
            background: {indicator_bg};
            color: {TEXT_COLOR};
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 11px;
        """)
        row.addWidget(status)

        # Deadline - fixed width, always show, standard text color
        if item.deadline and not isinstance(item.deadline, str):
            days_until = (item.deadline - date.today()).days
            if days_until < 0:
                deadline_text = f"{abs(days_until)}d overdue"
            elif days_until == 0:
                deadline_text = "Today"
            elif days_until <= 7:
                deadline_text = f"{days_until}d"
            else:
                deadline_text = f"{days_until}d"
        else:
            deadline_text = "—"

        deadline = QLabel(deadline_text)
        deadline.setFixedWidth(75)
        deadline.setAlignment(Qt.AlignRight | Qt.AlignVCenter)
        deadline.setStyleSheet(f"font-size: 11px; color: {TEXT_COLOR}; background: transparent;")
        row.addWidget(deadline)

        return row

    def _toggle_collapse(self):
        """Toggle collapsed state"""
        self.is_collapsed = not self.is_collapsed
        self.content_widget.setVisible(not self.is_collapsed)
        self.collapse_btn.setText("▶" if self.is_collapsed else "▼")

    def _toggle_show_all(self):
        """Toggle showing all items"""
        self.show_all = not self.show_all
        self._populate_items()

    def update_sort(self, sort_key):
        """Update sort key and refresh"""
        self.sort_key = sort_key
        self._populate_items()


class ActiveItemsView(QScrollArea):
    """Active items view grouped by assignee or workstream"""

    def __init__(self, project_data: Optional[ProjectData], parent=None):
        super().__init__(parent)
        self.project_data = project_data
        self.group_by = "status_group"  # Default to Status Group (severity-based)
        self.sort_by = "deadline"
        self.group_cards = []

        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet("QScrollArea { border: none; background: #f5f5f5; }")

        # Container
        self.container = QWidget()
        self.container.setStyleSheet("background: #f5f5f5;")
        self.setWidget(self.container)

        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(24, 24, 24, 24)
        self.main_layout.setSpacing(16)

        self._build_ui()

    def _build_ui(self):
        """Build the UI"""
        # Header row
        header_layout = QHBoxLayout()

        title = QLabel("Active Items")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #1a1a2e; background: transparent;")
        header_layout.addWidget(title)

        header_layout.addStretch()

        # Controls frame - modern pill-style design
        controls = QFrame()
        controls.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 12px;
            }
            QComboBox {
                padding: 8px 16px;
                padding-right: 30px;
                border: none;
                border-radius: 8px;
                background: #f5f5f5;
                font-size: 13px;
                color: #333333;
                min-width: 130px;
            }
            QComboBox:hover {
                background: #e9ecef;
            }
            QComboBox:focus {
                background: #e9ecef;
            }
            QComboBox::drop-down {
                border: none;
                width: 24px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #666666;
                margin-right: 8px;
            }
            QComboBox QAbstractItemView {
                background: white;
                border: 1px solid #e0e0e0;
                border-radius: 8px;
                padding: 4px;
                selection-background-color: #f0f0f0;
                selection-color: #333333;
            }
            QLabel {
                color: #666666;
                font-size: 12px;
                background: transparent;
            }
        """)
        add_shadow(controls, blur=10, offset=2)

        controls_layout = QHBoxLayout(controls)
        controls_layout.setContentsMargins(12, 8, 12, 8)
        controls_layout.setSpacing(8)

        # Group by selector
        group_label = QLabel("Group:")
        controls_layout.addWidget(group_label)

        self.group_selector = QComboBox()
        self.group_selector.addItems(["Status Group", "Status", "Assignee", "Workstream", "Type"])
        self.group_selector.currentTextChanged.connect(self._on_group_changed)
        controls_layout.addWidget(self.group_selector)

        controls_layout.addSpacing(8)

        # Sort by selector
        sort_label = QLabel("Sort:")
        controls_layout.addWidget(sort_label)

        self.sort_selector = QComboBox()
        self.sort_selector.addItems(["Deadline", "Start Date", "Finish Date", "Priority", "Item #", "Title", "% Complete"])
        self.sort_selector.currentTextChanged.connect(self._on_sort_changed)
        controls_layout.addWidget(self.sort_selector)

        controls_layout.addSpacing(8)

        # Collapse all / Expand all buttons - pill style
        btn_style = """
            QPushButton {
                background: #f5f5f5;
                color: #333333;
                border: none;
                border-radius: 8px;
                padding: 8px 14px;
                font-size: 12px;
            }
            QPushButton:hover {
                background: #e9ecef;
            }
            QPushButton:pressed {
                background: #dee2e6;
            }
        """

        self.collapse_btn = QPushButton("Collapse All")
        self.collapse_btn.setStyleSheet(btn_style)
        self.collapse_btn.setCursor(Qt.PointingHandCursor)
        self.collapse_btn.clicked.connect(self._collapse_all)
        controls_layout.addWidget(self.collapse_btn)

        self.expand_btn = QPushButton("Expand All")
        self.expand_btn.setStyleSheet(btn_style)
        self.expand_btn.setCursor(Qt.PointingHandCursor)
        self.expand_btn.clicked.connect(self._expand_all)
        controls_layout.addWidget(self.expand_btn)

        header_layout.addWidget(controls)

        self.main_layout.addLayout(header_layout)

        # Content area (will be rebuilt on refresh)
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        self.content_layout.setSpacing(16)
        self.main_layout.addWidget(self.content_widget)

        self.main_layout.addStretch()

        self._rebuild_content()

    def _on_group_changed(self, text):
        """Handle group by change"""
        # Map display text to internal key
        group_map = {
            "Status Group": "status_group",
            "Status": "status",
            "Assignee": "assignee",
            "Workstream": "workstream",
            "Type": "type"
        }
        self.group_by = group_map.get(text, "status_group")
        self._rebuild_content()

    def _on_sort_changed(self, text):
        """Handle sort by change"""
        sort_map = {
            "Deadline": "deadline",
            "Start Date": "start",
            "Finish Date": "finish",
            "Priority": "priority",
            "Item #": "item_num",
            "Title": "title",
            "% Complete": "percent"
        }
        self.sort_by = sort_map.get(text, "deadline")

        # Update all cards
        for card in self.group_cards:
            card.update_sort(self.sort_by)

    def _collapse_all(self):
        """Collapse all group cards"""
        for card in self.group_cards:
            if not card.is_collapsed:
                card._toggle_collapse()

    def _expand_all(self):
        """Expand all group cards"""
        for card in self.group_cards:
            if card.is_collapsed:
                card._toggle_collapse()

    def _rebuild_content(self):
        """Rebuild the grouped content"""
        # Clear existing content
        self.group_cards = []
        while self.content_layout.count():
            child = self.content_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()

        if not self.project_data:
            no_data = QLabel("No data loaded")
            no_data.setStyleSheet("font-size: 14px; color: #666; background: transparent;")
            self.content_layout.addWidget(no_data)
            return

        # Get active items (must have an indicator and not be completed)
        completed_indicators = ["Completed", "Completed Recently", "Done", "Closed", "Cancelled", "Resolved"]
        open_items = [
            i for i in self.project_data.items
            if i.indicator  # Must have an indicator (not blank/None)
            and i.indicator not in completed_indicators
        ]

        if not open_items:
            no_items = QLabel("No active items")
            no_items.setStyleSheet("font-size: 14px; color: #666; background: transparent;")
            self.content_layout.addWidget(no_items)
            return

        # Group items
        if self.group_by == "status_group":
            groups = self._group_by_status_group(open_items)
        elif self.group_by == "status":
            groups = self._group_by_indicator(open_items)
        else:
            groups = self._group_by_field(open_items)

        # Create cards for each group
        for group_name, group_data in groups:
            items = group_data.get("items", group_data) if isinstance(group_data, dict) else group_data
            color = group_data.get("color", "#1a1a2e") if isinstance(group_data, dict) else None

            if not items:
                continue

            card = CollapsibleGroupCard(group_name, items, color, self.sort_by)
            self.group_cards.append(card)
            self.content_layout.addWidget(card)

    def _group_by_status_group(self, items):
        """Group items by status group (severity-based: Critical, Warning, etc.)"""
        groups = {name: {"items": [], "color": data["color"], "order": data["order"]}
                  for name, data in STATUS_GROUPS.items()}

        for item in items:
            indicator = item.indicator or ""
            # Get severity from indicator
            severity = INDICATOR_SEVERITY.get(indicator, "")

            # Find matching group by severity
            placed = False
            for group_name, group_data in STATUS_GROUPS.items():
                if severity == group_data["severity"]:
                    groups[group_name]["items"].append(item)
                    placed = True
                    break

            # Items with 'done' or 'draft' severity are not shown (matches HTML)
            # So we don't add them to any group

        # Sort by order and filter empty groups
        sorted_groups = sorted(
            [(name, data) for name, data in groups.items() if data["items"]],
            key=lambda x: x[1]["order"]
        )

        return sorted_groups

    def _group_by_indicator(self, items):
        """Group items by actual indicator/status value (In Progress, Starting Soon!, etc.)"""
        groups = {}

        for item in items:
            indicator = item.indicator
            # Items without indicators are already filtered out in _rebuild_content
            if not indicator:
                continue

            if indicator not in groups:
                groups[indicator] = {"items": [], "color": GROUP_HEADER_COLOR}
            groups[indicator]["items"].append(item)

        # Sort by severity order, then alphabetically within same severity
        def sort_key(group_tuple):
            name, data = group_tuple
            severity = INDICATOR_SEVERITY.get(name, "zzz")
            severity_order = {"critical": 0, "warning": 1, "upcoming": 2, "active": 3, "completed": 4, "done": 5, "draft": 6}
            return (severity_order.get(severity, 99), name)

        sorted_groups = sorted(groups.items(), key=sort_key)

        return sorted_groups

    def _group_by_field(self, items):
        """Group items by a field (assignee, workstream, type)"""
        groups = {}

        for item in items:
            if self.group_by == "assignee":
                key = item.assigned_to or "Unassigned"
            elif self.group_by == "workstream":
                key = item.workstream or "No Workstream"
            elif self.group_by == "type":
                key = item.type or "Plan Item"
            else:
                key = "All Items"

            if key not in groups:
                groups[key] = {"items": [], "color": GROUP_HEADER_COLOR}
            groups[key]["items"].append(item)

        # Sort groups by item count (descending)
        sorted_groups = sorted(groups.items(), key=lambda x: -len(x[1]["items"]))

        return sorted_groups

    def refresh(self, project_data, budget):
        """Refresh with new data"""
        self.project_data = project_data
        self._rebuild_content()
