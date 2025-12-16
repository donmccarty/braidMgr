"""
Timeline View - PySide6 Version
Visual timeline/Gantt-style view of items with dates.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QGraphicsDropShadowEffect, QComboBox
)
from PySide6.QtCore import Qt, QRect, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QFont, QPainterPath
from typing import Optional
from datetime import date, timedelta

from src.core.models import ProjectData
from src.ui_qt.styles import INDICATOR_COLORS, INDICATOR_SEVERITY


def add_shadow(widget, blur=15, offset=2, color=QColor(0, 0, 0, 25)):
    """Add drop shadow to a widget"""
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setOffset(0, offset)
    shadow.setColor(color)
    widget.setGraphicsEffect(shadow)


class TimelineChart(QWidget):
    """Custom timeline/Gantt chart widget"""

    # Signal emitted when item is double-clicked (item_num)
    item_clicked = Signal(int)

    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.items = items
        self.row_height = 32
        self.header_height = 40
        self.left_margin = 250
        self.right_margin = 20

        # Enable mouse tracking for tooltips
        self.setMouseTracking(True)

        # Calculate date range
        self._calculate_date_range()

        # Set minimum size based on items
        min_height = self.header_height + len(self.items) * self.row_height + 20
        self.setMinimumHeight(max(400, min_height))

    def mouseMoveEvent(self, event):
        """Show tooltip on hover and update cursor"""
        y = event.pos().y()
        if y < self.header_height:
            self.setToolTip("")
            self.setCursor(Qt.ArrowCursor)
            return

        row_index = (y - self.header_height) // self.row_height
        if 0 <= row_index < len(self.items):
            item = self.items[row_index]
            tooltip = self._build_tooltip(item)
            self.setToolTip(tooltip)
            # Show pointer cursor to indicate row is clickable
            self.setCursor(Qt.PointingHandCursor)
        else:
            self.setToolTip("")
            self.setCursor(Qt.ArrowCursor)

    def leaveEvent(self, event):
        """Reset cursor when leaving widget"""
        self.setCursor(Qt.ArrowCursor)
        super().leaveEvent(event)

    def mouseDoubleClickEvent(self, event):
        """Handle double-click to open edit dialog"""
        y = event.pos().y()
        if y < self.header_height:
            return

        row_index = (y - self.header_height) // self.row_height
        if 0 <= row_index < len(self.items):
            item = self.items[row_index]
            self.item_clicked.emit(item['num'])

    def mousePressEvent(self, event):
        """Handle single-click to open edit dialog (same as double-click for convenience)"""
        # Only respond to left-click
        if event.button() != Qt.LeftButton:
            return

        y = event.pos().y()
        if y < self.header_height:
            return

        row_index = (y - self.header_height) // self.row_height
        if 0 <= row_index < len(self.items):
            item = self.items[row_index]
            self.item_clicked.emit(item['num'])

    def _build_tooltip(self, item):
        """Build tooltip text for an item"""
        lines = []
        lines.append(f"#{item['num']}: {item['title']}")
        lines.append(f"Type: {item.get('type', 'N/A')}")
        if item.get('assigned'):
            lines.append(f"Assigned: {item['assigned']}")
        if item.get('workstream'):
            lines.append(f"Workstream: {item['workstream']}")
        lines.append(f"Status: {item.get('indicator', 'N/A')}")
        if item.get('start'):
            lines.append(f"Start: {item['start'].strftime('%m/%d/%Y')}")
        if item.get('end'):
            lines.append(f"Finish: {item['end'].strftime('%m/%d/%Y')}")
        if item.get('deadline'):
            lines.append(f"Deadline: {item['deadline'].strftime('%m/%d/%Y')}")
        if item.get('pct') is not None:
            lines.append(f"Progress: {item['pct']}%")

        # Add description (truncated if long)
        if item.get('description'):
            desc = item['description']
            if len(desc) > 100:
                desc = desc[:97] + "..."
            lines.append(f"---")
            lines.append(f"{desc}")

        # Add last note (notes format: "> DATE - AUTHOR - TEXT")
        if item.get('notes'):
            notes_text = item['notes']
            note_lines = [n.strip() for n in notes_text.split('\n') if n.strip().startswith('>')]
            if note_lines:
                last_note = note_lines[-1].lstrip('> ').strip()
                if len(last_note) > 80:
                    last_note = last_note[:77] + "..."
                lines.append(f"---")
                lines.append(f"Last Note: {last_note}")

        return "\n".join(lines)

    def _calculate_date_range(self):
        """Calculate the date range for the timeline"""
        today = date.today()
        self.start_date = today - timedelta(days=30)
        self.end_date = today + timedelta(days=60)

        # Adjust based on items
        for item in self.items:
            if item.get('start') and item['start'] < self.start_date:
                self.start_date = item['start'] - timedelta(days=7)
            if item.get('end') and item['end'] > self.end_date:
                self.end_date = item['end'] + timedelta(days=7)
            if item.get('deadline') and item['deadline'] > self.end_date:
                self.end_date = item['deadline'] + timedelta(days=7)

        self.total_days = (self.end_date - self.start_date).days

    def _date_to_x(self, d):
        """Convert a date to x coordinate"""
        if not d:
            return None
        days_from_start = (d - self.start_date).days
        available_width = self.width() - self.left_margin - self.right_margin
        return self.left_margin + int((days_from_start / self.total_days) * available_width)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()
        today = date.today()

        # Background
        painter.fillRect(0, 0, w, h, QColor("white"))

        # Draw header background
        painter.fillRect(0, 0, w, self.header_height, QColor("#f8f9fa"))

        # Draw month labels and lines
        painter.setPen(QColor("#666666"))
        font = QFont()
        font.setPixelSize(11)
        font.setBold(True)
        painter.setFont(font)

        current = self.start_date.replace(day=1)
        while current <= self.end_date:
            x = self._date_to_x(current)
            if x and self.left_margin <= x <= w - self.right_margin:
                month_name = current.strftime("%b %Y")
                painter.drawText(x + 2, 14, month_name)

                # Month line (thicker)
                painter.setPen(QPen(QColor("#cccccc"), 1))
                painter.drawLine(x, self.header_height, x, h)
                painter.setPen(QColor("#666666"))

            # Move to next month
            if current.month == 12:
                current = current.replace(year=current.year + 1, month=1)
            else:
                current = current.replace(month=current.month + 1)

        # Draw week tick marks and day numbers
        font.setPixelSize(9)
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(QColor("#999999"))

        # Find first Sunday on or after start_date
        days_until_sunday = (6 - self.start_date.weekday()) % 7
        current_week = self.start_date + timedelta(days=days_until_sunday)

        while current_week <= self.end_date:
            x = self._date_to_x(current_week)
            if x and self.left_margin <= x <= w - self.right_margin:
                # Draw small tick mark
                painter.setPen(QPen(QColor("#e0e0e0"), 1))
                painter.drawLine(x, self.header_height - 8, x, self.header_height)

                # Draw day number
                painter.setPen(QColor("#999999"))
                day_str = str(current_week.day)
                painter.drawText(x - 4, self.header_height - 10, day_str)

                # Light vertical guideline
                painter.setPen(QPen(QColor("#f0f0f0"), 1))
                painter.drawLine(x, self.header_height, x, h)

            current_week += timedelta(days=7)

        # Draw today line (on top)
        today_x = self._date_to_x(today)
        if today_x and self.left_margin <= today_x <= w - self.right_margin:
            painter.setPen(QPen(QColor("#dc3545"), 2))
            painter.drawLine(today_x, self.header_height, today_x, h)

            # Today label with date
            painter.setPen(QColor("#dc3545"))
            font.setPixelSize(9)
            font.setBold(True)
            painter.setFont(font)
            today_str = f"Today ({today.strftime('%m/%d')})"
            painter.drawText(today_x - 25, self.header_height - 10, today_str)

        # Draw items
        font.setPixelSize(12)
        font.setBold(False)
        painter.setFont(font)

        for i, item in enumerate(self.items):
            y = self.header_height + i * self.row_height + 8

            # Row background (alternating)
            if i % 2 == 0:
                painter.fillRect(0, y - 8, w, self.row_height, QColor("#fafafa"))

            # Item number and title on left
            painter.setPen(QColor("#1a1a2e"))
            title_text = f"#{item['num']}: {item['title']}"
            if len(title_text) > 35:
                title_text = title_text[:32] + "..."
            painter.drawText(10, y + 12, title_text)

            # Draw bar - use indicator color (status-based, like HTML version)
            indicator = item.get('indicator', 'Not Started')
            color = QColor(INDICATOR_COLORS.get(indicator, "#6c757d"))

            start_x = self._date_to_x(item.get('start'))
            end_x = self._date_to_x(item.get('end') or item.get('deadline'))

            if start_x and end_x and start_x < end_x:
                # Draw bar
                bar_y = y + 4
                bar_h = self.row_height - 16

                path = QPainterPath()
                path.addRoundedRect(start_x, bar_y, end_x - start_x, bar_h, 4, 4)

                # Fill based on completion
                pct = item.get('pct', 0) / 100
                if pct > 0:
                    # Completed portion (solid)
                    completed_width = int((end_x - start_x) * pct)
                    painter.fillPath(path, QColor(color.red(), color.green(), color.blue(), 80))

                    if completed_width > 0:
                        completed_path = QPainterPath()
                        completed_path.addRoundedRect(start_x, bar_y, completed_width, bar_h, 4, 4)
                        painter.fillPath(completed_path, color)
                else:
                    painter.fillPath(path, QColor(color.red(), color.green(), color.blue(), 80))

                # Border
                painter.setPen(QPen(color, 1))
                painter.drawPath(path)

            elif item.get('deadline'):
                # Just a deadline marker (diamond)
                deadline_x = self._date_to_x(item['deadline'])
                if deadline_x:
                    marker_y = y + self.row_height // 2 - 4
                    painter.setBrush(QBrush(color))
                    painter.setPen(Qt.NoPen)

                    # Diamond shape
                    points = [
                        (deadline_x, marker_y),
                        (deadline_x + 6, marker_y + 6),
                        (deadline_x, marker_y + 12),
                        (deadline_x - 6, marker_y + 6),
                    ]
                    from PySide6.QtGui import QPolygon
                    from PySide6.QtCore import QPoint
                    polygon = QPolygon([QPoint(int(p[0]), int(p[1])) for p in points])
                    painter.drawPolygon(polygon)

            elif item.get('start'):
                # Start-only marker (circle)
                start_marker_x = self._date_to_x(item['start'])
                if start_marker_x:
                    marker_y = y + self.row_height // 2
                    painter.setBrush(QBrush(color))
                    painter.setPen(Qt.NoPen)
                    painter.drawEllipse(start_marker_x - 5, marker_y - 5, 10, 10)

        # Draw left margin separator
        painter.setPen(QPen(QColor("#e0e0e0"), 1))
        painter.drawLine(self.left_margin - 10, 0, self.left_margin - 10, h)


class TimelineView(QScrollArea):
    """Timeline view showing items on a Gantt-style chart"""

    # Signal emitted when item is double-clicked (item_num)
    item_clicked = Signal(int)

    def __init__(self, project_data: Optional[ProjectData], parent=None):
        super().__init__(parent)
        self.project_data = project_data

        # Filter state
        self.filter_type = ""
        self.filter_assigned = ""
        self.filter_workstream = ""
        self.filter_status = ""  # Default: All Active
        self.sort_by = "start"

        # Reference to chart card for easy replacement
        self.chart_card = None

        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
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
        # Title
        self.title_label = QLabel("Timeline")
        self.title_label.setStyleSheet("font-size: 28px; font-weight: bold; color: #1a1a2e; background: transparent;")
        self.main_layout.addWidget(self.title_label)

        # Filter controls card
        filter_card = QFrame()
        filter_card.setStyleSheet("QFrame { background: white; border-radius: 8px; padding: 8px; }")
        add_shadow(filter_card, blur=10, offset=1)

        filter_layout = QHBoxLayout(filter_card)
        filter_layout.setContentsMargins(16, 12, 16, 12)
        filter_layout.setSpacing(24)

        # Build filter options from data
        types, assigned_list, workstreams = self._get_filter_options()

        # Type filter
        type_layout = QHBoxLayout()
        type_layout.setSpacing(8)
        type_lbl = QLabel("Type:")
        type_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #1a1a2e; background: transparent;")
        type_layout.addWidget(type_lbl)
        self.type_combo = QComboBox()
        self.type_combo.addItem("All", "")
        for t in types:
            self.type_combo.addItem(t, t)
        self.type_combo.setStyleSheet("font-size: 12px; min-width: 100px;")
        self.type_combo.currentIndexChanged.connect(self._on_filter_changed)
        type_layout.addWidget(self.type_combo)
        filter_layout.addLayout(type_layout)

        # Assigned filter
        assigned_layout = QHBoxLayout()
        assigned_layout.setSpacing(8)
        assigned_lbl = QLabel("Assigned:")
        assigned_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #1a1a2e; background: transparent;")
        assigned_layout.addWidget(assigned_lbl)
        self.assigned_combo = QComboBox()
        self.assigned_combo.addItem("All", "")
        for a in assigned_list:
            self.assigned_combo.addItem(a, a)
        self.assigned_combo.setStyleSheet("font-size: 12px; min-width: 120px;")
        self.assigned_combo.currentIndexChanged.connect(self._on_filter_changed)
        assigned_layout.addWidget(self.assigned_combo)
        filter_layout.addLayout(assigned_layout)

        # Workstream filter
        ws_layout = QHBoxLayout()
        ws_layout.setSpacing(8)
        ws_lbl = QLabel("Workstream:")
        ws_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #1a1a2e; background: transparent;")
        ws_layout.addWidget(ws_lbl)
        self.workstream_combo = QComboBox()
        self.workstream_combo.addItem("All", "")
        for w in workstreams:
            self.workstream_combo.addItem(w, w)
        self.workstream_combo.setStyleSheet("font-size: 12px; min-width: 120px;")
        self.workstream_combo.currentIndexChanged.connect(self._on_filter_changed)
        ws_layout.addWidget(self.workstream_combo)
        filter_layout.addLayout(ws_layout)

        # Status filter
        status_layout = QHBoxLayout()
        status_layout.setSpacing(8)
        status_lbl = QLabel("Status:")
        status_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #1a1a2e; background: transparent;")
        status_layout.addWidget(status_lbl)
        self.status_combo = QComboBox()
        self.status_combo.addItem("All Active", "")
        self.status_combo.addItem("All Open", "all_open")
        self.status_combo.addItem("All", "all")
        self.status_combo.addItem("Critical", "critical")
        self.status_combo.addItem("Warning", "warning")
        self.status_combo.addItem("In Progress", "in_progress")
        self.status_combo.setStyleSheet("font-size: 12px; min-width: 100px;")
        self.status_combo.currentIndexChanged.connect(self._on_filter_changed)
        status_layout.addWidget(self.status_combo)
        filter_layout.addLayout(status_layout)

        # Sort control
        sort_layout = QHBoxLayout()
        sort_layout.setSpacing(8)
        sort_lbl = QLabel("Sort:")
        sort_lbl.setStyleSheet("font-size: 12px; font-weight: 600; color: #1a1a2e; background: transparent;")
        sort_layout.addWidget(sort_lbl)
        self.sort_combo = QComboBox()
        self.sort_combo.addItem("Start Date", "start")
        self.sort_combo.addItem("Finish Date", "finish")
        self.sort_combo.addItem("Item #", "item_num")
        self.sort_combo.setStyleSheet("font-size: 12px; min-width: 100px;")
        self.sort_combo.currentIndexChanged.connect(self._on_filter_changed)
        sort_layout.addWidget(self.sort_combo)
        filter_layout.addLayout(sort_layout)

        filter_layout.addStretch()
        self.main_layout.addWidget(filter_card)

        # Build timeline data with filters
        timeline_items = self._build_timeline_items()

        # Update title with count
        self.title_label.setText(f"Timeline ({len(timeline_items)} items)")

        # Legend - show key indicator colors (status-based, like HTML)
        legend_layout = QHBoxLayout()
        legend_layout.setSpacing(16)

        # Key indicators to show in legend (matching HTML)
        legend_items = [
            ("Beyond Deadline", INDICATOR_COLORS.get("Beyond Deadline!!!", "#b91c1c")),
            ("Late/Overdue", INDICATOR_COLORS.get("Overdue", "#dc2626")),
            ("Trending Late", INDICATOR_COLORS.get("Trending Late!", "#d97706")),
            ("Due Soon", INDICATOR_COLORS.get("Due Soon", "#eab308")),
            ("In Progress", INDICATOR_COLORS.get("In Progress", "#ca8a04")),
            ("Not Started", INDICATOR_COLORS.get("Not Started", "#d1d5db")),
        ]

        for name, color in legend_items:
            item_layout = QHBoxLayout()
            item_layout.setSpacing(6)

            color_box = QFrame()
            color_box.setFixedSize(14, 14)
            color_box.setStyleSheet(f"background: {color}; border-radius: 3px;")
            item_layout.addWidget(color_box)

            label = QLabel(name)
            label.setStyleSheet("font-size: 11px; color: #666; background: transparent;")
            item_layout.addWidget(label)

            legend_layout.addLayout(item_layout)

        # Today marker in legend
        today_layout = QHBoxLayout()
        today_layout.setSpacing(6)
        today_line = QFrame()
        today_line.setFixedSize(14, 2)
        today_line.setStyleSheet("background: #dc3545;")
        today_layout.addWidget(today_line)
        today_label = QLabel("Today")
        today_label.setStyleSheet("font-size: 11px; color: #dc3545; background: transparent;")
        today_layout.addWidget(today_label)
        legend_layout.addLayout(today_layout)

        legend_layout.addStretch()
        self.main_layout.addLayout(legend_layout)

        # Chart card - store reference for filter updates
        self.chart_card = QFrame()
        self.chart_card.setStyleSheet("QFrame { background: white; border-radius: 8px; }")
        add_shadow(self.chart_card)

        card_layout = QVBoxLayout(self.chart_card)
        card_layout.setContentsMargins(0, 0, 0, 0)

        # Use pre-built timeline data
        if timeline_items:
            chart = TimelineChart(timeline_items)
            chart.item_clicked.connect(self.item_clicked.emit)
            card_layout.addWidget(chart)
        else:
            no_data = QLabel("No items with dates to display")
            no_data.setStyleSheet("font-size: 14px; color: #666; padding: 40px; background: transparent;")
            no_data.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(no_data)

        self.main_layout.addWidget(self.chart_card)
        self.main_layout.addStretch()

    def _get_filter_options(self):
        """Get unique values for filter dropdowns"""
        if not self.project_data:
            return [], [], []

        types = set()
        assigned = set()
        workstreams = set()

        for item in self.project_data.items:
            if item.type:
                types.add(item.type)
            if item.assigned_to:
                assigned.add(item.assigned_to)
            if item.workstream:
                workstreams.add(item.workstream)

        return sorted(types), sorted(assigned), sorted(workstreams)

    def _on_filter_changed(self):
        """Handle filter/sort changes - rebuild the chart"""
        # Get current filter values
        self.filter_type = self.type_combo.currentData() or ""
        self.filter_assigned = self.assigned_combo.currentData() or ""
        self.filter_workstream = self.workstream_combo.currentData() or ""
        self.filter_status = self.status_combo.currentData() or ""
        self.sort_by = self.sort_combo.currentData() or "start"

        # Rebuild just the chart area
        self._rebuild_chart()

    def _rebuild_chart(self):
        """Rebuild the chart with current filters"""
        # Remove the old chart card using stored reference
        if self.chart_card:
            self.main_layout.removeWidget(self.chart_card)
            self.chart_card.deleteLater()

        # Build new timeline data
        timeline_items = self._build_timeline_items()

        # Update title count
        self.title_label.setText(f"Timeline ({len(timeline_items)} items)")

        # Create new chart card
        self.chart_card = QFrame()
        self.chart_card.setStyleSheet("QFrame { background: white; border-radius: 8px; }")
        add_shadow(self.chart_card)

        card_layout = QVBoxLayout(self.chart_card)
        card_layout.setContentsMargins(0, 0, 0, 0)

        if timeline_items:
            chart = TimelineChart(timeline_items)
            chart.item_clicked.connect(self.item_clicked.emit)
            card_layout.addWidget(chart)
        else:
            no_data = QLabel("No items match the current filters")
            no_data.setStyleSheet("font-size: 14px; color: #666; padding: 40px; background: transparent;")
            no_data.setAlignment(Qt.AlignCenter)
            card_layout.addWidget(no_data)

        # Insert before the stretch
        self.main_layout.insertWidget(self.main_layout.count() - 1, self.chart_card)

    def _build_timeline_items(self):
        """Build list of items with date info for timeline, applying filters"""
        if not self.project_data:
            return []

        items = []
        completed_indicators = ["Completed", "Completed Recently", "Done", "Closed", "Cancelled", "Resolved"]

        for item in self.project_data.items:
            # Status filter logic
            if self.filter_status == "all":
                # Show everything including Draft
                pass
            elif self.filter_status == "all_open":
                # Show everything except Draft (includes Completed)
                if item.indicator == "Draft":
                    continue
            elif self.filter_status == "critical":
                severity = INDICATOR_SEVERITY.get(item.indicator, "")
                if severity != "critical":
                    continue
            elif self.filter_status == "warning":
                severity = INDICATOR_SEVERITY.get(item.indicator, "")
                if severity != "warning":
                    continue
            elif self.filter_status == "in_progress":
                severity = INDICATOR_SEVERITY.get(item.indicator, "")
                if severity not in ("active", "upcoming"):
                    continue
            else:
                # Default: All Active - exclude Draft and Completed
                if item.indicator in ["Draft"] + completed_indicators:
                    continue

            # Apply type filter
            if self.filter_type and item.type != self.filter_type:
                continue

            # Apply assigned filter
            if self.filter_assigned and item.assigned_to != self.filter_assigned:
                continue

            # Apply workstream filter
            if self.filter_workstream and item.workstream != self.filter_workstream:
                continue

            # Must have EITHER start+finish dates (for bar) OR deadline/start (for milestone)
            has_bar_dates = (
                (item.start and not isinstance(item.start, str)) and
                (item.finish and not isinstance(item.finish, str))
            )
            has_deadline = item.deadline and not isinstance(item.deadline, str)
            has_start_only = item.start and not isinstance(item.start, str)

            if not has_bar_dates and not has_deadline and not has_start_only:
                continue

            timeline_item = {
                'num': item.item_num,
                'title': item.title or "Untitled",
                'type': item.type or "Plan Item",
                'indicator': item.indicator or "Not Started",
                'assigned': item.assigned_to or "",
                'workstream': item.workstream or "",
                'start': item.start if item.start and not isinstance(item.start, str) else None,
                'end': item.finish if item.finish and not isinstance(item.finish, str) else None,
                'deadline': item.deadline if item.deadline and not isinstance(item.deadline, str) else None,
                'pct': item.percent_complete or 0,
                'description': item.description or "",
                'notes': item.notes or "",
            }

            items.append(timeline_item)

        # Apply sorting
        if self.sort_by == "finish":
            items.sort(key=lambda x: x.get('end') or date.max)
        elif self.sort_by == "item_num":
            items.sort(key=lambda x: x.get('num') or 0)
        else:
            items.sort(key=lambda x: x.get('start') or date.max)

        return items[:50]  # Increased limit since we have filters

    def refresh(self, project_data, budget):
        """Refresh with new data"""
        self.project_data = project_data

        # Clear and rebuild
        while self.main_layout.count():
            child = self.main_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout(child.layout())

        self._build_ui()

    def _clear_layout(self, layout):
        """Recursively clear a layout"""
        while layout.count():
            child = layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()
            elif child.layout():
                self._clear_layout(child.layout())
