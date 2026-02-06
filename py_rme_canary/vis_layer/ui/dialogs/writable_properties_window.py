"""Writable Properties Window - Edit books and readable items.

Dialog for editing text content in writable items (books, scrolls, signs).
Mirrors legacy C++ WritablePropertiesWindow from source/ui/properties/writable_properties_window.cpp.

Reference:
    - C++ WritablePropertiesWindow: source/ui/properties/writable_properties_window.h
    - Item attributes: core/data/item.py
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QFont
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from py_rme_canary.core.data.item import Item
    from py_rme_canary.core.data.tile import Tile

logger = logging.getLogger(__name__)


class WritablePropertiesWindow(QDialog):
    """Dialog for editing writable item properties.

    Allows editing:
    - Action ID / Unique ID
    - Text content (for books, scrolls, signs)

    Signals:
        properties_changed: Emitted when user confirms changes.
    """

    properties_changed = pyqtSignal(dict)  # {action_id, unique_id, text}

    # Maximum text length for writable items
    MAX_TEXT_LENGTH = 4096

    def __init__(
        self,
        item: Item | None = None,
        tile: Tile | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize writable properties window.

        Args:
            item: The writable item to edit (must have readable/writable flag).
            tile: The tile containing the item.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._item = item
        self._tile = tile

        self.setWindowTitle("Edit Text")
        self.setMinimumSize(450, 400)
        self.setModal(True)

        self._setup_ui()
        self._apply_style()
        self._load_values()

    def _setup_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header with item info
        header = QHBoxLayout()
        self._item_label = QLabel("Book")
        self._item_label.setObjectName("headerLabel")
        header.addWidget(self._item_label)
        header.addStretch()
        layout.addLayout(header)

        # ID Fields group
        id_group = QGroupBox("Identifiers")
        id_layout = QFormLayout(id_group)
        id_layout.setSpacing(10)

        self._action_id = QSpinBox()
        self._action_id.setRange(0, 65535)
        self._action_id.setSpecialValueText("None")
        self._action_id.setToolTip("Action ID for scripting")
        id_layout.addRow("Action ID:", self._action_id)

        self._unique_id = QSpinBox()
        self._unique_id.setRange(0, 65535)
        self._unique_id.setSpecialValueText("None")
        self._unique_id.setToolTip("Unique ID (must be unique on map)")
        id_layout.addRow("Unique ID:", self._unique_id)

        layout.addWidget(id_group)

        # Text content group
        text_group = QGroupBox("Text Content")
        text_layout = QVBoxLayout(text_group)
        text_layout.setSpacing(10)

        # Character count label
        self._char_count = QLabel("0 / 4096 characters")
        self._char_count.setObjectName("charCount")
        text_layout.addWidget(self._char_count)

        # Text editor
        self._text_edit = QTextEdit()
        self._text_edit.setPlaceholderText("Enter text content...")
        self._text_edit.setAcceptRichText(False)
        self._text_edit.textChanged.connect(self._on_text_changed)

        # Use monospace font for text editing
        font = QFont("Consolas", 10)
        font.setStyleHint(QFont.StyleHint.Monospace)
        self._text_edit.setFont(font)

        text_layout.addWidget(self._text_edit, 1)

        layout.addWidget(text_group, 1)

        # Writer field (optional, for signed books)
        writer_group = QGroupBox("Metadata")
        writer_layout = QFormLayout(writer_group)

        self._writer_label = QLabel("Unknown")
        self._writer_label.setObjectName("writerLabel")
        writer_layout.addRow("Written by:", self._writer_label)

        layout.addWidget(writer_group)

        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _apply_style(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet(
            """
            QDialog {
                background-color: #1E1E2E;
                color: #CDD6F4;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #45475A;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 12px;
                background-color: #181825;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #8B5CF6;
            }
            QLabel {
                color: #CDD6F4;
            }
            QLabel#headerLabel {
                font-size: 14px;
                font-weight: bold;
                color: #8B5CF6;
            }
            QLabel#charCount {
                font-size: 11px;
                color: #6C7086;
            }
            QLabel#writerLabel {
                color: #A6ADC8;
                font-style: italic;
            }
            QSpinBox {
                background-color: #313244;
                border: 1px solid #45475A;
                border-radius: 4px;
                padding: 6px 10px;
                color: #CDD6F4;
                min-width: 100px;
            }
            QSpinBox:focus {
                border-color: #8B5CF6;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #45475A;
                border: none;
                width: 20px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #585B70;
            }
            QTextEdit {
                background-color: #313244;
                border: 1px solid #45475A;
                border-radius: 6px;
                padding: 10px;
                color: #CDD6F4;
                selection-background-color: #8B5CF6;
            }
            QTextEdit:focus {
                border-color: #8B5CF6;
            }
            QPushButton {
                background-color: #45475A;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                color: #CDD6F4;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #585B70;
            }
            QPushButton:pressed {
                background-color: #8B5CF6;
            }
            QDialogButtonBox QPushButton {
                min-width: 90px;
            }
        """
        )

    def _load_values(self) -> None:
        """Load values from the item."""
        if self._item is None:
            return

        # Get item name
        item_name = getattr(self._item, "name", None) or f"Item #{getattr(self._item, 'id', 0)}"
        self._item_label.setText(item_name)

        # Load Action ID
        action_id = getattr(self._item, "action_id", 0) or 0
        self._action_id.setValue(action_id)

        # Load Unique ID
        unique_id = getattr(self._item, "unique_id", 0) or 0
        self._unique_id.setValue(unique_id)

        # Load text content
        text = getattr(self._item, "text", "") or ""
        self._text_edit.setPlainText(text)

        # Load writer info
        writer = getattr(self._item, "writer", None)
        if writer:
            self._writer_label.setText(writer)
        else:
            self._writer_label.setText("Unknown")

    def _on_text_changed(self) -> None:
        """Handle text content changes - update character count."""
        text = self._text_edit.toPlainText()
        length = len(text)

        # Update character count
        self._char_count.setText(f"{length} / {self.MAX_TEXT_LENGTH} characters")

        # Change color if approaching limit
        if length > self.MAX_TEXT_LENGTH * 0.9:
            self._char_count.setStyleSheet("color: #F38BA8;")  # Red warning
        elif length > self.MAX_TEXT_LENGTH * 0.75:
            self._char_count.setStyleSheet("color: #FAB387;")  # Orange warning
        else:
            self._char_count.setStyleSheet("color: #6C7086;")  # Normal

        # Enforce maximum length
        if length > self.MAX_TEXT_LENGTH:
            cursor = self._text_edit.textCursor()
            pos = cursor.position()
            self._text_edit.setPlainText(text[: self.MAX_TEXT_LENGTH])
            cursor.setPosition(min(pos, self.MAX_TEXT_LENGTH))
            self._text_edit.setTextCursor(cursor)

    def _on_accept(self) -> None:
        """Handle OK button click."""
        properties = {
            "action_id": self._action_id.value() or None,
            "unique_id": self._unique_id.value() or None,
            "text": self._text_edit.toPlainText(),
        }

        # Apply to item if available
        if self._item is not None:
            if hasattr(self._item, "action_id"):
                self._item.action_id = properties["action_id"]
            if hasattr(self._item, "unique_id"):
                self._item.unique_id = properties["unique_id"]
            if hasattr(self._item, "text"):
                self._item.text = properties["text"]

        self.properties_changed.emit(properties)
        self.accept()

    def get_text(self) -> str:
        """Get the current text content.

        Returns:
            The text in the editor.
        """
        return self._text_edit.toPlainText()

    def set_text(self, text: str) -> None:
        """Set the text content.

        Args:
            text: Text to set in the editor.
        """
        self._text_edit.setPlainText(text[: self.MAX_TEXT_LENGTH])

    def get_properties(self) -> dict:
        """Get all properties as a dictionary.

        Returns:
            Dictionary with action_id, unique_id, and text.
        """
        return {
            "action_id": self._action_id.value() or None,
            "unique_id": self._unique_id.value() or None,
            "text": self._text_edit.toPlainText(),
        }
