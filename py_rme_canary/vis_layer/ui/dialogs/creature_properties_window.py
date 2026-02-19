"""Creature Properties Window.

Edit creature spawn time and direction - matches C++ CreaturePropertiesWindow from Redux.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING

from PyQt6.QtCore import pyqtSignal
from PyQt6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QGroupBox,
    QLabel,
    QSpinBox,
    QVBoxLayout,
)

from py_rme_canary.vis_layer.ui.theme import get_theme_manager

if TYPE_CHECKING:
    pass


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
class CreatureData:
    """Creature configuration data."""

    name: str = ""
    creature_type: str = ""
    spawn_time: int = 60  # seconds
    direction: Direction = Direction.SOUTH


class CreaturePropertiesWindow(QDialog):
    """Edit creature spawn time and direction.

    Matches C++ CreaturePropertiesWindow from Redux - provides controls
    for spawn interval and initial facing direction.
    """

    properties_changed = pyqtSignal(object)  # CreatureData

    def __init__(self, parent=None, data: CreatureData | None = None):
        super().__init__(parent)
        self._data = data or CreatureData()

        self.setWindowTitle("Creature Properties")
        self.setMinimumWidth(_scale_dip(self, 350))
        self._setup_ui()
        self._style()
        self._load_data()

    def _setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setSpacing(_scale_dip(self, 12))
        margin = _scale_dip(self, 16)
        layout.setContentsMargins(margin, margin, margin, margin)

        c = get_theme_manager().tokens["color"]

        # Properties group
        props_group = QGroupBox("Creature Properties")
        props_layout = QFormLayout(props_group)
        props_layout.setSpacing(_scale_dip(self, 10))

        # Creature name
        self._name_label = QLabel(f'"{self._data.name}"')
        self._name_label.setStyleSheet(f"font-weight: bold; color: {c['brand']['primary']};")
        props_layout.addRow("Creature:", self._name_label)

        # Spawn interval
        self.spawn_time_spin = QSpinBox()
        self.spawn_time_spin.setRange(10, 86400)  # 10 seconds to 24 hours
        self.spawn_time_spin.setSuffix(" sec")
        self.spawn_time_spin.setToolTip(
            "Spawn interval in seconds (10-86400).\n" "This is how long until the creature respawns after being killed."
        )
        props_layout.addRow("Spawn Interval:", self.spawn_time_spin)

        # Direction
        self.direction_combo = QComboBox()
        self.direction_combo.addItems(Direction.names())
        self.direction_combo.setToolTip("Initial facing direction when spawned.")
        props_layout.addRow("Direction:", self.direction_combo)

        layout.addWidget(props_group)

        # Info label
        info_label = QLabel(
            "Note: Spawn interval determines how often this creature\n" "respawns after being killed in-game."
        )
        info_label.setStyleSheet(f"color: {c['text']['tertiary']}; font-size: 11px;")
        layout.addWidget(info_label)

        # Buttons
        btn_box = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        btn_box.accepted.connect(self._on_ok)
        btn_box.rejected.connect(self.reject)
        layout.addWidget(btn_box)

    def _style(self):
        c = get_theme_manager().tokens["color"]
        r = get_theme_manager().tokens["radius"]

        self.setStyleSheet(
            f"""
            CreaturePropertiesWindow {{
                background: {c['surface']['primary']};
            }}
            QGroupBox {{
                color: {c['text']['primary']};
                font-weight: bold;
                border: 1px solid {c['border']['default']};
                border-radius: {r['sm']}px;
                margin-top: 8px;
                padding-top: 8px;
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 8px;
                padding: 0 4px;
            }}
            QLabel {{
                color: {c['text']['primary']};
            }}
            QSpinBox, QComboBox {{
                background: {c['surface']['secondary']};
                color: {c['text']['primary']};
                border: 1px solid {c['border']['default']};
                border-radius: {r['sm']}px;
                padding: 6px;
                min-width: 120px;
            }}
            QSpinBox:focus, QComboBox:focus {{
                border-color: {c['brand']['primary']};
            }}
            QComboBox::drop-down {{
                border: none;
                width: 20px;
            }}
            QComboBox QAbstractItemView {{
                background: {c['surface']['secondary']};
                color: {c['text']['primary']};
                selection-background-color: {c['brand']['primary']};
            }}
            QPushButton {{
                background: {c['surface']['secondary']};
                color: {c['text']['primary']};
                border: 1px solid {c['border']['default']};
                border-radius: {r['sm']}px;
                padding: 8px 16px;
                min-width: 80px;
            }}
            QPushButton:hover {{
                background: {c['state']['hover']};
            }}
            QPushButton:pressed {{
                background: {c['brand']['primary']};
            }}
        """
        )

    def _load_data(self):
        """Load data into UI controls."""
        self._name_label.setText(f'"{self._data.name}"')
        self.spawn_time_spin.setValue(self._data.spawn_time)
        self.direction_combo.setCurrentIndex(int(self._data.direction))

    def _on_ok(self):
        """Save data and accept."""
        self._data.spawn_time = self.spawn_time_spin.value()
        self._data.direction = Direction(self.direction_combo.currentIndex())

        self.properties_changed.emit(self._data)
        self.accept()

    def get_data(self) -> CreatureData:
        """Get the creature configuration data."""
        return self._data

    def get_spawn_time(self) -> int:
        """Get the spawn time in seconds."""
        return self._data.spawn_time

    def get_direction(self) -> Direction:
        """Get the facing direction."""
        return self._data.direction


def _scale_dip(dialog: QDialog, value: int) -> int:
    app = QApplication.instance()
    if app is None:
        return int(value)
    screen = dialog.screen() or app.primaryScreen()
    if screen is None:
        return int(value)
    factor = float(screen.logicalDotsPerInch()) / 96.0
    return max(1, int(round(float(value) * max(1.0, factor))))
