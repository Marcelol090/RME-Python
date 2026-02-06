"""Splash Properties Window - Edit fluid/liquid items.

Dialog for editing splash items (water, blood, slime, etc).
Mirrors legacy C++ SplashPropertiesWindow from source/ui/properties/splash_properties_window.cpp.

Reference:
    - C++ SplashPropertiesWindow: source/ui/properties/splash_properties_window.h
    - Fluid types: core/data/enums.py
"""

from __future__ import annotations

import logging
from enum import IntEnum
from typing import TYPE_CHECKING

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtGui import QColor, QPainter
from PyQt6.QtWidgets import (
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from py_rme_canary.core.data.item import Item
    from py_rme_canary.core.data.tile import Tile

logger = logging.getLogger(__name__)


class FluidType(IntEnum):
    """Fluid types matching Tibia protocol.

    Standard fluid colors/types used in the game.
    """

    EMPTY = 0
    WATER = 1
    BLOOD = 2
    BEER = 3
    SLIME = 4
    LEMONADE = 5
    MILK = 6
    MANA = 7
    LIFE = 8  # Health fluid
    OIL = 9
    URINE = 10
    COCONUT_MILK = 11
    WINE = 12
    MUD = 13
    FRUIT_JUICE = 14
    LAVA = 15
    RUM = 16
    SWAMP = 17
    TEA = 18
    MEAD = 19


# Fluid colors for visual preview
FLUID_COLORS: dict[FluidType, tuple[int, int, int]] = {
    FluidType.EMPTY: (128, 128, 128),
    FluidType.WATER: (50, 100, 200),
    FluidType.BLOOD: (180, 30, 30),
    FluidType.BEER: (200, 150, 50),
    FluidType.SLIME: (50, 180, 50),
    FluidType.LEMONADE: (255, 255, 100),
    FluidType.MILK: (250, 250, 250),
    FluidType.MANA: (50, 50, 200),
    FluidType.LIFE: (200, 50, 50),
    FluidType.OIL: (50, 50, 50),
    FluidType.URINE: (200, 200, 50),
    FluidType.COCONUT_MILK: (245, 245, 220),
    FluidType.WINE: (150, 30, 60),
    FluidType.MUD: (100, 80, 50),
    FluidType.FRUIT_JUICE: (255, 150, 50),
    FluidType.LAVA: (255, 80, 30),
    FluidType.RUM: (180, 120, 60),
    FluidType.SWAMP: (80, 100, 50),
    FluidType.TEA: (150, 100, 50),
    FluidType.MEAD: (220, 180, 80),
}


class FluidPreviewWidget(QFrame):
    """Widget showing fluid color preview."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._fluid_type = FluidType.EMPTY
        self.setFixedSize(40, 40)
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)

    def set_fluid_type(self, fluid_type: FluidType) -> None:
        """Set the fluid type to preview."""
        self._fluid_type = fluid_type
        self.update()

    def paintEvent(self, event) -> None:
        """Draw the fluid color."""
        super().paintEvent(event)
        painter = QPainter(self)

        color = FLUID_COLORS.get(self._fluid_type, (128, 128, 128))
        painter.fillRect(2, 2, self.width() - 4, self.height() - 4, QColor(*color))

        painter.end()


class SplashPropertiesWindow(QDialog):
    """Dialog for editing splash/fluid item properties.

    Allows editing:
    - Action ID / Unique ID
    - Fluid type (water, blood, slime, etc)

    Signals:
        properties_changed: Emitted when user confirms changes.
    """

    properties_changed = pyqtSignal(dict)  # {action_id, unique_id, fluid_type}

    def __init__(
        self,
        item: Item | None = None,
        tile: Tile | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize splash properties window.

        Args:
            item: The splash/fluid item to edit.
            tile: The tile containing the item.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._item = item
        self._tile = tile

        self.setWindowTitle("Edit Fluid")
        self.setMinimumSize(380, 300)
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
        self._item_label = QLabel("Fluid Item")
        self._item_label.setObjectName("headerLabel")
        header.addWidget(self._item_label)
        header.addStretch()
        layout.addLayout(header)

        # ID Fields group
        id_group = QGroupBox("Identifiers")
        id_layout = QFormLayout(id_group)
        id_layout.setSpacing(10)

        self._action_id = QSpinBox()
        self._action_id.setRange(0, 65535)
        self._action_id.setSpecialValueText("None")
        self._action_id.setToolTip("Action ID for scripting")
        id_layout.addRow("Action ID:", self._action_id)

        self._unique_id = QSpinBox()
        self._unique_id.setRange(0, 65535)
        self._unique_id.setSpecialValueText("None")
        self._unique_id.setToolTip("Unique ID (must be unique on map)")
        id_layout.addRow("Unique ID:", self._unique_id)

        layout.addWidget(id_group)

        # Fluid type group
        fluid_group = QGroupBox("Fluid Type")
        fluid_layout = QVBoxLayout(fluid_group)
        fluid_layout.setSpacing(12)

        # Fluid selector with preview
        selector_layout = QHBoxLayout()

        self._fluid_preview = FluidPreviewWidget()
        selector_layout.addWidget(self._fluid_preview)

        self._fluid_combo = QComboBox()
        self._fluid_combo.setMinimumWidth(200)

        # Populate fluid types
        for fluid in FluidType:
            name = fluid.name.replace("_", " ").title()
            self._fluid_combo.addItem(name, fluid)

        self._fluid_combo.currentIndexChanged.connect(self._on_fluid_changed)
        selector_layout.addWidget(self._fluid_combo, 1)

        fluid_layout.addLayout(selector_layout)

        # Fluid info label
        self._fluid_info = QLabel("Select a fluid type")
        self._fluid_info.setObjectName("fluidInfo")
        self._fluid_info.setWordWrap(True)
        fluid_layout.addWidget(self._fluid_info)

        layout.addWidget(fluid_group)

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
            QLabel#fluidInfo {
                font-size: 11px;
                color: #6C7086;
                padding: 6px;
                background-color: #313244;
                border-radius: 4px;
            }
            QSpinBox {
                background-color: #313244;
                border: 1px solid #45475A;
                border-radius: 4px;
                padding: 6px 10px;
                color: #CDD6F4;
                min-width: 100px;
            }
            QSpinBox:focus {
                border-color: #8B5CF6;
            }
            QSpinBox::up-button, QSpinBox::down-button {
                background-color: #45475A;
                border: none;
                width: 20px;
            }
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {
                background-color: #585B70;
            }
            QComboBox {
                background-color: #313244;
                border: 1px solid #45475A;
                border-radius: 4px;
                padding: 8px 12px;
                color: #CDD6F4;
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

        # Load Action ID
        action_id = getattr(self._item, "action_id", 0) or 0
        self._action_id.setValue(action_id)

        # Load Unique ID
        unique_id = getattr(self._item, "unique_id", 0) or 0
        self._unique_id.setValue(unique_id)

        # Load fluid type
        fluid_type = getattr(self._item, "fluid_type", 0) or 0
        try:
            fluid = FluidType(fluid_type)
            index = self._fluid_combo.findData(fluid)
            if index >= 0:
                self._fluid_combo.setCurrentIndex(index)
        except ValueError:
            pass

    def _on_fluid_changed(self, index: int) -> None:
        """Handle fluid type selection change."""
        fluid = self._fluid_combo.currentData()
        if fluid is not None:
            self._fluid_preview.set_fluid_type(fluid)

            # Update info text
            info_texts = {
                FluidType.EMPTY: "No fluid contents",
                FluidType.WATER: "Clear water - commonly found in wells and lakes",
                FluidType.BLOOD: "Blood - dropped by creatures when killed",
                FluidType.BEER: "Alcoholic beverage - found in taverns",
                FluidType.SLIME: "Green slime - toxic substance",
                FluidType.LEMONADE: "Refreshing citrus drink",
                FluidType.MILK: "Fresh milk from cows",
                FluidType.MANA: "Blue magical fluid - restores mana",
                FluidType.LIFE: "Red health fluid - restores hitpoints",
                FluidType.OIL: "Dark oil - flammable liquid",
                FluidType.URINE: "Yellow waste fluid",
                FluidType.COCONUT_MILK: "Tropical coconut milk",
                FluidType.WINE: "Red wine - alcoholic beverage",
                FluidType.MUD: "Brown muddy water",
                FluidType.FRUIT_JUICE: "Orange fruit juice",
                FluidType.LAVA: "Molten lava - extremely hot",
                FluidType.RUM: "Strong alcoholic spirit",
                FluidType.SWAMP: "Murky swamp water",
                FluidType.TEA: "Hot brewed tea",
                FluidType.MEAD: "Honey-based alcoholic drink",
            }
            self._fluid_info.setText(info_texts.get(fluid, "Unknown fluid type"))

    def _on_accept(self) -> None:
        """Handle OK button click."""
        fluid = self._fluid_combo.currentData()

        properties = {
            "action_id": self._action_id.value() or None,
            "unique_id": self._unique_id.value() or None,
            "fluid_type": fluid.value if fluid else 0,
        }

        # Apply to item if available
        if self._item is not None:
            if hasattr(self._item, "action_id"):
                self._item.action_id = properties["action_id"]
            if hasattr(self._item, "unique_id"):
                self._item.unique_id = properties["unique_id"]
            if hasattr(self._item, "fluid_type"):
                self._item.fluid_type = properties["fluid_type"]

        self.properties_changed.emit(properties)
        self.accept()

    def get_fluid_type(self) -> int:
        """Get the selected fluid type.

        Returns:
            The fluid type value.
        """
        fluid = self._fluid_combo.currentData()
        return fluid.value if fluid else 0

    def set_fluid_type(self, fluid_type: int) -> None:
        """Set the fluid type.

        Args:
            fluid_type: The fluid type value to set.
        """
        try:
            fluid = FluidType(fluid_type)
            index = self._fluid_combo.findData(fluid)
            if index >= 0:
                self._fluid_combo.setCurrentIndex(index)
        except ValueError:
            pass

    def get_properties(self) -> dict:
        """Get all properties as a dictionary.

        Returns:
            Dictionary with action_id, unique_id, and fluid_type.
        """
        fluid = self._fluid_combo.currentData()
        return {
            "action_id": self._action_id.value() or None,
            "unique_id": self._unique_id.value() or None,
            "fluid_type": fluid.value if fluid else 0,
        }
