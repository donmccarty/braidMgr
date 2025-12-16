"""
Help View - Built-in documentation for BRAID Manager
"""

from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QScrollArea, QLabel, QFrame
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont


HELP_CONTENT = """
<style>
    h1 { color: #1a1a2e; font-size: 28px; margin-bottom: 16px; }
    h2 { color: #1a1a2e; font-size: 20px; margin-top: 24px; margin-bottom: 12px; border-bottom: 2px solid #e0e0e0; padding-bottom: 8px; }
    h3 { color: #333; font-size: 16px; margin-top: 16px; margin-bottom: 8px; }
    p { color: #333; font-size: 14px; line-height: 1.6; margin-bottom: 12px; }
    ul { color: #333; font-size: 14px; line-height: 1.8; margin-left: 20px; }
    li { margin-bottom: 6px; }
    .highlight { background: #f0f7ff; padding: 12px; border-radius: 6px; border-left: 4px solid #3b82f6; margin: 12px 0; }
    .item-type { display: inline-block; padding: 2px 8px; border-radius: 4px; font-weight: 600; font-size: 12px; margin-right: 8px; }
    .risk { background: #fee2e2; color: #dc2626; }
    .issue { background: #ffedd5; color: #ea580c; }
    .action { background: #dbeafe; color: #2563eb; }
    .decision { background: #f3e8ff; color: #7c3aed; }
    .deliverable { background: #dcfce7; color: #16a34a; }
    .budget { background: #ccfbf1; color: #0d9488; }
    code { background: #f1f5f9; padding: 2px 6px; border-radius: 4px; font-family: monospace; }
</style>

<h1>BRAID Manager Help</h1>

<p>BRAID Manager helps you track <b>B</b>udget, <b>R</b>isks, <b>A</b>ction Items, <b>I</b>ssues, and <b>D</b>ecisions for your projects.</p>

<h2>Getting Started</h2>

<h3>Creating a New Project</h3>
<p>Click <b>New Project</b> in the sidebar to create a fresh project. Enter a name when prompted. This will replace any existing project data.</p>

<h3>Importing Existing Data</h3>
<p>If you have existing BRAID or Budget YAML files:</p>
<ul>
    <li><b>Import BRAID</b> - Import a BRAID/RAID log YAML file</li>
    <li><b>Import Budget</b> - Import a Budget YAML file</li>
</ul>
<p>Imported files are copied into the app's data folder, keeping your originals safe.</p>

<h3>Exporting Your Data</h3>
<p>Click <b>Export</b> to save copies of your project files to your Downloads folder. Use this to back up your data or share with others.</p>

<h2>Item Types</h2>

<p>BRAID Manager supports several item types, each with a specific purpose:</p>

<p><span class="item-type risk">Risk</span> Something that <i>could</i> impact the project negatively. Track potential problems before they occur.</p>

<p><span class="item-type issue">Issue</span> Something that <i>is currently</i> impacting the project. Active problems that need resolution.</p>

<p><span class="item-type action">Action Item</span> Work assigned to a team member. Tasks that need to be completed.</p>

<p><span class="item-type decision">Decision</span> The outcome of a discussion or choice made. Document key decisions for reference.</p>

<p><span class="item-type deliverable">Deliverable</span> A tangible output to be produced. Track what needs to be delivered.</p>

<p><span class="item-type budget">Budget</span> Financial tracking items. Include budget amounts for cost tracking.</p>

<h2>Navigation Views</h2>

<h3>Dashboard</h3>
<p>Overview of your project with key statistics:</p>
<ul>
    <li>Total items and completion status</li>
    <li>Items by status (Critical, Warning, On Track)</li>
    <li>Budget summary (if budget data is loaded)</li>
</ul>
<p>Click on any statistic card to jump to filtered items.</p>

<h3>Active Items</h3>
<p>Shows items grouped by severity:</p>
<ul>
    <li><b>Critical</b> - Items needing immediate attention (red indicator)</li>
    <li><b>Warning</b> - Items approaching deadlines or at risk (yellow indicator)</li>
    <li><b>Upcoming</b> - Items starting soon or in progress (blue/green indicator)</li>
</ul>
<p>Sections are collapsible - click the header to expand/collapse.</p>

<h3>All Items</h3>
<p>Complete list of all project items in a table format. Features:</p>
<ul>
    <li>Click column headers to sort</li>
    <li>Use the Type filter to show specific item types</li>
    <li>Use Search to find items by title or content</li>
    <li>Double-click any row to edit the item</li>
</ul>

<h3>Timeline</h3>
<p>Visual timeline showing items with start/finish dates. Helpful for seeing project schedule at a glance.</p>

<h3>Chronology</h3>
<p>Activity log showing all dated notes from items, sorted by date (newest first). Great for:</p>
<ul>
    <li>Seeing recent project activity</li>
    <li>Finding when decisions were made</li>
    <li>Tracking progress over time</li>
</ul>
<p>Use Expand All / Collapse All to manage the view. Double-click any entry to edit the source item.</p>

<h3>Budget</h3>
<p>Budget tracking view (requires budget data). Shows:</p>
<ul>
    <li>Total budget and spent amounts</li>
    <li>Burn rate and projections</li>
    <li>Weekly spending breakdown</li>
</ul>

<h2>Adding and Editing Items</h2>

<h3>Editing an Item</h3>
<p>Double-click any item in the All Items, Timeline, or Chronology views to open the edit dialog.</p>

<h3>Item Fields</h3>
<ul>
    <li><b>Title</b> - Brief description of the item</li>
    <li><b>Type</b> - Risk, Issue, Action Item, Decision, Deliverable, or Budget</li>
    <li><b>Workstream</b> - Category or area of the project</li>
    <li><b>Assigned To</b> - Person responsible</li>
    <li><b>Start / Finish</b> - Date range for the item</li>
    <li><b>Deadline</b> - Due date (used for indicator calculations)</li>
    <li><b>% Complete</b> - Progress (0-100%)</li>
    <li><b>Notes</b> - Detailed notes and activity log</li>
</ul>

<h3>Adding Notes</h3>
<p>Use this format for dated notes that appear in Chronology:</p>
<div class="highlight">
<code>> 2024-12-15 - Your Name - Note text goes here...</code>
</div>
<p>Notes without this format are still saved but won't appear in Chronology.</p>

<h2>Managing Item Status</h2>

<p>Item status is controlled by the <b>% Complete</b> field:</p>

<h3>Marking an Item In Progress</h3>
<p>Set <b>% Complete</b> to any value greater than 0 (e.g., 10%, 25%, 50%).</p>
<div class="highlight">
<b>0%</b> = Not Started<br>
<b>1-99%</b> = In Progress<br>
<b>100%</b> = Completed
</div>

<h3>Marking an Item Complete</h3>
<p>Set <b>% Complete</b> to <b>100</b>. The item will show as "Completed" or "Completed Recently" (if finished within the last 2 weeks).</p>

<h3>Reopening a Completed Item</h3>
<p>Set <b>% Complete</b> back to a value less than 100 to reopen a completed item.</p>

<h2>Status Indicators</h2>

<p>Indicators are <b>calculated automatically</b> based on dates, deadlines, and percent complete. You don't set them directly - the system determines them for you.</p>

<h3>Indicator Logic (Priority Order)</h3>
<p>The system checks these conditions in order and assigns the first matching indicator:</p>

<table style="width: 100%; border-collapse: collapse; font-size: 13px; margin: 12px 0;">
<tr style="background: #f8f9fa; border-bottom: 2px solid #dee2e6;">
    <th style="text-align: left; padding: 8px;">Indicator</th>
    <th style="text-align: left; padding: 8px;">Condition</th>
</tr>
<tr style="border-bottom: 1px solid #dee2e6;">
    <td style="padding: 8px;"><span style="color: #dc2626; font-weight: 600;">Beyond Deadline!!!</span></td>
    <td style="padding: 8px;">Deadline has passed</td>
</tr>
<tr style="border-bottom: 1px solid #dee2e6;">
    <td style="padding: 8px;"><span style="color: #dc2626; font-weight: 600;">Late Finish!!</span></td>
    <td style="padding: 8px;">Finish date passed but not 100% complete</td>
</tr>
<tr style="border-bottom: 1px solid #dee2e6;">
    <td style="padding: 8px;"><span style="color: #dc2626; font-weight: 600;">Late Start!!</span></td>
    <td style="padding: 8px;">Start date passed but still at 0%</td>
</tr>
<tr style="border-bottom: 1px solid #dee2e6;">
    <td style="padding: 8px;"><span style="color: #f59e0b; font-weight: 600;">Trending Late!</span></td>
    <td style="padding: 8px;">Remaining work exceeds remaining time</td>
</tr>
<tr style="border-bottom: 1px solid #dee2e6;">
    <td style="padding: 8px;"><span style="color: #0d6efd; font-weight: 600;">Finishing Soon!</span></td>
    <td style="padding: 8px;">Finish date within 2 weeks</td>
</tr>
<tr style="border-bottom: 1px solid #dee2e6;">
    <td style="padding: 8px;"><span style="color: #6f42c1; font-weight: 600;">Starting Soon!</span></td>
    <td style="padding: 8px;">Start date within 2 weeks, not yet started</td>
</tr>
<tr style="border-bottom: 1px solid #dee2e6;">
    <td style="padding: 8px;"><span style="color: #0d6efd; font-weight: 600;">In Progress</span></td>
    <td style="padding: 8px;">% complete is between 1-99%</td>
</tr>
<tr style="border-bottom: 1px solid #dee2e6;">
    <td style="padding: 8px;"><span style="color: #198754; font-weight: 600;">Completed Recently</span></td>
    <td style="padding: 8px;">100% complete, finished within 2 weeks</td>
</tr>
<tr style="border-bottom: 1px solid #dee2e6;">
    <td style="padding: 8px;"><span style="color: #6c757d; font-weight: 600;">Completed</span></td>
    <td style="padding: 8px;">100% complete</td>
</tr>
<tr>
    <td style="padding: 8px;"><span style="color: #6c757d; font-weight: 600;">Not Started</span></td>
    <td style="padding: 8px;">Has dates but 0% complete</td>
</tr>
</table>

<h3>Updating Indicators</h3>
<p>Click <b>Update Indicators</b> in the sidebar to recalculate all indicators based on today's date. Do this daily to keep status colors current.</p>

<h2>Data Storage</h2>

<p>Your project data is stored at:</p>
<div class="highlight">
<code>~/Library/Application Support/BRAID Manager/</code>
</div>
<p>Use <b>Export</b> regularly to back up your data to Downloads.</p>

<h2>Tips</h2>

<ul>
    <li>Use <b>Reload Data</b> if you've edited files externally</li>
    <li>Run <b>Update Indicators</b> daily to keep status colors current</li>
    <li>Double-click items to edit - changes save automatically</li>
    <li>The window title shows your current project name</li>
</ul>
"""


class HelpView(QScrollArea):
    """Help view with built-in documentation"""

    def __init__(self, parent=None):
        super().__init__(parent)

        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.setStyleSheet("QScrollArea { border: none; background: #f5f5f5; }")

        # Container
        container = QWidget()
        container.setStyleSheet("background: #f5f5f5;")
        self.setWidget(container)

        layout = QVBoxLayout(container)
        layout.setContentsMargins(24, 24, 24, 24)
        layout.setSpacing(0)

        # Content card
        card = QFrame()
        card.setStyleSheet("""
            QFrame {
                background: white;
                border-radius: 12px;
                padding: 32px;
            }
        """)

        card_layout = QVBoxLayout(card)
        card_layout.setContentsMargins(32, 32, 32, 32)

        # Help content
        content = QLabel(HELP_CONTENT)
        content.setWordWrap(True)
        content.setTextFormat(Qt.RichText)
        content.setAlignment(Qt.AlignTop | Qt.AlignLeft)
        content.setStyleSheet("background: transparent;")
        card_layout.addWidget(content)

        layout.addWidget(card)
        layout.addStretch()

    def refresh(self, project_data, budget):
        """Refresh - no-op for help view"""
        pass
