"""Podium Properties Window.

Configure outfit display on podiums - matches C++ PodiumPropertiesWindow from Redux.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import IntEnum
from typing import TYPE_CHECKING

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSpinBox,
    QVBoxLayout,
)

if TYPE_CHECKING:
    pass

OUTFIT_COLOR_MAX = 133


class Direction(IntEnum):
    """Creature facing direction."""

    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3

    @classmethod
    def names(cls) -> list[str]:
        return ["North", "East", "South", "West"]


@dataclass
class PodiumOutfit:
    """Outfit configuration for podium display."""

    look_type: int = 0
    look_head: int = 0
    look_body: int = 0
    look_legs: int = 0
    look_feet: int = 0
    look_addon: int = 0
    look_mount: int = 0
    look_mount_head: int = 0
    look_mount_body: int = 0
    look_mount_legs: int = 0
    look_mount_feet: int = 0


@dataclass
class PodiumData:
    """Complete podium configuration."""

    item_id: int = 0
    item_name: str = ""
    action_id: int = 0
    unique_id: int = 0
    tier: int = 0
    classification: int = 0
    direction: Direction = Direction.SOUTH
    show_outfit: bool = True
    show_mount: bool = False
    show_platform: bool = True
    outfit: PodiumOutfit = field(default_factory=PodiumOutfit)


class PodiumPropertiesWindow(QDialog):
    """Configure outfit display on podiums.

    Matches C++ PodiumPropertiesWindow from Redux - provides full control
    over outfit colors, mount colors, and display options.
    """

    properties_changed = pyqtSignal(object)  # PodiumData

    def __init__(self, parent=None, data: PodiumData | None = None):
        super().__init__(parent)
        self._data = data or PodiumData()

        self.setWindowTitle("Podium Properties")
        self.setMinimumWidth(_scale_dip(self, 700))
        self._setup_ui()
        self._style()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(_scale_dip(self, 12))
        margin = _scale_dip(self, 16)
        layout.setContentsMargins(margin, margin, margin, margin)

        # Main properties group
        main_group = QGroupBox("Podium Properties")
        main_layout = QFormLayout(main_group)
        main_layout.setSpacing(_scale_dip(self, 8))

        # ID display
        self._id_label = QLabel(f'ID: {self._data.item_id}  "{self._data.item_name}"')
        main_layout.addRow(self._id_label)

        # Action ID
        self.action_id_spin = QSpinBox()
        self.action_id_spin.setRange(0, 65535)
        self.action_id_spin.setToolTip("Action ID (0-65535). Used for scripting.")
        main_layout.addRow("Action ID:", self.action_id_spin)

        # Unique ID
        self.unique_id_spin = QSpinBox()
        self.unique_id_spin.setRange(0, 65535)
        self.unique_id_spin.setToolTip("Unique ID (0-65535). Must be unique on the map.")
        main_layout.addRow("Unique ID:", self.unique_id_spin)

        # Tier (only for classified items)
        self.tier_spin = QSpinBox()
        self.tier_spin.setRange(0, 255)
        self.tier_spin.setToolTip("Item tier (0-255).")
        main_layout.addRow("Tier:", self.tier_spin)

        # Direction
        self.direction_combo = QComboBox()
        self.direction_combo.addItems(Direction.names())
        main_layout.addRow("Direction:", self.direction_combo)

        # Display options
        self.show_outfit_check = QCheckBox("Show outfit")
        self.show_outfit_check.setToolTip("Display outfit on the podium.")
        main_layout.addRow(self.show_outfit_check)

        self.show_mount_check = QCheckBox("Show mount")
        self.show_mount_check.setToolTip("Display mount on the podium.")
        main_layout.addRow(self.show_mount_check)

        self.show_platform_check = QCheckBox("Show platform")
        self.show_platform_check.setToolTip("Display the podium platform.")
        main_layout.addRow(self.show_platform_check)

        layout.addWidget(main_group)

        # Outfit and Mount in horizontal layout
        outfit_mount_layout = QHBoxLayout()

        # Outfit group
        outfit_group = QGroupBox("Outfit")
        outfit_layout = QFormLayout(outfit_group)
        outfit_layout.setSpacing(_scale_dip(self, 6))

        self.look_type_spin = QSpinBox()
        self.look_type_spin.setRange(0, 65535)
        self.look_type_spin.setToolTip("Outfit look type ID.")
        outfit_layout.addRow("LookType:", self.look_type_spin)

        self.look_head_spin = QSpinBox()
        self.look_head_spin.setRange(0, OUTFIT_COLOR_MAX)
        self.look_head_spin.setToolTip(f"Head color (0-{OUTFIT_COLOR_MAX}).")
        outfit_layout.addRow("Head:", self.look_head_spin)

        self.look_body_spin = QSpinBox()
        self.look_body_spin.setRange(0, OUTFIT_COLOR_MAX)
        self.look_body_spin.setToolTip(f"Body/Primary color (0-{OUTFIT_COLOR_MAX}).")
        outfit_layout.addRow("Body:", self.look_body_spin)

        self.look_legs_spin = QSpinBox()
        self.look_legs_spin.setRange(0, OUTFIT_COLOR_MAX)
        self.look_legs_spin.setToolTip(f"Legs/Secondary color (0-{OUTFIT_COLOR_MAX}).")
        outfit_layout.addRow("Legs:", self.look_legs_spin)

        self.look_feet_spin = QSpinBox()
        self.look_feet_spin.setRange(0, OUTFIT_COLOR_MAX)
        self.look_feet_spin.setToolTip(f"Feet/Detail color (0-{OUTFIT_COLOR_MAX}).")
        outfit_layout.addRow("Feet:", self.look_feet_spin)

        self.look_addon_spin = QSpinBox()
        self.look_addon_spin.setRange(0, 3)
        self.look_addon_spin.setToolTip("Addons bitmask (0=none, 1=first, 2=second, 3=both).")
        outfit_layout.addRow("Addons:", self.look_addon_spin)

        outfit_mount_layout.addWidget(outfit_group)

        # Mount group
        mount_group = QGroupBox("Mount")
        mount_layout = QFormLayout(mount_group)
        mount_layout.setSpacing(_scale_dip(self, 6))

        self.look_mount_spin = QSpinBox()
        self.look_mount_spin.setRange(0, 65535)
        self.look_mount_spin.setToolTip("Mount look type ID.")
        mount_layout.addRow("LookMount:", self.look_mount_spin)

        self.look_mount_head_spin = QSpinBox()
        self.look_mount_head_spin.setRange(0, OUTFIT_COLOR_MAX)
        self.look_mount_head_spin.setToolTip(f"Mount head color (0-{OUTFIT_COLOR_MAX}).")
        mount_layout.addRow("Head:", self.look_mount_head_spin)

        self.look_mount_body_spin = QSpinBox()
        self.look_mount_body_spin.setRange(0, OUTFIT_COLOR_MAX)
        self.look_mount_body_spin.setToolTip(f"Mount body color (0-{OUTFIT_COLOR_MAX}).")
        mount_layout.addRow("Body:", self.look_mount_body_spin)

        self.look_mount_legs_spin = QSpinBox()
        self.look_mount_legs_spin.setRange(0, OUTFIT_COLOR_MAX)
        self.look_mount_legs_spin.setToolTip(f"Mount legs color (0-{OUTFIT_COLOR_MAX}).")
        mount_layout.addRow("Legs:", self.look_mount_legs_spin)

        self.look_mount_feet_spin = QSpinBox()
        self.look_mount_feet_spin.setRange(0, OUTFIT_COLOR_MAX)
        self.look_mount_feet_spin.setToolTip(f"Mount feet color (0-{OUTFIT_COLOR_MAX}).")
        mount_layout.addRow("Feet:", self.look_mount_feet_spin)

        outfit_mount_layout.addWidget(mount_group)

        layout.addLayout(outfit_mount_layout)

        # Buttons
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(self._on_ok)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _style(self):
        self.setStyleSheet(
            """
            PodiumPropertiesWindow {
                background: #1E1E2E;
            }
            QGroupBox {
                color: #E5E5E7;
                font-weight: bold;
                border: 1px solid #363650;
                border-radius: 4px;
                margin-top: 8px;
                padding-top: 8px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }
            QLabel {
                color: #E5E5E7;
            }
            QSpinBox, QComboBox {
                background: #2A2A3E;
                color: #E5E5E7;
                border: 1px solid #363650;
                border-radius: 4px;
                padding: 4px;
                min-width: 80px;
            }
            QSpinBox:focus, QComboBox:focus {
                border-color: #8B5CF6;
            }
            QComboBox::drop-down {
                border: none;
                width: 20px;
            }
            QComboBox QAbstractItemView {
                background: #2A2A3E;
                color: #E5E5E7;
                selection-background-color: #8B5CF6;
            }
            QCheckBox {
                color: #E5E5E7;
                spacing: 8px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border: 1px solid #363650;
                border-radius: 3px;
                background: #2A2A3E;
            }
            QCheckBox::indicator:checked {
                background: #8B5CF6;
                border-color: #8B5CF6;
            }
            QPushButton {
                background: #2A2A3E;
                color: #E5E5E7;
                border: 1px solid #363650;
                border-radius: 4px;
                padding: 8px 16px;
                min-width: 80px;
            }
            QPushButton:hover {
                background: #363650;
            }
            QPushButton:pressed {
                background: #8B5CF6;
            }
        """
        )

    def _load_data(self):
        """Load data into UI controls."""
        self.action_id_spin.setValue(self._data.action_id)
        self.unique_id_spin.setValue(self._data.unique_id)
        self.tier_spin.setValue(self._data.tier)
        self.direction_combo.setCurrentIndex(int(self._data.direction))

        self.show_outfit_check.setChecked(self._data.show_outfit)
        self.show_mount_check.setChecked(self._data.show_mount)
        self.show_platform_check.setChecked(self._data.show_platform)

        outfit = self._data.outfit
        self.look_type_spin.setValue(outfit.look_type)
        self.look_head_spin.setValue(outfit.look_head)
        self.look_body_spin.setValue(outfit.look_body)
        self.look_legs_spin.setValue(outfit.look_legs)
        self.look_feet_spin.setValue(outfit.look_feet)
        self.look_addon_spin.setValue(outfit.look_addon)

        self.look_mount_spin.setValue(outfit.look_mount)
        self.look_mount_head_spin.setValue(outfit.look_mount_head)
        self.look_mount_body_spin.setValue(outfit.look_mount_body)
        self.look_mount_legs_spin.setValue(outfit.look_mount_legs)
        self.look_mount_feet_spin.setValue(outfit.look_mount_feet)

    def _on_ok(self):
        """Save data and accept."""
        self._data.action_id = self.action_id_spin.value()
        self._data.unique_id = self.unique_id_spin.value()
        self._data.tier = self.tier_spin.value()
        self._data.direction = Direction(self.direction_combo.currentIndex())

        self._data.show_outfit = self.show_outfit_check.isChecked()
        self._data.show_mount = self.show_mount_check.isChecked()
        self._data.show_platform = self.show_platform_check.isChecked()

        self._data.outfit.look_type = self.look_type_spin.value()
        self._data.outfit.look_head = self.look_head_spin.value()
        self._data.outfit.look_body = self.look_body_spin.value()
        self._data.outfit.look_legs = self.look_legs_spin.value()
        self._data.outfit.look_feet = self.look_feet_spin.value()
        self._data.outfit.look_addon = self.look_addon_spin.value()

        self._data.outfit.look_mount = self.look_mount_spin.value()
        self._data.outfit.look_mount_head = self.look_mount_head_spin.value()
        self._data.outfit.look_mount_body = self.look_mount_body_spin.value()
        self._data.outfit.look_mount_legs = self.look_mount_legs_spin.value()
        self._data.outfit.look_mount_feet = self.look_mount_feet_spin.value()

        self.properties_changed.emit(self._data)
        self.accept()

    def get_data(self) -> PodiumData:
        """Get the podium configuration data."""
        return self._data


def _scale_dip(dialog: QDialog, value: int) -> int:
    app = QApplication.instance()
    if app is None:
        return int(value)
    screen = dialog.screen() or app.primaryScreen()
    if screen is None:
        return int(value)
    factor = float(screen.logicalDotsPerInch()) / 96.0
    return max(1, int(round(float(value) * max(1.0, factor))))
