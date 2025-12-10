"""
Dashboard View - PySide6 Version
Matches HTML project viewer layout exactly.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QSizePolicy, QGraphicsDropShadowEffect,
    QGridLayout
)
from PySide6.QtCore import Qt, QSize, Signal
from PySide6.QtGui import QFont, QColor, QPainter, QPen, QBrush, QPainterPath
from typing import Optional
from datetime import date, timedelta

from src.core.models import ProjectData
from src.core.budget import CalculatedBudget, format_currency
from src.core.indicators import get_indicator_config
from src.ui_qt.styles import COLORS, TYPE_COLORS, INDICATOR_COLORS


def add_shadow(widget, blur=15, offset=2, color=QColor(0, 0, 0, 25)):
    """Add drop shadow to a widget"""
    shadow = QGraphicsDropShadowEffect()
    shadow.setBlurRadius(blur)
    shadow.setOffset(0, offset)
    shadow.setColor(color)
    widget.setGraphicsEffect(shadow)


class Card(QFrame):
    """Styled card widget with shadow"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("card")
        self.setStyleSheet("""
            QFrame#card {
                background: white;
                border-radius: 8px;
            }
        """)
        add_shadow(self)


class HeaderCard(Card):
    """Header card with large value"""

    def __init__(self, value: str, label: str, sublabel: str = "", color: str = "#1a1a2e",
                 show_status_pill: bool = False, parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(24, 20, 24, 20)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignCenter)

        # Value
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet(f"""
            font-size: 48px;
            font-weight: bold;
            color: {color};
            background: transparent;
        """)
        layout.addWidget(value_label)

        # Label
        label_widget = QLabel(label)
        label_widget.setAlignment(Qt.AlignCenter)
        label_widget.setStyleSheet("font-size: 12px; color: #666666; background: transparent;")
        layout.addWidget(label_widget)

        # Status pill (green oval for "On Track", etc.)
        if show_status_pill and sublabel:
            pill = QLabel(sublabel)
            pill.setAlignment(Qt.AlignCenter)
            pill.setStyleSheet(f"""
                background: {color};
                color: white;
                padding: 4px 16px;
                border-radius: 12px;
                font-size: 11px;
                font-weight: bold;
            """)
            layout.addWidget(pill, alignment=Qt.AlignCenter)
        elif sublabel:
            sub_widget = QLabel(sublabel)
            sub_widget.setAlignment(Qt.AlignCenter)
            sub_widget.setStyleSheet(f"font-size: 11px; color: #666666; background: transparent;")
            layout.addWidget(sub_widget)


class StatCard(Card):
    """Stat card with colored value"""

    # Signal emitted when card is clicked (filter_type, filter_value)
    clicked = Signal(str, str)

    def __init__(self, value: str, label: str, color: str, filter_type: str = "", filter_value: str = "", parent=None):
        super().__init__(parent)

        self.filter_type = filter_type
        self.filter_value = filter_value

        # Make clickable if filter is set
        if filter_type:
            self.setCursor(Qt.PointingHandCursor)
            self.setStyleSheet("""
                QFrame#card {
                    background: white;
                    border-radius: 8px;
                }
                QFrame#card:hover {
                    background: #f8f9fa;
                }
            """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignCenter)

        # Value
        value_label = QLabel(value)
        value_label.setAlignment(Qt.AlignCenter)
        value_label.setStyleSheet(f"""
            font-size: 32px;
            font-weight: bold;
            color: {color};
            background: transparent;
        """)
        layout.addWidget(value_label)

        # Label
        label_widget = QLabel(label)
        label_widget.setAlignment(Qt.AlignCenter)
        label_widget.setStyleSheet("font-size: 12px; color: #666666; background: transparent;")
        layout.addWidget(label_widget)

    def mousePressEvent(self, event):
        if self.filter_type:
            self.clicked.emit(self.filter_type, self.filter_value)
        super().mousePressEvent(event)


