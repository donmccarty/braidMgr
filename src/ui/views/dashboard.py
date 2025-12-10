"""
Dashboard View - Project overview with key metrics.
Matches HTML project viewer layout exactly.
"""

import customtkinter as ctk
from typing import Optional
from datetime import date, timedelta
import io
import math

# Matplotlib for charts
import matplotlib
matplotlib.use('Agg')  # Non-interactive backend
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Circle, Wedge
import numpy as np
from PIL import Image

from src.core.models import ProjectData
from src.core.budget import CalculatedBudget, format_currency
from src.core.indicators import get_indicator_config, INDICATOR_CONFIG


def get_theme_colors():
    """Get colors based on current appearance mode"""
    mode = ctk.get_appearance_mode()
    if mode == "Dark":
        return {
            "card_bg": "#2d2d2d",
            "card_border": "#3d3d3d",
            "text_primary": "#ffffff",
            "text_secondary": "#888888",
            "text_muted": "#666666",
            "row_bg": "#363636",
        }
    else:
        return {
            "card_bg": "#ffffff",
            "card_border": "#e0e0e0",
            "text_primary": "#333333",
            "text_secondary": "#666666",
            "text_muted": "#999999",
            "row_bg": "#f5f5f5",
        }


# Status colors (same for both modes)
CRITICAL_COLOR = "#dc3545"
WARNING_COLOR = "#ffc107"
ACTIVE_COLOR = "#0d6efd"
SUCCESS_COLOR = "#28a745"
NEUTRAL_COLOR = "#6c757d"

# Type colors
TYPE_COLORS = {
    "Risk": "#dc3545",
    "Issue": "#fd7e14",
    "Action Item": "#0d6efd",
    "Decision": "#6f42c1",
    "Deliverable": "#28a745",
    "Budget": "#20c997",
    "Plan Item": "#6c757d"
}

# Deadline pill colors (matching HTML exactly)
DEADLINE_OVERDUE_BG = "#f8d7da"
DEADLINE_OVERDUE_TEXT = "#721c24"
DEADLINE_SOON_BG = "#fff3cd"
DEADLINE_SOON_TEXT = "#856404"
DEADLINE_UPCOMING_BG = "#e9ecef"
DEADLINE_UPCOMING_TEXT = "#495057"


