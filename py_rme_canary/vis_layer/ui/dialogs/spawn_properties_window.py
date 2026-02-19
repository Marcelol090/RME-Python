"""Spawn Properties Window - Edit spawn area properties.

Dialog for editing spawn zones where creatures appear.
Mirrors legacy C++ SpawnPropertiesWindow from source/ui/properties/spawn_properties_window.cpp.

Reference:
    - C++ SpawnPropertiesWindow: source/ui/properties/spawn_properties_window.h
    - Spawn system: core/data/spawn.py
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPen
from PyQt6.QtWidgets import (
    QApplication,
    QDialog,
    QDialogButtonBox,
    QFormLayout,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QLabel,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

from py_rme_canary.vis_layer.ui.theme import get_theme_manager

if TYPE_CHECKING:
    from py_rme_canary.core.data.spawn import Spawn
    from py_rme_canary.core.data.tile import Tile

logger = logging.getLogger(__name__)


class SpawnRadiusPreview(QFrame):
    """Widget showing spawn radius preview visualization."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._radius = 3
        self._max_creatures = 4
        size = _scale_dip(self, 150)
        self.setFixedSize(size, size)
        self.setFrameStyle(QFrame.Shape.Box | QFrame.Shadow.Sunken)

    def set_radius(self, radius: int) -> None:
        """Set the spawn radius."""
        self._radius = max(1, min(radius, 10))
        self.update()

    def set_max_creatures(self, count: int) -> None:
        """Set max creatures count for display."""
        self._max_creatures = count
        self.update()

    def paintEvent(self, event) -> None:
        """Draw the spawn radius visualization."""
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        c = get_theme_manager().tokens["color"]

        # Background
        painter.fillRect(self.rect(), QColor(c["surface"]["secondary"]))

        # Calculate center and scale
        cx = self.width() // 2
        cy = self.height() // 2
        scale = min(self.width(), self.height()) // (self._radius * 2 + 4)
        scale = max(scale, 5)

        # Draw spawn radius circle
        pen = QPen(QColor(c["brand"]["primary"]))
        pen.setWidth(2)
        painter.setPen(pen)
        brand_color = QColor(c["brand"]["primary"])
        brand_color.setAlpha(50)
        painter.setBrush(brand_color)

        radius_pixels = self._radius * scale
        painter.drawEllipse(
            int(cx - radius_pixels),
            int(cy - radius_pixels),
            int(radius_pixels * 2),
            int(radius_pixels * 2),
        )

        # Draw center point (spawn origin)
        painter.setBrush(QColor(c["state"]["error"]))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(cx - 4, cy - 4, 8, 8)

        # Draw sample creature positions
        import math

        creature_color = QColor(c["state"]["success"])
        painter.setBrush(creature_color)

        for i in range(min(self._max_creatures, 8)):
            angle = (2 * math.pi * i) / max(self._max_creatures, 1)
            dist = radius_pixels * 0.6
            x = cx + int(math.cos(angle) * dist)
            y = cy + int(math.sin(angle) * dist)
            painter.drawEllipse(x - 3, y - 3, 6, 6)

        # Draw info text
        painter.setPen(QColor(c["text"]["primary"]))
        painter.drawText(
            self.rect().adjusted(0, 0, 0, -5),
            Qt.AlignmentFlag.AlignBottom | Qt.AlignmentFlag.AlignHCenter,
            f"r={self._radius}",
        )

        painter.end()


