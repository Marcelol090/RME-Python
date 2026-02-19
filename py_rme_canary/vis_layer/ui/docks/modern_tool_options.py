"""Modern Tool Options Widget — Antigravity Design.

Provides controls for brush size, shape, variability and tool-option toggles
(Preview AutoBorder, Lock Doors) with glassmorphism panels and gradient accent styling.

C++ Reference: remeres-map-editor-redux/source/ui/tool_options_surface.cpp
  - preview_check  → SHOW_AUTOBORDER_PREVIEW (terrain/collection only)
  - lock_check     → DRAW_LOCKED_DOOR        (terrain/collection only)
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import QRectF, QSettings, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QIcon, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (
    QButtonGroup,
    QCheckBox,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from py_rme_canary.vis_layer.ui.theme import get_theme_manager

if TYPE_CHECKING:
    pass

# ---------------------------------------------------------------------------
# Painted shape icons for consistency
# ---------------------------------------------------------------------------

_SETTINGS_ORG = "PyRME"
_SETTINGS_APP = "Canary"
_KEY_PREVIEW = "tool_options/show_autoborder_preview"
_KEY_LOCK = "tool_options/draw_locked_door"


def _shape_icon(shape: str, size: int = 18, checked: bool = False) -> QIcon:
    """Draw shape icon — square or circle."""
    px = QPixmap(size, size)
    px.fill(QColor(0, 0, 0, 0))
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)

    if checked:
        stroke = QColor(255, 255, 255, 220)
        fill = QColor(139, 92, 246, 50)
    else:
        stroke = QColor(161, 161, 170, 140)
        fill = QColor(161, 161, 170, 15)

    p.setPen(QPen(stroke, 1.5))
    p.setBrush(QBrush(fill))
    m = size * 0.18
    rect = QRectF(m, m, size - 2 * m, size - 2 * m)

    if shape == "circle":
        p.drawEllipse(rect)
    else:
        p.drawRoundedRect(rect, 2.5, 2.5)

    p.end()
    return QIcon(px)


class ModernToolOptionsWidget(QWidget):
    """Tool options panel (Size, Shape, Variation, Preview Border, Lock Doors) — Antigravity style.

    C++ parity: ToolOptionsSurface (tool_options_surface.cpp)
    - Preview AutoBorder checkbox  → mirrors interactables.preview_check_rect / SHOW_AUTOBORDER_PREVIEW
    - Lock Doors (Shift) checkbox  → mirrors interactables.lock_check_rect  / DRAW_LOCKED_DOOR
    """

    size_changed = pyqtSignal(int)
    shape_changed = pyqtSignal(str)  # "square" or "circle"
    variation_changed = pyqtSignal(int)
    preview_border_changed = pyqtSignal(bool)  # NEW: Preview AutoBorder toggle
    lock_doors_changed = pyqtSignal(bool)  # NEW: Lock Doors toggle

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_brush_type = "terrain"
        self._settings = QSettings(_SETTINGS_ORG, _SETTINGS_APP)
        self._setup_ui()
        self._apply_style()
        self._load_persisted_settings()

    # ------------------------------------------------------------------
    # Build UI
    # ------------------------------------------------------------------

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(14, 14, 14, 14)
        layout.setSpacing(14)

        # Header
        self.label = QLabel("TOOL OPTIONS")
        self.label.setObjectName("header")
        layout.addWidget(self.label)

        # 1. Brush Size
        self.size_container = QWidget()
        size_layout = QVBoxLayout(self.size_container)
        size_layout.setContentsMargins(0, 0, 0, 0)
        size_layout.setSpacing(8)

        size_header = QHBoxLayout()
        size_label = QLabel("Size")
        size_label.setObjectName("sectionLabel")
        size_header.addWidget(size_label)
        self.size_val_label = QLabel("1")
        self.size_val_label.setObjectName("valueLabel")
        size_header.addWidget(self.size_val_label)
        size_header.addStretch()
        size_layout.addLayout(size_header)

        self.size_slider = QSlider(Qt.Orientation.Horizontal)
        self.size_slider.setObjectName("ToolSlider")
        self.size_slider.setRange(1, 13)
        self.size_slider.setValue(1)
        self.size_slider.setTickPosition(QSlider.TickPosition.TicksBelow)
        self.size_slider.setTickInterval(2)
        self.size_slider.valueChanged.connect(self._on_size_changed)
        size_layout.addWidget(self.size_slider)

        layout.addWidget(self.size_container)

        # 2. Brush Shape
        self.shape_container = QWidget()
        shape_layout = QVBoxLayout(self.shape_container)
        shape_layout.setContentsMargins(0, 0, 0, 0)
        shape_layout.setSpacing(8)

        shape_label = QLabel("Shape")
        shape_label.setObjectName("sectionLabel")
        shape_layout.addWidget(shape_label)

        btn_layout = QHBoxLayout()
        btn_layout.setSpacing(8)
        self.shape_group = QButtonGroup(self)

        self.btn_square = QPushButton("Square")
        self.btn_square.setFixedHeight(34)
        self.btn_square.setCheckable(True)
        self.btn_square.setChecked(True)
        self.btn_square.setObjectName("shapeBtn")
        self.btn_square.setIcon(_shape_icon("square", 16, True))
        self.btn_square.setIconSize(QSize(16, 16))
        self.shape_group.addButton(self.btn_square)
        btn_layout.addWidget(self.btn_square)

        self.btn_circle = QPushButton("Circle")
        self.btn_circle.setFixedHeight(34)
        self.btn_circle.setCheckable(True)
        self.btn_circle.setObjectName("shapeBtn")
        self.btn_circle.setIcon(_shape_icon("circle", 16, False))
        self.btn_circle.setIconSize(QSize(16, 16))
        self.shape_group.addButton(self.btn_circle)
        btn_layout.addWidget(self.btn_circle)

        shape_layout.addLayout(btn_layout)

        self.shape_group.buttonClicked.connect(self._on_shape_changed)
        layout.addWidget(self.shape_container)

        # 3. Variation / Thickness (for Doodads / Collection)
        self.var_container = QWidget()
        var_layout = QVBoxLayout(self.var_container)
        var_layout.setContentsMargins(0, 0, 0, 0)
        var_layout.setSpacing(8)

        var_header = QHBoxLayout()
        var_label = QLabel("Variation")
        var_label.setObjectName("sectionLabel")
        var_header.addWidget(var_label)
        self.var_val_label = QLabel("100%")
        self.var_val_label.setObjectName("valueLabel")
        var_header.addWidget(self.var_val_label)
        var_header.addStretch()
        var_layout.addLayout(var_header)

        self.var_slider = QSlider(Qt.Orientation.Horizontal)
        self.var_slider.setObjectName("ToolSlider")
        self.var_slider.setRange(1, 100)
        self.var_slider.setValue(100)
        self.var_slider.valueChanged.connect(self._on_variation_changed)
        var_layout.addWidget(self.var_slider)

        layout.addWidget(self.var_container)

        # 4. Terrain toggles — Preview AutoBorder + Lock Doors
        #    C++ parity: ToolOptionsSurface.interactables.preview_check_rect / lock_check_rect
        #    Visible only when brush type is terrain or collection (has_tools gate)
        self.toggles_container = QWidget()
        toggles_layout = QVBoxLayout(self.toggles_container)
        toggles_layout.setContentsMargins(0, 4, 0, 0)
        toggles_layout.setSpacing(6)

        self.chk_preview_border = QCheckBox("Preview AutoBorder")
        self.chk_preview_border.setObjectName("toolToggle")
        self.chk_preview_border.setToolTip(
            "Show live auto-border preview while painting terrain"
        )
        self.chk_preview_border.stateChanged.connect(self._on_preview_border_changed)
        toggles_layout.addWidget(self.chk_preview_border)

        self.chk_lock_doors = QCheckBox("Lock Doors (Shift)")
        self.chk_lock_doors.setObjectName("toolToggle")
        self.chk_lock_doors.setToolTip(
            "Place locked doors when painting door brushes"
        )
        self.chk_lock_doors.stateChanged.connect(self._on_lock_doors_changed)
        toggles_layout.addWidget(self.chk_lock_doors)

        layout.addWidget(self.toggles_container)

        layout.addStretch()

    # ------------------------------------------------------------------
    # Persistence helpers
    # ------------------------------------------------------------------

    def _load_persisted_settings(self) -> None:
        """Load checkbox states from QSettings (mirrors C++ Config::SHOW_AUTOBORDER_PREVIEW / DRAW_LOCKED_DOOR)."""
        preview = self._settings.value(_KEY_PREVIEW, False, type=bool)
        lock = self._settings.value(_KEY_LOCK, False, type=bool)
        self.chk_preview_border.blockSignals(True)
        self.chk_lock_doors.blockSignals(True)
        self.chk_preview_border.setChecked(preview)
        self.chk_lock_doors.setChecked(lock)
        self.chk_preview_border.blockSignals(False)
        self.chk_lock_doors.blockSignals(False)

    def get_preview_border(self) -> bool:
        """Return current Preview AutoBorder state."""
        return self.chk_preview_border.isChecked()

    def get_lock_doors(self) -> bool:
        """Return current Lock Doors state."""
        return self.chk_lock_doors.isChecked()

    # ------------------------------------------------------------------
    # Styling
    # ------------------------------------------------------------------

    def _apply_style(self) -> None:
        tm = get_theme_manager()
        c = tm.tokens["color"]
        r = tm.tokens["radius"]

        self.setStyleSheet(
            f"""
            #header {{
                font-weight: 700;
                color: {c["text"]["disabled"]};
                font-size: 10px;
                letter-spacing: 1.5px;
            }}
            #sectionLabel {{
                color: {c["text"]["secondary"]};
                font-size: 12px;
                font-weight: 600;
            }}
            #valueLabel {{
                color: {c["brand"]["secondary"]};
                font-family: 'JetBrains Mono', 'Consolas', monospace;
                font-weight: bold;
                font-size: 13px;
            }}
            QPushButton#shapeBtn {{
                background: {c["surface"]["secondary"]};
                border: 1px solid {c["border"]["default"]};
                border-radius: {r["md"]}px;
                padding: 4px 16px;
                color: {c["text"]["secondary"]};
                font-size: 12px;
                font-weight: 600;
            }}
            QPushButton#shapeBtn:checked {{
                background: {c["brand"]["primary"]};
                color: {c["text"]["primary"]};
                border: 1px solid {c["brand"]["primary"]};
            }}
            QPushButton#shapeBtn:hover:!checked {{
                border-color: {c["brand"]["primary"]};
                background: {c["state"]["hover"]};
            }}
            #ToolSlider::groove:horizontal {{
                background: {c["surface"]["tertiary"]};
                height: 4px;
                border-radius: 2px;
            }}
            #ToolSlider::handle:horizontal {{
                background: {c["brand"]["primary"]};
                border: 2px solid {c["brand"]["secondary"]};
                width: 14px;
                height: 14px;
                margin: -6px 0;
                border-radius: 8px;
            }}
            #ToolSlider::handle:horizontal:hover {{
                background: {c["brand"]["secondary"]};
            }}
            #ToolSlider::sub-page:horizontal {{
                background: {c["brand"]["primary"]};
                border-radius: 2px;
            }}
            QCheckBox#toolToggle {{
                color: {c["text"]["secondary"]};
                font-size: 12px;
                spacing: 8px;
            }}
            QCheckBox#toolToggle::indicator {{
                width: 14px;
                height: 14px;
                border: 1px solid {c["border"]["default"]};
                border-radius: 3px;
                background: {c["surface"]["secondary"]};
            }}
            QCheckBox#toolToggle::indicator:checked {{
                background: {c["brand"]["primary"]};
                border-color: {c["brand"]["primary"]};
            }}
            QCheckBox#toolToggle:hover {{
                color: {c["text"]["primary"]};
            }}
        """
        )

    def refresh_theme(self) -> None:
        """Re-apply styling after theme switch."""
        self._apply_style()

    # ------------------------------------------------------------------
    # Brush-type visibility (C++ parity: RebuildLayout has_tools gate)
    # ------------------------------------------------------------------

    # Brush types that display the terrain tool toggles (has_tools in C++)
    _HAS_TOOLS_TYPES: frozenset[str] = frozenset({"terrain", "collection"})

    # Visibility map: (show_size, show_shape, show_var)
    _VISIBILITY_BY_PALETTE: dict[str, tuple[bool, bool, bool]] = {
        "terrain": (True, True, False),
        "collection": (True, True, True),
        "doodad": (True, True, True),
        "item": (False, False, False),
        "house": (False, False, False),
        "spawn": (True, True, False),
        "raw": (False, False, False),
    }

    def set_brush_type(self, brush_type: str) -> None:
        """Update visibility based on brush type."""
        self._current_brush_type = brush_type.lower()

        show_size, show_shape, show_var = self._VISIBILITY_BY_PALETTE.get(
            self._current_brush_type, (True, True, False)
        )
        self.size_container.setVisible(show_size)
        self.shape_container.setVisible(show_shape)
        self.var_container.setVisible(show_var)

        # Terrain toggles visible only for has_tools types (terrain, collection)
        self.toggles_container.setVisible(
            self._current_brush_type in self._HAS_TOOLS_TYPES
        )

    # ------------------------------------------------------------------
    # Signal handlers
    # ------------------------------------------------------------------

    def _on_size_changed(self, value: int) -> None:
        self.size_val_label.setText(str(value))
        self.size_changed.emit(value)

    def _on_shape_changed(self, btn: QPushButton) -> None:
        shape = "square" if btn == self.btn_square else "circle"
        self.btn_square.setIcon(_shape_icon("square", 16, shape == "square"))
        self.btn_circle.setIcon(_shape_icon("circle", 16, shape == "circle"))
        self.shape_changed.emit(shape)

    def _on_variation_changed(self, value: int) -> None:
        self.var_val_label.setText(f"{value}%")
        self.variation_changed.emit(value)

    def _on_preview_border_changed(self, state: int) -> None:
        checked = state == Qt.CheckState.Checked.value
        self._settings.setValue(_KEY_PREVIEW, checked)
        self.preview_border_changed.emit(checked)

    def _on_lock_doors_changed(self, state: int) -> None:
        checked = state == Qt.CheckState.Checked.value
        self._settings.setValue(_KEY_LOCK, checked)
        self.lock_doors_changed.emit(checked)
