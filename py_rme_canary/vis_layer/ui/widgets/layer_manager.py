"""Layer Manager Panel.

Controls visibility of map layers:
- Ground
- Items
- Creatures (spawns)
- Houses
- Zones
- Waypoints
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QCheckBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    pass


@dataclass
class Layer:
    """A map display layer."""

    layer_id: str
    name: str
    icon: str
    visible: bool = True
    opacity: float = 1.0
    color: str = "#FFFFFF"


class LayerRow(QFrame):
    """Single layer row with visibility and opacity controls."""

    visibility_changed = pyqtSignal(str, bool)  # layer_id, visible
    opacity_changed = pyqtSignal(str, float)  # layer_id, opacity

    def __init__(self, layer: Layer, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._layer = layer

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 4, 8, 4)
        layout.setSpacing(8)

        # Visibility checkbox
        self.check_visible = QCheckBox()
        self.check_visible.setChecked(self._layer.visible)
        self.check_visible.stateChanged.connect(self._on_visibility_changed)
        layout.addWidget(self.check_visible)

        # Icon and name
        icon = QLabel(self._layer.icon)
        layout.addWidget(icon)

        name = QLabel(self._layer.name)
        name.setStyleSheet("color: #E5E5E7;")
        layout.addWidget(name)

        layout.addStretch()

        # Opacity slider
        self.opacity_slider = QSlider(Qt.Orientation.Horizontal)
        self.opacity_slider.setRange(0, 100)
        self.opacity_slider.setValue(int(self._layer.opacity * 100))
        self.opacity_slider.setFixedWidth(60)
        self.opacity_slider.valueChanged.connect(self._on_opacity_changed)
        layout.addWidget(self.opacity_slider)

        # Opacity label
        self.opacity_label = QLabel(f"{int(self._layer.opacity * 100)}%")
        self.opacity_label.setFixedWidth(35)
        self.opacity_label.setStyleSheet("color: #A1A1AA; font-size: 10px;")
        layout.addWidget(self.opacity_label)

    def _apply_style(self) -> None:
        """Apply styling."""
        self.setStyleSheet(
            """
            LayerRow {
                background: transparent;
                border-radius: 6px;
            }
            LayerRow:hover {
                background: #363650;
            }

            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 4px;
                background: #2A2A3E;
                border: 1px solid #52525B;
            }

            QCheckBox::indicator:checked {
                background: #8B5CF6;
                border-color: #8B5CF6;
            }

            QSlider::groove:horizontal {
                background: #363650;
                height: 4px;
                border-radius: 2px;
            }

            QSlider::handle:horizontal {
                background: #8B5CF6;
                width: 12px;
                height: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }

            QSlider::sub-page:horizontal {
                background: #8B5CF6;
                border-radius: 2px;
            }
        """
        )

    def _on_visibility_changed(self, state: int) -> None:
        """Handle visibility change."""
        visible = state == Qt.CheckState.Checked.value
        self._layer.visible = visible
        self.visibility_changed.emit(self._layer.layer_id, visible)

    def _on_opacity_changed(self, value: int) -> None:
        """Handle opacity change."""
        opacity = value / 100.0
        self._layer.opacity = opacity
        self.opacity_label.setText(f"{value}%")
        self.opacity_changed.emit(self._layer.layer_id, opacity)


class LayerManager(QFrame):
    """Layer manager panel.

    Signals:
        layer_visibility_changed: Emits (layer_id, visible)
        layer_opacity_changed: Emits (layer_id, opacity)
    """

    layer_visibility_changed = pyqtSignal(str, bool)
    layer_opacity_changed = pyqtSignal(str, float)

    DEFAULT_LAYERS = [
        Layer("ground", "Ground", "GR"),
        Layer("items", "Items", "IT"),
        Layer("creatures", "Creatures", "CR"),
        Layer("houses", "Houses", "HS"),
        Layer("zones", "Zones", "ZN"),
        Layer("waypoints", "Waypoints", "WP"),
        Layer("spawns", "Spawns", "SP"),
        Layer("grid", "Grid", "GD", visible=True, opacity=0.5),
    ]

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._layers = self.DEFAULT_LAYERS.copy()
        self._layer_rows: dict[str, LayerRow] = {}

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        # Header
        header = QHBoxLayout()

        title = QLabel("Layers")
        title.setStyleSheet("font-size: 13px; font-weight: 600; color: #E5E5E7;")
        header.addWidget(title)

        header.addStretch()

        # Show all button
        btn_show_all = QPushButton("Show")
        btn_show_all.setFixedSize(44, 24)
        btn_show_all.setToolTip("Show all layers")
        btn_show_all.clicked.connect(self._show_all)
        header.addWidget(btn_show_all)

        # Hide all button
        btn_hide_all = QPushButton("Hide")
        btn_hide_all.setFixedSize(44, 24)
        btn_hide_all.setToolTip("Hide all layers")
        btn_hide_all.clicked.connect(self._hide_all)
        header.addWidget(btn_hide_all)

        layout.addLayout(header)

        # Layer rows
        for layer in self._layers:
            row = LayerRow(layer)
            row.visibility_changed.connect(self.layer_visibility_changed.emit)
            row.opacity_changed.connect(self.layer_opacity_changed.emit)
            layout.addWidget(row)
            self._layer_rows[layer.layer_id] = row

        layout.addStretch()

    def _apply_style(self) -> None:
        """Apply styling."""
        self.setStyleSheet(
            """
            LayerManager {
                background: #2A2A3E;
                border: 1px solid #363650;
                border-radius: 10px;
            }

            QPushButton {
                background: transparent;
                border: none;
                border-radius: 4px;
            }

            QPushButton:hover {
                background: #363650;
            }
        """
        )

    def _show_all(self) -> None:
        """Show all layers."""
        for _layer_id, row in self._layer_rows.items():
            row.check_visible.setChecked(True)

    def _hide_all(self) -> None:
        """Hide all layers."""
        for _layer_id, row in self._layer_rows.items():
            row.check_visible.setChecked(False)

    def set_layer_visible(self, layer_id: str, visible: bool) -> None:
        """Set layer visibility."""
        if layer_id in self._layer_rows:
            self._layer_rows[layer_id].check_visible.setChecked(visible)

    def set_layer_opacity(self, layer_id: str, opacity: float) -> None:
        """Set layer opacity."""
        if layer_id in self._layer_rows:
            self._layer_rows[layer_id].opacity_slider.setValue(int(opacity * 100))

    def get_layer_visibility(self, layer_id: str) -> bool:
        """Get layer visibility."""
        if layer_id in self._layer_rows:
            return self._layer_rows[layer_id].check_visible.isChecked()
        return True

    def get_layer_opacity(self, layer_id: str) -> float:
        """Get layer opacity."""
        if layer_id in self._layer_rows:
            return self._layer_rows[layer_id].opacity_slider.value() / 100.0
        return 1.0
