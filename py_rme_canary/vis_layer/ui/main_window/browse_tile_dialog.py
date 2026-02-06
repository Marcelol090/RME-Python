"""Browse Tile Window for py_rme_canary.

Ported from C++ BrowseTileWindow (browse_tile_window.cpp - 312 lines).
Provides UI for browsing and managing items on a selected tile.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QHBoxLayout,
    QLabel,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QVBoxLayout,
)

if TYPE_CHECKING:
    from py_rme_canary.core.data.tile import Tile
    from py_rme_canary.core.database.items_database import ItemsDatabase


class BrowseTileDialog(QDialog):
    """Dialog for browsing items on a tile.

    Based on C++ BrowseTileWindow (browse_tile_window.cpp).
    Shows all items on a tile with ability to:
    - Select/deselect items
    - View item properties
    - Remove selected items
    - Navigate to item properties dialog
    """

    def __init__(
        self,
        parent=None,
        *,
        tile: Tile | None = None,
        items_db: ItemsDatabase | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Browse Tile")
        self.setModal(True)
        self.setMinimumSize(400, 300)

        self._tile = tile
        self._items_db = items_db

        # Create UI
        layout = QVBoxLayout(self)

        # Tile info
        info_label = QLabel(f"Tile Position: ({tile.x}, {tile.y}, {tile.z})") if tile else QLabel("No tile selected")
        layout.addWidget(info_label)

        # Items list
        self._items_list = QListWidget()
        self._items_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self._items_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self._items_list)

        # Action buttons
        button_layout = QHBoxLayout()

        self._remove_btn = QPushButton("Remove Selected")
        self._remove_btn.clicked.connect(self._on_remove_selected)
        button_layout.addWidget(self._remove_btn)

        self._properties_btn = QPushButton("Properties")
        self._properties_btn.clicked.connect(self._on_show_properties)
        button_layout.addWidget(self._properties_btn)

        layout.addLayout(button_layout)

        # Dialog buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Close)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Populate items list
        self._update_items_list()

    def _update_items_list(self) -> None:
        """Update the items list widget with tile contents."""
        self._items_list.clear()

        if not self._tile:
            return

        # Add ground item
        if self._tile.ground:
            item_name = self._get_item_name(self._tile.ground.id)
            item_text = f"Ground: {self._tile.ground.id} - {item_name}"
            list_item = QListWidgetItem(item_text)
            list_item.setData(Qt.ItemDataRole.UserRole, ("ground", self._tile.ground))
            self._items_list.addItem(list_item)

        # Add items (in reverse order to match C++ visual ordering)
        if self._tile.items:
            for idx, item in enumerate(reversed(self._tile.items)):
                item_name = self._get_item_name(item.id)
                item_text = f"{item.id} - {item_name}"
                list_item = QListWidgetItem(item_text)
                list_item.setData(Qt.ItemDataRole.UserRole, ("item", item, len(self._tile.items) - 1 - idx))
                self._items_list.addItem(list_item)

        # Update button states
        self._remove_btn.setEnabled(self._items_list.count() > 0)
        self._properties_btn.setEnabled(self._items_list.count() > 0)

    def _get_item_name(self, item_id: int) -> str:
        """Get item name from database."""
        if self._items_db:
            item_type = self._items_db.get_item_type(item_id)
            if item_type:
                return item_type.name
        return "<Unknown>"

    def _on_item_double_clicked(self, item: QListWidgetItem) -> None:
        """Handle item double-click - show properties."""
        self._on_show_properties()

    def _on_remove_selected(self) -> None:
        """Remove selected items from the tile."""
        selected_items = self._items_list.selectedItems()
        if not selected_items or not self._tile:
            return

        # Collect indices to remove (from items list, not ground)
        indices_to_remove = []
        for list_item in selected_items:
            data = list_item.data(Qt.ItemDataRole.UserRole)
            if data[0] == "item":
                _, item_obj, original_idx = data
                indices_to_remove.append(original_idx)

        # Remove items in reverse order to maintain indices
        for idx in sorted(indices_to_remove, reverse=True):
            if 0 <= idx < len(self._tile.items):
                del self._tile.items[idx]

        # Update list
        self._update_items_list()

    def _on_show_properties(self) -> None:
        """Show properties dialog for selected item."""
        selected = self._items_list.selectedItems()
        if not selected:
            return

        # Get first selected item
        list_item = selected[0]
        data = list_item.data(Qt.ItemDataRole.UserRole)

        # TODO: Open properties dialog for the selected item
        # For now, just show a placeholder message
        from PyQt6.QtWidgets import QMessageBox

        if data[0] == "ground":
            QMessageBox.information(self, "Properties", f"Ground item: {data[1].id}")
        else:
            QMessageBox.information(self, "Properties", f"Item: {data[1].id}")

    def get_tile(self) -> Tile | None:
        """Get the tile being browsed.

        Returns:
            The tile object (with any modifications)
        """
        return self._tile
