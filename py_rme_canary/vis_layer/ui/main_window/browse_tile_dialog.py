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
    QFormLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

from py_rme_canary.vis_layer.ui.dialogs.base_modern import ModernDialog

if TYPE_CHECKING:
    from py_rme_canary.core.data.tile import Tile
    from py_rme_canary.core.database.items_database import ItemsDatabase


class BrowseTileDialog(ModernDialog):
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
        super().__init__(parent, title="Browse Tile")
        self.setModal(True)
        self.setMinimumSize(400, 300)

        self._tile = tile
        self._items_db = items_db

        # Create UI
        layout = self.content_layout

        # Tile info
        info_label = QLabel(f"Tile Position: ({tile.x}, {tile.y}, {tile.z})") if tile else QLabel("No tile selected")
        layout.addWidget(info_label)

        # Items list
        self._items_list = QListWidget()
        self._items_list.setSelectionMode(QListWidget.SelectionMode.ExtendedSelection)
        self._items_list.itemDoubleClicked.connect(self._on_item_double_clicked)
        layout.addWidget(self._items_list)

        # Action buttons (Moved to content layout above list or below list?
        # Original had them below list. ModernDialog footer is at the very bottom.
        # But "Remove Selected" and "Properties" act on the list selection.
        # It's better to keep them near the list or put them in the footer.
        # Putting them in the footer is standard for "Modern" look if they are main actions.
        # "Remove" is destructive, "Properties" is action.
        # And "Close" is the dialog action.

        # Let's keep them in the content area for now as they are specific to the list context,
        # and use the footer for the main dialog action "Close".

        button_layout = QHBoxLayout()

        self._remove_btn = QPushButton("Remove Selected")
        self._remove_btn.clicked.connect(self._on_remove_selected)
        button_layout.addWidget(self._remove_btn)

        self._properties_btn = QPushButton("Properties")
        self._properties_btn.clicked.connect(self._on_show_properties)
        button_layout.addWidget(self._properties_btn)

        layout.addLayout(button_layout)

        # Dialog buttons (Footer)
        self.add_spacer_to_footer()
        self.add_button("Close", self.reject)

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
        item = data[1]
        current_row = self._items_list.row(list_item)
        if _edit_item_basic_properties(self, item):
            self._update_items_list()
            if 0 <= current_row < self._items_list.count():
                self._items_list.setCurrentRow(current_row)

    def get_tile(self) -> Tile | None:
        """Get the tile being browsed.

        Returns:
            The tile object (with any modifications)
        """
        return self._tile


def _edit_item_basic_properties(parent: QDialog, item: object) -> bool:
    dialog = QDialog(parent)
    dialog.setWindowTitle(f"Item Properties - ID {int(getattr(item, 'id', 0))}")
    dialog.setModal(True)
    dialog.setMinimumWidth(320)

    action_id_spin = QSpinBox(dialog)
    action_id_spin.setRange(0, 65535)
    action_id_spin.setSpecialValueText("None")
    action_id_spin.setValue(int(getattr(item, "action_id", None) or 0))

    unique_id_spin = QSpinBox(dialog)
    unique_id_spin.setRange(0, 65535)
    unique_id_spin.setSpecialValueText("None")
    unique_id_spin.setValue(int(getattr(item, "unique_id", None) or 0))

    text_edit = QLineEdit(dialog)
    text_edit.setText(str(getattr(item, "text", "") or ""))

    form = QFormLayout()
    form.addRow("Action ID:", action_id_spin)
    form.addRow("Unique ID:", unique_id_spin)
    form.addRow("Text:", text_edit)

    buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
    buttons.accepted.connect(dialog.accept)
    buttons.rejected.connect(dialog.reject)

    root = QVBoxLayout(dialog)
    root.addLayout(form)
    root.addWidget(buttons)

    if dialog.exec() != QDialog.DialogCode.Accepted:
        return False

    action_id = int(action_id_spin.value())
    unique_id = int(unique_id_spin.value())
    text = str(text_edit.text() or "")
    item.action_id = action_id if action_id > 0 else None
    item.unique_id = unique_id if unique_id > 0 else None
    item.text = text if text else None
    return True
