"""
Items View - PySide6 Version
Filterable table of all RAID items.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QTableWidget, QTableWidgetItem, QHeaderView,
    QComboBox, QLineEdit, QPushButton, QAbstractItemView
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor
from typing import Optional
from datetime import date

from src.core.models import ProjectData
from src.core.indicators import get_indicator_config
from src.ui_qt.styles import TEXT_COLOR, TYPE_COLORS, INDICATOR_COLORS, INDICATOR_SEVERITY


class ItemsView(QWidget):
    """Items list view with filtering"""

    # Signal emitted when item is double-clicked (item_num)
    item_clicked = Signal(int)

    def __init__(self, project_data: Optional[ProjectData], parent=None):
        super().__init__(parent)
        self.project_data = project_data
        self.filtered_items = []

        self.setStyleSheet("background: #f5f5f5;")

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(16)

        # Title
        title = QLabel("All Items")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #1a1a2e; background: transparent;")
        layout.addWidget(title)

        # Filters row
        self._create_filters(layout)

        # Table
        self._create_table(layout)

        # Load data
        self._apply_filters()

    def _create_filters(self, parent_layout):
        """Create filter controls - modern pill-style design with collapsible filters"""
        from PySide6.QtWidgets import QGraphicsDropShadowEffect

        # Common styles
        control_style = """
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
                min-width: 110px;
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
            QLineEdit {
                padding: 8px 16px;
                border: none;
                border-radius: 8px;
                background: #f5f5f5;
                font-size: 13px;
                color: #333333;
            }
            QLineEdit:hover, QLineEdit:focus {
                background: #e9ecef;
            }
            QLabel {
                color: #666666;
                font-size: 12px;
                background: transparent;
            }
        """

        # === Primary controls (always visible): Search, Sort, Filters toggle, Count ===
        primary_frame = QFrame()
        primary_frame.setStyleSheet(control_style)

        shadow = QGraphicsDropShadowEffect()
        shadow.setBlurRadius(10)
        shadow.setOffset(0, 2)
        shadow.setColor(QColor(0, 0, 0, 25))
        primary_frame.setGraphicsEffect(shadow)

        primary_layout = QHBoxLayout(primary_frame)
        primary_layout.setContentsMargins(12, 8, 12, 8)
        primary_layout.setSpacing(8)

        # Search
        search_label = QLabel("Search:")
        primary_layout.addWidget(search_label)

        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search all fields...")
        self.search_input.setMinimumWidth(200)
        self.search_input.textChanged.connect(self._apply_filters)
        primary_layout.addWidget(self.search_input)

        primary_layout.addSpacing(12)

        # Sort by
        sort_label = QLabel("Sort:")
        primary_layout.addWidget(sort_label)

        self.sort_selector = QComboBox()
        self.sort_selector.addItems(["Item #", "Title", "Start Date", "Finish Date", "Deadline", "% Complete", "Type", "Last Updated"])
        self.sort_selector.currentTextChanged.connect(self._apply_filters)
        primary_layout.addWidget(self.sort_selector)

        primary_layout.addSpacing(12)

        # Filters toggle button
        self.filters_btn = QPushButton("Filters ▼")
        self.filters_btn.setStyleSheet("""
            QPushButton {
                background: #f5f5f5;
                color: #333333;
                border: none;
                border-radius: 8px;
                padding: 8px 16px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #e9ecef;
            }
            QPushButton:pressed {
                background: #dee2e6;
            }
        """)
        self.filters_btn.setCursor(Qt.PointingHandCursor)
        self.filters_btn.clicked.connect(self._toggle_filters)
        primary_layout.addWidget(self.filters_btn)

        primary_layout.addStretch()

        # Count label
        self.count_label = QLabel("0 items")
        self.count_label.setStyleSheet("""
            font-size: 12px;
            color: #666666;
            background: #f5f5f5;
            padding: 6px 12px;
            border-radius: 8px;
        """)
        primary_layout.addWidget(self.count_label)

        parent_layout.addWidget(primary_frame)

        # === Secondary controls (collapsible): Type, Status, Assignee ===
        self.filters_frame = QFrame()
        self.filters_frame.setStyleSheet(control_style.replace("border-radius: 12px;", "border-radius: 10px;"))
        self.filters_frame.setVisible(False)  # Hidden by default

        shadow2 = QGraphicsDropShadowEffect()
        shadow2.setBlurRadius(8)
        shadow2.setOffset(0, 2)
        shadow2.setColor(QColor(0, 0, 0, 20))
        self.filters_frame.setGraphicsEffect(shadow2)

        filters_layout = QHBoxLayout(self.filters_frame)
        filters_layout.setContentsMargins(12, 8, 12, 8)
        filters_layout.setSpacing(8)

        # Type filter
        type_label = QLabel("Type:")
        filters_layout.addWidget(type_label)

        self.type_filter = QComboBox()
        self.type_filter.addItems(["All Types", "Risk", "Issue", "Action Item", "Decision", "Deliverable", "Budget", "Plan Item"])
        self.type_filter.currentTextChanged.connect(self._apply_filters)
        filters_layout.addWidget(self.type_filter)

        filters_layout.addSpacing(12)

        # Status filter
        status_label = QLabel("Status:")
        filters_layout.addWidget(status_label)

        self.status_filter = QComboBox()
        self.status_filter.addItems(["All Statuses", "Open", "Completed", "Critical", "Warning", "Active", "Draft"])
        self.status_filter.currentTextChanged.connect(self._apply_filters)
        filters_layout.addWidget(self.status_filter)

        filters_layout.addSpacing(12)

        # Assignee filter
        assignee_label = QLabel("Assignee:")
        filters_layout.addWidget(assignee_label)

        self.assignee_filter = QComboBox()
        self.assignee_filter.addItem("All Assignees")
        self.assignee_filter.currentTextChanged.connect(self._apply_filters)
        filters_layout.addWidget(self.assignee_filter)

        filters_layout.addStretch()

        # Clear filters button
        clear_btn = QPushButton("Clear Filters")
        clear_btn.setStyleSheet("""
            QPushButton {
                background: transparent;
                color: #0d6efd;
                border: none;
                padding: 6px 12px;
                font-size: 12px;
            }
            QPushButton:hover {
                text-decoration: underline;
            }
        """)
        clear_btn.setCursor(Qt.PointingHandCursor)
        clear_btn.clicked.connect(self._clear_filters)
        filters_layout.addWidget(clear_btn)

        parent_layout.addWidget(self.filters_frame)

    def _toggle_filters(self):
        """Toggle visibility of filter controls"""
        is_visible = self.filters_frame.isVisible()
        self.filters_frame.setVisible(not is_visible)
        self.filters_btn.setText("Filters ▲" if not is_visible else "Filters ▼")

    def _clear_filters(self):
        """Reset all filters to default"""
        self.type_filter.setCurrentIndex(0)
        self.status_filter.setCurrentIndex(0)
        self.assignee_filter.setCurrentIndex(0)
        self.search_input.clear()

    def _create_table(self, parent_layout):
        """Create the items table"""
        self.table = QTableWidget()
        self.table.setStyleSheet("""
            QTableWidget {
                background: white;
                border: none;
                border-radius: 8px;
                gridline-color: #f0f0f0;
                color: #333333;
            }
            QTableWidget::item {
                padding: 8px;
                border-bottom: 1px solid #f0f0f0;
                color: #333333;
            }
            QTableWidget::item:selected {
                background: #e7f1ff;
                color: #1a1a2e;
            }
            QHeaderView::section {
                background: #f8f9fa;
                padding: 10px 8px;
                border: none;
                border-bottom: 2px solid #e0e0e0;
                font-weight: bold;
                font-size: 12px;
                color: #666;
            }
        """)

        # Columns
        columns = ["#", "Type", "Title", "Assigned To", "Status", "Start", "Finish", "Deadline", "%", "Updated"]
        self.table.setColumnCount(len(columns))
        self.table.setHorizontalHeaderLabels(columns)

        # Header settings
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeToContents)  # #
        header.setSectionResizeMode(1, QHeaderView.ResizeToContents)  # Type
        header.setSectionResizeMode(2, QHeaderView.Stretch)           # Title
        header.setSectionResizeMode(3, QHeaderView.ResizeToContents)  # Assigned
        header.setSectionResizeMode(4, QHeaderView.ResizeToContents)  # Status
        header.setSectionResizeMode(5, QHeaderView.ResizeToContents)  # Start
        header.setSectionResizeMode(6, QHeaderView.ResizeToContents)  # Finish
        header.setSectionResizeMode(7, QHeaderView.ResizeToContents)  # Deadline
        header.setSectionResizeMode(8, QHeaderView.ResizeToContents)  # %
        header.setSectionResizeMode(9, QHeaderView.ResizeToContents)  # Updated

        # Table settings
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        self.table.verticalHeader().setVisible(False)
        self.table.verticalHeader().setDefaultSectionSize(36)  # Row height for pills
        self.table.setShowGrid(False)

        # Connect double-click to open edit dialog
        self.table.doubleClicked.connect(self._on_row_double_click)

        parent_layout.addWidget(self.table)

    def _populate_assignee_filter(self):
        """Populate assignee filter with unique values"""
        if not self.project_data:
            return

        assignees = set()
        for item in self.project_data.items:
            if item.assigned_to:
                assignees.add(item.assigned_to)

        self.assignee_filter.clear()
        self.assignee_filter.addItem("All Assignees")
        for assignee in sorted(assignees):
            self.assignee_filter.addItem(assignee)

    def _apply_filters(self):
        """Apply all filters and update table"""
        if not self.project_data:
            return

        search_text = self.search_input.text().lower()
        type_filter = self.type_filter.currentText()
        status_filter = self.status_filter.currentText()
        assignee_filter = self.assignee_filter.currentText()

        # Use severity mapping from centralized styles
        completed_severities = ["done", "completed"]
        critical_severities = ["critical"]
        warning_severities = ["warning"]
        active_severities = ["active"]
        draft_severities = ["draft"]

        self.filtered_items = []
        for item in self.project_data.items:
            # Search filter - searches all text fields
            if search_text:
                title_match = search_text in (item.title or "").lower()
                id_match = search_text in str(item.item_num)
                desc_match = search_text in (item.description or "").lower()
                notes_match = search_text in (item.notes or "").lower()
                assignee_match = search_text in (item.assigned_to or "").lower()
                if not (title_match or id_match or desc_match or notes_match or assignee_match):
                    continue

            # Type filter
            if type_filter != "All Types":
                if (item.type or "Plan Item") != type_filter:
                    continue

            # Status filter - uses severity mapping
            if status_filter != "All Statuses":
                indicator = item.indicator or ""
                severity = INDICATOR_SEVERITY.get(indicator, "")
                if status_filter == "Open" and severity in completed_severities:
                    continue
                elif status_filter == "Completed" and severity not in completed_severities:
                    continue
                elif status_filter == "Critical" and severity not in critical_severities:
                    continue
                elif status_filter == "Warning" and severity not in warning_severities:
                    continue
                elif status_filter == "Active" and severity not in active_severities:
                    continue
                elif status_filter == "Draft" and severity not in draft_severities:
                    continue

            # Assignee filter
            if assignee_filter != "All Assignees":
                if item.assigned_to != assignee_filter:
                    continue

            self.filtered_items.append(item)

        # Apply sorting
        sort_key = self.sort_selector.currentText()
        self.filtered_items = self._sort_items(self.filtered_items, sort_key)

        self._update_table()
        self.count_label.setText(f"{len(self.filtered_items)} items")

    def _sort_items(self, items, sort_key):
        """Sort items by the selected key"""
        if sort_key == "Item #":
            return sorted(items, key=lambda x: x.item_num)
        elif sort_key == "Title":
            return sorted(items, key=lambda x: (x.title or "").lower())
        elif sort_key == "Start Date":
            return sorted(items, key=lambda x: (
                x.start if x.start and not isinstance(x.start, str) else date.max
            ))
        elif sort_key == "Finish Date":
            return sorted(items, key=lambda x: (
                x.finish if x.finish and not isinstance(x.finish, str) else date.max
            ))
        elif sort_key == "Deadline":
            return sorted(items, key=lambda x: (
                x.deadline if x.deadline and not isinstance(x.deadline, str) else date.max
            ))
        elif sort_key == "% Complete":
            return sorted(items, key=lambda x: -(x.percent_complete or 0))
        elif sort_key == "Type":
            return sorted(items, key=lambda x: (x.type or "Plan Item"))
        elif sort_key == "Last Updated":
            return sorted(items, key=lambda x: (
                x.last_updated if x.last_updated and not isinstance(x.last_updated, str) else date.min
            ), reverse=True)
        else:
            return items

    def _create_pill_widget(self, text, color):
        """Create a pill-style label widget for table cells"""
        # Convert hex color to rgba with 30% opacity
        r = int(color[1:3], 16)
        g = int(color[3:5], 16)
        b = int(color[5:7], 16)
        bg_rgba = f"rgba({r}, {g}, {b}, 0.3)"

        pill = QLabel(text)
        pill.setStyleSheet(f"""
            background: {bg_rgba};
            color: {TEXT_COLOR};
            padding: 2px 6px;
            border-radius: 3px;
            font-size: 12px;
        """)
        return pill

    def _update_table(self):
        """Update table with filtered items"""
        from PySide6.QtGui import QFont, QBrush

        self.table.setRowCount(len(self.filtered_items))

        # Standard text color (from centralized styles)
        text_color = QColor(TEXT_COLOR)

        for row, item in enumerate(self.filtered_items):
            # Item number - bold
            num_item = QTableWidgetItem(f"#{item.item_num}")
            num_item.setTextAlignment(Qt.AlignCenter)
            bold_font = QFont()
            bold_font.setBold(True)
            num_item.setFont(bold_font)
            num_item.setForeground(text_color)
            self.table.setItem(row, 0, num_item)

            # Type - pill widget
            type_text = item.type or "Plan Item"
            type_color = TYPE_COLORS.get(type_text, "#6c757d")
            type_widget = self._create_pill_widget(type_text, type_color)
            self.table.setCellWidget(row, 1, type_widget)

            # Title
            title_item = QTableWidgetItem(item.title or "Untitled")
            title_item.setForeground(text_color)
            self.table.setItem(row, 2, title_item)

            # Assigned To
            assignee_item = QTableWidgetItem(item.assigned_to or "—")
            assignee_item.setForeground(text_color)
            self.table.setItem(row, 3, assignee_item)

            # Status/Indicator - pill widget
            indicator = item.indicator or "—"
            status_color = INDICATOR_COLORS.get(indicator, "#6c757d")
            status_widget = self._create_pill_widget(indicator, status_color)
            self.table.setCellWidget(row, 4, status_widget)

            # Start date
            if item.start and not isinstance(item.start, str):
                start_text = item.start.strftime("%m/%d/%y")
            else:
                start_text = "—"
            start_item = QTableWidgetItem(start_text)
            start_item.setTextAlignment(Qt.AlignCenter)
            start_item.setForeground(text_color)
            self.table.setItem(row, 5, start_item)

            # Finish date
            if item.finish and not isinstance(item.finish, str):
                finish_text = item.finish.strftime("%m/%d/%y")
            else:
                finish_text = "—"
            finish_item = QTableWidgetItem(finish_text)
            finish_item.setTextAlignment(Qt.AlignCenter)
            finish_item.setForeground(text_color)
            self.table.setItem(row, 6, finish_item)

            # Deadline
            if item.deadline and not isinstance(item.deadline, str):
                deadline_text = item.deadline.strftime("%m/%d/%y")
                days_until = (item.deadline - date.today()).days
                if days_until < 0:
                    deadline_text += f" ({abs(days_until)}d)"
                elif days_until <= 7:
                    deadline_text += f" ({days_until}d)"
            else:
                deadline_text = "—"
            deadline_item = QTableWidgetItem(deadline_text)
            deadline_item.setTextAlignment(Qt.AlignCenter)
            deadline_item.setForeground(text_color)
            self.table.setItem(row, 7, deadline_item)

            # Percent complete
            pct = item.percent_complete or 0
            pct_item = QTableWidgetItem(f"{pct}%")
            pct_item.setTextAlignment(Qt.AlignCenter)
            pct_item.setForeground(text_color)
            self.table.setItem(row, 8, pct_item)

            # Last Updated
            if item.last_updated and not isinstance(item.last_updated, str):
                updated_text = item.last_updated.strftime("%m/%d/%y")
            else:
                updated_text = "—"
            updated_item = QTableWidgetItem(updated_text)
            updated_item.setTextAlignment(Qt.AlignCenter)
            updated_item.setForeground(text_color)
            self.table.setItem(row, 9, updated_item)

    def refresh(self, project_data, budget):
        """Refresh with new data"""
        self.project_data = project_data
        self._populate_assignee_filter()
        self._apply_filters()

    def apply_filter(self, filter_type: str, filter_value: str):
        """Apply a filter programmatically (called from Dashboard click-through)"""
        # Show filters panel if hidden
        if not self.filters_frame.isVisible():
            self._toggle_filters()

        # Clear other filters first
        self._clear_filters()

        # Apply the requested filter
        if filter_type == "status":
            # Map filter values to combo box items
            status_map = {
                "Critical": "Critical",
                "Warning": "Warning",
                "Active": "Active",
                "Completed": "Completed",
                "Draft": "Draft",
                "Open": "Open",
                "All": "All Statuses",
            }
            combo_value = status_map.get(filter_value, "All Statuses")
            index = self.status_filter.findText(combo_value)
            if index >= 0:
                self.status_filter.setCurrentIndex(index)

        elif filter_type == "type":
            # Find and set the type filter
            index = self.type_filter.findText(filter_value)
            if index >= 0:
                self.type_filter.setCurrentIndex(index)

        elif filter_type == "assignee":
            # Find and set the assignee filter
            index = self.assignee_filter.findText(filter_value)
            if index >= 0:
                self.assignee_filter.setCurrentIndex(index)

    def _on_row_double_click(self, index):
        """Handle double-click on table row"""
        row = index.row()
        if 0 <= row < len(self.filtered_items):
            item = self.filtered_items[row]
            self.item_clicked.emit(item.item_num)