class SpawnPropertiesWindow(QDialog):
    """Dialog for editing spawn area properties.

    Allows editing:
    - Spawn radius (area where creatures can spawn)
    - Maximum creature count
    - Spawn interval (time between spawns)

    Signals:
        properties_changed: Emitted when user confirms changes.
    """

    properties_changed = pyqtSignal(dict)  # {radius, max_creatures, interval}

    # Default spawn values
    DEFAULT_RADIUS = 3
    DEFAULT_MAX_CREATURES = 4
    DEFAULT_INTERVAL = 60  # seconds

    # Limits
    MIN_RADIUS = 1
    MAX_RADIUS = 10
    MIN_CREATURES = 1
    MAX_CREATURES = 100
    MIN_INTERVAL = 1
    MAX_INTERVAL = 3600

    def __init__(
        self,
        spawn: Spawn | None = None,
        tile: Tile | None = None,
        parent: QWidget | None = None,
    ) -> None:
        """Initialize spawn properties window.

        Args:
            spawn: The spawn object to edit.
            tile: The tile containing the spawn.
            parent: Parent widget.
        """
        super().__init__(parent)
        self._spawn = spawn
        self._tile = tile

        self.setWindowTitle("Edit Spawn")
        self.setMinimumSize(_scale_dip(self, 450), _scale_dip(self, 420))
        self.setModal(True)

        self._setup_ui()
        self._apply_style()
        self._load_values()

    def _setup_ui(self) -> None:
        """Initialize UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(_scale_dip(self, 16))
        margin = _scale_dip(self, 20)
        layout.setContentsMargins(margin, margin, margin, margin)

        # Header
        header = QHBoxLayout()
        self._header_label = QLabel("Spawn Configuration")
        self._header_label.setObjectName("headerLabel")
        header.addWidget(self._header_label)
        header.addStretch()
        layout.addLayout(header)

        # Main content - preview and settings side by side
        content_layout = QHBoxLayout()
        content_layout.setSpacing(_scale_dip(self, 20))

        # Left side - Preview
        preview_group = QGroupBox("Preview")
        preview_layout = QVBoxLayout(preview_group)
        preview_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)

        self._preview = SpawnRadiusPreview()
        preview_layout.addWidget(self._preview)

        # Preview legend
        legend = QLabel("● Center  ● Creatures")
        legend.setObjectName("legend")
        legend.setAlignment(Qt.AlignmentFlag.AlignCenter)
        preview_layout.addWidget(legend)

        content_layout.addWidget(preview_group)

        # Right side - Settings
        settings_group = QGroupBox("Settings")
        settings_layout = QFormLayout(settings_group)
        settings_layout.setSpacing(_scale_dip(self, 16))

        # Spawn Radius
        radius_layout = QHBoxLayout()

        self._radius_spin = QSpinBox()
        self._radius_spin.setRange(self.MIN_RADIUS, self.MAX_RADIUS)
        self._radius_spin.setValue(self.DEFAULT_RADIUS)
        self._radius_spin.setToolTip("Radius in tiles where creatures can spawn")
        self._radius_spin.valueChanged.connect(self._on_radius_changed)
        radius_layout.addWidget(self._radius_spin)

        self._radius_slider = QSlider(Qt.Orientation.Horizontal)
        self._radius_slider.setRange(self.MIN_RADIUS, self.MAX_RADIUS)
        self._radius_slider.setValue(self.DEFAULT_RADIUS)
        self._radius_slider.valueChanged.connect(self._radius_spin.setValue)
        self._radius_spin.valueChanged.connect(self._radius_slider.setValue)
        radius_layout.addWidget(self._radius_slider, 1)

        settings_layout.addRow("Radius:", radius_layout)

        # Max Creatures
        self._creatures_spin = QSpinBox()
        self._creatures_spin.setRange(self.MIN_CREATURES, self.MAX_CREATURES)
        self._creatures_spin.setValue(self.DEFAULT_MAX_CREATURES)
        self._creatures_spin.setToolTip("Maximum number of creatures in this spawn")
        self._creatures_spin.valueChanged.connect(self._on_creatures_changed)
        settings_layout.addRow("Max Creatures:", self._creatures_spin)

        # Spawn Interval
        interval_layout = QHBoxLayout()

        self._interval_spin = QSpinBox()
        self._interval_spin.setRange(self.MIN_INTERVAL, self.MAX_INTERVAL)
        self._interval_spin.setValue(self.DEFAULT_INTERVAL)
        self._interval_spin.setSuffix(" sec")
        self._interval_spin.setToolTip("Time between creature respawns")
        interval_layout.addWidget(self._interval_spin)

        # Quick interval presets
        interval_presets = QHBoxLayout()
        for label, value in [("30s", 30), ("60s", 60), ("2m", 120), ("5m", 300)]:
            btn = QLabel(f"[{label}]")
            btn.setObjectName("presetLabel")
            btn.setCursor(Qt.CursorShape.PointingHandCursor)
            btn.mousePressEvent = lambda e, v=value: self._interval_spin.setValue(v)
            interval_presets.addWidget(btn)
        interval_presets.addStretch()

        interval_container = QVBoxLayout()
        interval_container.addLayout(interval_layout)
        interval_container.addLayout(interval_presets)

        settings_layout.addRow("Interval:", interval_container)

        content_layout.addWidget(settings_group, 1)
        layout.addLayout(content_layout)

        # Statistics info
        stats_group = QGroupBox("Statistics")
        stats_layout = QVBoxLayout(stats_group)

        self._stats_label = QLabel()
        self._stats_label.setObjectName("statsLabel")
        self._stats_label.setWordWrap(True)
        stats_layout.addWidget(self._stats_label)

        layout.addWidget(stats_group)

        self._update_stats()

        layout.addStretch()

        # Dialog buttons
        buttons = QDialogButtonBox(QDialogButtonBox.StandardButton.Ok | QDialogButtonBox.StandardButton.Cancel)
        buttons.accepted.connect(self._on_accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def _apply_style(self) -> None:
        """Apply themed styling."""
        c = get_theme_manager().tokens["color"]
        r = get_theme_manager().tokens["radius"]

        self.setStyleSheet(
            f"""
            QDialog {{
                background-color: {c['surface']['primary']};
                color: {c['text']['primary']};
            }}
            QGroupBox {{
                font-weight: bold;
                border: 1px solid {c['border']['default']};
                border-radius: {r['sm']}px;
                margin-top: 12px;
                padding-top: 12px;
                background-color: {c['surface']['secondary']};
            }}
            QGroupBox::title {{
                subcontrol-origin: margin;
                left: 12px;
                padding: 0 6px;
                color: {c['brand']['primary']};
            }}
            QLabel {{
                color: {c['text']['primary']};
            }}
            QLabel#headerLabel {{
                font-size: 14px;
                font-weight: bold;
                color: {c['brand']['primary']};
            }}
            QLabel#legend {{
                font-size: 10px;
                color: {c['text']['tertiary']};
            }}
            QLabel#presetLabel {{
                font-size: 11px;
                color: {c['brand']['active']};
                padding: 2px 4px;
            }}
            QLabel#presetLabel:hover {{
                color: {c['brand']['primary']};
            }}
            QLabel#statsLabel {{
                font-size: 11px;
                color: {c['text']['secondary']};
                padding: 8px;
                background-color: {c['surface']['tertiary']};
                border-radius: 4px;
            }}
            QSpinBox {{
                background-color: {c['surface']['tertiary']};
                border: 1px solid {c['border']['default']};
                border-radius: 4px;
                padding: 6px 10px;
                color: {c['text']['primary']};
                min-width: 80px;
            }}
            QSpinBox:focus {{
                border-color: {c['brand']['primary']};
            }}
            QSpinBox::up-button, QSpinBox::down-button {{
                background-color: {c['border']['default']};
                border: none;
                width: 20px;
            }}
            QSpinBox::up-button:hover, QSpinBox::down-button:hover {{
                background-color: {c['state']['hover']};
            }}
            QSlider::groove:horizontal {{
                border: 1px solid {c['border']['default']};
                height: 6px;
                background-color: {c['surface']['tertiary']};
                border-radius: 3px;
            }}
            QSlider::handle:horizontal {{
                background-color: {c['brand']['primary']};
                border: none;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }}
            QSlider::handle:horizontal:hover {{
                background-color: {c['brand']['active']};
            }}
            QSlider::sub-page:horizontal {{
                background-color: {c['brand']['primary']};
                border-radius: 3px;
            }}
            QPushButton {{
                background-color: {c['border']['default']};
                border: none;
                border-radius: {r['sm']}px;
                padding: 8px 20px;
                color: {c['text']['primary']};
                font-weight: 500;
            }}
            QPushButton:hover {{
                background-color: {c['state']['hover']};
            }}
            QPushButton:pressed {{
                background-color: {c['brand']['primary']};
            }}
            QDialogButtonBox QPushButton {{
                min-width: 90px;
            }}
        """
        )

    def _load_values(self) -> None:
        """Load values from the spawn."""
        if self._spawn is None:
            return

        # Load radius
        radius = getattr(self._spawn, "radius", self.DEFAULT_RADIUS)
        self._radius_spin.setValue(radius)

        # Load max creatures
        max_creatures = getattr(self._spawn, "max_creatures", self.DEFAULT_MAX_CREATURES)
        if max_creatures is None:
            max_creatures = getattr(self._spawn, "size", self.DEFAULT_MAX_CREATURES)
        self._creatures_spin.setValue(max_creatures or self.DEFAULT_MAX_CREATURES)

        # Load interval
        interval = getattr(self._spawn, "interval", self.DEFAULT_INTERVAL)
        if interval is None:
            interval = getattr(self._spawn, "spawn_time", self.DEFAULT_INTERVAL)
        self._interval_spin.setValue(interval or self.DEFAULT_INTERVAL)

    def _on_radius_changed(self, value: int) -> None:
        """Handle radius change."""
        self._preview.set_radius(value)
        self._update_stats()

    def _on_creatures_changed(self, value: int) -> None:
        """Handle max creatures change."""
        self._preview.set_max_creatures(value)
        self._update_stats()

    def _update_stats(self) -> None:
        """Update statistics display."""
        radius = self._radius_spin.value()
        max_creatures = self._creatures_spin.value()
        interval = self._interval_spin.value()

        # Calculate area (pi * r^2)
        import math

        area = math.pi * radius * radius

        # Approximate tiles in spawn area
        tiles = int(area)

        # Creatures per hour
        creatures_per_hour = (3600 // interval) * max_creatures

        self._stats_label.setText(
            f"Spawn Area: ~{tiles} tiles  |  "
            f"Density: {max_creatures/max(tiles, 1):.2f} creatures/tile  |  "
            f"Spawns/hour: ~{creatures_per_hour}"
        )

    def _on_accept(self) -> None:
        """Handle OK button click."""
        properties = {
            "radius": self._radius_spin.value(),
            "max_creatures": self._creatures_spin.value(),
            "interval": self._interval_spin.value(),
        }

        # Apply to spawn if available
        if self._spawn is not None:
            if hasattr(self._spawn, "radius"):
                self._spawn.radius = properties["radius"]
            if hasattr(self._spawn, "max_creatures"):
                self._spawn.max_creatures = properties["max_creatures"]
            elif hasattr(self._spawn, "size"):
                self._spawn.size = properties["max_creatures"]
            if hasattr(self._spawn, "interval"):
                self._spawn.interval = properties["interval"]
            elif hasattr(self._spawn, "spawn_time"):
                self._spawn.spawn_time = properties["interval"]

        self.properties_changed.emit(properties)
        self.accept()

    def get_radius(self) -> int:
        """Get the spawn radius.

        Returns:
            The radius value.
        """
        return self._radius_spin.value()

    def set_radius(self, radius: int) -> None:
        """Set the spawn radius.

        Args:
            radius: The radius to set.
        """
        self._radius_spin.setValue(max(self.MIN_RADIUS, min(radius, self.MAX_RADIUS)))

    def get_properties(self) -> dict:
        """Get all properties as a dictionary.

        Returns:
            Dictionary with radius, max_creatures, and interval.
        """
        return {
            "radius": self._radius_spin.value(),
            "max_creatures": self._creatures_spin.value(),
            "interval": self._interval_spin.value(),
        }


def _scale_dip(widget: QWidget, value: int) -> int:
    app = QApplication.instance()
    if app is None:
        return int(value)
    screen = widget.screen() or app.primaryScreen()
    if screen is None:
        return int(value)
    factor = float(screen.logicalDotsPerInch()) / 96.0
    return max(1, int(round(float(value) * max(1.0, factor))))
