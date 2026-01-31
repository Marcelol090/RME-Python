"""Browse Tile Dialog - Inspect and edit item stacks on a tile.

Allows mappers to:
- View all items stacked on a tile (ground + items)
- Edit properties of individual items
- Reorder items via drag & drop
- Remove/Copy/Paste items

Reference: RME/source/ui/browse_tile_window.cpp
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QListWidget,
    QLabel,
    QPushButton,
    QGroupBox,
    QLineEdit,
    QTextEdit,
    QSpinBox,
    QWidget,
    QListWidgetItem,
    QFormLayout,
    QDialogButtonBox,
)

if TYPE_CHECKING:
    from py_rme_canary.core.data.tile import Tile
    from py_rme_canary.core.data.item import Item
    from py_rme_canary.logic_layer.asset_manager import AssetManager


@dataclass(slots=True)
class ItemStackEntry:
    """Represents an item in the tile stack."""
    item: Item
    index: int  # Position in stack (0 = ground)
    is_ground: bool
    sprite_pixmap: QPixmap | None = None


class ItemStackItemWidget(QWidget):
    """Custom widget for each item in the stack list."""

    def __init__(self, stack_entry: ItemStackEntry, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.stack_entry = stack_entry
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup widget UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(8)

        # Sprite icon
        sprite_label = QLabel()
        sprite_label.setFixedSize(32, 32)
        sprite_label.setStyleSheet("""
            QLabel {
                background: #1E1E2E;
                border: 1px solid #363650;
                border-radius: 4px;
            }
        """)
        
        if self.stack_entry.sprite_pixmap:
            sprite_label.setPixmap(
                self.stack_entry.sprite_pixmap.scaled(
                    32, 32,
                    Qt.AspectRatioMode.KeepAspectRatio,
                    Qt.TransformationMode.SmoothTransformation
                )
            )
        else:
            # Placeholder text
            sprite_label.setText("?")
            sprite_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        layout.addWidget(sprite_label)

        # Item info
        item = self.stack_entry.item
        info_text = f"ID {item.id}"
        
        # Add ground indicator
        if self.stack_entry.is_ground:
            info_text = f"[Ground] {info_text}"
        
        # Add attributes
        attrs = []
        if item.action_id:
            attrs.append(f"AID:{item.action_id}")
        if item.unique_id:
            attrs.append(f"UID:{item.unique_id}")
        if item.text:
            attrs.append(f'Text:"{item.text[:20]}..."' if len(item.text) > 20 else f'Text:"{item.text}"')
        
        if attrs:
            info_text += f" ({', '.join(attrs)})"
        
        info_label = QLabel(info_text)
        info_label.setStyleSheet("""
            QLabel {
                color: #E5E5E7;
                font-size: 13px;
            }
        """)
        layout.addWidget(info_label, 1)


class ItemStackListWidget(QListWidget):
    """Custom list widget with drag & drop support for reordering items."""

    items_reordered = pyqtSignal(list)  # Emits new order of ItemStackEntry

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setDragDropMode(QListWidget.DragDropMode.InternalMove)
        self.setDefaultDropAction(Qt.DropAction.MoveAction)
        self.setSelectionMode(QListWidget.SelectionMode.SingleSelection)
        self.setSpacing(2)
        
        # Connect to detect reordering
        self.model().rowsMoved.connect(self._on_rows_moved)
        
        self.setStyleSheet("""
            ItemStackListWidget {
                background: #1E1E2E;
                border: 1px solid #363650;
                border-radius: 8px;
                padding: 4px;
            }
            ItemStackListWidget::item {
                background: #2A2A3E;
                border-radius: 4px;
                padding: 2px;
                margin: 1px 0;
            }
            ItemStackListWidget::item:selected {
                background: #363650;
                border: 1px solid #8B5CF6;
            }
            ItemStackListWidget::item:hover {
                background: #363650;
            }
        """)

    def _on_rows_moved(self, parent, start: int, end: int, destination, row: int) -> None:
        """Callback when items are reordered via drag & drop."""
        # Extract new order
        new_order = []
        for i in range(self.count()):
            list_item = self.item(i)
            item_widget = self.itemWidget(list_item)
            if isinstance(item_widget, ItemStackItemWidget):
                new_order.append(item_widget.stack_entry)
        
        self.items_reordered.emit(new_order)


class BrowseTileDialog(QDialog):
    """Dialog for browsing and editing items on a specific tile.
    
    Features:
    - Display all items stacked on a tile (ground + items)
    - Reorder items via drag & drop
    - Edit item properties (ActionID, UniqueID, Text, etc.)
    - Remove items from stack
    - Copy/Paste items
    """

    def __init__(
        self,
        tile: Tile,
        position: tuple[int, int, int],
        asset_manager: AssetManager | None = None,
        parent: QWidget | None = None
    ) -> None:
        super().__init__(parent)
        self.tile = tile
        self.position = position
        self.asset_manager = asset_manager
        
        self._stack_entries: list[ItemStackEntry] = []
        self._original_stack: list[Item] = []  # For undo
        self._selected_entry: ItemStackEntry | None = None
        
        self.setWindowTitle(f"Browse Tile @ ({position[0]}, {position[1]}, Floor {position[2]})")
        self.setMinimumSize(500, 600)
        
        self._setup_ui()
        self._load_items()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(12)
        layout.setContentsMargins(16, 16, 16, 16)

        # Header with position info
        header = QLabel(f"Position: ({self.position[0]}, {self.position[1]}, Floor {self.position[2]})")
        header.setStyleSheet("""
            QLabel {
                color: #E5E5E7;
                font-size: 14px;
                font-weight: 600;
                padding: 8px;
                background: #2A2A3E;
                border-radius: 6px;
            }
        """)
        layout.addWidget(header)

        # Item stack list
        stack_group = QGroupBox("Item Stack")
        stack_group.setStyleSheet("""
            QGroupBox {
                color: #E5E5E7;
                font-weight: 600;
                border: 1px solid #363650;
                border-radius: 8px;
                margin-top: 12px;
                padding-top: 12px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                subcontrol-position: top left;
                padding: 0 8px;
            }
        """)
        
        stack_layout = QVBoxLayout(stack_group)
        
        self.item_list = ItemStackListWidget()
        self.item_list.currentRowChanged.connect(self._on_selection_changed)
        self.item_list.items_reordered.connect(self._on_items_reordered)
        stack_layout.addWidget(self.item_list)
        
        layout.addWidget(stack_group)

        # Properties panel
        props_group = QGroupBox("Properties")
        props_group.setStyleSheet(stack_group.styleSheet())
        props_layout = QFormLayout(props_group)
        
        self.action_id_spin = QSpinBox()
        self.action_id_spin.setRange(0, 65535)
        self.action_id_spin.setSpecialValueText("None")
        props_layout.addRow("Action ID:", self.action_id_spin)
        
        self.unique_id_spin = QSpinBox()
        self.unique_id_spin.setRange(0, 65535)
        self.unique_id_spin.setSpecialValueText("None")
        props_layout.addRow("Unique ID:", self.unique_id_spin)
        
        self.text_edit = QLineEdit()
        self.text_edit.setPlaceholderText("Text content...")
        props_layout.addRow("Text:", self.text_edit)
        
        layout.addWidget(props_group)

        # Action buttons
        button_layout = QHBoxLayout()
        
        self.remove_btn = QPushButton("Remove Item")
        self.remove_btn.clicked.connect(self._on_remove_item)
        button_layout.addWidget(self.remove_btn)
        
        self.move_up_btn = QPushButton("Move Up")
        self.move_up_btn.clicked.connect(self._on_move_up)
        button_layout.addWidget(self.move_up_btn)
        
        self.move_down_btn = QPushButton("Move Down")
        self.move_down_btn.clicked.connect(self._on_move_down)
        button_layout.addWidget(self.move_down_btn)
        
        button_layout.addStretch()
        layout.addLayout(button_layout)

        # Dialog buttons
        dialog_buttons = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        dialog_buttons.accepted.connect(self.accept)
        dialog_buttons.rejected.connect(self.reject)
        layout.addWidget(dialog_buttons)

    def _load_items(self) -> None:
        """Load items from tile into the list."""
        # Store original for undo
        self._original_stack = []
        
        # Add ground
        if self.tile.ground:
            sprite = self._get_sprite(self.tile.ground)
            entry = ItemStackEntry(
                item=self.tile.ground,
                index=0,
                is_ground=True,
                sprite_pixmap=sprite
            )
            self._stack_entries.append(entry)
            self._original_stack.append(self.tile.ground)
        
        # Add items
        for i, item in enumerate(self.tile.items):
            sprite = self._get_sprite(item)
            entry = ItemStackEntry(
                item=item,
                index=i + 1,
                is_ground=False,
                sprite_pixmap=sprite
            )
            self._stack_entries.append(entry)
            self._original_stack.append(item)
        
        # Populate list widget
        self._refresh_list()

    def _refresh_list(self) -> None:
        """Refresh the item list widget."""
        self.item_list.clear()
        
        for entry in self._stack_entries:
            item_widget = ItemStackItemWidget(entry)
            list_item = QListWidgetItem(self.item_list)
            list_item.setSizeHint(item_widget.sizeHint())
            self.item_list.addItem(list_item)
            self.item_list.setItemWidget(list_item, item_widget)

    def _get_sprite(self, item: Item) -> QPixmap | None:
        """Get sprite pixmap for an item."""
        if not self.asset_manager:
            return None
        
        try:
            return self.asset_manager.get_item_sprite(int(item.id))
        except Exception:
            return None

    def _on_selection_changed(self, current_row: int) -> None:
        """Handle item selection change."""
        if current_row < 0 or current_row >= len(self._stack_entries):
            self._selected_entry = None
            self._clear_properties()
            return
        
        self._selected_entry = self._stack_entries[current_row]
        self._load_properties(self._selected_entry.item)

    def _load_properties(self, item: Item) -> None:
        """Load item properties into edit fields."""
        self.action_id_spin.setValue(item.action_id if item.action_id else 0)
        self.unique_id_spin.setValue(item.unique_id if item.unique_id else 0)
        self.text_edit.setText(item.text if item.text else "")

    def _clear_properties(self) -> None:
        """Clear property edit fields."""
        self.action_id_spin.setValue(0)
        self.unique_id_spin.setValue(0)
        self.text_edit.clear()

    def _on_items_reordered(self, new_order: list[ItemStackEntry]) -> None:
        """Handle drag & drop reordering."""
        self._stack_entries = new_order
        # Update indices
        for i, entry in enumerate(self._stack_entries):
            entry.index = i

    def _on_remove_item(self) -> None:
        """Remove selected item from stack."""
        if not self._selected_entry:
            return
        
        if self._selected_entry.is_ground:
            # Can't remove ground
            return
        
        self._stack_entries.remove(self._selected_entry)
        self._refresh_list()

    def _on_move_up(self) -> None:
        """Move selected item up in stack."""
        if not self._selected_entry:
            return
        
        current_idx = self._stack_entries.index(self._selected_entry)
        if current_idx > 1:  # Can't move above ground
            self._stack_entries[current_idx], self._stack_entries[current_idx - 1] = \
                self._stack_entries[current_idx - 1], self._stack_entries[current_idx]
            self._refresh_list()
            self.item_list.setCurrentRow(current_idx - 1)

    def _on_move_down(self) -> None:
        """Move selected item down in stack."""
        if not self._selected_entry:
            return
        
        current_idx = self._stack_entries.index(self._selected_entry)
        if current_idx < len(self._stack_entries) - 1:
            self._stack_entries[current_idx], self._stack_entries[current_idx + 1] = \
                self._stack_entries[current_idx + 1], self._stack_entries[current_idx]
            self._refresh_list()
            self.item_list.setCurrentRow(current_idx + 1)

    def _apply_style(self) -> None:
        """Apply modern dark theme."""
        self.setStyleSheet("""
            BrowseTileDialog {
                background: #1E1E2E;
            }
            QSpinBox, QLineEdit {
                background: #2A2A3E;
                color: #E5E5E7;
                border: 1px solid #363650;
                border-radius: 6px;
                padding: 6px;
            }
            QSpinBox:focus, QLineEdit:focus {
                border-color: #8B5CF6;
            }
            QPushButton {
                background: #8B5CF6;
                color: white;
                border: none;
                border-radius: 6px;
                padding: 8px 16px;
                font-weight: 500;
            }
            QPushButton:hover {
                background: #A78BFA;
            }
            QPushButton:pressed {
                background: #7C3AED;
            }
        """)

    def get_modified_items(self) -> tuple[Item | None, list[Item]]:
        """Get modified ground and items list.
        
        Returns:
            Tuple of (ground_item, items_list)
        """
        ground = None
        items = []
        
        for entry in self._stack_entries:
            if entry.is_ground:
                ground = entry.item
            else:
                items.append(entry.item)
        
        return ground, items
