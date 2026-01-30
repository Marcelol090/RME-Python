"""Undo/Redo History Panel.

Visual history of actions with ability to jump to any point.
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    pass


class HistoryEntry:
    """Single history entry."""

    def __init__(
        self,
        action_name: str,
        icon: str = "✏️",
        details: str = "",
        timestamp: float = 0.0
    ) -> None:
        self.action_name = action_name
        self.icon = icon
        self.details = details
        self.timestamp = timestamp


class UndoRedoPanel(QFrame):
    """Panel showing undo/redo history.

    Signals:
        jump_to_index: Emits index to jump to
    """

    jump_to_index = pyqtSignal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._entries: list[HistoryEntry] = []
        self._current_index = -1

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Header
        header = QHBoxLayout()

        title = QLabel("📜 History")
        title.setStyleSheet("font-size: 13px; font-weight: 600; color: #E5E5E7;")
        header.addWidget(title)

        header.addStretch()

        self.count_label = QLabel("0 actions")
        self.count_label.setStyleSheet("color: #A1A1AA; font-size: 11px;")
        header.addWidget(self.count_label)

        layout.addLayout(header)

        # History list
        self.history_list = QListWidget()
        self.history_list.itemClicked.connect(self._on_item_clicked)
        layout.addWidget(self.history_list)

        # Buttons
        button_row = QHBoxLayout()
        button_row.setSpacing(8)

        self.btn_undo = QPushButton("↩ Undo")
        self.btn_undo.setEnabled(False)
        self.btn_undo.clicked.connect(self._undo)
        button_row.addWidget(self.btn_undo)

        self.btn_redo = QPushButton("↪ Redo")
        self.btn_redo.setEnabled(False)
        self.btn_redo.clicked.connect(self._redo)
        button_row.addWidget(self.btn_redo)

        layout.addLayout(button_row)

    def _apply_style(self) -> None:
        """Apply styling."""
        self.setStyleSheet("""
            UndoRedoPanel {
                background: #2A2A3E;
                border: 1px solid #363650;
                border-radius: 10px;
            }

            QListWidget {
                background: #1E1E2E;
                border: 1px solid #363650;
                border-radius: 6px;
                color: #E5E5E7;
                outline: none;
            }

            QListWidget::item {
                padding: 6px 10px;
                border-radius: 4px;
                margin: 1px 2px;
            }

            QListWidget::item:hover {
                background: #363650;
            }

            QListWidget::item:selected {
                background: #8B5CF6;
            }

            QPushButton {
                background: #363650;
                color: #E5E5E7;
                border: none;
                border-radius: 6px;
                padding: 6px 12px;
                font-size: 11px;
            }

            QPushButton:hover {
                background: #8B5CF6;
            }

            QPushButton:disabled {
                background: #2A2A3E;
                color: #52525B;
            }
        """)

    def add_entry(self, entry: HistoryEntry) -> None:
        """Add a history entry."""
        # Remove any entries after current index (redo stack)
        if self._current_index < len(self._entries) - 1:
            self._entries = self._entries[:self._current_index + 1]

        self._entries.append(entry)
        self._current_index = len(self._entries) - 1

        self._refresh_list()

    def _refresh_list(self) -> None:
        """Refresh the history list display."""
        self.history_list.clear()

        for i, entry in enumerate(self._entries):
            text = f"{entry.icon} {entry.action_name}"
            if entry.details:
                text += f"\n   {entry.details}"

            item = QListWidgetItem(text)
            item.setData(Qt.ItemDataRole.UserRole, i)

            # Dim items after current index (redo stack)
            if i > self._current_index:
                item.setForeground(Qt.GlobalColor.gray)

            self.history_list.addItem(item)

        # Select current item
        if 0 <= self._current_index < self.history_list.count():
            self.history_list.setCurrentRow(self._current_index)

        # Update count
        self.count_label.setText(f"{len(self._entries)} action{'s' if len(self._entries) != 1 else ''}")

        # Update buttons
        self.btn_undo.setEnabled(self._current_index >= 0)
        self.btn_redo.setEnabled(self._current_index < len(self._entries) - 1)

    def _on_item_clicked(self, item: QListWidgetItem) -> None:
        """Handle click on history item."""
        index = item.data(Qt.ItemDataRole.UserRole)
        if index is not None and index != self._current_index:
            self._current_index = index
            self._refresh_list()
            self.jump_to_index.emit(index)

    def _undo(self) -> None:
        """Undo one step."""
        if self._current_index >= 0:
            self._current_index -= 1
            self._refresh_list()
            self.jump_to_index.emit(self._current_index)

    def _redo(self) -> None:
        """Redo one step."""
        if self._current_index < len(self._entries) - 1:
            self._current_index += 1
            self._refresh_list()
            self.jump_to_index.emit(self._current_index)

    def set_current_index(self, index: int) -> None:
        """Set current history index."""
        if 0 <= index < len(self._entries):
            self._current_index = index
            self._refresh_list()

    def clear_history(self) -> None:
        """Clear all history."""
        self._entries.clear()
        self._current_index = -1
        self._refresh_list()


class QuickUndoRedo(QFrame):
    """Compact undo/redo buttons for toolbar.

    Signals:
        undo_clicked
        redo_clicked
    """

    undo_clicked = pyqtSignal()
    redo_clicked = pyqtSignal()

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._undo_count = 0
        self._redo_count = 0

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(2)

        self.btn_undo = QPushButton("↩")
        self.btn_undo.setFixedSize(32, 28)
        self.btn_undo.setToolTip("Undo (Ctrl+Z)")
        self.btn_undo.clicked.connect(self.undo_clicked.emit)
        layout.addWidget(self.btn_undo)

        self.btn_redo = QPushButton("↪")
        self.btn_redo.setFixedSize(32, 28)
        self.btn_redo.setToolTip("Redo (Ctrl+Y)")
        self.btn_redo.clicked.connect(self.redo_clicked.emit)
        layout.addWidget(self.btn_redo)

    def _apply_style(self) -> None:
        """Apply styling."""
        self.setStyleSheet("""
            QuickUndoRedo {
                background: transparent;
            }

            QPushButton {
                background: #363650;
                color: #E5E5E7;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: 700;
            }

            QPushButton:hover {
                background: #8B5CF6;
            }

            QPushButton:disabled {
                background: #2A2A3E;
                color: #52525B;
            }
        """)

    def set_counts(self, undo_count: int, redo_count: int) -> None:
        """Update undo/redo counts."""
        self._undo_count = undo_count
        self._redo_count = redo_count

        self.btn_undo.setEnabled(undo_count > 0)
        self.btn_redo.setEnabled(redo_count > 0)

        self.btn_undo.setToolTip(f"Undo (Ctrl+Z) - {undo_count} available")
        self.btn_redo.setToolTip(f"Redo (Ctrl+Y) - {redo_count} available")
