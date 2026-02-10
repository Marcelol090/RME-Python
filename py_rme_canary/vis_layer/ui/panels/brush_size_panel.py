"""Brush Size Control Panel with visual preview.

Modern brush size selector with:
- Animated visual size preview with gradient fill
- Quick size buttons with hover glow
- Slider + spinbox
- Shape toggle with painted icons
"""

from __future__ import annotations

from PyQt6.QtCore import QRectF, Qt, pyqtSignal
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QRadialGradient,
)
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

    Shows a grid representing the brush footprint with gradient fills
    and a subtle glow effect on the active area.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._size = 1
        self._is_circle = False

        self.setMinimumSize(88, 88)
        self.setMaximumSize(110, 110)
        self.setStyleSheet(
            """
            BrushSizePreview {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 #1E1E2E, stop:1 #16161F);
                border: 1px solid #363650;
                border-radius: 10px;
            }
        """
        )

    def set_size(self, size: int) -> None:
        """Set brush size."""
        self._size = max(1, min(11, size))
        self.update()

    def set_circle(self, is_circle: bool) -> None:
        """Set circle or square shape."""
        self._is_circle = is_circle
        self.update()

    def paintEvent(self, event: object) -> None:
        """Paint the brush preview with gradient fill and glow."""
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

        center_x = float(start_x + total_size / 2.0)
        center_y = float(start_y + total_size / 2.0)

        # Draw subtle glow behind the active area
        glow = QRadialGradient(center_x, center_y, float(total_size * 0.8))
        glow.setColorAt(0.0, QColor(139, 92, 246, 50))
        glow.setColorAt(1.0, QColor(139, 92, 246, 0))
        painter.setBrush(QBrush(glow))
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawEllipse(
            QRectF(
                center_x - total_size * 0.8,
                center_y - total_size * 0.8,
                total_size * 1.6,
                total_size * 1.6,
            )
        )

        # Draw cells with gradient
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

                # Calculate distance from center for gradient intensity
                dist = ((col + 0.5 - center) ** 2 + (row + 0.5 - center) ** 2) ** 0.5
                max_dist = center * 1.414
                intensity = max(0.3, 1.0 - (dist / max_dist) * 0.6) if max_dist > 0 else 1.0

                # Gradient cell fill
                cell_gradient = QLinearGradient(x, y, x, y + cell_size)
                cell_gradient.setColorAt(
                    0.0, QColor(139, 92, 246, int(220 * intensity))
                )
                cell_gradient.setColorAt(
                    1.0, QColor(109, 62, 216, int(180 * intensity))
                )
                painter.setBrush(QBrush(cell_gradient))
                painter.setPen(Qt.PenStyle.NoPen)

                # Rounded cell corners for size > 1
                if cell_size > 4:
                    path = QPainterPath()
                    path.addRoundedRect(
                        QRectF(x + 0.5, y + 0.5, cell_size - 1.5, cell_size - 1.5),
                        2.0,
                        2.0,
                    )
                    painter.drawPath(path)
                else:
                    painter.drawRect(x, y, cell_size - 1, cell_size - 1)

        # Draw border
        border_color = QColor(139, 92, 246, 200)
        painter.setPen(QPen(border_color, 2.0))
        painter.setBrush(Qt.BrushStyle.NoBrush)

        if self._is_circle:
            painter.drawEllipse(start_x, start_y, total_size - 1, total_size - 1)
        else:
            path = QPainterPath()
            path.addRoundedRect(
                QRectF(start_x, start_y, total_size - 1, total_size - 1), 3.0, 3.0
            )
            painter.drawPath(path)

        painter.end()


