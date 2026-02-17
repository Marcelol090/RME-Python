"""Keyboard Shortcuts Help Dialog.

Shows all available keyboard shortcuts in a searchable dialog.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from py_rme_canary.vis_layer.ui.dialogs.base_modern import ModernDialog

if TYPE_CHECKING:
    pass


class ShortcutCategory(QFrame):
    """Category of shortcuts."""

    def __init__(self, title: str, shortcuts: list[tuple[str, str]], parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._title = title
        self._shortcuts = shortcuts
        self._rows: list[QWidget] = []

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Title
        title = QLabel(self._title)
        title.setStyleSheet(
            """
            font-size: 13px;
            font-weight: 700;
            color: #8B5CF6;
            padding-bottom: 4px;
        """
        )
        layout.addWidget(title)

        # Shortcuts
        for key, description in self._shortcuts:
            row = QFrame()
            row_layout = QHBoxLayout(row)
            row_layout.setContentsMargins(8, 4, 8, 4)

            # Key
            key_label = QLabel(key)
            key_label.setStyleSheet(
                """
                background: #363650;
                color: #E5E5E7;
                padding: 4px 8px;
                border-radius: 4px;
                font-family: monospace;
                font-weight: 600;
            """
            )
            key_label.setFixedWidth(120)
            row_layout.addWidget(key_label)

            # Description
            desc_label = QLabel(description)
            desc_label.setStyleSheet("color: #A1A1AA;")
            row_layout.addWidget(desc_label)
            row_layout.addStretch()

            layout.addWidget(row)
            self._rows.append(row)

    def _apply_style(self) -> None:
        """Apply styling."""
        self.setStyleSheet(
            """
            ShortcutCategory {
                background: #2A2A3E;
                border: 1px solid #363650;
                border-radius: 8px;
            }
        """
        )

    def filter_shortcuts(self, query: str) -> bool:
        """Filter shortcuts by query. Returns True if any visible."""
        query = query.lower()
        visible_count = 0

        for i, (key, desc) in enumerate(self._shortcuts):
            visible = not query or query in key.lower() or query in desc.lower()
            self._rows[i].setVisible(visible)
            if visible:
                visible_count += 1

        self.setVisible(visible_count > 0 or not query)
        return visible_count > 0


class KeyboardShortcutsDialog(ModernDialog):
    """Dialog showing all keyboard shortcuts."""

    SHORTCUTS = {
        "File": [
            ("Ctrl+N", "New map"),
            ("Ctrl+O", "Open map"),
            ("Ctrl+S", "Save map"),
            ("Ctrl+Shift+S", "Save as"),
            ("Ctrl+W", "Close map"),
        ],
        "Edit": [
            ("Ctrl+Z", "Undo"),
            ("Ctrl+Y", "Redo"),
            ("Ctrl+C", "Copy"),
            ("Ctrl+X", "Cut"),
            ("Ctrl+V", "Paste"),
            ("Del", "Delete selection"),
            ("Ctrl+A", "Select all"),
            ("Escape", "Deselect / Cancel"),
        ],
        "View": [
            ("Ctrl++", "Zoom in"),
            ("Ctrl+-", "Zoom out"),
            ("Ctrl+0", "Reset zoom"),
            ("PgUp", "Floor up"),
            ("PgDn", "Floor down"),
            ("F3", "Toggle grid"),
            ("F5", "Refresh view"),
        ],
        "Tools": [
            ("V", "Selection tool"),
            ("B", "Brush / Draw"),
            ("E", "Eraser"),
            ("G", "Fill / Bucket"),
            ("M", "Rectangle select"),
            ("I", "Color picker"),
            ("Q", "Toggle brush shape"),
            ("A", "Toggle automagic"),
            ("[", "Decrease brush size"),
            ("]", "Increase brush size"),
        ],
        "Navigation": [
            ("Ctrl+G", "Go to position"),
            ("Ctrl+F", "Find"),
            ("Ctrl+Shift+F", "Global search"),
            ("Space+Drag", "Pan view"),
            ("Middle Click", "Pan view"),
        ],
    }

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent, title="Keyboard Shortcuts")

        self._categories: list[ShortcutCategory] = []

        self.setMinimumSize(500, 600)
        # ModernDialog is modal and frameless by default

        self._setup_ui()
        # self._apply_style() # Dialog style handled by ModernDialog

    def _setup_ui(self) -> None:
        """Initialize UI."""
        # Use existing content layout
        layout = self.content_layout
        layout.setSpacing(12)
        layout.setContentsMargins(20, 20, 20, 20)

        # Search
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Search shortcuts...")
        self.search_input.textChanged.connect(self._on_search)

        # Style search input (keep custom style for specific widget)
        self.search_input.setStyleSheet(
            """
            QLineEdit {
                background: #2A2A3E;
                border: 2px solid #363650;
                border-radius: 8px;
                padding: 10px 14px;
                color: #E5E5E7;
                font-size: 14px;
            }

            QLineEdit:focus {
                border-color: #8B5CF6;
            }
            """
        )
        layout.addWidget(self.search_input)

        # Scroll area
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        # Transparent background to blend with ModernDialog
        scroll.setStyleSheet(
            """
            QScrollArea { background: transparent; border: none; }
            QScrollBar:vertical {
                background: #1E1E2E;
                width: 8px;
                border-radius: 4px;
            }

            QScrollBar::handle:vertical {
                background: #363650;
                border-radius: 4px;
            }

            QScrollBar::handle:vertical:hover {
                background: #8B5CF6;
            }
            """
        )

        content = QWidget()
        content.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        content_layout = QVBoxLayout(content)
        content_layout.setSpacing(12)
        content_layout.setContentsMargins(0, 0, 0, 0)

        # Categories
        for title, shortcuts in self.SHORTCUTS.items():
            category = ShortcutCategory(title, shortcuts)
            content_layout.addWidget(category)
            self._categories.append(category)

        content_layout.addStretch()

        scroll.setWidget(content)
        layout.addWidget(scroll)

        # Add Close button to footer
        self.add_button("Close", self.close)

    def _on_search(self, query: str) -> None:
        """Filter shortcuts by search query."""
        for category in self._categories:
            category.filter_shortcuts(query)
