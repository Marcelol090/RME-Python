"""Add Item Window for py_rme_canary.

Ported from C++ AddItemWindow (add_item_window.cpp - 153 lines).
Provides UI for adding items to tilesets by server ID.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QMessageBox,
    QSpinBox,
    QVBoxLayout,
)

if TYPE_CHECKING:
    from PyQt6.QtWidgets import QWidget

    from py_rme_canary.core.database.items_database import ItemsDatabase


class AddItemDialog(QDialog):
    """Dialog for adding items to tilesets.

    Based on C++ AddItemWindow (add_item_window.cpp).
    Allows selecting an item by server ID and adding it to a tileset category.
    """

    def __init__(
        self,
        parent: QWidget | None = None,
        *,
        items_db: ItemsDatabase | None = None,
        tileset_name: str = "",
        initial_item_id: int = 100,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Add Item")
        self.setModal(True)
        self.setMinimumWidth(350)

        self._items_db = items_db
        self._tileset_name = tileset_name
        self._selected_item_id = 0

        # Create UI
        layout = QVBoxLayout(self)

        # Item info display
        info_group = QGroupBox("Item Information")
        info_layout = QVBoxLayout(info_group)

        self._item_id_label = QLabel("ID: 0")
        self._item_name_label = QLabel("Name: None")
        info_layout.addWidget(self._item_id_label)
        info_layout.addWidget(self._item_name_label)

        layout.addWidget(info_group)

        # Item selection
        form = QFormLayout()

        self._item_id_spin = QSpinBox()
        self._item_id_spin.setRange(1, 100000)
        initial = max(1, min(100000, int(initial_item_id)))
        self._item_id_spin.setValue(initial)
        self._item_id_spin.valueChanged.connect(self._on_item_id_changed)
        form.addRow("Item ID (Server):", self._item_id_spin)

        layout.addLayout(form)

        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        button_box.accepted.connect(self._on_add_clicked)
        button_box.rejected.connect(self.reject)

        layout.addWidget(button_box)

        # Initialize item info
        self._on_item_id_changed(self._item_id_spin.value())

    def _on_item_id_changed(self, item_id: int) -> None:
        """Update item information when ID changes."""
        self._selected_item_id = item_id
        self._item_id_label.setText(f"ID: {item_id}")

        if self._items_db:
            item_type = self._items_db.get_item_type(item_id)
            if item_type:
                self._item_name_label.setText(f"Name: {item_type.name}")
            else:
                self._item_name_label.setText("Name: <Unknown Item>")
        else:
            self._item_name_label.setText("Name: <No database loaded>")

    def _on_add_clicked(self) -> None:
        """Handle Add button click."""
        if self._selected_item_id == 0:
            QMessageBox.warning(self, "Invalid Item", "Please select a valid item ID.")
            return

        # Keep tileset confirmation for legacy flow, but avoid noisy popups when
        # this dialog is reused by other workflows (e.g., container editing).
        if self._tileset_name:
            QMessageBox.information(
                self,
                "Item Added",
                f"Item {self._selected_item_id} has been added to tileset '{self._tileset_name}'.",
            )
        self.accept()

    def get_selected_item_id(self) -> int:
        """Get the selected item server ID.

        Returns:
            Selected server ID
        """
        return self._selected_item_id