class DashboardView(ctk.CTkScrollableFrame):
    """Dashboard view showing project overview"""

    def __init__(self, parent, project_data: Optional[ProjectData], budget: Optional[CalculatedBudget]):
        super().__init__(parent, fg_color="transparent")

        self.project_data = project_data
        self.budget = budget

        self.grid_columnconfigure(0, weight=1)

        # Fix macOS scroll wheel/trackpad
        self._setup_scroll_bindings()

        self._create_widgets()

    def _setup_scroll_bindings(self):
        """Setup scroll bindings for macOS trackpad/mouse wheel"""
        canvas = self._parent_canvas

        def _on_mousewheel(event):
            # macOS uses delta differently
            if event.delta:
                canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")
            elif event.num == 4:
                canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                canvas.yview_scroll(1, "units")

        # Bind for macOS (MouseWheel) and Linux (Button-4/5)
        canvas.bind_all("<MouseWheel>", _on_mousewheel)
        canvas.bind_all("<Button-4>", _on_mousewheel)
        canvas.bind_all("<Button-5>", _on_mousewheel)

    def _create_widgets(self):
        """Create dashboard widgets"""
        colors = get_theme_colors()
        row = 0

        # Title
        if self.project_data:
            title = self.project_data.metadata.project_name
        else:
            title = "BRAID Log"

        title_label = ctk.CTkLabel(
            self,
            text=title,
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=colors["text_primary"]
        )
        title_label.grid(row=row, column=0, sticky="w", pady=(0, 20))
        row += 1

        # === Header Row: Health Score, Velocity, Budget Summary ===
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=row, column=0, sticky="ew", pady=(0, 20))
        header_frame.grid_columnconfigure((0, 1, 2), weight=1, uniform="header")
        row += 1

        if self.project_data:
            items = self.project_data.items

            # Calculate health score
            health_score, health_class, health_status = self._calculate_health_score(items)
            self._create_health_card(header_frame, health_score, health_status, health_class, colors, 0)

            # Calculate velocity
            velocity_current, velocity_prior = self._calculate_velocity(items)
            self._create_velocity_card(header_frame, velocity_current, velocity_prior, colors, 1)

            # Budget summary card
            self._create_budget_card(header_frame, colors, 2)
        else:
            # No data placeholders
            for i in range(3):
                card = ctk.CTkFrame(header_frame, fg_color=colors["card_bg"], corner_radius=8)
                card.grid(row=0, column=i, padx=6, sticky="nsew")
                ctk.CTkLabel(card, text="No data", text_color=colors["text_muted"]).pack(pady=30)

        # === Stats Grid: Critical, Warning, Active, Completed, Total ===
        stats_frame = ctk.CTkFrame(self, fg_color="transparent")
        stats_frame.grid(row=row, column=0, sticky="ew", pady=(0, 20))
        stats_frame.grid_columnconfigure((0, 1, 2, 3, 4), weight=1, uniform="stat")
        row += 1

        if self.project_data:
            items = self.project_data.items
            counts = self._count_by_status(items)

            self._create_stat_card(stats_frame, "Critical", str(counts["critical"]), CRITICAL_COLOR, colors, 0)
            self._create_stat_card(stats_frame, "Warning", str(counts["warning"]), WARNING_COLOR, colors, 1)
            self._create_stat_card(stats_frame, "Active", str(counts["active"]), ACTIVE_COLOR, colors, 2)
            self._create_stat_card(stats_frame, "Completed", str(counts["completed"]), SUCCESS_COLOR, colors, 3)
            self._create_stat_card(stats_frame, "Total", str(counts["total"]), NEUTRAL_COLOR, colors, 4)

        # === Row 1: Open Items by Type (left), Upcoming Deadlines (right) ===
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.grid(row=row, column=0, sticky="nsew", pady=(0, 20))
        content_frame.grid_columnconfigure(0, weight=1, uniform="col")
        content_frame.grid_columnconfigure(1, weight=1, uniform="col")
        row += 1

        # Left: Open Items by Type (with donut chart)
        left_card = self._create_card(content_frame, "Open Items by Type", colors)
        left_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12), pady=0)
        self._populate_type_breakdown(left_card, colors)

        # Right: Upcoming Deadlines
        right_card = self._create_card(content_frame, "Upcoming Deadlines", colors)
        right_card.grid(row=0, column=1, sticky="nsew", padx=(12, 0), pady=0)
        self._populate_deadlines(right_card, colors)

        # === Row 2: Items by Assigned To (left), Items by Workstream (right) ===
        content_frame2 = ctk.CTkFrame(self, fg_color="transparent")
        content_frame2.grid(row=row, column=0, sticky="nsew", pady=(0, 20))
        content_frame2.grid_columnconfigure(0, weight=1, uniform="col2")
        content_frame2.grid_columnconfigure(1, weight=1, uniform="col2")
        row += 1

        # Left: Items by Assigned To
        assignee_card = self._create_card(content_frame2, "Items by Assigned To", colors)
        assignee_card.grid(row=0, column=0, sticky="nsew", padx=(0, 12), pady=0)
        self._populate_assignee_breakdown(assignee_card, colors)

        # Right: Items by Workstream (treemap style)
        ws_card = self._create_card(content_frame2, "Items by Workstream", colors)
        ws_card.grid(row=0, column=1, sticky="nsew", padx=(12, 0), pady=0)
        self._populate_workstream_treemap(ws_card, colors)

    def _calculate_health_score(self, items):
        """Calculate project health score 0-100"""
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
        """Calculate completion velocity (last 14 days vs prior 14 days)"""
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
        """Count items by status/severity"""
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

    def _create_health_card(self, parent, score, status, health_class, colors, col):
        """Create health score card"""
        card = ctk.CTkFrame(parent, fg_color=colors["card_bg"], corner_radius=8)
        card.grid(row=0, column=col, padx=6, sticky="nsew")

        # Score color
        if health_class == "critical":
            score_color = CRITICAL_COLOR
        elif health_class == "warning":
            score_color = WARNING_COLOR
        else:
            score_color = SUCCESS_COLOR

        score_label = ctk.CTkLabel(
            card, text=str(score),
            font=ctk.CTkFont(size=48, weight="bold"),
            text_color=score_color
        )
        score_label.pack(pady=(20, 4))

        title_label = ctk.CTkLabel(
            card, text="Project Health",
            font=ctk.CTkFont(size=12),
            text_color=colors["text_secondary"]
        )
        title_label.pack()

        status_label = ctk.CTkLabel(
            card, text=status,
            font=ctk.CTkFont(size=11, weight="bold"),
            text_color=score_color
        )
        status_label.pack(pady=(4, 20))

    def _create_velocity_card(self, parent, current, prior, colors, col):
        """Create velocity card"""
        card = ctk.CTkFrame(parent, fg_color=colors["card_bg"], corner_radius=8)
        card.grid(row=0, column=col, padx=6, sticky="nsew")

        diff = current - prior
        if diff > 0:
            arrow = "↑"
            arrow_color = SUCCESS_COLOR
        elif diff < 0:
            arrow = "↓"
            arrow_color = CRITICAL_COLOR
        else:
            arrow = "→"
            arrow_color = NEUTRAL_COLOR

        value_frame = ctk.CTkFrame(card, fg_color="transparent")
        value_frame.pack(pady=(20, 4))

        num_label = ctk.CTkLabel(
            value_frame, text=str(current),
            font=ctk.CTkFont(size=40, weight="bold"),
            text_color=colors["text_primary"]
        )
        num_label.pack(side="left")

        arrow_label = ctk.CTkLabel(
            value_frame, text=f" {arrow}",
            font=ctk.CTkFont(size=24, weight="bold"),
            text_color=arrow_color
        )
        arrow_label.pack(side="left")

        title_label = ctk.CTkLabel(
            card, text="Completed (14d)",
            font=ctk.CTkFont(size=12),
            text_color=colors["text_secondary"]
        )
        title_label.pack()

        detail_label = ctk.CTkLabel(
            card, text=f"vs {prior} prior period",
            font=ctk.CTkFont(size=10),
            text_color=colors["text_muted"]
        )
        detail_label.pack(pady=(2, 20))

    def _create_budget_card(self, parent, colors, col):
        """Create budget summary card"""
        card = ctk.CTkFrame(parent, fg_color=colors["card_bg"], corner_radius=8)
        card.grid(row=0, column=col, padx=6, sticky="nsew")

        if not self.budget:
            ctk.CTkLabel(
                card, text="—",
                font=ctk.CTkFont(size=32),
                text_color=colors["text_muted"]
            ).pack(pady=(20, 4))
            ctk.CTkLabel(
                card, text="No Budget Data",
                font=ctk.CTkFont(size=12),
                text_color=colors["text_secondary"]
            ).pack(pady=(0, 20))
            return

        m = self.budget.metrics

        # Status color
        if m.budget_remaining < 0:
            status_color = CRITICAL_COLOR
        elif m.burn_pct > 85:
            status_color = WARNING_COLOR
        else:
            status_color = SUCCESS_COLOR

        value_label = ctk.CTkLabel(
            card, text=format_currency(m.budget_total),
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=colors["text_primary"]
        )
        value_label.pack(pady=(20, 4))

        title_label = ctk.CTkLabel(
            card, text="Total Budget",
            font=ctk.CTkFont(size=12),
            text_color=colors["text_secondary"]
        )
        title_label.pack()

        status_label = ctk.CTkLabel(
            card, text=m.budget_status_icon,
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=status_color
        )
        status_label.pack(pady=(4, 2))

        detail_label = ctk.CTkLabel(
            card, text=f"{format_currency(m.burn_to_date)} burned ({m.burn_pct:.0f}%)",
            font=ctk.CTkFont(size=10),
            text_color=colors["text_muted"]
        )
        detail_label.pack(pady=(0, 20))

    def _create_stat_card(self, parent, label: str, value: str, color: str, colors: dict, col: int):
        """Create a stat card"""
        card = ctk.CTkFrame(parent, fg_color=colors["card_bg"], corner_radius=8)
        card.grid(row=0, column=col, padx=4, pady=0, sticky="nsew")

        value_label = ctk.CTkLabel(
            card, text=value,
            font=ctk.CTkFont(size=32, weight="bold"),
            text_color=color
        )
        value_label.pack(pady=(16, 4))

        name_label = ctk.CTkLabel(
            card, text=label,
            font=ctk.CTkFont(size=12),
            text_color=colors["text_secondary"]
        )
        name_label.pack(pady=(0, 16))

    def _create_card(self, parent, title: str, colors: dict) -> ctk.CTkFrame:
        """Create a card container with title"""
        card = ctk.CTkFrame(parent, fg_color=colors["card_bg"], corner_radius=8)

        title_label = ctk.CTkLabel(
            card, text=title,
            font=ctk.CTkFont(size=16, weight="bold"),
            text_color=colors["text_primary"]
        )
        title_label.pack(anchor="w", padx=20, pady=(16, 12))

        sep = ctk.CTkFrame(card, height=1, fg_color=colors["card_border"])
        sep.pack(fill="x", padx=20, pady=(0, 12))

        return card

    def _populate_deadlines(self, card, colors):
        """Populate upcoming deadlines with small pills matching HTML exactly"""
        if not self.project_data:
            ctk.CTkLabel(card, text="No data", text_color=colors["text_muted"]).pack(pady=20)
            return

        today = date.today()
        thirty_days = today + timedelta(days=30)

        # Get items with deadlines
        completed_indicators = ["Completed", "Completed Recently", "Done", "Closed", "Cancelled", "Resolved"]
        deadline_items = []

        for item in self.project_data.items:
            if not item.deadline:
                continue
            if item.indicator in completed_indicators:
                continue
            deadline = item.deadline
            if isinstance(deadline, str):
                continue
            if deadline <= thirty_days:
                days_until = (deadline - today).days
                deadline_items.append((item, days_until))

        # Sort by deadline
        deadline_items.sort(key=lambda x: x[1])
        deadline_items = deadline_items[:5]  # Top 5

        if not deadline_items:
            ctk.CTkLabel(
                card, text="No upcoming deadlines",
                text_color=colors["text_muted"],
                font=ctk.CTkFont(size=12, slant="italic")
            ).pack(pady=20, padx=20)
            return

        for item, days_until in deadline_items:
            # Row container with flexbox-like layout
            row = ctk.CTkFrame(card, fg_color="transparent", height=36)
            row.pack(fill="x", padx=16, pady=3)
            row.pack_propagate(False)

            # Title on left (truncated)
            title_text = f"#{item.item_num}: {item.title or 'Untitled'}"
            if len(title_text) > 35:
                title_text = title_text[:32] + "..."

            title_label = ctk.CTkLabel(
                row, text=title_text,
                anchor="w", text_color=colors["text_primary"],
                font=ctk.CTkFont(size=12)
            )
            title_label.pack(side="left", fill="y")

            # Small pill on right (matching HTML: padding 0.2rem 0.5rem, border-radius 4px)
            if days_until < 0:
                days_text = f"{abs(days_until)}d overdue"
                pill_bg = DEADLINE_OVERDUE_BG
                pill_text = DEADLINE_OVERDUE_TEXT
            elif days_until == 0:
                days_text = "Today"
                pill_bg = DEADLINE_OVERDUE_BG
                pill_text = DEADLINE_OVERDUE_TEXT
            elif days_until <= 7:
                days_text = f"{days_until}d"
                pill_bg = DEADLINE_SOON_BG
                pill_text = DEADLINE_SOON_TEXT
            else:
                days_text = f"{days_until}d"
                pill_bg = DEADLINE_UPCOMING_BG
                pill_text = DEADLINE_UPCOMING_TEXT

            # Small pill (not full width)
            pill = ctk.CTkFrame(row, fg_color=pill_bg, corner_radius=4)
            pill.pack(side="right", padx=(10, 0))

            pill_label = ctk.CTkLabel(
                pill, text=days_text,
                text_color=pill_text,
                font=ctk.CTkFont(size=11)
            )
            pill_label.pack(padx=8, pady=3)

        # Padding at bottom
        ctk.CTkFrame(card, fg_color="transparent", height=8).pack()

    def _populate_type_breakdown(self, card, colors):
        """Populate items by type with SVG-style donut chart matching HTML"""
        if not self.project_data:
            ctk.CTkLabel(card, text="No data", text_color=colors["text_muted"]).pack(pady=20)
            return

        # Count open items by type
        completed_indicators = ["Completed", "Completed Recently", "Done", "Closed", "Cancelled", "Resolved"]
        open_items = [i for i in self.project_data.items if i.indicator not in completed_indicators]

        by_type = {}
        for item in open_items:
            t = item.type or "Plan Item"
            by_type[t] = by_type.get(t, 0) + 1

        sorted_types = sorted(by_type.items(), key=lambda x: -x[1])

        if not sorted_types:
            ctk.CTkLabel(card, text="No open items", text_color=colors["text_muted"]).pack(pady=20)
            return

        # Layout frame: donut on left, legend on right
        chart_frame = ctk.CTkFrame(card, fg_color="transparent")
        chart_frame.pack(fill="both", expand=True, padx=16, pady=8)

        # Left side: donut chart
        left_frame = ctk.CTkFrame(chart_frame, fg_color="transparent")
        left_frame.pack(side="left", fill="both", expand=True)

        # Right side: legend
        right_frame = ctk.CTkFrame(chart_frame, fg_color="transparent")
        right_frame.pack(side="right", fill="y", padx=(10, 0))

        # Create stroke-based donut chart (matching HTML SVG with stroke-width=25)
        bg_color = colors["card_bg"]
        text_color = colors["text_primary"]
        muted_color = colors["text_muted"]

        fig, ax = plt.subplots(figsize=(2.2, 2.2), facecolor=bg_color)
        ax.set_facecolor(bg_color)

        labels = [t[0] for t in sorted_types]
        sizes = [t[1] for t in sorted_types]
        chart_colors = [TYPE_COLORS.get(t, NEUTRAL_COLOR) for t in labels]
        total = sum(sizes)

        # Draw stroke-based donut (like SVG stroke-dasharray)
        # Outer radius 0.85, inner radius 0.60 gives stroke-width equivalent
        wedges, _ = ax.pie(
            sizes, colors=chart_colors, startangle=90,
            wedgeprops=dict(width=0.28, edgecolor=bg_color, linewidth=1.5),
            radius=0.88
        )

        # Center text
        ax.text(0, 0.06, str(len(open_items)), ha='center', va='center',
                fontsize=26, fontweight='bold', color=text_color)
        ax.text(0, -0.18, "Open", ha='center', va='center',
                fontsize=10, color=muted_color)

        ax.axis('equal')
        plt.tight_layout(pad=0)

        # Convert to image
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, facecolor=bg_color,
                    edgecolor='none', bbox_inches='tight', pad_inches=0.02)
        buf.seek(0)
        plt.close(fig)

        img = Image.open(buf)
        ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)

        chart_label = ctk.CTkLabel(left_frame, image=ctk_image, text="")
        chart_label.ctk_image = ctk_image
        chart_label.pack(pady=5)

        # Legend as column (matching HTML .donut-legend)
        for type_name, count in sorted_types:
            row_frame = ctk.CTkFrame(right_frame, fg_color="transparent", height=28)
            row_frame.pack(fill="x", pady=2)
            row_frame.pack_propagate(False)

            color = TYPE_COLORS.get(type_name, NEUTRAL_COLOR)

            # Square color box (14x14, border-radius 3px)
            color_box = ctk.CTkFrame(row_frame, width=14, height=14, fg_color=color, corner_radius=3)
            color_box.pack(side="left", padx=(0, 8))
            color_box.pack_propagate(False)

            # Type name
            name = ctk.CTkLabel(
                row_frame, text=type_name,
                anchor="w", text_color=colors["text_primary"],
                font=ctk.CTkFont(size=11)
            )
            name.pack(side="left")

            # Count on right (bold)
            count_label = ctk.CTkLabel(
                row_frame, text=str(count),
                text_color=colors["text_primary"],
                font=ctk.CTkFont(size=11, weight="bold")
            )
            count_label.pack(side="right", padx=(12, 0))

    def _populate_assignee_breakdown(self, card, colors):
        """Populate lollipop chart matching HTML exactly"""
        if not self.project_data:
            ctk.CTkLabel(card, text="No data", text_color=colors["text_muted"]).pack(pady=20)
            return

        # Count items by assignee, split by active vs backlog
        completed_indicators = ["Completed", "Completed Recently", "Done", "Closed", "Cancelled", "Resolved"]
        active_indicators = ["Active", "In Progress", "Started"]

        by_assignee = {}
        for item in self.project_data.items:
            if item.indicator in completed_indicators:
                continue
            assignee = item.assigned_to or "Unassigned"
            if assignee not in by_assignee:
                by_assignee[assignee] = {"active": 0, "backlog": 0}
            if item.indicator in active_indicators:
                by_assignee[assignee]["active"] += 1
            else:
                by_assignee[assignee]["backlog"] += 1

        # Sort by total count
        sorted_assignees = sorted(by_assignee.items(),
                                   key=lambda x: -(x[1]["active"] + x[1]["backlog"]))[:8]

        if not sorted_assignees:
            ctk.CTkLabel(card, text="No assignees", text_color=colors["text_muted"]).pack(pady=20)
            return

        # Create lollipop chart matching HTML design exactly
        bg_color = colors["card_bg"]
        text_color = colors["text_primary"]
        text_secondary = colors["text_secondary"]

        fig, ax = plt.subplots(figsize=(4.5, 3.2), facecolor=bg_color)
        ax.set_facecolor(bg_color)

        names = [a[0][:15] + "..." if len(a[0]) > 15 else a[0] for a in reversed(sorted_assignees)]
        active_counts = [a[1]["active"] for a in reversed(sorted_assignees)]
        backlog_counts = [a[1]["backlog"] for a in reversed(sorted_assignees)]
        total_counts = [a + b for a, b in zip(active_counts, backlog_counts)]

        y_pos = range(len(names))
        max_count = max(total_counts) if total_counts else 1

        # HTML: gray line across full width, dots positioned at values
        for i, (name, total, active, backlog) in enumerate(zip(names, total_counts, active_counts, backlog_counts)):
            # Full-width gray background line
            ax.hlines(y=i, xmin=0, xmax=max_count + 1, color='#e9ecef', linewidth=3, zorder=1)

            # Gradient stem from left to total (blue gradient effect)
            ax.hlines(y=i, xmin=0, xmax=total, color='#6c757d', linewidth=2, alpha=0.4, zorder=2)

            # Backlog dot (white with gray border - HTML .backlog-dot)
            # 22px = approximately s=380 in matplotlib
            if backlog > 0:
                ax.scatter(total, i, s=380, facecolor='white', edgecolor='#6c757d',
                          linewidth=2, zorder=4)
                ax.text(total, i, str(total), ha='center', va='center',
                       fontsize=8, color='#6c757d', fontweight='bold', zorder=5)

            # Active dot (blue filled - HTML .active-dot)
            if active > 0:
                ax.scatter(active, i, s=380, facecolor=ACTIVE_COLOR, edgecolor='white',
                          linewidth=1.5, zorder=6)
                ax.text(active, i, str(active), ha='center', va='center',
                       fontsize=8, color='white', fontweight='bold', zorder=7)

        ax.set_yticks(y_pos)
        ax.set_yticklabels(names)
        ax.tick_params(axis='y', labelsize=10, colors=text_color, length=0, pad=8)

        # X limit with padding
        ax.set_xlim(-0.5, max_count + 1.5)

        # Remove spines
        for spine in ax.spines.values():
            spine.set_visible(False)
        ax.xaxis.set_visible(False)

        # Legend at bottom matching HTML
        from matplotlib.lines import Line2D
        legend_elements = [
            Line2D([0], [0], marker='o', color='w', markerfacecolor=ACTIVE_COLOR,
                   markersize=10, label='Active', markeredgecolor='white', markeredgewidth=1),
            Line2D([0], [0], marker='o', color='w', markerfacecolor='white',
                   markersize=10, label='Backlog', markeredgecolor='#6c757d', markeredgewidth=2)
        ]
        ax.legend(handles=legend_elements, loc='lower right', fontsize=9, frameon=False,
                  labelcolor=text_secondary, handletextpad=0.5)

        plt.tight_layout(pad=0.3)

        # Convert to image
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, facecolor=bg_color,
                    edgecolor='none', bbox_inches='tight', pad_inches=0.1)
        buf.seek(0)
        plt.close(fig)

        img = Image.open(buf)
        ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)

        chart_label = ctk.CTkLabel(card, image=ctk_image, text="")
        chart_label.ctk_image = ctk_image
        chart_label.pack(pady=(5, 15), padx=10)

    def _populate_workstream_treemap(self, card, colors):
        """Populate treemap matching HTML flex-wrap layout with 3px gap"""
        if not self.project_data:
            ctk.CTkLabel(card, text="No data", text_color=colors["text_muted"]).pack(pady=20)
            return

        by_workstream = {}
        for item in self.project_data.items:
            ws = item.workstream or "Unassigned"
            by_workstream[ws] = by_workstream.get(ws, 0) + 1

        sorted_ws = sorted(by_workstream.items(), key=lambda x: -x[1])[:9]  # Top 9

        if not sorted_ws:
            ctk.CTkLabel(card, text="No workstreams", text_color=colors["text_muted"]).pack(pady=20)
            return

        # Treemap colors matching HTML
        ws_colors = ["#28a745", "#20c997", "#ffc107", "#17a2b8", "#6f42c1", "#fd7e14", "#dc3545", "#6c757d", "#0d6efd"]

        bg_color = colors["card_bg"]

        # Create treemap with flex-wrap style layout (3px gap, rounded corners)
        fig, ax = plt.subplots(figsize=(4.5, 3.2), facecolor=bg_color)
        ax.set_facecolor(bg_color)

        n = len(sorted_ws)
        total = sum(c for _, c in sorted_ws)
        gap = 0.008  # 3px equivalent

        # Squarified treemap algorithm - simplified for our case
        # We'll use a 3-row layout similar to HTML flex-wrap behavior

        # Calculate row assignments based on count (flex-grow equivalent)
        # Row 1: largest 2 items
        # Row 2: next 3-4 items
        # Row 3: remaining items

        row1 = sorted_ws[:2] if n >= 2 else sorted_ws
        row2 = sorted_ws[2:5] if n > 2 else []
        row3 = sorted_ws[5:9] if n > 5 else []

        # Row heights proportional to total counts
        row1_total = sum(c for _, c in row1) if row1 else 0
        row2_total = sum(c for _, c in row2) if row2 else 0
        row3_total = sum(c for _, c in row3) if row3 else 0

        all_total = row1_total + row2_total + row3_total

        # Base heights with minimum heights
        h1 = 0.4 if row1 else 0
        h2 = 0.32 if row2 else 0
        h3 = 0.24 if row3 else 0

        # Adjust if fewer rows
        if not row3:
            h1 = 0.52
            h2 = 0.44
        if not row2:
            h1 = 0.96

        color_idx = 0

        # Draw Row 1 (top)
        if row1:
            row_total = sum(c for _, c in row1)
            x = 0
            y = 1 - h1
            for ws_name, count in row1:
                w = (count / row_total) * (1 - gap * (len(row1) - 1)) if row_total > 0 else 0.5
                color = ws_colors[color_idx % len(ws_colors)]
                color_idx += 1

                rect = FancyBboxPatch(
                    (x, y + gap), w, h1 - gap * 2,
                    boxstyle="round,pad=0,rounding_size=0.015",
                    facecolor=color, edgecolor='none'
                )
                ax.add_patch(rect)

                cx = x + w / 2
                cy = y + h1 / 2

                # Count above name (HTML .treemap-count above .treemap-label)
                ax.text(cx, cy + 0.04, str(count), ha='center', va='center',
                       fontsize=16, fontweight='bold', color='white')
                display_name = ws_name if len(ws_name) <= 14 else ws_name[:12] + "..."
                ax.text(cx, cy - 0.06, display_name, ha='center', va='center',
                       fontsize=9, color='white', alpha=0.9)

                x += w + gap

        # Draw Row 2 (middle)
        if row2:
            row_total = sum(c for _, c in row2)
            x = 0
            y = 1 - h1 - h2
            for ws_name, count in row2:
                w = (count / row_total) * (1 - gap * (len(row2) - 1)) if row_total > 0 else 0.33
                color = ws_colors[color_idx % len(ws_colors)]
                color_idx += 1

                rect = FancyBboxPatch(
                    (x, y + gap), w, h2 - gap * 2,
                    boxstyle="round,pad=0,rounding_size=0.015",
                    facecolor=color, edgecolor='none'
                )
                ax.add_patch(rect)

                cx = x + w / 2
                cy = y + h2 / 2
                ax.text(cx, cy + 0.03, str(count), ha='center', va='center',
                       fontsize=13, fontweight='bold', color='white')
                display_name = ws_name if len(ws_name) <= 12 else ws_name[:10] + "..."
                ax.text(cx, cy - 0.05, display_name, ha='center', va='center',
                       fontsize=8, color='white', alpha=0.9)

                x += w + gap

        # Draw Row 3 (bottom)
        if row3:
            row_total = sum(c for _, c in row3)
            x = 0
            y = 0
            for ws_name, count in row3:
                w = (count / row_total) * (1 - gap * (len(row3) - 1)) if row_total > 0 else 0.25
                color = ws_colors[color_idx % len(ws_colors)]
                color_idx += 1

                rect = FancyBboxPatch(
                    (x, y + gap), w, h3 - gap,
                    boxstyle="round,pad=0,rounding_size=0.015",
                    facecolor=color, edgecolor='none'
                )
                ax.add_patch(rect)

                cx = x + w / 2
                cy = y + h3 / 2
                ax.text(cx, cy + 0.02, str(count), ha='center', va='center',
                       fontsize=11, fontweight='bold', color='white')
                display_name = ws_name if len(ws_name) <= 10 else ws_name[:8] + "..."
                ax.text(cx, cy - 0.04, display_name, ha='center', va='center',
                       fontsize=7, color='white', alpha=0.9)

                x += w + gap

        ax.set_xlim(0, 1)
        ax.set_ylim(0, 1)
        ax.axis('off')

        plt.tight_layout(pad=0)

        # Convert to image
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, facecolor=bg_color,
                    edgecolor='none', bbox_inches='tight', pad_inches=0.05)
        buf.seek(0)
        plt.close(fig)

        img = Image.open(buf)
        ctk_image = ctk.CTkImage(light_image=img, dark_image=img, size=img.size)

        chart_label = ctk.CTkLabel(card, image=ctk_image, text="")
        chart_label.ctk_image = ctk_image
        chart_label.pack(pady=(5, 15), padx=10)
