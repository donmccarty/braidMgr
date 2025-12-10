"""
Budget View - Budget tracking and visualization.
Styled to match HTML project viewer.
"""

import customtkinter as ctk
from typing import Optional

from src.core.budget import CalculatedBudget, format_currency

# Colors matching other views
CARD_BG = "#2d2d2d"
CARD_BORDER = "#3d3d3d"
ROW_BG = "#363636"
TEXT_PRIMARY = "#ffffff"
TEXT_SECONDARY = "#888888"
TEXT_MUTED = "#666666"

# Status colors
GREEN = "#28a745"
RED = "#dc3545"
YELLOW = "#ffc107"
BLUE = "#0d6efd"


class BudgetView(ctk.CTkFrame):
    """Budget view with metrics and charts"""

    def __init__(self, parent, budget: Optional[CalculatedBudget]):
        super().__init__(parent, fg_color="transparent")

        self.budget = budget

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(1, weight=1)

        self._create_widgets()

    def _create_widgets(self):
        """Create budget view widgets"""
        # Header with title
        header_frame = ctk.CTkFrame(self, fg_color="transparent")
        header_frame.grid(row=0, column=0, columnspan=2, sticky="ew", pady=(0, 16))

        title = ctk.CTkLabel(
            header_frame,
            text="Budget Overview",
            font=ctk.CTkFont(size=28, weight="bold"),
            text_color=TEXT_PRIMARY
        )
        title.pack(side="left")

        if not self.budget:
            no_data_card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=8)
            no_data_card.grid(row=1, column=0, columnspan=2, sticky="nsew")
            no_data = ctk.CTkLabel(
                no_data_card,
                text="No budget data available",
                text_color=TEXT_MUTED,
                font=ctk.CTkFont(size=14)
            )
            no_data.pack(pady=50)
            return

        # Left column - Key Metrics
        left_card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=8)
        left_card.grid(row=1, column=0, sticky="nsew", padx=(0, 8), pady=0)
        left_card.grid_columnconfigure(0, weight=1)

        self._create_metrics_panel(left_card)

        # Right column - Weekly Burn / Resource Burn
        right_card = ctk.CTkFrame(self, fg_color=CARD_BG, corner_radius=8)
        right_card.grid(row=1, column=1, sticky="nsew", padx=(8, 0), pady=0)
        right_card.grid_columnconfigure(0, weight=1)
        right_card.grid_rowconfigure(2, weight=1)

        self._create_burn_panels(right_card)

    def _create_metrics_panel(self, parent):
        """Create key metrics panel"""
        header = ctk.CTkLabel(
            parent,
            text="Key Metrics",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEXT_PRIMARY
        )
        header.pack(pady=(16, 16), padx=16, anchor="w")

        # Separator
        sep = ctk.CTkFrame(parent, height=1, fg_color=CARD_BORDER)
        sep.pack(fill="x", padx=16)

        m = self.budget.metrics

        # Budget status card - prominent display
        status_frame = ctk.CTkFrame(parent, fg_color=ROW_BG, corner_radius=6)
        status_frame.pack(fill="x", padx=16, pady=16)

        status_icon = m.budget_status_icon
        status_color = GREEN if m.budget_remaining > 0 else RED

        status_label = ctk.CTkLabel(
            status_frame,
            text=f"{status_icon} Budget Status",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color=status_color
        )
        status_label.pack(pady=(16, 4))

        remaining_label = ctk.CTkLabel(
            status_frame,
            text=f"{format_currency(m.budget_remaining)} remaining",
            font=ctk.CTkFont(size=14),
            text_color=TEXT_SECONDARY
        )
        remaining_label.pack(pady=(0, 16))

        # Metrics list
        pct_time_elapsed = round(m.weeks_completed / m.weeks_total * 100) if m.weeks_total > 0 else 0
        projected_variance = m.budget_total - m.est_total_burn

        metrics = [
            ("Total Budget", format_currency(m.budget_total), None),
            ("Burn to Date", f"{format_currency(m.burn_to_date)} ({m.burn_pct:.0f}%)", None),
            ("Budget Remaining", format_currency(m.budget_remaining), GREEN if m.budget_remaining > 0 else RED),
            ("---", "", None),  # Spacer
            ("Weekly Average Burn", format_currency(m.wkly_avg_burn), None),
            ("Estimated Final", format_currency(m.est_total_burn), None),
            ("Projected Variance", format_currency(projected_variance), GREEN if projected_variance >= 0 else RED),
            ("---", "", None),  # Spacer
            ("Weeks Completed", f"{m.weeks_completed} of {m.weeks_total}", None),
            ("Weeks Remaining", str(m.weeks_remaining), None),
            ("% Time Elapsed", f"{pct_time_elapsed}%", None),
        ]

        for i, (label, value, color) in enumerate(metrics):
            if label == "---":
                spacer = ctk.CTkFrame(parent, fg_color="transparent", height=12)
                spacer.pack(fill="x")
                continue

            # Alternating background
            row_color = ROW_BG if i % 2 == 0 else "transparent"
            row = ctk.CTkFrame(parent, fg_color=row_color, height=32)
            row.pack(fill="x", padx=16, pady=1)
            row.pack_propagate(False)

            label_widget = ctk.CTkLabel(
                row,
                text=label,
                anchor="w",
                text_color=TEXT_SECONDARY,
                font=ctk.CTkFont(size=13)
            )
            label_widget.pack(side="left", padx=12, fill="y")

            value_widget = ctk.CTkLabel(
                row,
                text=value,
                anchor="e",
                text_color=color if color else TEXT_PRIMARY,
                font=ctk.CTkFont(size=13, weight="bold" if color else "normal")
            )
            value_widget.pack(side="right", padx=12, fill="y")

        # Progress bar section
        progress_frame = ctk.CTkFrame(parent, fg_color="transparent")
        progress_frame.pack(fill="x", padx=16, pady=(20, 16))

        progress_label = ctk.CTkLabel(
            progress_frame,
            text="Budget Utilization",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color=TEXT_PRIMARY
        )
        progress_label.pack(anchor="w")

        burn_pct = min(m.burn_pct / 100, 1.0)

        # Progress bar container with background
        bar_container = ctk.CTkFrame(progress_frame, fg_color=CARD_BORDER, corner_radius=4, height=20)
        bar_container.pack(fill="x", pady=(8, 4))
        bar_container.pack_propagate(False)

        progress_bar = ctk.CTkProgressBar(
            bar_container,
            height=16,
            corner_radius=3,
            fg_color=CARD_BORDER
        )
        progress_bar.pack(fill="x", padx=2, pady=2)
        progress_bar.set(burn_pct)

        # Color the progress bar based on status
        if m.burn_pct > 100:
            progress_bar.configure(progress_color=RED)
        elif m.burn_pct > 90:
            progress_bar.configure(progress_color=YELLOW)
        else:
            progress_bar.configure(progress_color=GREEN)

        pct_label = ctk.CTkLabel(
            progress_frame,
            text=f"{m.burn_pct}% used",
            text_color=TEXT_SECONDARY,
            font=ctk.CTkFont(size=12)
        )
        pct_label.pack(anchor="w")

    def _create_burn_panels(self, parent):
        """Create burn analysis panels"""
        # Weekly burn section
        weekly_header = ctk.CTkLabel(
            parent,
            text="Weekly Burn",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEXT_PRIMARY
        )
        weekly_header.pack(pady=(16, 12), padx=16, anchor="w")

        # Separator
        sep1 = ctk.CTkFrame(parent, height=1, fg_color=CARD_BORDER)
        sep1.pack(fill="x", padx=16)

        # Weekly scroll area
        weekly_scroll = ctk.CTkScrollableFrame(
            parent,
            height=160,
            fg_color="transparent",
            scrollbar_button_color=CARD_BORDER,
            scrollbar_button_hover_color=TEXT_MUTED
        )
        weekly_scroll.pack(fill="x", padx=16, pady=(8, 16))

        # Header row
        header_frame = ctk.CTkFrame(weekly_scroll, fg_color=ROW_BG, height=32, corner_radius=4)
        header_frame.pack(fill="x", pady=(0, 4))
        header_frame.pack_propagate(False)

        ctk.CTkLabel(
            header_frame, text="Week", font=ctk.CTkFont(size=12, weight="bold"),
            width=80, anchor="w", text_color=TEXT_SECONDARY
        ).pack(side="left", padx=12)
        ctk.CTkLabel(
            header_frame, text="Cost", font=ctk.CTkFont(size=12, weight="bold"),
            width=100, anchor="e", text_color=TEXT_SECONDARY
        ).pack(side="left", padx=12)
        ctk.CTkLabel(
            header_frame, text="Cumulative", font=ctk.CTkFont(size=12, weight="bold"),
            width=100, anchor="e", text_color=TEXT_SECONDARY
        ).pack(side="right", padx=12)

        # Weekly data (most recent first)
        for i, wb in enumerate(reversed(self.budget.weekly_burn[-10:])):
            row_bg = ROW_BG if i % 2 == 1 else "transparent"
            row = ctk.CTkFrame(weekly_scroll, fg_color=row_bg, height=28)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)

            ctk.CTkLabel(
                row, text=wb.week_ending.strftime("%m/%d"),
                width=80, anchor="w", text_color=TEXT_SECONDARY, font=ctk.CTkFont(size=12)
            ).pack(side="left", padx=12)
            ctk.CTkLabel(
                row, text=format_currency(wb.cost),
                width=100, anchor="e", text_color=TEXT_PRIMARY, font=ctk.CTkFont(size=12)
            ).pack(side="left", padx=12)
            ctk.CTkLabel(
                row, text=format_currency(wb.cumulative),
                width=100, anchor="e", text_color=TEXT_PRIMARY, font=ctk.CTkFont(size=12)
            ).pack(side="right", padx=12)

        # Resource burn section
        resource_header = ctk.CTkLabel(
            parent,
            text="Burn by Resource",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color=TEXT_PRIMARY
        )
        resource_header.pack(pady=(8, 12), padx=16, anchor="w")

        # Separator
        sep2 = ctk.CTkFrame(parent, height=1, fg_color=CARD_BORDER)
        sep2.pack(fill="x", padx=16)

        # Resource scroll area
        resource_scroll = ctk.CTkScrollableFrame(
            parent,
            fg_color="transparent",
            scrollbar_button_color=CARD_BORDER,
            scrollbar_button_hover_color=TEXT_MUTED
        )
        resource_scroll.pack(fill="both", expand=True, padx=16, pady=(8, 16))

        # Header row
        res_header = ctk.CTkFrame(resource_scroll, fg_color=ROW_BG, height=32, corner_radius=4)
        res_header.pack(fill="x", pady=(0, 4))
        res_header.pack_propagate(False)

        ctk.CTkLabel(
            res_header, text="Resource", font=ctk.CTkFont(size=12, weight="bold"),
            anchor="w", text_color=TEXT_SECONDARY
        ).pack(side="left", fill="x", expand=True, padx=12)
        ctk.CTkLabel(
            res_header, text="Hours", font=ctk.CTkFont(size=12, weight="bold"),
            width=60, anchor="e", text_color=TEXT_SECONDARY
        ).pack(side="left", padx=12)
        ctk.CTkLabel(
            res_header, text="Cost", font=ctk.CTkFont(size=12, weight="bold"),
            width=100, anchor="e", text_color=TEXT_SECONDARY
        ).pack(side="right", padx=12)

        # Sort by cost descending
        sorted_resources = sorted(self.budget.resource_burn, key=lambda x: -x.cost)

        for i, rb in enumerate(sorted_resources):
            row_bg = ROW_BG if i % 2 == 1 else "transparent"
            row = ctk.CTkFrame(resource_scroll, fg_color=row_bg, height=28)
            row.pack(fill="x", pady=1)
            row.pack_propagate(False)

            ctk.CTkLabel(
                row, text=rb.resource,
                anchor="w", text_color=TEXT_SECONDARY, font=ctk.CTkFont(size=12)
            ).pack(side="left", fill="x", expand=True, padx=12)
            ctk.CTkLabel(
                row, text=f"{rb.hours:.1f}",
                width=60, anchor="e", text_color=TEXT_PRIMARY, font=ctk.CTkFont(size=12)
            ).pack(side="left", padx=12)
            ctk.CTkLabel(
                row, text=format_currency(rb.cost),
                width=100, anchor="e", text_color=TEXT_PRIMARY, font=ctk.CTkFont(size=12)
            ).pack(side="right", padx=12)

    def refresh(self, budget: Optional[CalculatedBudget]):
        """Refresh with new data"""
        self.budget = budget
        # Clear and recreate widgets
        for widget in self.winfo_children():
            widget.destroy()
        self._create_widgets()
