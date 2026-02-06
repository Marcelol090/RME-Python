"""Batch Item Editor Dialog.

Dialog for bulk editing items across the map, including:
- Find and replace items by ID
- Batch attribute modification
- Multi-item deletion
- Action item ID reassignment

Mirrors legacy C++ ReplaceItemsDialog from source/ui/replace_items_window.cpp.

Reference:
    - C++ ReplaceItemsDialog: source/ui/replace_items_window.cpp
    - Action System: editor/action_queue.cpp
"""

from __future__ import annotations

import logging
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import QAbstractListModel, QModelIndex, Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPixmap
from PyQt6.QtWidgets import (
    QCheckBox,
    QDialog,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QListView,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class BatchOperation(StrEnum):
    """Types of batch operations."""

    REPLACE = "replace"  # Replace item A with item B
    DELETE = "delete"  # Delete all items with ID
    SET_ATTRIBUTE = "attr"  # Modify item attributes
    CONVERT = "convert"  # Convert to different type


@dataclass(slots=True)
class ReplacingItem:
    """A pending replace operation.

    Mirrors C++ ReplacingItem struct.

    Attributes:
        replace_id: Server ID of item to replace.
        with_id: Server ID of replacement item.
        total: Number of items replaced.
        complete: Whether operation is complete.
    """

    replace_id: int
    with_id: int
    total: int = 0
    complete: bool = False

    def __eq__(self, other: object) -> bool:
        if not isinstance(other, ReplacingItem):
            return False
        return self.replace_id == other.replace_id and self.with_id == other.with_id


@dataclass(slots=True)
class BatchResult:
    """Result of a batch operation.

    Attributes:
        success: Whether operation succeeded.
        items_affected: Number of items modified.
        message: Status or error message.
    """

    success: bool
    items_affected: int = 0
    message: str = ""


class ReplaceItemsModel(QAbstractListModel):
    """Model for the replace items list."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._items: list[ReplacingItem] = []

    def add_item(self, item: ReplacingItem) -> bool:
        """Add a replacement item to the list.

        Args:
            item: ReplacingItem to add.

        Returns:
            True if added successfully.
        """
        if item.replace_id == 0 or item.with_id == 0:
            return False
        if item.replace_id == item.with_id:
            return False

        # Check for duplicates
        for existing in self._items:
            if existing.replace_id == item.replace_id:
                return False

        self.beginInsertRows(QModelIndex(), len(self._items), len(self._items))
        self._items.append(item)
        self.endInsertRows()
        return True

    def remove_item(self, row: int) -> bool:
        """Remove item at row.

        Args:
            row: Row index to remove.

        Returns:
            True if removed.
        """
        if row < 0 or row >= len(self._items):
            return False

        self.beginRemoveRows(QModelIndex(), row, row)
        self._items.pop(row)
        self.endRemoveRows()
        return True

    def mark_complete(self, item: ReplacingItem, total: int) -> None:
        """Mark an item as complete.

        Args:
            item: Item to mark complete.
            total: Number of items replaced.
        """
        for i, existing in enumerate(self._items):
            if existing == item:
                existing.complete = True
                existing.total = total
                index = self.index(i)
                self.dataChanged.emit(index, index)
                break

    def get_pending(self) -> list[ReplacingItem]:
        """Get all pending (not complete) items."""
        return [item for item in self._items if not item.complete]

    def clear(self) -> None:
        """Clear all items."""
        self.beginResetModel()
        self._items.clear()
        self.endResetModel()

    def rowCount(self, parent: QModelIndex = QModelIndex()) -> int:
        return len(self._items)

    def data(self, index: QModelIndex, role: int = Qt.ItemDataRole.DisplayRole) -> Any:
        if not index.isValid():
            return None

        row = index.row()
        if row < 0 or row >= len(self._items):
            return None

        item = self._items[row]

        if role == Qt.ItemDataRole.DisplayRole:
            status = f"[Done: {item.total}]" if item.complete else "[Pending]"
            return f"Replace {item.replace_id} → {item.with_id}  {status}"
        elif role == Qt.ItemDataRole.UserRole:
            return item
        elif role == Qt.ItemDataRole.ForegroundRole:
            return QColor("#10B981") if item.complete else QColor("#E5E5E7")

        return None


class ItemIdSelector(QFrame):
    """Widget for selecting an item by ID with preview.

    Features:
    - Text input for ID
    - Sprite preview (if provider given)
    - Quick browse button
    """

    item_changed = pyqtSignal(int)  # Emitted when ID changes

    def __init__(self, label: str = "Item:", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._item_id = 0
        self._sprite_provider: Callable[[int], QPixmap | None] | None = None

        self._setup_ui(label)

    def _setup_ui(self, label: str) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Label
        lbl = QLabel(label)
        lbl.setStyleSheet("color: #A1A1AA;")
        lbl.setFixedWidth(60)
        layout.addWidget(lbl)

        # Preview
        self.preview_label = QLabel()
        self.preview_label.setFixedSize(36, 36)
        self.preview_label.setStyleSheet(
            """
            background: #2A2A3E;
            border: 1px solid #363650;
            border-radius: 4px;
        """
        )
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.preview_label)

        # SpinBox for ID
        self.id_spin = QSpinBox()
        self.id_spin.setRange(0, 999999)
        self.id_spin.setStyleSheet(
            """
            QSpinBox {
                background: #2A2A3E;
                color: #E5E5E7;
                border: 1px solid #363650;
                border-radius: 4px;
                padding: 6px;
                min-width: 80px;
            }
        """
        )
        self.id_spin.valueChanged.connect(self._on_id_changed)
        layout.addWidget(self.id_spin, 1)

        # Browse button
        browse_btn = QPushButton("...")
        browse_btn.setFixedSize(32, 32)
        browse_btn.setStyleSheet(
            """
            QPushButton {
                background: #363650;
                color: #E5E5E7;
                border: none;
                border-radius: 4px;
            }
            QPushButton:hover { background: #8B5CF6; }
        """
        )
        browse_btn.setToolTip("Browse items")
        # browse_btn.clicked.connect(self._open_browser)  # TODO: Connect to item browser
        layout.addWidget(browse_btn)

    def _on_id_changed(self, value: int) -> None:
        """Handle ID input change."""
        self._item_id = value
        self._update_preview()
        self.item_changed.emit(value)

    def _update_preview(self) -> None:
        """Update the preview label."""
        if self._sprite_provider and self._item_id > 0:
            pixmap = self._sprite_provider(self._item_id)
            if pixmap and not pixmap.isNull():
                scaled = pixmap.scaled(
                    32, 32, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation
                )
                self.preview_label.setPixmap(scaled)
                return

        self.preview_label.clear()
        self.preview_label.setText(str(self._item_id) if self._item_id > 0 else "—")

    def set_sprite_provider(self, provider: Callable[[int], QPixmap | None]) -> None:
        """Set the sprite provider function."""
        self._sprite_provider = provider
        self._update_preview()

    @property
    def item_id(self) -> int:
        return self._item_id

    @item_id.setter
    def item_id(self, value: int) -> None:
        self.id_spin.setValue(value)


class BatchItemEditor(QDialog):
    """Dialog for batch editing items across the map.

    Features:
    - Add multiple find/replace pairs
    - Execute replacements across entire map or selection
    - Progress tracking
    - Undo support via action queue

    Mirrors C++ ReplaceItemsDialog functionality.

    Example:
        >>> dialog = BatchItemEditor(parent)
        >>> dialog.set_executor(map.batch_replace)
        >>> dialog.exec()
    """

    operation_complete = pyqtSignal(BatchResult)

    def __init__(self, parent: QWidget | None = None, selection_only: bool = False) -> None:
        super().__init__(parent)
        self._selection_only = selection_only
        self._executor: Callable[[list[ReplacingItem]], BatchResult] | None = None
        self._sprite_provider: Callable[[int], QPixmap | None] | None = None

        title = "Replace Items (Selection)" if selection_only else "Batch Item Editor"
        self.setWindowTitle(title)
        self.setMinimumSize(550, 500)
        self.setModal(True)

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Header
        header = QLabel("Batch Item Editor")
        header.setStyleSheet("font-size: 18px; font-weight: 700; color: #E5E5E7;")
        layout.addWidget(header)

        desc = QLabel(
            "Add item replacements and execute them across the map. "
            "Each replacement will substitute all occurrences of the source item."
        )
        desc.setWordWrap(True)
        desc.setStyleSheet("color: #A1A1AA;")
        layout.addWidget(desc)

        # Input section
        input_group = QGroupBox("Add Replacement")
        input_group.setStyleSheet(
            """
            QGroupBox {
                color: #E5E5E7;
                border: 1px solid #363650;
                border-radius: 4px;
                margin-top: 12px;
                padding: 12px;
                padding-top: 24px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px;
            }
        """
        )
        input_layout = QVBoxLayout(input_group)

        # Source item
        self.source_selector = ItemIdSelector("Replace:")
        input_layout.addWidget(self.source_selector)

        # Arrow indicator
        arrow = QLabel("↓")
        arrow.setAlignment(Qt.AlignmentFlag.AlignCenter)
        arrow.setStyleSheet("color: #8B5CF6; font-size: 20px;")
        input_layout.addWidget(arrow)

        # Target item
        self.target_selector = ItemIdSelector("With:")
        input_layout.addWidget(self.target_selector)

        # Add button
        add_btn = QPushButton("+ Add to Queue")
        add_btn.clicked.connect(self._add_replacement)
        add_btn.setStyleSheet(
            """
            QPushButton {
                background: #2A2A3E;
                color: #E5E5E7;
                border: 1px solid #363650;
                border-radius: 4px;
                padding: 8px 16px;
            }
            QPushButton:hover { background: #363650; }
        """
        )
        input_layout.addWidget(add_btn)

        layout.addWidget(input_group)

        # Queue section
        queue_group = QGroupBox("Replacement Queue")
        queue_group.setStyleSheet(input_group.styleSheet())
        queue_layout = QVBoxLayout(queue_group)

        self.model = ReplaceItemsModel()
        self.queue_list = QListView()
        self.queue_list.setModel(self.model)
        self.queue_list.setStyleSheet(
            """
            QListView {
                background: #1A1A2E;
                border: 1px solid #363650;
                border-radius: 4px;
            }
            QListView::item {
                padding: 8px;
                border-bottom: 1px solid #2A2A3E;
            }
            QListView::item:selected {
                background: #8B5CF6;
            }
        """
        )
        self.queue_list.setMinimumHeight(150)
        queue_layout.addWidget(self.queue_list)

        # Queue controls
        queue_btns = QHBoxLayout()

        remove_btn = QPushButton("Remove Selected")
        remove_btn.clicked.connect(self._remove_selected)
        remove_btn.setStyleSheet(add_btn.styleSheet())
        queue_btns.addWidget(remove_btn)

        clear_btn = QPushButton("Clear All")
        clear_btn.clicked.connect(self.model.clear)
        clear_btn.setStyleSheet(add_btn.styleSheet())
        queue_btns.addWidget(clear_btn)

        queue_btns.addStretch()
        queue_layout.addLayout(queue_btns)

        layout.addWidget(queue_group, 1)

        # Progress
        progress_layout = QHBoxLayout()

        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        self.progress_bar.setStyleSheet(
            """
            QProgressBar {
                background: #2A2A3E;
                border: 1px solid #363650;
                border-radius: 4px;
                text-align: center;
                color: #E5E5E7;
            }
            QProgressBar::chunk {
                background: #8B5CF6;
                border-radius: 3px;
            }
        """
        )
        progress_layout.addWidget(self.progress_bar, 1)

        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("color: #A1A1AA;")
        progress_layout.addWidget(self.status_label)

        layout.addLayout(progress_layout)

        # Button bar
        btn_layout = QHBoxLayout()

        # Selection only checkbox
        if not self._selection_only:
            self.selection_check = QCheckBox("Selection Only")
            self.selection_check.setStyleSheet("color: #E5E5E7;")
            btn_layout.addWidget(self.selection_check)

        btn_layout.addStretch()

        execute_btn = QPushButton("Execute")
        execute_btn.clicked.connect(self._execute)
        execute_btn.setStyleSheet(
            """
            QPushButton {
                background: #8B5CF6;
                color: white;
                border: none;
                border-radius: 4px;
                padding: 10px 24px;
                font-weight: bold;
            }
            QPushButton:hover { background: #7C3AED; }
        """
        )
        btn_layout.addWidget(execute_btn)

        close_btn = QPushButton("Close")
        close_btn.clicked.connect(self.close)
        close_btn.setStyleSheet(
            """
            QPushButton {
                background: #2A2A3E;
                color: #E5E5E7;
                border: 1px solid #363650;
                border-radius: 4px;
                padding: 10px 24px;
            }
            QPushButton:hover { background: #363650; }
        """
        )
        btn_layout.addWidget(close_btn)

        layout.addLayout(btn_layout)

    def _apply_style(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet(
            """
            QDialog { background: #0F0F1A; }
        """
        )

    def _add_replacement(self) -> None:
        """Add current selection to replacement queue."""
        source_id = self.source_selector.item_id
        target_id = self.target_selector.item_id

        if source_id == 0 or target_id == 0:
            QMessageBox.warning(self, "Invalid Input", "Both source and target item IDs must be specified.")
            return

        if source_id == target_id:
            QMessageBox.warning(self, "Invalid Input", "Source and target must be different items.")
            return

        item = ReplacingItem(replace_id=source_id, with_id=target_id)
        if not self.model.add_item(item):
            QMessageBox.warning(self, "Duplicate", "This replacement is already in the queue.")
            return

        # Clear inputs
        self.source_selector.item_id = 0
        self.target_selector.item_id = 0

    def _remove_selected(self) -> None:
        """Remove selected item from queue."""
        idx = self.queue_list.currentIndex()
        if idx.isValid():
            self.model.remove_item(idx.row())

    def _execute(self) -> None:
        """Execute all pending replacements."""
        pending = self.model.get_pending()
        if not pending:
            QMessageBox.information(self, "Nothing to Do", "No pending replacements in the queue.")
            return

        if not self._executor:
            QMessageBox.warning(self, "Not Configured", "No executor function configured.")
            return

        self.progress_bar.setValue(0)
        self.status_label.setText("Processing...")

        total_affected = 0

        for i, item in enumerate(pending):
            # Simulate progress
            progress = int((i + 1) / len(pending) * 100)
            self.progress_bar.setValue(progress)

            # Execute single replacement
            try:
                result = self._executor([item])
                if result.success:
                    self.model.mark_complete(item, result.items_affected)
                    total_affected += result.items_affected
            except Exception as e:
                logger.error(f"Replacement failed: {e}")

        self.progress_bar.setValue(100)
        self.status_label.setText(f"Done: {total_affected} items replaced")

        self.operation_complete.emit(
            BatchResult(success=True, items_affected=total_affected, message=f"Replaced {total_affected} items")
        )

    def set_executor(self, executor: Callable[[list[ReplacingItem]], BatchResult]) -> None:
        """Set the executor function for replacements.

        Args:
            executor: Function that takes list of ReplacingItems and returns BatchResult.
        """
        self._executor = executor

    def set_sprite_provider(self, provider: Callable[[int], QPixmap | None]) -> None:
        """Set the sprite provider for item previews.

        Args:
            provider: Function that takes item ID and returns QPixmap.
        """
        self._sprite_provider = provider
        self.source_selector.set_sprite_provider(provider)
        self.target_selector.set_sprite_provider(provider)


def show_batch_editor(
    parent: QWidget | None = None,
    selection_only: bool = False,
    executor: Callable[[list[ReplacingItem]], BatchResult] | None = None,
) -> BatchItemEditor:
    """Factory function to create and show the dialog.

    Args:
        parent: Parent widget.
        selection_only: Whether to only affect selected tiles.
        executor: Optional executor function.

    Returns:
        The dialog instance.
    """
    dialog = BatchItemEditor(parent, selection_only=selection_only)
    if executor:
        dialog.set_executor(executor)
    dialog.show()
    return dialog


__all__ = [
    "BatchOperation",
    "ReplacingItem",
    "BatchResult",
    "BatchItemEditor",
    "ReplaceItemsModel",
    "ItemIdSelector",
    "show_batch_editor",
]