class DonutChart(QWidget):
    """SVG-style donut chart"""

    def __init__(self, data: list, center_value: str, center_label: str, parent=None):
        super().__init__(parent)
        self.data = data  # [(label, count, color), ...]
        self.center_value = center_value
        self.center_label = center_label
        self.setMinimumSize(180, 180)
        self.setMaximumSize(180, 180)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        # Calculate total
        total = sum(d[1] for d in self.data)
        if total == 0:
            return

        # Draw donut
        rect = self.rect().adjusted(15, 15, -15, -15)
        start_angle = 90 * 16  # Start at top (Qt uses 1/16 degrees)

        for label, count, color in self.data:
            span_angle = int((count / total) * 360 * 16)

            # Draw arc
            pen = QPen(QColor(color))
            pen.setWidth(25)
            pen.setCapStyle(Qt.FlatCap)
            painter.setPen(pen)
            painter.drawArc(rect, start_angle, -span_angle)

            start_angle -= span_angle

        # Draw center text - position value and label to not overlap
        center_x = self.width() // 2
        center_y = self.height() // 2

        # Draw value (above center)
        painter.setPen(QColor("#1a1a2e"))
        font = QFont()
        font.setPixelSize(32)
        font.setBold(True)
        painter.setFont(font)
        value_rect = self.rect().adjusted(0, -12, 0, -12)
        painter.drawText(value_rect, Qt.AlignCenter, self.center_value)

        # Draw center label (below value)
        font.setPixelSize(12)
        font.setBold(False)
        painter.setFont(font)
        painter.setPen(QColor("#666666"))
        label_rect = self.rect().adjusted(0, 22, 0, 22)
        painter.drawText(label_rect, Qt.AlignCenter, self.center_label)


class LollipopChart(QWidget):
    """Lollipop chart matching HTML design"""

    def __init__(self, data: list, parent=None):
        super().__init__(parent)
        # data: [(name, active, backlog), ...]
        self.data = data
        self.setMinimumHeight(len(data) * 40 + 40)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if not self.data:
            return

        # Calculate max for scaling
        max_total = max(d[1] + d[2] for d in self.data) if self.data else 1

        # Layout
        left_margin = 120
        right_margin = 40
        available_width = self.width() - left_margin - right_margin
        row_height = 40
        dot_radius = 11

        for i, (name, active, backlog) in enumerate(self.data):
            y = i * row_height + 20
            total = active + backlog

            # Name on left
            painter.setPen(QColor("#1a1a2e"))
            font = QFont()
            font.setPixelSize(12)
            painter.setFont(font)
            name_display = name if len(name) <= 15 else name[:12] + "..."
            painter.drawText(0, y - 6, left_margin - 10, 20, Qt.AlignRight | Qt.AlignVCenter, name_display)

            # Background line (full width, light gray)
            painter.setPen(QPen(QColor("#e9ecef"), 3))
            painter.drawLine(left_margin, y, left_margin + available_width, y)

            # Stem line (from start to total position)
            if total > 0:
                total_x = left_margin + int((total / max_total) * (available_width - 20))
                painter.setPen(QPen(QColor("#6c757d"), 2))
                painter.drawLine(left_margin, y, total_x, y)

                # Backlog dot (white with gray border) at total position
                painter.setBrush(QBrush(QColor("white")))
                painter.setPen(QPen(QColor("#6c757d"), 2))
                painter.drawEllipse(total_x - dot_radius, y - dot_radius, dot_radius * 2, dot_radius * 2)

                # Number in backlog dot
                painter.setPen(QColor("#6c757d"))
                font.setPixelSize(9)
                font.setBold(True)
                painter.setFont(font)
                painter.drawText(total_x - dot_radius, y - dot_radius, dot_radius * 2, dot_radius * 2,
                               Qt.AlignCenter, str(total))

            # Active dot (blue filled) at active position
            if active > 0:
                active_x = left_margin + int((active / max_total) * (available_width - 20))
                painter.setBrush(QBrush(QColor("#0d6efd")))
                painter.setPen(QPen(QColor("white"), 1.5))
                painter.drawEllipse(active_x - dot_radius, y - dot_radius, dot_radius * 2, dot_radius * 2)

                # Number in active dot
                painter.setPen(QColor("white"))
                font.setPixelSize(9)
                font.setBold(True)
                painter.setFont(font)
                painter.drawText(active_x - dot_radius, y - dot_radius, dot_radius * 2, dot_radius * 2,
                               Qt.AlignCenter, str(active))

        # Legend at bottom
        legend_y = len(self.data) * row_height + 10
        painter.setPen(QColor("#666666"))
        font.setPixelSize(11)
        font.setBold(False)
        painter.setFont(font)

        # Active legend
        painter.setBrush(QBrush(QColor("#0d6efd")))
        painter.setPen(Qt.NoPen)
        painter.drawEllipse(left_margin, legend_y, 12, 12)
        painter.setPen(QColor("#666666"))
        painter.drawText(left_margin + 18, legend_y, 60, 12, Qt.AlignLeft | Qt.AlignVCenter, "Active")

        # Backlog legend
        painter.setBrush(QBrush(QColor("white")))
        painter.setPen(QPen(QColor("#6c757d"), 2))
        painter.drawEllipse(left_margin + 80, legend_y, 12, 12)
        painter.setPen(QColor("#666666"))
        painter.drawText(left_margin + 98, legend_y, 60, 12, Qt.AlignLeft | Qt.AlignVCenter, "Backlog")


