"""Brush Size Control Panel with visual preview.

Modern brush size selector with:
- Visual size preview
- Quick size buttons
- Slider + spinbox
- Shape toggle
"""
from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal, QSize
from PyQt6.QtGui import QColor, QPainter, QPen
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


class BrushSizePreview(QFrame):
    """Visual preview of current brush size.

    Shows a grid representing the brush footprint.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._size = 1
        self._is_circle = False

        self.setMinimumSize(80, 80)
        self.setMaximumSize(100, 100)
        self.setStyleSheet("""
            BrushSizePreview {
                background: #1E1E2E;
                border: 1px solid #363650;
                border-radius: 8px;
            }
        """)

    def set_size(self, size: int) -> None:
        """Set brush size."""
        self._size = max(1, min(11, size))
        self.update()

    def set_circle(self, is_circle: bool) -> None:
        """Set circle or square shape."""
        self._is_circle = is_circle
        self.update()

    def paintEvent(self, event: object) -> None:
        """Paint the brush preview."""
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        w = self.width()
        h = self.height()

        # Calculate cell size
        max_cells = 11
        cell_size = min(w, h) // max_cells

        # Center the grid
        total_size = self._size * cell_size
        start_x = (w - total_size) // 2
        start_y = (h - total_size) // 2

        # Draw cells
        fill_color = QColor(139, 92, 246, 180)  # Purple
        border_color = QColor(139, 92, 246, 255)

        center = self._size / 2.0
        radius_sq = (self._size / 2.0) ** 2

        for row in range(self._size):
            for col in range(self._size):
                x = start_x + col * cell_size
                y = start_y + row * cell_size

                # Check if in circle (if circle mode)
                if self._is_circle:
                    dx = col + 0.5 - center
                    dy = row + 0.5 - center
                    if dx * dx + dy * dy > radius_sq:
                        continue

                # Draw cell
                painter.fillRect(x, y, cell_size - 1, cell_size - 1, fill_color)

        # Draw border
        painter.setPen(QPen(border_color, 2))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        if self._is_circle:
            painter.drawEllipse(
                start_x, start_y,
                total_size - 1, total_size - 1
            )
        else:
            painter.drawRect(
                start_x, start_y,
                total_size - 1, total_size - 1
            )


class BrushSizePanel(QWidget):
    """Complete brush size control panel.

    Signals:
        size_changed: Emits new brush size (1-11)
        shape_changed: Emits True for circle, False for square
    """

    size_changed = pyqtSignal(int)
    shape_changed = pyqtSignal(bool)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._current_size = 1
        self._is_circle = False

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Header
        header = QLabel("Brush Size")
        header.setStyleSheet("""
            font-size: 12px;
            font-weight: 600;
            color: #A1A1AA;
        """)
        layout.addWidget(header)

        # Preview + controls
        main_row = QHBoxLayout()
        main_row.setSpacing(12)

        # Preview
        self.preview = BrushSizePreview()
        main_row.addWidget(self.preview)

        # Controls column
        controls = QVBoxLayout()
        controls.setSpacing(8)

        # Slider + spinbox row
        slider_row = QHBoxLayout()

        self.slider = QSlider(Qt.Orientation.Horizontal)
        self.slider.setMinimum(1)
        self.slider.setMaximum(11)
        self.slider.setValue(1)
        self.slider.valueChanged.connect(self._on_slider_changed)
        slider_row.addWidget(self.slider)

        self.spinbox = QSpinBox()
        self.spinbox.setMinimum(1)
        self.spinbox.setMaximum(11)
        self.spinbox.setValue(1)
        self.spinbox.setFixedWidth(50)
        self.spinbox.valueChanged.connect(self._on_spinbox_changed)
        slider_row.addWidget(self.spinbox)

        controls.addLayout(slider_row)

        # Quick size buttons
        quick_row = QHBoxLayout()
        quick_row.setSpacing(4)

        self.size_buttons = QButtonGroup(self)
        for size in [1, 2, 3, 5, 7, 9, 11]:
            btn = QPushButton(str(size))
            btn.setCheckable(True)
            btn.setFixedSize(28, 28)
            btn.clicked.connect(lambda checked, s=size: self._set_size(s))
            self.size_buttons.addButton(btn, size)
            quick_row.addWidget(btn)

        # Select first button
        first_btn = self.size_buttons.button(1)
        if first_btn:
            first_btn.setChecked(True)

        controls.addLayout(quick_row)

        # Shape toggle
        shape_row = QHBoxLayout()
        shape_row.setSpacing(8)

        shape_label = QLabel("Shape:")
        shape_label.setStyleSheet("color: #A1A1AA; font-size: 11px;")
        shape_row.addWidget(shape_label)

        self.btn_square = QPushButton("▢")
        self.btn_square.setCheckable(True)
        self.btn_square.setChecked(True)
        self.btn_square.setFixedSize(32, 32)
        self.btn_square.setToolTip("Square [Q]")
        self.btn_square.clicked.connect(lambda: self._set_shape(False))
        shape_row.addWidget(self.btn_square)

        self.btn_circle = QPushButton("○")
        self.btn_circle.setCheckable(True)
        self.btn_circle.setFixedSize(32, 32)
        self.btn_circle.setToolTip("Circle [Q]")
        self.btn_circle.clicked.connect(lambda: self._set_shape(True))
        shape_row.addWidget(self.btn_circle)

        shape_row.addStretch()

        controls.addLayout(shape_row)

        main_row.addLayout(controls)
        layout.addLayout(main_row)

    def _apply_style(self) -> None:
        """Apply modern styling."""
        self.setStyleSheet("""
            BrushSizePanel {
                background: #2A2A3E;
                border: 1px solid #363650;
                border-radius: 8px;
            }

            QSlider::groove:horizontal {
                background: #363650;
                height: 6px;
                border-radius: 3px;
            }

            QSlider::handle:horizontal {
                background: #8B5CF6;
                width: 16px;
                height: 16px;
                margin: -5px 0;
                border-radius: 8px;
            }

            QSlider::sub-page:horizontal {
                background: #8B5CF6;
                border-radius: 3px;
            }

            QSpinBox {
                background: #1E1E2E;
                border: 1px solid #363650;
                border-radius: 4px;
                padding: 4px;
                color: #E5E5E7;
            }

            QSpinBox:focus {
                border-color: #8B5CF6;
            }

            QPushButton {
                background: #363650;
                color: #A1A1AA;
                border: 1px solid #52525B;
                border-radius: 4px;
                font-weight: 600;
            }

            QPushButton:hover {
                background: #404060;
                color: #E5E5E7;
            }

            QPushButton:checked {
                background: #8B5CF6;
                color: white;
                border-color: #8B5CF6;
            }
        """)

    def _set_size(self, size: int) -> None:
        """Set the brush size."""
        size = max(1, min(11, size))
        if size == self._current_size:
            return

        self._current_size = size

        # Update all controls
        self.slider.blockSignals(True)
        self.slider.setValue(size)
        self.slider.blockSignals(False)

        self.spinbox.blockSignals(True)
        self.spinbox.setValue(size)
        self.spinbox.blockSignals(False)

        # Update button selection
        btn = self.size_buttons.button(size)
        if btn:
            btn.setChecked(True)

        # Update preview
        self.preview.set_size(size)

        # Emit signal
        self.size_changed.emit(size)

    def _on_slider_changed(self, value: int) -> None:
        """Handle slider change."""
        self._set_size(value)

    def _on_spinbox_changed(self, value: int) -> None:
        """Handle spinbox change."""
        self._set_size(value)

    def _set_shape(self, is_circle: bool) -> None:
        """Set brush shape."""
        self._is_circle = is_circle

        self.btn_square.setChecked(not is_circle)
        self.btn_circle.setChecked(is_circle)

        self.preview.set_circle(is_circle)

        self.shape_changed.emit(is_circle)

    def get_size(self) -> int:
        """Get current brush size."""
        return self._current_size

    def is_circle(self) -> bool:
        """Get current shape."""
        return self._is_circle

    def set_size(self, size: int) -> None:
        """Set brush size externally."""
        self._set_size(size)

    def set_circle(self, is_circle: bool) -> None:
        """Set shape externally."""
        self._set_shape(is_circle)
