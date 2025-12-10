"""
Budget View - PySide6 Version
Shows budget metrics, burn rate chart, and resource breakdown.
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame,
    QScrollArea, QGraphicsDropShadowEffect, QGridLayout,
    QDialog, QPushButton, QSizePolicy
)
from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QColor, QPainter, QPen, QBrush, QFont, QPainterPath
from typing import Optional

from src.core.budget import CalculatedBudget, format_currency, format_currency_full, format_currency_rounded
from src.ui_qt.styles import WARNING_COLOR, SUCCESS_COLOR, DANGER_COLOR, ACCENT_COLOR


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
        self.setStyleSheet("QFrame { background: white; border-radius: 8px; }")
        add_shadow(self)


class MetricCard(Card):
    """Card showing a single metric with label"""

    def __init__(self, value: str, label: str, sublabel: str = "", color: str = "#1a1a2e", parent=None):
        super().__init__(parent)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 16, 20, 16)
        layout.setSpacing(4)
        layout.setAlignment(Qt.AlignCenter)

        # Value
        value_lbl = QLabel(value)
        value_lbl.setAlignment(Qt.AlignCenter)
        value_lbl.setStyleSheet(f"""
            font-size: 28px;
            font-weight: bold;
            color: {color};
            background: transparent;
        """)
        layout.addWidget(value_lbl)

        # Label
        label_lbl = QLabel(label)
        label_lbl.setAlignment(Qt.AlignCenter)
        label_lbl.setStyleSheet("font-size: 12px; color: #666666; background: transparent;")
        layout.addWidget(label_lbl)

        # Sublabel
        if sublabel:
            sub_lbl = QLabel(sublabel)
            sub_lbl.setAlignment(Qt.AlignCenter)
            sub_lbl.setStyleSheet("font-size: 11px; color: #999999; background: transparent;")
            layout.addWidget(sub_lbl)


class BurnProgressBar(QWidget):
    """Visual progress bar showing budget burn"""

    def __init__(self, burn_pct: float, budget_total: float, burn_to_date: float, parent=None):
        super().__init__(parent)
        self.burn_pct = min(burn_pct, 100)
        self.budget_total = budget_total
        self.burn_to_date = burn_to_date
        self.setMinimumHeight(60)
        self.setMaximumHeight(60)

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        w = self.width()
        h = self.height()

        # Bar dimensions
        bar_y = 15
        bar_h = 24

        # Background bar
        bg_path = QPainterPath()
        bg_path.addRoundedRect(0, bar_y, w, bar_h, 4, 4)
        painter.fillPath(bg_path, QColor("#e9ecef"))

        # Filled portion
        if self.burn_pct > 0:
            fill_w = int((self.burn_pct / 100) * w)
            fill_path = QPainterPath()
            fill_path.addRoundedRect(0, bar_y, fill_w, bar_h, 4, 4)

            # Color based on percentage
            if self.burn_pct > 100:
                fill_color = QColor(DANGER_COLOR)   # Red - over budget
            elif self.burn_pct > 85:
                fill_color = QColor(WARNING_COLOR)  # Amber - warning
            else:
                fill_color = QColor(SUCCESS_COLOR)  # Green - healthy

            painter.fillPath(fill_path, fill_color)

        # Percentage label in bar
        painter.setPen(QColor("white" if self.burn_pct > 15 else "#333"))
        font = QFont()
        font.setPixelSize(12)
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(10, bar_y, w - 20, bar_h, Qt.AlignVCenter, f"{self.burn_pct:.0f}% burned")

        # Labels below
        painter.setPen(QColor("#666666"))
        font.setPixelSize(11)
        font.setBold(False)
        painter.setFont(font)

        # Left label
        painter.drawText(0, bar_y + bar_h + 5, w // 2, 15, Qt.AlignLeft,
                         f"Burned: {format_currency_full(self.burn_to_date)}")

        # Right label
        remaining = self.budget_total - self.burn_to_date
        painter.drawText(w // 2, bar_y + bar_h + 5, w // 2, 15, Qt.AlignRight,
                         f"Remaining: {format_currency_full(remaining)}")


class WeeklyBurnChart(QWidget):
    """Dual Y-axis chart: Weekly bars (left), Cumulative/Remaining areas (right)"""

    def __init__(self, weekly_data: list, budget_total: float, parent=None):
        super().__init__(parent)
        self.weekly_data = weekly_data
        self.budget_total = budget_total
        self.setMinimumHeight(220)  # Slightly taller for date labels

    def _calc_rolling_avg(self, window=3):
        """Calculate 3-week rolling average"""
        if not self.weekly_data:
            return []
        avgs = []
        for i, week in enumerate(self.weekly_data):
            start = max(0, i - window + 1)
            costs = [self.weekly_data[j].cost for j in range(start, i + 1)]
            avgs.append(sum(costs) / len(costs))
        return avgs

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)

        if not self.weekly_data:
            painter.setPen(QColor("#666666"))
            painter.drawText(self.rect(), Qt.AlignCenter, "No weekly data available")
            return

        w = self.width()
        h = self.height()

        # Layout - extra right margin for second Y-axis
        left_margin = 60
        right_margin = 70  # More space for cumulative axis title
        top_margin = 25
        bottom_margin = 60  # More space for date labels
        chart_w = w - left_margin - right_margin
        chart_h = h - top_margin - bottom_margin

        # Calculate scales - DUAL Y-AXIS
        max_weekly = max(d.cost for d in self.weekly_data) if self.weekly_data else 1
        max_cumulative = max(self.weekly_data[-1].cumulative, self.budget_total) if self.weekly_data else 1

        # Left axis: Weekly spend (scale to show bars clearly)
        max_y_left = max_weekly * 1.15
        # Right axis: Cumulative/Budget
        max_y_right = max_cumulative * 1.1

        bar_count = len(self.weekly_data)
        bar_width = max(8, min(30, (chart_w - 20) // bar_count - 6))
        bar_spacing = (chart_w - bar_count * bar_width) / (bar_count + 1)

        font = QFont()

        # Draw grid lines
        painter.setPen(QPen(QColor("#e9ecef"), 1))
        for i in range(5):
            y_pos = top_margin + int(i / 4 * chart_h)
            painter.drawLine(left_margin, y_pos, w - right_margin, y_pos)

        # Draw LEFT Y-axis labels (Weekly)
        painter.setPen(QColor(ACCENT_COLOR))
        font.setPixelSize(13)  # Axis title - dashboard standard
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(0, top_margin - 20, left_margin, 16, Qt.AlignCenter, "Weekly $")
        font.setBold(False)
        font.setPixelSize(11)  # Axis labels - readable
        painter.setFont(font)

        for i in range(5):
            y_val = max_y_left * (1 - i / 4)
            y_pos = top_margin + int(i / 4 * chart_h)
            painter.drawText(0, y_pos - 7, left_margin - 5, 14, Qt.AlignRight, format_currency(y_val))

        # Draw RIGHT Y-axis labels (Cumulative)
        painter.setPen(QColor(SUCCESS_COLOR))
        font.setPixelSize(13)  # Axis title - dashboard standard
        font.setBold(True)
        painter.setFont(font)
        painter.drawText(w - right_margin - 10, top_margin - 20, right_margin + 10, 16, Qt.AlignCenter, "Cumulative $")
        font.setBold(False)
        font.setPixelSize(11)  # Axis labels - readable
        painter.setFont(font)

        for i in range(5):
            y_val = max_y_right * (1 - i / 4)
            y_pos = top_margin + int(i / 4 * chart_h)
            painter.drawText(w - right_margin + 5, y_pos - 7, right_margin - 5, 14, Qt.AlignLeft, format_currency(y_val))

        # Draw remaining budget area (green, fading to top)
        if self.budget_total > 0 and len(self.weekly_data) > 1:
            path = QPainterPath()
            # Start from first cumulative point
            first_x = left_margin + bar_spacing + bar_width / 2
            first_cum_y = top_margin + chart_h - int((self.weekly_data[0].cumulative / max_y_right) * chart_h)
            path.moveTo(first_x, first_cum_y)

            # Draw cumulative line (bottom of remaining area)
            for i, week in enumerate(self.weekly_data):
                x = left_margin + bar_spacing + i * (bar_width + bar_spacing) + bar_width / 2
                y = top_margin + chart_h - int((week.cumulative / max_y_right) * chart_h)
                path.lineTo(x, y)

            # Draw up to budget line and back
            last_x = left_margin + bar_spacing + (len(self.weekly_data) - 1) * (bar_width + bar_spacing) + bar_width / 2
            budget_y = top_margin + chart_h - int((self.budget_total / max_y_right) * chart_h)
            path.lineTo(last_x, budget_y)
            path.lineTo(first_x, budget_y)
            path.closeSubpath()

            # Fill with semi-transparent green (remaining budget) - slightly darker
            remaining_color = QColor(34, 139, 76, 70)  # Darker green with alpha
            painter.fillPath(path, remaining_color)

        # Draw cumulative spend area (under the cumulative line)
        if len(self.weekly_data) > 1:
            area_path = QPainterPath()
            first_x = left_margin + bar_spacing + bar_width / 2
            area_path.moveTo(first_x, top_margin + chart_h)

            for i, week in enumerate(self.weekly_data):
                x = left_margin + bar_spacing + i * (bar_width + bar_spacing) + bar_width / 2
                y = top_margin + chart_h - int((week.cumulative / max_y_right) * chart_h)
                area_path.lineTo(x, y)

            last_x = left_margin + bar_spacing + (len(self.weekly_data) - 1) * (bar_width + bar_spacing) + bar_width / 2
            area_path.lineTo(last_x, top_margin + chart_h)
            area_path.closeSubpath()

            # Fill with semi-transparent blue
            painter.fillPath(area_path, QColor(52, 152, 219, 30))

        # Draw bars (weekly cost) - using LEFT axis
        for i, week in enumerate(self.weekly_data):
            x = left_margin + bar_spacing + i * (bar_width + bar_spacing)
            bar_h = int((week.cost / max_y_left) * chart_h) if max_y_left > 0 else 0
            y = top_margin + chart_h - bar_h

            # Bar with slight transparency
            painter.setBrush(QBrush(QColor(77, 171, 247, 200)))
            painter.setPen(QPen(QColor(ACCENT_COLOR), 1))
            painter.drawRoundedRect(int(x), y, bar_width, bar_h, 2, 2)

        # Draw date labels on X-axis
        painter.setPen(QColor("#666666"))
        font.setPixelSize(11)  # Readable date labels
        painter.setFont(font)

        # Show every Nth label to avoid crowding
        label_interval = max(1, len(self.weekly_data) // 6)
        for i, week in enumerate(self.weekly_data):
            if i % label_interval == 0 or i == len(self.weekly_data) - 1:
                x = left_margin + bar_spacing + i * (bar_width + bar_spacing) + bar_width / 2
                date_str = week.week_ending.strftime("%m/%d")
                painter.drawText(int(x) - 22, top_margin + chart_h + 5, 44, 14, Qt.AlignCenter, date_str)

        # Draw cumulative line (using RIGHT axis)
        if len(self.weekly_data) > 1:
            painter.setPen(QPen(QColor(SUCCESS_COLOR), 2))
            points = []
            for i, week in enumerate(self.weekly_data):
                x = left_margin + bar_spacing + i * (bar_width + bar_spacing) + bar_width / 2
                y = top_margin + chart_h - int((week.cumulative / max_y_right) * chart_h)
                points.append((x, y))

            for i in range(len(points) - 1):
                painter.drawLine(int(points[i][0]), int(points[i][1]),
                                 int(points[i + 1][0]), int(points[i + 1][1]))

            # Points
            painter.setBrush(QBrush(QColor(SUCCESS_COLOR)))
            painter.setPen(Qt.NoPen)
            for x, y in points:
                painter.drawEllipse(int(x) - 3, int(y) - 3, 6, 6)

        # Draw 3-week rolling average (using LEFT axis)
        rolling_avg = self._calc_rolling_avg(3)
        if len(rolling_avg) > 1:
            painter.setPen(QPen(QColor(WARNING_COLOR), 2, Qt.DashLine))
            points = []
            for i, avg in enumerate(rolling_avg):
                x = left_margin + bar_spacing + i * (bar_width + bar_spacing) + bar_width / 2
                y = top_margin + chart_h - int((avg / max_y_left) * chart_h)
                points.append((x, y))

            for i in range(len(points) - 1):
                painter.drawLine(int(points[i][0]), int(points[i][1]),
                                 int(points[i + 1][0]), int(points[i + 1][1]))

        # Draw budget line (using RIGHT axis)
        if self.budget_total > 0:
            budget_y = top_margin + chart_h - int((self.budget_total / max_y_right) * chart_h)
            painter.setPen(QPen(QColor(DANGER_COLOR), 2, Qt.DashLine))
            painter.drawLine(left_margin, budget_y, w - right_margin, budget_y)

            # Label
            painter.setPen(QColor(DANGER_COLOR))
            font.setPixelSize(10)
            painter.setFont(font)
            painter.drawText(w - right_margin - 50, budget_y - 12, 50, 12, Qt.AlignRight, "Budget")

        # Legend
        legend_y = h - 22
        painter.setPen(QColor("#666666"))
        font.setPixelSize(12)  # Dashboard-standard legend size
        painter.setFont(font)

        legend_x = left_margin

        # Weekly bars
        painter.setBrush(QBrush(QColor(ACCENT_COLOR)))
        painter.setPen(Qt.NoPen)
        painter.drawRect(legend_x, legend_y, 14, 12)
        painter.setPen(QColor("#666666"))
        painter.drawText(legend_x + 18, legend_y - 1, 55, 14, Qt.AlignLeft, "Weekly")
        legend_x += 75

        # Rolling avg
        painter.setPen(QPen(QColor(WARNING_COLOR), 2, Qt.DashLine))
        painter.drawLine(legend_x, legend_y + 6, legend_x + 18, legend_y + 6)
        painter.setPen(QColor("#666666"))
        painter.drawText(legend_x + 22, legend_y - 1, 55, 14, Qt.AlignLeft, "3wk Avg")
        legend_x += 80

        # Cumulative
        painter.setPen(QPen(QColor(SUCCESS_COLOR), 2))
        painter.drawLine(legend_x, legend_y + 6, legend_x + 18, legend_y + 6)
        painter.setPen(QColor("#666666"))
        painter.drawText(legend_x + 22, legend_y - 1, 75, 14, Qt.AlignLeft, "Cumulative")
        legend_x += 100

        # Remaining
        painter.setBrush(QBrush(QColor(34, 139, 76, 70)))
        painter.setPen(Qt.NoPen)
        painter.drawRect(legend_x, legend_y, 14, 12)
        painter.setPen(QColor("#666666"))
        painter.drawText(legend_x + 18, legend_y - 1, 70, 14, Qt.AlignLeft, "Remaining")


class ExpandedChartDialog(QDialog):
    """Dialog showing enlarged chart view"""

    def __init__(self, weekly_data: list, budget_total: float, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Weekly Burn Chart - Expanded View")
        self.setMinimumSize(900, 600)
        self.resize(1000, 650)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)

        # Title
        title = QLabel("Weekly Burn Trend")
        title.setStyleSheet("font-size: 20px; font-weight: bold; color: #1a1a2e;")
        layout.addWidget(title)

        # Chart (larger)
        chart = WeeklyBurnChart(weekly_data, budget_total)
        chart.setMinimumHeight(450)
        layout.addWidget(chart)

        # Summary stats
        if weekly_data:
            stats_layout = QHBoxLayout()
            stats_layout.setSpacing(30)

            total_spent = weekly_data[-1].cumulative
            avg_weekly = total_spent / len(weekly_data)
            remaining = budget_total - total_spent

            stats = [
                (format_currency_full(total_spent), "Total Spent"),
                (format_currency_full(avg_weekly), "Avg Weekly"),
                (format_currency_full(remaining), "Remaining"),
                (f"{len(weekly_data)}", "Weeks")
            ]

            for value, label in stats:
                stat_widget = QVBoxLayout()
                val_lbl = QLabel(value)
                val_lbl.setStyleSheet("font-size: 20px; font-weight: bold; color: #1a1a2e;")
                val_lbl.setAlignment(Qt.AlignCenter)
                stat_widget.addWidget(val_lbl)

                lbl = QLabel(label)
                lbl.setStyleSheet("font-size: 13px; color: #666;")
                lbl.setAlignment(Qt.AlignCenter)
                stat_widget.addWidget(lbl)

                stats_layout.addLayout(stat_widget)

            stats_layout.addStretch()
            layout.addLayout(stats_layout)

        # Close button
        close_btn = QPushButton("Close")
        close_btn.setStyleSheet("""
            QPushButton {
                background: #1a1a2e;
                color: white;
                border: none;
                padding: 8px 24px;
                border-radius: 4px;
                font-size: 13px;
            }
            QPushButton:hover {
                background: #2a2a4e;
            }
        """)
        close_btn.clicked.connect(self.accept)

        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        btn_layout.addWidget(close_btn)
        layout.addLayout(btn_layout)


class ResourceTable(QFrame):
    """Table showing resource burn breakdown"""

    def __init__(self, resource_data: list, parent=None):
        super().__init__(parent)
        self.setStyleSheet("QFrame { background: white; border-radius: 8px; }")
        add_shadow(self)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(8)

        # Title
        title = QLabel("Resource Breakdown")
        title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1a1a2e; background: transparent;")
        layout.addWidget(title)

        # Separator
        sep = QFrame()
        sep.setFixedHeight(1)
        sep.setStyleSheet("background: #e0e0e0;")
        layout.addWidget(sep)

        if not resource_data:
            no_data = QLabel("No resource data available")
            no_data.setStyleSheet("font-size: 12px; color: #666; font-style: italic; background: transparent;")
            layout.addWidget(no_data)
        else:
            # Header row
            header = QHBoxLayout()
            header.setSpacing(8)

            name_h = QLabel("Resource")
            name_h.setStyleSheet("font-size: 11px; font-weight: bold; color: #666; background: transparent;")
            header.addWidget(name_h, 2)

            hours_h = QLabel("Hours")
            hours_h.setAlignment(Qt.AlignRight)
            hours_h.setStyleSheet("font-size: 11px; font-weight: bold; color: #666; background: transparent;")
            header.addWidget(hours_h, 1)

            cost_h = QLabel("Cost")
            cost_h.setAlignment(Qt.AlignRight)
            cost_h.setStyleSheet("font-size: 11px; font-weight: bold; color: #666; background: transparent;")
            header.addWidget(cost_h, 1)

            layout.addLayout(header)

            # Data rows
            total_cost = sum(r.cost for r in resource_data)
            for res in resource_data[:10]:  # Limit to top 10
                row = QHBoxLayout()
                row.setSpacing(8)

                name = QLabel(res.resource)
                name.setStyleSheet("font-size: 12px; color: #1a1a2e; background: transparent;")
                row.addWidget(name, 2)

                hours = QLabel(f"{res.hours:.1f}")
                hours.setAlignment(Qt.AlignRight)
                hours.setStyleSheet("font-size: 12px; color: #666; background: transparent;")
                row.addWidget(hours, 1)

                cost = QLabel(format_currency_rounded(res.cost))
                cost.setAlignment(Qt.AlignRight)
                cost.setStyleSheet("font-size: 12px; color: #1a1a2e; background: transparent;")
                row.addWidget(cost, 1)

                layout.addLayout(row)

            # Total row
            total_sep = QFrame()
            total_sep.setFixedHeight(1)
            total_sep.setStyleSheet("background: #e0e0e0;")
            layout.addWidget(total_sep)

            total_row = QHBoxLayout()
            total_row.setSpacing(8)

            total_name = QLabel("Total")
            total_name.setStyleSheet("font-size: 12px; font-weight: bold; color: #1a1a2e; background: transparent;")
            total_row.addWidget(total_name, 2)

            total_hours = QLabel(f"{sum(r.hours for r in resource_data):.1f}")
            total_hours.setAlignment(Qt.AlignRight)
            total_hours.setStyleSheet("font-size: 12px; font-weight: bold; color: #666; background: transparent;")
            total_row.addWidget(total_hours, 1)

            total_cost_lbl = QLabel(format_currency_rounded(total_cost))
            total_cost_lbl.setAlignment(Qt.AlignRight)
            total_cost_lbl.setStyleSheet("font-size: 12px; font-weight: bold; color: #1a1a2e; background: transparent;")
            total_row.addWidget(total_cost_lbl, 1)

            layout.addLayout(total_row)


class BudgetView(QScrollArea):
    """Budget view with metrics, charts, and resource breakdown"""

    def __init__(self, budget: Optional[CalculatedBudget], parent=None):
        super().__init__(parent)
        self.budget = budget

        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setStyleSheet("QScrollArea { border: none; background: #f5f5f5; }")

        # Container
        self.container = QWidget()
        self.container.setStyleSheet("background: #f5f5f5;")
        self.setWidget(self.container)

        self.main_layout = QVBoxLayout(self.container)
        self.main_layout.setContentsMargins(24, 24, 24, 24)
        self.main_layout.setSpacing(20)

        self._build_ui()

    def _build_ui(self):
        """Build the budget UI"""
        # Title
        title = QLabel("Budget")
        title.setStyleSheet("font-size: 28px; font-weight: bold; color: #1a1a2e; background: transparent;")
        self.main_layout.addWidget(title)

        if not self.budget or not self.budget.metrics.budget_total:
            no_data = QLabel("No budget data available")
            no_data.setStyleSheet("font-size: 14px; color: #666; background: transparent;")
            self.main_layout.addWidget(no_data)
            self.main_layout.addStretch()
            return

        m = self.budget.metrics

        # === Metrics Cards Row ===
        metrics_layout = QHBoxLayout()
        metrics_layout.setSpacing(12)

        # Status color
        if m.budget_status == "over budget":
            status_color = "#dc3545"
        elif m.budget_status == "within 15%":
            status_color = "#ffc107"
        else:
            status_color = "#28a745"

        metrics_layout.addWidget(MetricCard(
            format_currency(m.budget_total), "Total Budget",
            f"Project: {m.proj_start.strftime('%m/%d') if m.proj_start else '?'} - {m.proj_end.strftime('%m/%d') if m.proj_end else '?'}"
        ))

        metrics_layout.addWidget(MetricCard(
            format_currency(m.burn_to_date), "Burned to Date",
            f"{m.burn_pct:.0f}% of budget", status_color
        ))

        metrics_layout.addWidget(MetricCard(
            format_currency(m.budget_remaining), "Projected Remaining",
            m.budget_status_icon, status_color
        ))

        metrics_layout.addWidget(MetricCard(
            f"${m.wkly_avg_burn:,.0f}", "Weekly Avg Burn",
            f"{m.weeks_completed} of {m.weeks_total} weeks"
        ))

        self.main_layout.addLayout(metrics_layout)

        # === Progress Bar ===
        progress_card = Card()
        progress_layout = QVBoxLayout(progress_card)
        progress_layout.setContentsMargins(20, 16, 20, 16)

        progress_title = QLabel("Budget Progress")
        progress_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1a1a2e; background: transparent;")
        progress_layout.addWidget(progress_title)

        progress_bar = BurnProgressBar(m.burn_pct, m.budget_total, m.burn_to_date)
        progress_layout.addWidget(progress_bar)

        self.main_layout.addWidget(progress_card)

        # === Charts Row ===
        charts_layout = QHBoxLayout()
        charts_layout.setSpacing(20)

        # Weekly burn chart
        chart_card = Card()
        chart_layout = QVBoxLayout(chart_card)
        chart_layout.setContentsMargins(16, 12, 16, 12)

        # Chart header with expand button
        chart_header = QHBoxLayout()
        chart_title = QLabel("Weekly Burn")
        chart_title.setStyleSheet("font-size: 16px; font-weight: bold; color: #1a1a2e; background: transparent;")
        chart_header.addWidget(chart_title)
        chart_header.addStretch()

        expand_btn = QPushButton("⤢")  # Expand icon
        expand_btn.setToolTip("Expand chart")
        expand_btn.setFixedSize(24, 24)
        expand_btn.setStyleSheet("""
            QPushButton {
                background: #f0f0f0;
                color: #1a1a2e;
                border: 1px solid #ddd;
                border-radius: 4px;
                font-size: 14px;
            }
            QPushButton:hover {
                background: #e0e0e0;
                border-color: #ccc;
            }
        """)
        expand_btn.setCursor(Qt.PointingHandCursor)
        expand_btn.clicked.connect(self._show_expanded_chart)
        chart_header.addWidget(expand_btn)

        chart_layout.addLayout(chart_header)

        chart = WeeklyBurnChart(self.budget.weekly_burn, m.budget_total)
        chart_layout.addWidget(chart)

        charts_layout.addWidget(chart_card, 2)

        # Resource breakdown
        resource_table = ResourceTable(self.budget.resource_burn)
        charts_layout.addWidget(resource_table, 1)

        self.main_layout.addLayout(charts_layout)

        self.main_layout.addStretch()

    def _show_expanded_chart(self):
        """Show the chart in an expanded dialog"""
        if self.budget and self.budget.weekly_burn:
            dialog = ExpandedChartDialog(
                self.budget.weekly_burn,
                self.budget.metrics.budget_total,
                self
            )
            dialog.exec()

    def refresh(self, project_data, budget):
        """Refresh with new data"""
        self.budget = budget

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
