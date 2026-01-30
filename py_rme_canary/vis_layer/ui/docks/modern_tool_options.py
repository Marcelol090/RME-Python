"""Modern Tool Options Widget.

Provides controls for brush size, shape, and variability.
Reference: GAP_ANALYSIS_LEGACY_UI.md
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtWidgets import (
    QButtonGroup,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSlider,
    QSpinBox,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    pass


class ModernToolOptionsWidget(QWidget):
    """Tool options panel (Size, Shape, Variation)."""

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
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(12)

        # Header
        self.label = QLabel("Tool Options")
        self.label.setObjectName("header")
        layout.addWidget(self.label)

        # 1. Brush Size
        self.size_container = QWidget()
        size_layout = QVBoxLayout(self.size_container)
        size_layout.setContentsMargins(0, 0, 0, 0)
        
        size_header = QHBoxLayout()
        size_header.addWidget(QLabel("Size"))
        self.size_val_label = QLabel("1")
        self.size_val_label.setObjectName("valueLabel")
        size_header.addWidget(self.size_val_label)
        size_header.addStretch()
        size_layout.addLayout(size_header)

        self.size_slider = QSlider(Qt.Orientation.Horizontal)
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
        
        shape_layout.addWidget(QLabel("Shape"))
        
        btn_layout = QHBoxLayout()
        self.shape_group = QButtonGroup(self)
        
        self.btn_square = QPushButton("Square")
        self.btn_square.setCheckable(True)
        self.btn_square.setChecked(True)
        self.btn_square.setObjectName("shapeBtn")
        self.shape_group.addButton(self.btn_square)
        btn_layout.addWidget(self.btn_square)
        
        self.btn_circle = QPushButton("Circle")
        self.btn_circle.setCheckable(True)
        self.btn_circle.setObjectName("shapeBtn")
        self.shape_group.addButton(self.btn_circle)
        btn_layout.addWidget(self.btn_circle)
        
        shape_layout.addLayout(btn_layout)
        
        self.shape_group.buttonClicked.connect(self._on_shape_changed)
        layout.addWidget(self.shape_container)

        # 3. Variation / Thickness (for Doodads)
        self.var_container = QWidget()
        var_layout = QVBoxLayout(self.var_container)
        var_layout.setContentsMargins(0, 0, 0, 0)
        
        var_header = QHBoxLayout()
        var_header.addWidget(QLabel("Variation (Thickness)"))
        self.var_val_label = QLabel("100%")
        self.var_val_label.setObjectName("valueLabel")
        var_header.addWidget(self.var_val_label)
        var_header.addStretch()
        var_layout.addLayout(var_header)
        
        self.var_slider = QSlider(Qt.Orientation.Horizontal)
        self.var_slider.setRange(1, 100)
        self.var_slider.setValue(100)
        self.var_slider.valueChanged.connect(self._on_variation_changed)
        var_layout.addWidget(self.var_slider)
        
        layout.addWidget(self.var_container)

        layout.addStretch()

    def _apply_style(self) -> None:
        self.setStyleSheet("""
            #header {
                font-weight: 600;
                color: #A1A1AA;
                text-transform: uppercase;
                font-size: 11px;
            }
            #valueLabel {
                color: #8B5CF6;
                font-family: 'JetBrains Mono', monospace;
                font-weight: bold;
            }
            QPushButton#shapeBtn {
                background: #2A2A3E;
                border: 1px solid #363650;
                border-radius: 4px;
                padding: 4px 12px;
                color: #E5E5E7;
            }
            QPushButton#shapeBtn:checked {
                background: #8B5CF6;
                color: white;
                border: none;
            }
            QPushButton#shapeBtn:hover:!checked {
                border-color: #8B5CF6;
            }
        """)

    def set_brush_type(self, brush_type: str) -> None:
        """Update visibility based on brush type."""
        self._current_brush_type = brush_type.lower()
        
        mapping = {
            "terrain": (True, True, False),
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
        self.shape_changed.emit(shape)

    def _on_variation_changed(self, value: int) -> None:
        self.var_val_label.setText(f"{value}%")
        self.variation_changed.emit(value)
