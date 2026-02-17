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

from py_rme_canary.vis_layer.ui.dialogs.base_modern import ModernDialog

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
        self._browse_callback: Callable[[int], int | None] | None = None

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
        self.browse_btn = QPushButton("...")
        self.browse_btn.setFixedSize(32, 32)
        self.browse_btn.setStyleSheet(
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
        self.browse_btn.setToolTip("Browse items")
        self.browse_btn.clicked.connect(self._on_browse_clicked)
        layout.addWidget(self.browse_btn)

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

    def set_browse_callback(self, callback: Callable[[int], int | None] | None) -> None:
        """Set callback used by browse button to pick a server ID."""
        self._browse_callback = callback

    def _on_browse_clicked(self) -> None:
        selected_id: int | None = None
        if self._browse_callback is not None:
            try:
                selected_id = self._browse_callback(int(self._item_id))
            except Exception as exc:
                logger.exception("Browse callback failed: %s", exc)
                QMessageBox.warning(self, "Item Browser", "Failed to browse items with configured callback.")
                return
        else:
            selected_id = self._open_browser_with_dialog()

        if selected_id is None:
            return
        if int(selected_id) <= 0:
            return
        self.id_spin.setValue(int(selected_id))

    def _open_browser_with_dialog(self) -> int | None:
        try:
            from py_rme_canary.vis_layer.ui.main_window.dialogs import FindItemDialog
        except Exception:
            QMessageBox.information(self, "Item Browser", "Item browser is not available in this context.")
            return None

        dialog = FindItemDialog(self, title="Select Item")
        if self._item_id > 0:
            spin = getattr(dialog, "_id_spin", None)
            if spin is not None and hasattr(spin, "setValue"):
                spin.setValue(int(self._item_id))
        if dialog.exec() != QDialog.DialogCode.Accepted:
            return None

        result = dialog.result_value()
        if not result.resolved:
            QMessageBox.warning(self, "Item Browser", result.error or "Unable to resolve selected item.")
            return None
        if int(result.server_id) <= 0:
            return None
        return int(result.server_id)

    @property
    def item_id(self) -> int:
        return self._item_id

    @item_id.setter
    def item_id(self, value: int) -> None:
        self.id_spin.setValue(value)


class BatchItemEditor(ModernDialog):
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
        title = "Replace Items (Selection)" if selection_only else "Batch Item Editor"
        super().__init__(parent, title=title)
        self._selection_only = selection_only
        self._executor: Callable[[list[ReplacingItem]], BatchResult] | None = None
        self._sprite_provider: Callable[[int], QPixmap | None] | None = None

        self.setMinimumSize(550, 500)
        # ModernDialog is modal and frameless by default

        self._setup_ui()
        # No need for _apply_style() as ModernDialog handles theming

    def _setup_ui(self) -> None:
        """Initialize UI components."""
        # Use existing content layout from ModernDialog
        layout = self.content_layout
        layout.setSpacing(12)

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

        # Footer Actions

        # Selection only checkbox (Add to footer)
        if not self._selection_only:
            self.selection_check = QCheckBox("Selection Only")
            self.selection_check.setStyleSheet("color: #E5E5E7;")
            # Insert before buttons
            self.footer_layout.addWidget(self.selection_check)

        self.add_spacer_to_footer() # Push buttons to the right

        # Add buttons to footer
        self.add_button("Execute", self._execute, role="primary")
        self.add_button("Close", self.close)

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

    def set_item_browser(self, browser: Callable[[int], int | None] | None) -> None:
        """Set item browser callback for source/target selectors."""
        self.source_selector.set_browse_callback(browser)
        self.target_selector.set_browse_callback(browser)


def show_batch_editor(
    parent: QWidget | None = None,
    selection_only: bool = False,
    executor: Callable[[list[ReplacingItem]], BatchResult] | None = None,
    item_browser: Callable[[int], int | None] | None = None,
) -> BatchItemEditor:
    """Factory function to create and show the dialog.

    Args:
        parent: Parent widget.
        selection_only: Whether to only affect selected tiles.
        executor: Optional executor function.
        item_browser: Optional callback used by browse buttons.

    Returns:
        The dialog instance.
    """
    dialog = BatchItemEditor(parent, selection_only=selection_only)
    if executor:
        dialog.set_executor(executor)
    if item_browser is not None:
        dialog.set_item_browser(item_browser)
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