class _ShapeButton(QPushButton):
    """Shape toggle button with custom-painted icon instead of Unicode characters."""

    def __init__(self, shape: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._shape = shape  # "square" or "circle"
        self.setFixedSize(36, 36)
        self.setCheckable(True)

    def paintEvent(self, event: object) -> None:
        super().paintEvent(event)
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Colors based on checked state
        if self.isChecked():
            pen_color = QColor(255, 255, 255, 230)
            fill_color = QColor(255, 255, 255, 40)
        else:
            pen_color = QColor(161, 161, 170, 200)
            fill_color = QColor(161, 161, 170, 20)

        painter.setPen(QPen(pen_color, 2.0))
        painter.setBrush(QBrush(fill_color))

        # Draw shape centered in button
        cx, cy = self.width() / 2.0, self.height() / 2.0
        size = 14.0

        if self._shape == "circle":
            painter.drawEllipse(QRectF(cx - size / 2, cy - size / 2, size, size))
        else:
            r = QRectF(cx - size / 2, cy - size / 2, size, size)
            painter.drawRoundedRect(r, 2.0, 2.0)

        painter.end()


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
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Header with icon
        header_row = QHBoxLayout()
        header_row.setSpacing(6)

        from py_rme_canary.vis_layer.ui.icons import icon_brush_size
        _icon = icon_brush_size(14)
        icon_label = QLabel()
        icon_label.setPixmap(_icon.pixmap(14, 14))
        icon_label.setFixedSize(16, 16)
        header_row.addWidget(icon_label)

        header = QLabel("BRUSH SIZE")
        header.setStyleSheet(
            """
            font-size: 10px;
            font-weight: 700;
            color: rgba(161, 161, 170, 0.6);
            letter-spacing: 1.5px;
        """
        )
        header_row.addWidget(header)
        header_row.addStretch()
        layout.addLayout(header_row)

        # Preview + controls
        main_row = QHBoxLayout()
        main_row.setSpacing(14)

        # Preview
        self.preview = BrushSizePreview()
        main_row.addWidget(self.preview)

        # Controls column
        controls = QVBoxLayout()
        controls.setSpacing(10)

        # Slider + spinbox row
        slider_row = QHBoxLayout()
        slider_row.setSpacing(8)

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
        self.spinbox.setFixedWidth(52)
        self.spinbox.setAlignment(Qt.AlignmentFlag.AlignCenter)
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
            btn.setFixedSize(30, 30)
            btn.setToolTip(f"Size {size}×{size}")
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

        shape_label = QLabel("Shape")
        shape_label.setStyleSheet("color: #8888A0; font-size: 11px; font-weight: 600;")
        shape_row.addWidget(shape_label)

        self.btn_square = _ShapeButton("square")
        self.btn_square.setChecked(True)
        self.btn_square.setToolTip("Square brush [Q]")
        self.btn_square.clicked.connect(lambda: self._set_shape(False))
        shape_row.addWidget(self.btn_square)

        self.btn_circle = _ShapeButton("circle")
        self.btn_circle.setToolTip("Circle brush [Q]")
        self.btn_circle.clicked.connect(lambda: self._set_shape(True))
        shape_row.addWidget(self.btn_circle)

        shape_row.addStretch()

        controls.addLayout(shape_row)

        main_row.addLayout(controls)
        layout.addLayout(main_row)

    def _apply_style(self) -> None:
        """Apply Antigravity premium styling."""
        self.setStyleSheet(
            """
            BrushSizePanel {
                background: rgba(16, 16, 24, 0.85);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 12px;
            }

            QSlider::groove:horizontal {
                background: rgba(54, 54, 80, 0.4);
                height: 4px;
                border-radius: 2px;
            }

            QSlider::handle:horizontal {
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.5,
                    fx:0.5, fy:0.3,
                    stop:0 #A78BFA, stop:1 #8B5CF6);
                width: 16px;
                height: 16px;
                margin: -6px 0;
                border-radius: 8px;
                border: 2px solid rgba(124, 58, 237, 0.7);
            }

            QSlider::handle:horizontal:hover {
                background: qradialgradient(cx:0.5, cy:0.5, radius:0.5,
                    fx:0.5, fy:0.3,
                    stop:0 #C4B5FD, stop:1 #A78BFA);
            }

            QSlider::sub-page:horizontal {
                background: qlineargradient(x1:0, y1:0, x2:1, y2:0,
                    stop:0 #7C3AED, stop:1 #8B5CF6);
                border-radius: 2px;
            }

            QSpinBox {
                background: rgba(19, 19, 29, 0.6);
                border: 1px solid rgba(255, 255, 255, 0.06);
                border-radius: 6px;
                padding: 4px;
                color: #E5E5E7;
                font-weight: 600;
                selection-background-color: rgba(139, 92, 246, 0.3);
            }

            QSpinBox:focus {
                border-color: rgba(139, 92, 246, 0.5);
                background: rgba(19, 19, 29, 0.8);
            }

            QPushButton {
                background: rgba(19, 19, 29, 0.6);
                color: rgba(161, 161, 170, 0.8);
                border: 1px solid transparent;
                border-radius: 6px;
                font-weight: 700;
                font-size: 11px;
            }

            QPushButton:hover {
                background: rgba(139, 92, 246, 0.12);
                border-color: rgba(139, 92, 246, 0.2);
                color: #E5E5E7;
            }

            QPushButton:checked {
                background: qlineargradient(x1:0, y1:0, x2:0, y2:1,
                    stop:0 rgba(139, 92, 246, 0.35), stop:1 rgba(124, 58, 237, 0.3));
                color: white;
                border: 1px solid rgba(139, 92, 246, 0.45);
            }
        """
        )

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
