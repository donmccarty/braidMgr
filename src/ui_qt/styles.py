"""
Qt Stylesheet - Matches HTML project viewer exactly
Centralized styling for all views.
"""

# Standard text color for all item text
TEXT_COLOR = "#333333"

# Uniform header color for all groups
GROUP_HEADER_COLOR = "#1a1a2e"

# Type colors - Blue (action) + Slate (outcome) with wide shade ranges
TYPE_COLORS = {
    # Blues - Action-oriented (dark to light)
    "Risk": "#1e3a8a",          # Blue 900 (Navy - darkest)
    "Issue": "#2563eb",         # Blue 600 (medium blue)
    "Action Item": "#60a5fa",   # Blue 400 (lighter blue)
    # Slates - Outcome-oriented (wider spread for distinction)
    "Decision": "#1e293b",      # Slate 800 (very dark gray)
    "Deliverable": "#94a3b8",   # Slate 400 (medium-light gray)
    "Budget": "#e2e8f0",        # Slate 200 (very light gray)
    # Neutral - lightest
    "Plan Item": "#cbd5e1",     # Slate 300 (very light)
}

# Unified semantic colors (use these for consistency)
WARNING_COLOR = "#f39c12"       # Amber - warnings
ACTIVE_COLOR = "#3498db"        # Blue - active/in progress
SUCCESS_COLOR = "#27ae60"       # Green - completed/success
DANGER_COLOR = "#dc3545"        # Red - critical/error
ACCENT_COLOR = "#4dabf7"        # Light blue - links, highlights

# Indicator colors - RYG with severity based on exclamation points
INDICATOR_COLORS = {
    # RED !!! - Most critical
    "Beyond Deadline!!!": "#b91c1c",    # Dark red
    # RED !! - Severe
    "Late Finish!!": "#dc2626",         # Medium red
    "Late Start!!": "#dc2626",          # Medium red
    "Overdue": "#dc2626",
    # AMBER ! - Warning
    "Trending Late!": "#d97706",        # Amber/Orange
    # YELLOW ! - Upcoming attention needed
    "Finishing Soon!": "#eab308",       # Yellow
    "Starting Soon!": "#eab308",        # Yellow
    "Due Soon": "#eab308",
    "Upcoming": "#eab308",
    # YELLOW - Active work
    "In Progress": "#ca8a04",           # Darker yellow
    "Active": "#ca8a04",
    # GREEN - Completed
    "Completed Recently": "#16a34a",    # Bright green
    "Completed": "#86efac",             # Light green
    "Done": "#86efac",                  # Light green
    # GRAY - Inactive/Draft/Cancelled
    "Draft": "#9ca3af",
    "Closed": "#9ca3af",
    "Cancelled": "#9ca3af",
    "Not Started": "#d1d5db",
}

# Indicator to severity mapping (matches index.html indicatorConfig)
INDICATOR_SEVERITY = {
    "Beyond Deadline!!!": "critical",
    "Late Finish!!": "critical",
    "Late Start!!": "critical",
    "Trending Late!": "warning",
    "Finishing Soon!": "upcoming",
    "Starting Soon!": "upcoming",
    "In Progress": "active",
    "Completed Recently": "completed",
    "Completed": "done",
    "Draft": "draft",
}

# Status groups for grouping by status (matches index.html renderActiveItems)
# Groups: Critical, Warning, Upcoming, In Progress, Completed Recently
STATUS_GROUPS = {
    "Critical": {
        "severity": "critical",
        "color": GROUP_HEADER_COLOR,
        "order": 1
    },
    "Warning": {
        "severity": "warning",
        "color": GROUP_HEADER_COLOR,
        "order": 2
    },
    "Upcoming": {
        "severity": "upcoming",
        "color": GROUP_HEADER_COLOR,
        "order": 3
    },
    "In Progress": {
        "severity": "active",
        "color": GROUP_HEADER_COLOR,
        "order": 4
    },
    "Completed Recently": {
        "severity": "completed",
        "color": GROUP_HEADER_COLOR,
        "order": 5
    }
}

# Colors from HTML (legacy, kept for compatibility)
COLORS = {
    # Sidebar
    "sidebar_bg": "#1a1a2e",
    "sidebar_hover": "rgba(255, 255, 255, 0.1)",
    "sidebar_active": "rgba(255, 255, 255, 0.15)",
    "sidebar_text": "rgba(255, 255, 255, 0.7)",
    "sidebar_text_dim": "rgba(255, 255, 255, 0.4)",
    "accent": "#4dabf7",

    # Content
    "content_bg": "#f5f5f5",
    "card_bg": "#ffffff",
    "card_shadow": "rgba(0, 0, 0, 0.1)",

    # Status colors
    "critical": "#dc3545",
    "warning": "#ffc107",
    "active": "#0d6efd",
    "success": "#28a745",
    "neutral": "#6c757d",

    # Type colors
    "risk": "#dc3545",
    "issue": "#fd7e14",
    "action_item": "#0d6efd",
    "decision": "#6f42c1",
    "deliverable": "#28a745",
    "budget": "#20c997",
    "plan_item": "#6c757d",

    # Text
    "text_primary": "#1a1a2e",
    "text_secondary": "#666666",
    "text_muted": "#999999",

    # Deadline pills
    "deadline_overdue_bg": "#f8d7da",
    "deadline_overdue_text": "#721c24",
    "deadline_soon_bg": "#fff3cd",
    "deadline_soon_text": "#856404",
    "deadline_upcoming_bg": "#e2e8f0",
    "deadline_upcoming_text": "#475569",
}

