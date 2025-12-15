"""
Edit Item Dialog - PySide6 Version
Modal dialog for viewing and editing RAID items.
"""

from PySide6.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QGridLayout,
    QLabel, QLineEdit, QTextEdit, QTextBrowser, QComboBox, QSpinBox,
    QDateEdit, QCheckBox, QPushButton, QFrame, QScrollArea,
    QWidget, QSizePolicy, QGraphicsDropShadowEffect
)
from PySide6.QtCore import Qt, QDate, Signal
from PySide6.QtGui import QColor, QFont
from typing import Optional
from datetime import date

from src.core.models import Item, ProjectMetadata
from src.ui_qt.styles import TYPE_COLORS, INDICATOR_COLORS
from src.ui_qt.views.chronology import urls_to_links


class EditItemDialog(QDialog):
    """Dialog for viewing/editing a RAID item"""

    # Signal emitted when item is saved (item_num)
    item_saved = Signal(int)

    def __init__(self, item: Item, metadata: ProjectMetadata, parent=None):
        super().__init__(parent)
        self.item = item
        self.metadata = metadata
        self.is_new = item.item_num is None  # New item flag (None, not 0)

        # Use item title in window title, fall back to item number
        if self.is_new:
            title = "New Item"
        elif item.title:
            title = f"#{item.item_num}: {item.title}"
        else:
            title = f"Edit Item #{item.item_num}"
        self.setWindowTitle(title)
        self.setMinimumSize(700, 600)
        self.setMaximumSize(900, 800)
        self.setModal(True)

        # Style
        self.setStyleSheet("""
            QDialog {
                background: #f5f5f5;
            }
            QLabel {
                color: #333333;
                font-size: 13px;
            }
            QLabel#field_label {
                font-weight: bold;
                color: #1a1a2e;
            }
            QLabel#section_header {
                font-size: 14px;
                font-weight: bold;
                color: #1a1a2e;
                padding: 8px 0 4px 0;
            }
            QLineEdit, QTextEdit, QComboBox, QSpinBox, QDateEdit {
                padding: 8px;
                border: 1px solid #d0d0d0;
                border-radius: 4px;
                background: white;
                color: #333333;
                font-size: 13px;
            }
            QLineEdit:focus, QTextEdit:focus, QComboBox:focus, QSpinBox:focus, QDateEdit:focus {
                border-color: #4dabf7;
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
                border: 1px solid #d0d0d0;
                selection-background-color: #4dabf7;
                selection-color: white;
            }
            QCheckBox {
                color: #333333;
                font-size: 13px;
            }
            QCheckBox::indicator {
                width: 18px;
                height: 18px;
            }
            QPushButton {
                padding: 10px 24px;
                border-radius: 4px;
                font-size: 13px;
                font-weight: bold;
            }
            QPushButton#primary_btn {
                background: #0d6efd;
                color: white;
                border: none;
            }
            QPushButton#primary_btn:hover {
                background: #0b5ed7;
            }
            QPushButton#secondary_btn {
                background: white;
                color: #333333;
                border: 1px solid #d0d0d0;
            }
            QPushButton#secondary_btn:hover {
                background: #f8f9fa;
            }
            QPushButton#danger_btn {
                background: #dc3545;
                color: white;
                border: none;
            }
            QPushButton#danger_btn:hover {
                background: #bb2d3b;
            }
            QFrame#separator {
                background: #e0e0e0;
            }
        """)

        self._build_ui()
        self._populate_fields()

    def _build_ui(self):
        """Build the dialog UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Header
        header = QFrame()
        header.setStyleSheet("background: white; border-bottom: 1px solid #e0e0e0;")
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(20, 16, 20, 16)

        # Item number and type pill
        header_left = QHBoxLayout()

        if not self.is_new:
            item_num_label = QLabel(f"#{self.item.item_num}")
            item_num_label.setStyleSheet("font-size: 18px; font-weight: bold; color: #1a1a2e;")
            header_left.addWidget(item_num_label)

        # Type pill (will be updated when type changes)
        self.type_pill = QLabel(self.item.type or "Plan Item")
        type_color = TYPE_COLORS.get(self.item.type or "Plan Item", "#6c757d")
        self.type_pill.setStyleSheet(f"""
            background: {type_color};
            color: white;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        """)
        header_left.addWidget(self.type_pill)
        header_left.addStretch()

        header_layout.addLayout(header_left)

        # Indicator pill (display only)
        if self.item.indicator:
            ind_color = INDICATOR_COLORS.get(self.item.indicator, "#6c757d")
            ind_label = QLabel(self.item.indicator)
            ind_label.setStyleSheet(f"""
                background: {ind_color};
                color: white;
                padding: 4px 12px;
                border-radius: 4px;
                font-size: 12px;
            """)
            header_layout.addWidget(ind_label)

        layout.addWidget(header)

        # Scrollable content area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("QScrollArea { border: none; background: #f5f5f5; }")

        content = QWidget()
        content.setStyleSheet("background: #f5f5f5;")
        content_layout = QVBoxLayout(content)
        content_layout.setContentsMargins(20, 16, 20, 16)
        content_layout.setSpacing(16)

        # === Basic Info Section ===
        basic_section = QLabel("Basic Information")
        basic_section.setObjectName("section_header")
        content_layout.addWidget(basic_section)

        basic_grid = QGridLayout()
        basic_grid.setSpacing(12)

        # Title
        basic_grid.addWidget(self._create_label("Title"), 0, 0)
        self.title_edit = QLineEdit()
        self.title_edit.setPlaceholderText("Enter item title...")
        basic_grid.addWidget(self.title_edit, 0, 1, 1, 3)

        # Type
        basic_grid.addWidget(self._create_label("Type"), 1, 0)
        self.type_combo = QComboBox()
        self.type_combo.addItems(["Plan Item", "Risk", "Issue", "Action Item", "Decision", "Deliverable", "Budget"])
        self.type_combo.currentTextChanged.connect(self._on_type_changed)
        basic_grid.addWidget(self.type_combo, 1, 1)

        # Workstream
        basic_grid.addWidget(self._create_label("Workstream"), 1, 2)
        self.workstream_combo = QComboBox()
        self.workstream_combo.setEditable(True)
        self.workstream_combo.addItem("")  # Empty option
        if self.metadata and self.metadata.workstreams:
            self.workstream_combo.addItems(self.metadata.workstreams)
        basic_grid.addWidget(self.workstream_combo, 1, 3)

        # Assigned To
        basic_grid.addWidget(self._create_label("Assigned To"), 2, 0)
        self.assignee_combo = QComboBox()
        self.assignee_combo.setEditable(True)
        self.assignee_combo.addItem("")  # Empty option
        # Will be populated with existing assignees
        basic_grid.addWidget(self.assignee_combo, 2, 1)

        # Priority
        basic_grid.addWidget(self._create_label("Priority"), 2, 2)
        self.priority_combo = QComboBox()
        self.priority_combo.addItems(["", "High", "Medium", "Low"])
        basic_grid.addWidget(self.priority_combo, 2, 3)

        content_layout.addLayout(basic_grid)

        # Description
        content_layout.addWidget(self._create_label("Description"))
        self.description_edit = QTextEdit()
        self.description_edit.setPlaceholderText("Enter description...")
        self.description_edit.setMinimumHeight(80)
        self.description_edit.setMaximumHeight(120)
        content_layout.addWidget(self.description_edit)

        # === Dates Section ===
        dates_section = QLabel("Dates & Progress")
        dates_section.setObjectName("section_header")
        content_layout.addWidget(dates_section)

        dates_grid = QGridLayout()
        dates_grid.setSpacing(12)

        # Start Date
        dates_grid.addWidget(self._create_label("Start"), 0, 0)
        self.start_edit = QDateEdit()
        self.start_edit.setCalendarPopup(True)
        self.start_edit.setDisplayFormat("MM/dd/yyyy")
        self.start_edit.setSpecialValueText("Not set")
        dates_grid.addWidget(self.start_edit, 0, 1)

        # Finish Date
        dates_grid.addWidget(self._create_label("Finish"), 0, 2)
        self.finish_edit = QDateEdit()
        self.finish_edit.setCalendarPopup(True)
        self.finish_edit.setDisplayFormat("MM/dd/yyyy")
        self.finish_edit.setSpecialValueText("Not set")
        dates_grid.addWidget(self.finish_edit, 0, 3)

        # Deadline
        dates_grid.addWidget(self._create_label("Deadline"), 1, 0)
        self.deadline_edit = QDateEdit()
        self.deadline_edit.setCalendarPopup(True)
        self.deadline_edit.setDisplayFormat("MM/dd/yyyy")
        self.deadline_edit.setSpecialValueText("Not set")
        dates_grid.addWidget(self.deadline_edit, 1, 1)

        # Percent Complete
        dates_grid.addWidget(self._create_label("% Complete"), 1, 2)
        pct_layout = QHBoxLayout()
        self.percent_spin = QSpinBox()
        self.percent_spin.setRange(0, 100)
        self.percent_spin.setSuffix("%")
        pct_layout.addWidget(self.percent_spin)
        pct_layout.addStretch()
        dates_grid.addLayout(pct_layout, 1, 3)

        content_layout.addLayout(dates_grid)

        # === Options Section ===
        options_section = QLabel("Options")
        options_section.setObjectName("section_header")
        content_layout.addWidget(options_section)

        options_layout = QHBoxLayout()
        self.draft_check = QCheckBox("Draft (not active)")
        self.client_visible_check = QCheckBox("Client Visible")
        options_layout.addWidget(self.draft_check)
        options_layout.addWidget(self.client_visible_check)
        options_layout.addStretch()
        content_layout.addLayout(options_layout)

        # Budget Amount (only for Budget type)
        self.budget_frame = QFrame()
        budget_layout = QHBoxLayout(self.budget_frame)
        budget_layout.setContentsMargins(0, 8, 0, 0)
        budget_layout.addWidget(self._create_label("Budget Amount"))
        self.budget_spin = QSpinBox()
        self.budget_spin.setRange(0, 99999999)
        self.budget_spin.setPrefix("$")
        self.budget_spin.setSingleStep(1000)
        budget_layout.addWidget(self.budget_spin)
        budget_layout.addStretch()
        content_layout.addWidget(self.budget_frame)
        self.budget_frame.setVisible(False)  # Hidden by default

        # === Notes Section ===
        notes_section = QLabel("Notes")
        notes_section.setObjectName("section_header")
        content_layout.addWidget(notes_section)

        # Notes display with rich text for clickable links (read-only mode)
        # and plain text edit (edit mode)
        self.notes_edit = QTextBrowser()
        self.notes_edit.setPlaceholderText("Enter notes (use > DATE - TEXT format)...")
        self.notes_edit.setMinimumHeight(120)
        self.notes_edit.setReadOnly(True)  # Read-only by default, shows formatted text
        self.notes_edit.setOpenExternalLinks(True)  # QTextBrowser supports this
        content_layout.addWidget(self.notes_edit)

        # Edit button to switch to edit mode
        edit_notes_btn = QPushButton("Edit Notes")
        edit_notes_btn.setObjectName("secondary_btn")
        edit_notes_btn.setMaximumWidth(120)
        edit_notes_btn.clicked.connect(self._toggle_notes_edit)
        content_layout.addWidget(edit_notes_btn)
        self.edit_notes_btn = edit_notes_btn
        self._notes_edit_mode = False

        # === Metadata (display only) ===
        if self.item.created_date or self.item.last_updated:
            meta_section = QLabel("Metadata")
            meta_section.setObjectName("section_header")
            content_layout.addWidget(meta_section)

            meta_layout = QHBoxLayout()
            if self.item.created_date:
                created_label = QLabel(f"Created: {self.item.created_date.strftime('%m/%d/%Y')}")
                created_label.setStyleSheet("color: #666666; font-size: 12px;")
                meta_layout.addWidget(created_label)
            if self.item.last_updated:
                updated_label = QLabel(f"Last Updated: {self.item.last_updated.strftime('%m/%d/%Y')}")
                updated_label.setStyleSheet("color: #666666; font-size: 12px;")
                meta_layout.addWidget(updated_label)
            meta_layout.addStretch()
            content_layout.addLayout(meta_layout)

        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Footer with buttons
        footer = QFrame()
        footer.setStyleSheet("background: white; border-top: 1px solid #e0e0e0;")
        footer_layout = QHBoxLayout(footer)
        footer_layout.setContentsMargins(20, 12, 20, 12)

        # Cancel button
        cancel_btn = QPushButton("Cancel")
        cancel_btn.setObjectName("secondary_btn")
        cancel_btn.clicked.connect(self.reject)
        footer_layout.addWidget(cancel_btn)

        footer_layout.addStretch()

        # Save button
        save_btn = QPushButton("Save Changes" if not self.is_new else "Create Item")
        save_btn.setObjectName("primary_btn")
        save_btn.clicked.connect(self._save_item)
        footer_layout.addWidget(save_btn)

        layout.addWidget(footer)

    def _create_label(self, text: str) -> QLabel:
        """Create a field label"""
        label = QLabel(text)
        label.setObjectName("field_label")
        return label

    def _populate_fields(self):
        """Populate fields with item data"""
        self.title_edit.setText(self.item.title or "")

        # Type
        idx = self.type_combo.findText(self.item.type or "Plan Item")
        if idx >= 0:
            self.type_combo.setCurrentIndex(idx)

        # Workstream
        if self.item.workstream:
            idx = self.workstream_combo.findText(self.item.workstream)
            if idx >= 0:
                self.workstream_combo.setCurrentIndex(idx)
            else:
                self.workstream_combo.setCurrentText(self.item.workstream)

        # Assigned To
        if self.item.assigned_to:
            self.assignee_combo.setCurrentText(self.item.assigned_to)

        # Priority
        if self.item.priority:
            idx = self.priority_combo.findText(self.item.priority)
            if idx >= 0:
                self.priority_combo.setCurrentIndex(idx)

        # Description
        self.description_edit.setPlainText(self.item.description or "")

        # Dates
        if self.item.start and not isinstance(self.item.start, str):
            self.start_edit.setDate(QDate(self.item.start.year, self.item.start.month, self.item.start.day))
        else:
            self.start_edit.setDate(QDate.currentDate())
            self.start_edit.setDate(self.start_edit.minimumDate())  # Clear to "Not set"

        if self.item.finish and not isinstance(self.item.finish, str):
            self.finish_edit.setDate(QDate(self.item.finish.year, self.item.finish.month, self.item.finish.day))
        else:
            self.finish_edit.setDate(self.finish_edit.minimumDate())

        if self.item.deadline and not isinstance(self.item.deadline, str):
            self.deadline_edit.setDate(QDate(self.item.deadline.year, self.item.deadline.month, self.item.deadline.day))
        else:
            self.deadline_edit.setDate(self.deadline_edit.minimumDate())

        # Percent complete
        self.percent_spin.setValue(self.item.percent_complete or 0)

        # Options
        self.draft_check.setChecked(self.item.draft)
        self.client_visible_check.setChecked(self.item.client_visible)

        # Budget amount
        if self.item.budget_amount:
            self.budget_spin.setValue(int(self.item.budget_amount))

        # Notes - store raw text and display formatted
        self._raw_notes = self.item.notes or ""
        self._show_formatted_notes()

        # Show budget field if type is Budget
        self._on_type_changed(self.item.type or "Plan Item")

    def _on_type_changed(self, type_text: str):
        """Handle type combo change"""
        # Update type pill color
        type_color = TYPE_COLORS.get(type_text, "#6c757d")
        self.type_pill.setText(type_text)
        self.type_pill.setStyleSheet(f"""
            background: {type_color};
            color: white;
            padding: 4px 12px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: bold;
        """)

        # Show/hide budget field
        self.budget_frame.setVisible(type_text == "Budget")

    def _show_formatted_notes(self):
        """Show notes with clickable links (read-only mode)"""
        if self._raw_notes:
            notes_html = urls_to_links(self._raw_notes).replace('\n', '<br>')
            self.notes_edit.setHtml(notes_html)
        else:
            self.notes_edit.setHtml("<i style='color: #999;'>No notes</i>")
        self.notes_edit.setReadOnly(True)
        self.edit_notes_btn.setText("Edit Notes")
        self._notes_edit_mode = False

    def _toggle_notes_edit(self):
        """Toggle between view and edit mode for notes"""
        if self._notes_edit_mode:
            # Save and switch to view mode
            self._raw_notes = self.notes_edit.toPlainText()
            self._show_formatted_notes()
        else:
            # Switch to edit mode
            self.notes_edit.setPlainText(self._raw_notes)
            self.notes_edit.setReadOnly(False)
            self.edit_notes_btn.setText("Done Editing")
            self._notes_edit_mode = True
            self.notes_edit.setFocus()

    def _save_item(self):
        """Save changes to the item"""
        # Update item with field values
        self.item.title = self.title_edit.text().strip()
        self.item.type = self.type_combo.currentText()
        self.item.workstream = self.workstream_combo.currentText().strip() or None
        self.item.assigned_to = self.assignee_combo.currentText().strip() or None
        self.item.priority = self.priority_combo.currentText() or None
        self.item.description = self.description_edit.toPlainText().strip() or None

        # Dates - check if set
        start_date = self.start_edit.date()
        if start_date != self.start_edit.minimumDate():
            self.item.start = date(start_date.year(), start_date.month(), start_date.day())
        else:
            self.item.start = None

        finish_date = self.finish_edit.date()
        if finish_date != self.finish_edit.minimumDate():
            self.item.finish = date(finish_date.year(), finish_date.month(), finish_date.day())
        else:
            self.item.finish = None

        deadline_date = self.deadline_edit.date()
        if deadline_date != self.deadline_edit.minimumDate():
            self.item.deadline = date(deadline_date.year(), deadline_date.month(), deadline_date.day())
        else:
            self.item.deadline = None

        self.item.percent_complete = self.percent_spin.value()
        self.item.draft = self.draft_check.isChecked()
        self.item.client_visible = self.client_visible_check.isChecked()

        if self.item.type == "Budget":
            self.item.budget_amount = self.budget_spin.value() or None
        else:
            self.item.budget_amount = None

        # If in edit mode, get current text; otherwise use stored raw notes
        if self._notes_edit_mode:
            self._raw_notes = self.notes_edit.toPlainText()
        self.item.notes = self._raw_notes.strip() or None

        # Update last_updated
        self.item.last_updated = date.today()

        # Emit signal
        self.item_saved.emit(self.item.item_num)

        # Close dialog
        self.accept()

    def populate_assignees(self, assignees: list[str]):
        """Populate assignee combo with existing assignees"""
        self.assignee_combo.clear()
        self.assignee_combo.addItem("")
        for assignee in sorted(set(assignees)):
            if assignee:
                self.assignee_combo.addItem(assignee)
        # Re-set current value
        if self.item.assigned_to:
            self.assignee_combo.setCurrentText(self.item.assigned_to)

    def get_updated_item(self) -> Item:
        """Get the updated item"""
        return self.item
