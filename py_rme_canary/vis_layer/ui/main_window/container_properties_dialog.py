"""Container Properties Dialog for py_rme_canary.

Ported from C++ ContainerPropertiesWindow (container_properties_window.cpp).
Provides UI for editing container item properties.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import (
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QListWidget,
    QListWidgetItem,
    QPushButton,
    QSpinBox,
    QVBoxLayout,
)

if TYPE_CHECKING:
    from py_rme_canary.core.data.item import Item
    from py_rme_canary.core.database.items_database import ItemsDatabase


class ContainerPropertiesDialog(QDialog):
    """Dialog for editing container properties.

    Based on C++ ContainerPropertiesWindow.
    Allows editing:
    - Container items list
    - Adding/removing items from container
    - Item properties within container
    """

    def __init__(
        self,
        parent=None,
        *,
        container_item: Item | None = None,
        items_db: ItemsDatabase | None = None,
    ) -> None:
        super().__init__(parent)
        self.setWindowTitle("Container Properties")
        self.setModal(True)
        self.setMinimumSize(400, 350)

        self._container = container_item
        self._items_db = items_db

        # Create UI
        layout = QVBoxLayout(self)

        # Container info
        info_group = QGroupBox("Container Information")
        info_layout = QFormLayout(info_group)

        if container_item:
            info_layout.addRow("Container ID:", QSpinBox())  # Read-only display

        layout.addWidget(info_group)

        # Items list
        items_group = QGroupBox("Container Items")
        items_layout = QVBoxLayout(items_group)

        self._items_list = QListWidget()
        items_layout.addWidget(self._items_list)

        # Add/Remove buttons
        from PyQt6.QtWidgets import QHBoxLayout
        btn_layout = QHBoxLayout()

        self._add_btn = QPushButton("Add Item")
        self._add_btn.clicked.connect(self._on_add_item)
        btn_layout.addWidget(self._add_btn)

        self._remove_btn = QPushButton("Remove Selected")
        self._remove_btn.clicked.connect(self._on_remove_item)
        btn_layout.addWidget(self._remove_btn)

        items_layout.addLayout(btn_layout)
        layout.addWidget(items_group)

        # Dialog buttons
        button_box = QDialogButtonBox(
            QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel
        )
        button_box.accepted.connect(self.accept)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

        # Populate items
        self._update_items_list()

    def _update_items_list(self) -> None:
        """Update the container items list."""
        self._items_list.clear()

        if not self._container or not hasattr(self._container, 'container_items'):
            return

        # Add container items
        for item in getattr(self._container, 'container_items', []):
            item_name = self._get_item_name(item.id)
            item_text = f"{item.id} - {item_name}"
            list_item = QListWidgetItem(item_text)
            list_item.setData(100, item)  # Store item reference
            self._items_list.addItem(list_item)

    def _get_item_name(self, item_id: int) -> str:
        """Get item name from database."""
        if self._items_db:
            item_type = self._items_db.get_item_type(item_id)
            if item_type:
                return item_type.name
        return "<Unknown>"

    def _on_add_item(self) -> None:
        """Add item to container."""
        # TODO: Open AddItemDialog and add selected item
        from PyQt6.QtWidgets import QMessageBox
        QMessageBox.information(self, "Add Item", "Add item functionality will be implemented.")

    def _on_remove_item(self) -> None:
        """Remove selected item from container."""
        selected = self._items_list.selectedItems()
        if not selected:
            return

        # Remove from container
        for list_item in selected:
            item = list_item.data(100)
            if hasattr(self._container, 'container_items'):
                try:
                    self._container.container_items.remove(item)
                except ValueError:
                    pass

        # Update list
        self._update_items_list()

    def get_container(self) -> Item | None:
        """Get the modified container item.

        Returns:
            Container item with modifications
        """
        return self._container
