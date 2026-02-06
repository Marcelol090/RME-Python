"""Depot Properties Window - Edit depot box properties.

Dialog for editing depot (player storage) items.
Mirrors legacy C++ DepotPropertiesWindow from source/ui/properties/depot_properties_window.cpp.

Reference:
    - C++ DepotPropertiesWindow: source/ui/properties/depot_properties_window.h
    - Depot system: core/data/depot.py
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from py_rme_canary.core.data.item import Item
    from py_rme_canary.core.data.tile import Tile

logger = logging.getLogger(__name__)


# Standard depot IDs in Tibia
DEPOT_TOWNS = [
    (0, "Default"),
    (1, "Thais"),
    (2, "Carlin"),
    (3, "Kazordoon"),
    (4, "Ab'Dendriel"),
    (5, "Edron"),
    (6, "Darashia"),
    (7, "Venore"),
    (8, "Ankrahmun"),
    (9, "Port Hope"),
    (10, "Liberty Bay"),
    (11, "Svargrond"),
    (12, "Yalahar"),
    (13, "Cormaya"),
    (14, "Roshamuul"),
    (15, "Rathleton"),
    (16, "Krailos"),
    (17, "Feyrist"),
    (18, "Gnomprona"),
    (19, "Issavi"),
    (20, "Marapur"),
]


class DepotPropertiesWindow(QDialog):
    """Dialog for editing depot item properties.

    Allows editing:
    - Depot ID (associated town/location)

    Depots are special containers that store player items
    and are associated with specific towns.

    Signals:
        properties_changed: Emitted when user confirms changes.
    """

    properties_changed = pyqtSignal(dict)  # {depot_id}

    def __init__(
        self,
        item: Item | None = None,
        tile: Tile | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize depot properties window.

        Args:
            item: The depot item to edit.
            tile: The tile containing the item.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._item = item
        self._tile = tile

        self.setWindowTitle("Edit Depot")
        self.setMinimumSize(400, 280)
        self.setModal(True)

        self._setup_ui()
        self._apply_style()
        self._load_values()

    def _setup_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(16)
        layout.setContentsMargins(20, 20, 20, 20)

        # Header with item info
        header = QHBoxLayout()
        self._item_label = QLabel("Depot Box")
        self._item_label.setObjectName("headerLabel")
        header.addWidget(self._item_label)
        header.addStretch()
        layout.addLayout(header)

        # Depot configuration group
        depot_group = QGroupBox("Depot Configuration")
        depot_layout = QFormLayout(depot_group)
        depot_layout.setSpacing(12)

        # Depot ID / Town selector
        self._depot_combo = QComboBox()
        self._depot_combo.setMinimumWidth(250)

        # Populate depot IDs/towns
        for depot_id, town_name in DEPOT_TOWNS:
            display = f"{depot_id} - {town_name}"
            self._depot_combo.addItem(display, depot_id)

        self._depot_combo.currentIndexChanged.connect(self._on_depot_changed)
        depot_layout.addRow("Depot ID / Town:", self._depot_combo)

        layout.addWidget(depot_group)

        # Info section
        info_group = QGroupBox("Information")
        info_layout = QVBoxLayout(info_group)

        self._info_label = QLabel(
            "Depots are special containers that store player items. "
            "Each town has its own depot ID. Players can access their "
            "items from any depot in the same town."
        )
        self._info_label.setObjectName("infoLabel")
        self._info_label.setWordWrap(True)
        info_layout.addWidget(self._info_label)

        # Current depot info
        self._current_info = QLabel("Selected: Default")
        self._current_info.setObjectName("currentInfo")
        info_layout.addWidget(self._current_info)

        layout.addWidget(info_group)

        layout.addStretch()

        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _apply_style(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet(
            """
            QDialog {
                background-color: #1E1E2E;
                color: #CDD6F4;
            }
            QGroupBox {
                font-weight: bold;
                border: 1px solid #45475A;
                border-radius: 6px;
                margin-top: 12px;
                padding-top: 12px;
                background-color: #181825;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: #8B5CF6;
            }
            QLabel {
                color: #CDD6F4;
            }
            QLabel#headerLabel {
                font-size: 14px;
                font-weight: bold;
                color: #8B5CF6;
            }
            QLabel#infoLabel {
                font-size: 11px;
                color: #A6ADC8;
                line-height: 1.4;
            }
            QLabel#currentInfo {
                font-size: 12px;
                color: #89B4FA;
                font-weight: 500;
                padding: 8px;
                background-color: #313244;
                border-radius: 4px;
                margin-top: 8px;
            }
            QComboBox {
                background-color: #313244;
                border: 1px solid #45475A;
                border-radius: 4px;
                padding: 8px 12px;
                color: #CDD6F4;
                min-height: 20px;
            }
            QComboBox:focus {
                border-color: #8B5CF6;
            }
            QComboBox::drop-down {
                border: none;
                width: 30px;
            }
            QComboBox::down-arrow {
                image: none;
                border-left: 5px solid transparent;
                border-right: 5px solid transparent;
                border-top: 6px solid #CDD6F4;
                margin-right: 10px;
            }
            QComboBox QAbstractItemView {
                background-color: #313244;
                border: 1px solid #45475A;
                selection-background-color: #8B5CF6;
                color: #CDD6F4;
            }
            QPushButton {
                background-color: #45475A;
                border: none;
                border-radius: 6px;
                padding: 8px 20px;
                color: #CDD6F4;
                font-weight: 500;
            }
            QPushButton:hover {
                background-color: #585B70;
            }
            QPushButton:pressed {
                background-color: #8B5CF6;
            }
            QDialogButtonBox QPushButton {
                min-width: 90px;
            }
        """
        )

    def _load_values(self) -> None:
        """Load values from the item."""
        if self._item is None:
            return

        # Get item name
        item_name = getattr(self._item, "name", None) or f"Item #{getattr(self._item, 'id', 0)}"
        self._item_label.setText(item_name)

        # Load depot ID
        depot_id = getattr(self._item, "depot_id", 0) or 0

        # Find matching depot in combo
        index = self._depot_combo.findData(depot_id)
        if index >= 0:
            self._depot_combo.setCurrentIndex(index)
        else:
            # If not found, try to add it as custom
            self._depot_combo.addItem(f"{depot_id} - Custom", depot_id)
            self._depot_combo.setCurrentIndex(self._depot_combo.count() - 1)

    def _on_depot_changed(self, index: int) -> None:
        """Handle depot selection change."""
        depot_id = self._depot_combo.currentData()
        if depot_id is not None:
            # Find town name
            town_name = "Unknown"
            for did, name in DEPOT_TOWNS:
                if did == depot_id:
                    town_name = name
                    break

            self._current_info.setText(f"Selected: {town_name} (ID: {depot_id})")

    def _on_accept(self) -> None:
        """Handle OK button click."""
        depot_id = self._depot_combo.currentData()

        properties = {
            "depot_id": depot_id if depot_id is not None else 0,
        }

        # Apply to item if available
        if self._item is not None:
            if hasattr(self._item, "depot_id"):
                self._item.depot_id = properties["depot_id"]

        self.properties_changed.emit(properties)
        self.accept()

    def get_depot_id(self) -> int:
        """Get the selected depot ID.

        Returns:
            The depot ID value.
        """
        depot_id = self._depot_combo.currentData()
        return depot_id if depot_id is not None else 0

    def set_depot_id(self, depot_id: int) -> None:
        """Set the depot ID.

        Args:
            depot_id: The depot ID to set.
        """
        index = self._depot_combo.findData(depot_id)
        if index >= 0:
            self._depot_combo.setCurrentIndex(index)
        else:
            # Add as custom if not found
            self._depot_combo.addItem(f"{depot_id} - Custom", depot_id)
            self._depot_combo.setCurrentIndex(self._depot_combo.count() - 1)

    def get_properties(self) -> dict:
        """Get all properties as a dictionary.

        Returns:
            Dictionary with depot_id.
        """
        depot_id = self._depot_combo.currentData()
        return {
            "depot_id": depot_id if depot_id is not None else 0,
        }