MAIN_STYLESHEET = """
/* Main Window */
QMainWindow {
    background-color: #f5f5f5;
}

/* Sidebar */
#sidebar {
    background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
        stop:0 #1a1a2e, stop:1 #16213e);
    min-width: 220px;
    max-width: 220px;
}

#sidebar_logo {
    color: white;
    font-size: 16px;
    font-weight: bold;
    padding: 16px;
}

#sidebar_section_label {
    color: rgba(255, 255, 255, 0.4);
    font-size: 11px;
    font-weight: bold;
    padding: 12px 16px 4px 16px;
    letter-spacing: 0.5px;
}

/* Nav buttons */
QPushButton#nav_button {
    background: transparent;
    color: rgba(255, 255, 255, 0.7);
    border: none;
    text-align: left;
    padding: 10px 16px;
    font-size: 14px;
}

QPushButton#nav_button:hover {
    background: rgba(255, 255, 255, 0.1);
}

QPushButton#nav_button:checked {
    background: rgba(255, 255, 255, 0.15);
    color: white;
}

/* Active indicator */
#nav_indicator {
    background: transparent;
    min-width: 4px;
    max-width: 4px;
}

#nav_indicator[active="true"] {
    background: #4dabf7;
}

/* Content area */
#content_area {
    background: #f5f5f5;
}

/* Scroll Area */
QScrollArea {
    border: none;
    background: transparent;
}

QScrollArea > QWidget > QWidget {
    background: transparent;
}

QScrollBar:vertical {
    background: #e5e5e5;
    width: 8px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #c0c0c0;
    border-radius: 4px;
    min-height: 30px;
}

QScrollBar::handle:vertical:hover {
    background: #a0a0a0;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0;
}

/* Cards */
QFrame#card {
    background: white;
    border-radius: 8px;
}

/* Stat cards */
QFrame#stat_card {
    background: white;
    border-radius: 8px;
}

QLabel#stat_value {
    font-size: 32px;
    font-weight: bold;
}

QLabel#stat_label {
    font-size: 12px;
    color: #666666;
}

/* Header cards */
QFrame#header_card {
    background: white;
    border-radius: 8px;
}

QLabel#header_value {
    font-size: 48px;
    font-weight: bold;
}

QLabel#header_label {
    font-size: 12px;
    color: #666666;
}

QLabel#header_status {
    font-size: 11px;
    font-weight: bold;
}

/* Section titles */
QLabel#section_title {
    font-size: 16px;
    font-weight: bold;
    color: #1a1a2e;
}

/* Deadline pills */
QFrame#deadline_pill_overdue {
    background: #f8d7da;
    border-radius: 4px;
    padding: 2px 8px;
}

QLabel#deadline_text_overdue {
    color: #721c24;
    font-size: 12px;
}

QFrame#deadline_pill_soon {
    background: #fff3cd;
    border-radius: 4px;
    padding: 2px 8px;
}

QLabel#deadline_text_soon {
    color: #856404;
    font-size: 12px;
}

QFrame#deadline_pill_upcoming {
    background: #e2e8f0;
    border-radius: 4px;
    padding: 2px 8px;
}

QLabel#deadline_text_upcoming {
    color: #475569;
    font-size: 12px;
}

/* Legend items */
QFrame#legend_color {
    border-radius: 3px;
    min-width: 14px;
    max-width: 14px;
    min-height: 14px;
    max-height: 14px;
}

QLabel#legend_label {
    font-size: 12px;
    color: #1a1a2e;
}

QLabel#legend_count {
    font-size: 12px;
    font-weight: bold;
    color: #1a1a2e;
}

/* Action buttons in sidebar */
QPushButton#action_button {
    background: transparent;
    color: rgba(255, 255, 255, 0.7);
    border: none;
    text-align: left;
    padding: 8px 16px;
    font-size: 13px;
}

QPushButton#action_button:hover {
    background: rgba(255, 255, 255, 0.1);
}

/* Status label */
QLabel#status_label {
    color: rgba(255, 255, 255, 0.4);
    font-size: 11px;
    padding: 16px;
}

/* Separator */
QFrame#separator {
    background: rgba(255, 255, 255, 0.1);
    max-height: 1px;
}

/* Card separator */
QFrame#card_separator {
    background: #e0e0e0;
    max-height: 1px;
}

/* Combo Box styling */
QComboBox {
    background: white;
    border: 1px solid #d0d0d0;
    border-radius: 4px;
    padding: 4px 8px;
    color: #1a1a2e;
}

QComboBox:hover {
    border-color: #4dabf7;
}

QComboBox::drop-down {
    border: none;
    width: 20px;
}

QComboBox::down-arrow {
    width: 10px;
    height: 10px;
}

QComboBox QAbstractItemView {
    background: white;
    border: 1px solid #d0d0d0;
    selection-background-color: #4dabf7;
    selection-color: white;
    color: #1a1a2e;
    outline: none;
}

QComboBox QAbstractItemView::item {
    padding: 6px 8px;
    min-height: 24px;
}

QComboBox QAbstractItemView::item:hover {
    background: #e8f4fd;
    color: #1a1a2e;
}

QComboBox QAbstractItemView::item:selected {
    background: #4dabf7;
    color: white;
}
"""
