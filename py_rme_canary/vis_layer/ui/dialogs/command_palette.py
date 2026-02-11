"""Command Palette Dialog (Ctrl+K)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QAction, QKeyEvent
from PyQt6.QtWidgets import (
    QDialog,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QVBoxLayout,
)

from py_rme_canary.vis_layer.ui.theme import get_theme_manager

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


class CommandPalette(QDialog):
    """Fuzzy search command palette for quick access to actions."""

    def __init__(self, editor: QtMapEditor) -> None:
        super().__init__(editor, Qt.WindowType.FramelessWindowHint | Qt.WindowType.Popup)
        self.editor = editor
        self._actions: list[tuple[str, QAction]] = []
        self._setup_ui()
        self._collect_actions()
        self._filter_list("")

    def _setup_ui(self) -> None:
        """Initialize UI components."""
        self.resize(600, 400)

        # Apply theme style
        tm = get_theme_manager()
        self.setStyleSheet(f"""
            QDialog {{
                background-color: {tm.tokens["color"]["surface"]["elevated"]};
                border: 1px solid {tm.tokens["color"]["border"]["strong"]};
                border-radius: {tm.tokens["radius"]["lg"]}px;
            }}
            QLineEdit {{
                background-color: transparent;
                border: none;
                color: {tm.tokens["color"]["text"]["primary"]};
                font-size: 18px;
                padding: 12px;
                border-bottom: 1px solid {tm.tokens["color"]["border"]["default"]};
            }}
            QListWidget {{
                background-color: transparent;
                border: none;
                outline: none;
            }}
            QListWidget::item {{
                padding: 8px 12px;
                color: {tm.tokens["color"]["text"]["primary"]};
                border-radius: {tm.tokens["radius"]["sm"]}px;
            }}
            QListWidget::item:selected {{
                background-color: {tm.tokens["color"]["brand"]["primary"]};
                color: white;
            }}
        """)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Search Input
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Type a command...")
        self.search_input.textChanged.connect(self._filter_list)
        layout.addWidget(self.search_input)

        # Results List
        self.results_list = QListWidget()
        self.results_list.itemActivated.connect(self._execute_selected)
        layout.addWidget(self.results_list)

        # Focus input on show
        QTimer.singleShot(0, self.search_input.setFocus)

    def _collect_actions(self) -> None:
        """Collect all QActions from the editor window."""
        seen_texts = set()

        # Recursively find all QActions in main window
        for child in self.editor.findChildren(QAction):
            text = child.text().replace("&", "")
            if not text or not child.isEnabled() or text in seen_texts:
                continue

            # Skip separator actions or empty ones
            if text == "-" or not child.isVisible():
                continue

            self._actions.append((text, child))
            seen_texts.add(text)

        # Sort alphabetically
        self._actions.sort(key=lambda x: x[0])

    def _filter_list(self, query: str) -> None:
        """Filter commands based on fuzzy search."""
        self.results_list.clear()
        query = query.lower()

        # Simple fuzzy matching: check if all chars in query exist in text in order
        # or just simple substring for now for performance/simplicity

        matches = []
        for text, action in self._actions:
            if not query:
                matches.append((text, action))
                continue

            # Score match
            if query in text.lower():
                matches.append((text, action))

        # Limit results
        for text, action in matches[:20]:
            item = QListWidgetItem(text)

            # Show shortcut if available
            shortcut = action.shortcut().toString()
            if shortcut:
                item.setText(f"{text}   ({shortcut})")

            item.setData(Qt.ItemDataRole.UserRole, action)

            # Add icon if available
            if not action.icon().isNull():
                item.setIcon(action.icon())

            self.results_list.addItem(item)

        if self.results_list.count() > 0:
            self.results_list.setCurrentRow(0)

    def _execute_selected(self, item: QListWidgetItem | None = None) -> None:
        """Execute the selected command."""
        if item is None:
            item = self.results_list.currentItem()

        if not item:
            return

        action = item.data(Qt.ItemDataRole.UserRole)
        if action:
            self.accept()
            action.trigger()

    def keyPressEvent(self, event: QKeyEvent) -> None:
        """Handle keyboard navigation."""
        if event.key() in (Qt.Key.Key_Up, Qt.Key.Key_Down):
            self.results_list.keyPressEvent(event)
        elif event.key() in (Qt.Key.Key_Enter, Qt.Key.Key_Return):
            self._execute_selected()
        elif event.key() == Qt.Key.Key_Escape:
            self.reject()
        else:
            super().keyPressEvent(event)
