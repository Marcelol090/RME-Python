"""Modern Tool Options Widget — Antigravity Design.

Provides controls for brush size, shape, and variability
with glassmorphism panels and gradient accent styling.
Reference: GAP_ANALYSIS_LEGACY_UI.md
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import QRectF, QSize, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QIcon, QPainter, QPen, QPixmap
from PyQt6.QtWidgets import (
    QButtonGroup,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    pass


# ---------------------------------------------------------------------------
# Painted shape icons for consistency
# ---------------------------------------------------------------------------

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
    """Tool options panel (Size, Shape, Variation) — Antigravity style."""

    size_changed = pyqtSignal(int)
    shape_changed = pyqtSignal(str)  # "square" or "circle"
    variation_changed = pyqtSignal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._current_brush_type = "terrain"
        self._setup_ui()
        self._apply_style()

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

        # 3. Variation / Thickness (for Doodads)
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

        layout.addStretch()

    def _apply_style(self) -> None:
        self.setStyleSheet("""
            #header {
                font-weight: 700;
                color: rgba(161, 161, 170, 0.6);
                font-size: 10px;
                letter-spacing: 1.5px;
            }
            #sectionLabel {
                color: rgba(200, 200, 210, 0.8);
                font-size: 12px;
                font-weight: 600;
            }
            #valueLabel {
                color: #A78BFA;
                font-family: 'JetBrains Mono', 'Consolas', monospace;
                font-weight: bold;
                font-size: 13px;
            }
            QPushButton#shapeBtn {
                background: rgba(19, 19, 29, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 8px;
                padding: 4px 16px;
                color: rgba(200, 200, 210, 0.8);
                font-size: 12px;
                font-weight: 600;
            }
            QPushButton#shapeBtn:checked {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(139, 92, 246, 0.3), stop:1 rgba(124, 58, 237, 0.25));
                color: white;
                border: 1px solid rgba(139, 92, 246, 0.45);
            }
            QPushButton#shapeBtn:hover:!checked {
                border-color: rgba(139, 92, 246, 0.3);
                background: rgba(139, 92, 246, 0.08);
            }
            #ToolSlider::groove:horizontal {
                background: rgba(54, 54, 80, 0.4);
                height: 4px;
                border-radius: 2px;
            }
            #ToolSlider::handle:horizontal {
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.5,
                    fx:0.5, fy:0.3,
                    stop:0 #A78BFA, stop:1 #8B5CF6);
                border: 2px solid rgba(124, 58, 237, 0.7);
                width: 14px;
                height: 14px;
                margin: -6px 0;
                border-radius: 8px;
            }
            #ToolSlider::handle:horizontal:hover {
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.5,
                    fx:0.5, fy:0.3,
                    stop:0 #C4B5FD, stop:1 #A78BFA);
            }
            #ToolSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7C3AED, stop:1 #8B5CF6);
                border-radius: 2px;
            }
        """)

    def set_brush_type(self, brush_type: str) -> None:
        """Update visibility based on brush type."""
        self._current_brush_type = brush_type.lower()

        mapping = {
            "terrain": (True, True, False),
            "collection": (True, True, True),
            "doodad": (True, True, True),
            "item": (False, False, False),
            "house": (False, False, False),
            "spawn": (True, True, False),  # Radius
            "raw": (False, False, False),
        }

        show_size, show_shape, show_var = mapping.get(self._current_brush_type, (True, True, False))

        self.size_container.setVisible(show_size)
        self.shape_container.setVisible(show_shape)
        self.var_container.setVisible(show_var)

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