class TreemapWidget(QWidget):
    """Treemap widget matching HTML flex-wrap layout"""

    def __init__(self, data: list, parent=None):
        super().__init__(parent)
        # data: [(name, count, color), ...]
        self.data = data
        self.setMinimumHeight(200)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if not self.data:
            return

        # Layout similar to HTML flex-wrap
        # Row 1: 2 largest, Row 2: next 3-4, Row 3: remaining
        n = len(self.data)
        gap = 3
        w = self.width()
        h = self.height()

        row1 = self.data[:2] if n >= 2 else self.data
        row2 = self.data[2:5] if n > 2 else []
        row3 = self.data[5:9] if n > 5 else []

        # Heights
        h1 = int(h * 0.4) if row1 else 0
        h2 = int(h * 0.32) if row2 else 0
        h3 = h - h1 - h2 - gap * 2 if row3 else 0

        if not row3:
            h1 = int(h * 0.55)
            h2 = h - h1 - gap
        if not row2:
            h1 = h

        y = 0

        # Draw Row 1
        if row1:
            row_total = sum(d[1] for d in row1)
            x = 0
            for name, count, color in row1:
                item_w = int((count / row_total) * w) - gap if row_total > 0 else w // 2
                self._draw_item(painter, x, y, item_w, h1, name, count, color)
                x += item_w + gap
            y += h1 + gap

        # Draw Row 2
        if row2:
            row_total = sum(d[1] for d in row2)
            x = 0
            for name, count, color in row2:
                item_w = int((count / row_total) * w) - gap if row_total > 0 else w // 3
                self._draw_item(painter, x, y, item_w, h2, name, count, color)
                x += item_w + gap
            y += h2 + gap

        # Draw Row 3
        if row3:
            row_total = sum(d[1] for d in row3)
            x = 0
            for name, count, color in row3:
                item_w = int((count / row_total) * w) - gap if row_total > 0 else w // 4
                self._draw_item(painter, x, y, item_w, h3, name, count, color)
                x += item_w + gap

    def _draw_item(self, painter, x, y, w, h, name, count, color):
        """Draw a single treemap item"""
        # Rounded rect
        path = QPainterPath()
        path.addRoundedRect(x, y, w, h, 4, 4)
        painter.fillPath(path, QColor(color))

        # Count (larger, above name)
        painter.setPen(QColor("white"))
        font = QFont()
        font.setPixelSize(min(20, h // 3))
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(x, y, w, h - 10, Qt.AlignCenter, str(count))

        # Name (smaller, below count)
        font.setPixelSize(min(11, h // 5))
        font.setBold(False)
        painter.setFont(font)
        name_display = name if len(name) <= 12 else name[:10] + "..."
        painter.drawText(x, y + 15, w, h, Qt.AlignCenter, name_display)


class DashboardView(QScrollArea):
    """Dashboard view with all charts and metrics"""

    # Signal to navigate to All Items with filter (filter_type, filter_value)
    navigate_to_items = Signal(str, str)

    def __init__(self, project_data: Optional[ProjectData], budget: Optional[CalculatedBudget], parent=None):
        super().__init__(parent)

        self.project_data = project_data
        self.budget = budget

        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet("QScrollArea { border: none; background: #f5f5f5; }")

        # Container
        container = QWidget()
        container.setStyleSheet("background: #f5f5f5;")
        self.setWidget(container)

        self.main_layout = QVBoxLayout(container)
        self.main_layout.setContentsMargins(24, 24, 24, 24)
        self.main_layout.setSpacing(20)

        self._build_ui()

    def _build_ui(self):
        """Build the dashboard UI"""
        # Title
        if self.project_data:
            title_text = self.project_data.metadata.project_name
        else:
            title_text = "BRAID Log"

        title = QLabel(title_text)
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #1a1a2e;")
        self.main_layout.addWidget(title)

        if not self.project_data:
            no_data = QLabel("No project data loaded")
            no_data.setStyleSheet("font-size: 14px; color: #666666;")
            self.main_layout.addWidget(no_data)
            self.main_layout.addStretch()
            return

        items = self.project_data.items

        # === Header Cards Row ===
        header_layout = QHBoxLayout()
        header_layout.setSpacing(12)

        # Health Score
        health_score, health_class, health_status = self._calculate_health_score(items)
        health_color = {"critical": "#dc3545", "warning": "#ffc107", "good": "#28a745"}[health_class]
        header_layout.addWidget(HeaderCard(str(health_score), "Project Health", health_status, health_color, show_status_pill=True))

        # Budget
        if self.budget:
            m = self.budget.metrics
            budget_color = "#28a745" if m.budget_remaining > 0 else "#dc3545"
            header_layout.addWidget(HeaderCard(
                format_currency(m.budget_total), "Total Budget",
                f"{format_currency(m.burn_to_date)} burned ({m.burn_pct:.0f}%)", budget_color
            ))
        else:
            header_layout.addWidget(HeaderCard("—", "Total Budget", "No data"))

        # Velocity
        current, prior = self._calculate_velocity(items)
        arrow = "→" if current == prior else ("↑" if current > prior else "↓")
        vel_color = "#28a745" if current >= prior else "#dc3545"
        header_layout.addWidget(HeaderCard(
            f"{current} {arrow}", "Completed (14d)",
            f"vs {prior} prior period", vel_color
        ))

        self.main_layout.addLayout(header_layout)

        # === Stats Row ===
        stats_layout = QHBoxLayout()
        stats_layout.setSpacing(8)

        counts = self._count_by_status(items)

        # Create clickable stat cards with filter parameters
        critical_card = StatCard(str(counts["critical"]), "Critical", "#dc3545", "status", "Critical")
        critical_card.clicked.connect(self.navigate_to_items.emit)
        stats_layout.addWidget(critical_card)

        warning_card = StatCard(str(counts["warning"]), "Warning", "#ffc107", "status", "Warning")
        warning_card.clicked.connect(self.navigate_to_items.emit)
        stats_layout.addWidget(warning_card)

        active_card = StatCard(str(counts["active"]), "Active", "#0d6efd", "status", "Active")
        active_card.clicked.connect(self.navigate_to_items.emit)
        stats_layout.addWidget(active_card)

        completed_card = StatCard(str(counts["completed"]), "Completed", "#28a745", "status", "Completed")
        completed_card.clicked.connect(self.navigate_to_items.emit)
        stats_layout.addWidget(completed_card)

        total_card = StatCard(str(counts["total"]), "Total Items", "#6c757d", "status", "All")
        total_card.clicked.connect(self.navigate_to_items.emit)
        stats_layout.addWidget(total_card)

        self.main_layout.addLayout(stats_layout)

        # === Content Row 1: Open Items by Type + Upcoming Deadlines ===
        row1_layout = QHBoxLayout()
        row1_layout.setSpacing(24)

        # Open Items by Type
        type_card = self._build_type_card(items)
        row1_layout.addWidget(type_card, 1)

        # Upcoming Deadlines
        deadline_card = self._build_deadline_card(items)
        row1_layout.addWidget(deadline_card, 1)

        self.main_layout.addLayout(row1_layout)

        # === Content Row 2: Assignees + Workstream ===
        row2_layout = QHBoxLayout()
        row2_layout.setSpacing(24)

        # Items by Assigned To
        assignee_card = self._build_assignee_card(items)
        row2_layout.addWidget(assignee_card, 1)

        # Items by Workstream
        workstream_card = self._build_workstream_card(items)
        row2_layout.addWidget(workstream_card, 1)

        self.main_layout.addLayout(row2_layout)

        self.main_layout.addStretch()

    def _build_type_card(self, items):
        """Build Open Items by Type card"""
        card = Card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Title
        title = QLabel("Open Items by Type")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1a1a2e; background: transparent;")
        layout.addWidget(title)

        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #e0e0e0;")
        layout.addWidget(sep)

        # Content: Donut + Legend
        content = QHBoxLayout()
        content.setSpacing(24)

        # Count open items by type
        completed_indicators = ["Completed", "Completed Recently", "Done", "Closed", "Cancelled", "Resolved"]
        open_items = [i for i in items if i.indicator not in completed_indicators]

        by_type = {}
        for item in open_items:
            t = item.type or "Plan Item"
            by_type[t] = by_type.get(t, 0) + 1

        sorted_types = sorted(by_type.items(), key=lambda x: -x[1])

        # Donut chart
        donut_data = [(t, c, TYPE_COLORS.get(t, "#6c757d")) for t, c in sorted_types]
        donut = DonutChart(donut_data, str(len(open_items)), "Open")
        content.addWidget(donut)

        # Legend
        legend_layout = QVBoxLayout()
        legend_layout.setSpacing(8)

        for type_name, count in sorted_types:
            row = QHBoxLayout()
            row.setSpacing(8)

            # Color box
            color_box = QFrame()
            color_box.setFixedSize(14, 14)
            color_box.setStyleSheet(f"background: {TYPE_COLORS.get(type_name, '#6c757d')}; border-radius: 3px;")
            row.addWidget(color_box)

            # Name
            name_label = QLabel(type_name)
            name_label.setStyleSheet("font-size: 12px; color: #1a1a2e; background: transparent;")
            row.addWidget(name_label)

            # Count
            count_label = QLabel(str(count))
            count_label.setStyleSheet("font-size: 12px; font-weight: bold; color: #1a1a2e; background: transparent;")
            row.addWidget(count_label)

            row.addStretch()
            legend_layout.addLayout(row)

        legend_layout.addStretch()
        content.addLayout(legend_layout)

        layout.addLayout(content)
        return card

    def _build_deadline_card(self, items):
        """Build Upcoming Deadlines card"""
        card = Card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Title
        title = QLabel("Upcoming Deadlines")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1a1a2e; background: transparent;")
        layout.addWidget(title)

        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #e0e0e0;")
        layout.addWidget(sep)

        # Get deadline items
        today = date.today()
        thirty_days = today + timedelta(days=30)
        completed_indicators = ["Completed", "Completed Recently", "Done", "Closed", "Cancelled", "Resolved"]

        deadline_items = []
        for item in items:
            if not item.deadline or item.indicator in completed_indicators:
                continue
            if isinstance(item.deadline, str):
                continue
            if item.deadline <= thirty_days:
                days_until = (item.deadline - today).days
                deadline_items.append((item, days_until))

        deadline_items.sort(key=lambda x: x[1])
        deadline_items = deadline_items[:5]

        if not deadline_items:
            no_items = QLabel("No upcoming deadlines")
            no_items.setStyleSheet("font-size: 12px; color: #666666; font-style: italic; background: transparent;")
            layout.addWidget(no_items)
        else:
            for item, days_until in deadline_items:
                row = QHBoxLayout()
                row.setSpacing(12)

                # Title
                title_text = f"#{item.item_num}: {item.title or 'Untitled'}"
                if len(title_text) > 40:
                    title_text = title_text[:37] + "..."
                item_label = QLabel(title_text)
                item_label.setStyleSheet("font-size: 14px; color: #1a1a2e; background: transparent;")
                row.addWidget(item_label, 1)

                # Pill
                if days_until < 0:
                    pill_text = f"{abs(days_until)} days"
                    pill_bg = "#f8d7da"
                    pill_color = "#721c24"
                elif days_until == 0:
                    pill_text = "Today"
                    pill_bg = "#f8d7da"
                    pill_color = "#721c24"
                elif days_until <= 7:
                    pill_text = f"{days_until} days"
                    pill_bg = "#e2e8f0"
                    pill_color = "#475569"
                else:
                    pill_text = f"{days_until} days"
                    pill_bg = "#e2e8f0"
                    pill_color = "#475569"

                pill = QLabel(pill_text)
                pill.setStyleSheet(f"""
                    background: {pill_bg};
                    color: {pill_color};
                    padding: 2px 8px;
                    border-radius: 4px;
                    font-size: 12px;
                """)
                row.addWidget(pill)

                layout.addLayout(row)

        layout.addStretch()
        return card

    def _build_assignee_card(self, items):
        """Build Items by Assigned To card"""
        card = Card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(12)

        # Title
        title = QLabel("Items by Assigned To")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1a1a2e; background: transparent;")
        layout.addWidget(title)

        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #e0e0e0;")
        layout.addWidget(sep)

        # Count by assignee
        completed_indicators = ["Completed", "Completed Recently", "Done", "Closed", "Cancelled", "Resolved"]
        active_indicators = ["Active", "In Progress", "Started"]

        by_assignee = {}
        for item in items:
            if item.indicator in completed_indicators:
                continue
            assignee = item.assigned_to or "Unassigned"
            if assignee not in by_assignee:
                by_assignee[assignee] = {"active": 0, "backlog": 0}
            if item.indicator in active_indicators:
                by_assignee[assignee]["active"] += 1
            else:
                by_assignee[assignee]["backlog"] += 1

        sorted_assignees = sorted(by_assignee.items(), key=lambda x: -(x[1]["active"] + x[1]["backlog"]))[:8]

        # Lollipop chart
        chart_data = [(name, data["active"], data["backlog"]) for name, data in sorted_assignees]
        chart = LollipopChart(chart_data)
        layout.addWidget(chart)

        return card

    def _build_workstream_card(self, items):
        """Build Items by Workstream card"""
        card = Card()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(20, 12, 20, 12)
        layout.setSpacing(8)

        # Title
        title = QLabel("Items by Workstream")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1a1a2e; background: transparent;")
        title.setFixedHeight(24)
        layout.addWidget(title)

        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #e0e0e0;")
        layout.addWidget(sep)

        # Count by workstream
        by_ws = {}
        for item in items:
            ws = item.workstream or "Unassigned"
            by_ws[ws] = by_ws.get(ws, 0) + 1

        sorted_ws = sorted(by_ws.items(), key=lambda x: -x[1])[:9]

        # Treemap colors
        ws_colors = ["#28a745", "#20c997", "#ffc107", "#17a2b8", "#6f42c1", "#fd7e14", "#dc3545", "#6c757d", "#0d6efd"]
        treemap_data = [(ws, count, ws_colors[i % len(ws_colors)]) for i, (ws, count) in enumerate(sorted_ws)]

        treemap = TreemapWidget(treemap_data)
        layout.addWidget(treemap)

        return card

    def _calculate_health_score(self, items):
        """Calculate project health score"""
        counts = self._count_by_status(items)
        active_items = counts["total"] - counts["completed"] - counts.get("draft", 0)

        health_score = 100
        if active_items > 0:
            critical_penalty = (counts["critical"] / active_items) * 60
            warning_penalty = (counts["warning"] / active_items) * 25
            health_score = max(0, round(100 - critical_penalty - warning_penalty))

        if health_score < 50:
            return health_score, "critical", "Needs Attention"
        elif health_score < 75:
            return health_score, "warning", "Some Concerns"
        else:
            return health_score, "good", "On Track"

    def _calculate_velocity(self, items):
        """Calculate completion velocity"""
        today = date.today()
        fourteen_days_ago = today - timedelta(days=14)
        twenty_eight_days_ago = today - timedelta(days=28)

        current_period = 0
        prior_period = 0

        completed_indicators = ["Completed", "Completed Recently", "Done", "Closed", "Resolved"]
        for item in items:
            if item.indicator not in completed_indicators:
                continue
            finish = item.finish
            if not finish or isinstance(finish, str):
                continue
            if fourteen_days_ago <= finish <= today:
                current_period += 1
            elif twenty_eight_days_ago <= finish < fourteen_days_ago:
                prior_period += 1

        return current_period, prior_period

    def _count_by_status(self, items):
        """Count items by status"""
        counts = {"critical": 0, "warning": 0, "active": 0, "completed": 0, "draft": 0, "total": len(items)}

        for item in items:
            indicator = item.indicator or ""
            config = get_indicator_config(indicator)
            if config:
                severity = config.severity
                if severity == "critical":
                    counts["critical"] += 1
                elif severity == "warning":
                    counts["warning"] += 1
                elif severity in ("active", "upcoming"):
                    counts["active"] += 1
                elif severity in ("completed", "done"):
                    counts["completed"] += 1
                elif severity == "draft":
                    counts["draft"] += 1

        return counts

    def refresh(self, project_data, budget):
        """Refresh with new data"""
        self.project_data = project_data
        self.budget = budget

        # Clear and rebuild
        container = self.widget()
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
