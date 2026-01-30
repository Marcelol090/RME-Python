"""Brush cursor overlay with animations.

Provides visual feedback for brush position, size, and shape
with smooth animations and modern design.
"""
from __future__ import annotations

import math
from typing import TYPE_CHECKING

from PyQt6.QtCore import (
    QEasingCurve,
    QPoint,
    QPointF,
    QPropertyAnimation,
    QRect,
    QRectF,
    Qt,
    QTimer,
    pyqtProperty,
)
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget

if TYPE_CHECKING:
    pass


class BrushCursorOverlay(QWidget):
    """Animated brush cursor overlay.

    Features:
    - Pulsing outline ring
    - Size indicator with smooth scaling
    - Shape morphing (square/circle)
    - Semi-transparent fill preview
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        # State
        self._center = QPoint(0, 0)
        self._radius = 16  # Pixels
        self._tile_size = 32  # Pixels per tile
        self._brush_size = 1  # In tiles
        self._is_circle = False
        self._pulse_phase = 0.0
        self._visible = False

        # Colors
        self._primary_color = QColor(139, 92, 246, 180)  # Purple
        self._secondary_color = QColor(139, 92, 246, 60)  # Lighter purple
        self._preview_color = QColor(139, 92, 246, 40)  # Fill preview

        # Setup
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint)

        # Animation timer for pulse
        self._pulse_timer = QTimer()
        self._pulse_timer.timeout.connect(self._update_pulse)
        self._pulse_timer.setInterval(16)  # ~60 FPS

        # Size animation
        self._size_anim = QPropertyAnimation(self, b"animRadius")
        self._size_anim.setDuration(200)
        self._size_anim.setEasingCurve(QEasingCurve.Type.OutCubic)

        # Shape morph animation
        self._shape_progress = 0.0  # 0 = square, 1 = circle
        self._shape_anim = QPropertyAnimation(self, b"shapeProgress")
        self._shape_anim.setDuration(150)
        self._shape_anim.setEasingCurve(QEasingCurve.Type.InOutQuad)

    @pyqtProperty(float)
    def animRadius(self) -> float:
        return float(self._radius)

    @animRadius.setter
    def animRadius(self, value: float) -> None:
        self._radius = int(value)
        self.update()

    @pyqtProperty(float)
    def shapeProgress(self) -> float:
        return self._shape_progress

    @shapeProgress.setter
    def shapeProgress(self, value: float) -> None:
        self._shape_progress = value
        self.update()

    def set_visible(self, visible: bool) -> None:
        """Show or hide the cursor overlay."""
        self._visible = visible
        if visible:
            self.show()
            self._pulse_timer.start()
        else:
            self.hide()
            self._pulse_timer.stop()

    def set_position(self, center: QPoint) -> None:
        """Set the cursor center position."""
        self._center = center
        self._update_geometry()
        self.update()

    def set_brush_size(self, size: int) -> None:
        """Set the brush size in tiles (with animation)."""
        self._brush_size = size
        new_radius = size * self._tile_size // 2

        self._size_anim.stop()
        self._size_anim.setStartValue(float(self._radius))
        self._size_anim.setEndValue(float(new_radius))
        self._size_anim.start()

    def set_circle_shape(self, is_circle: bool) -> None:
        """Set brush shape with morph animation."""
        self._is_circle = is_circle

        self._shape_anim.stop()
        self._shape_anim.setStartValue(self._shape_progress)
        self._shape_anim.setEndValue(1.0 if is_circle else 0.0)
        self._shape_anim.start()

    def set_tile_size(self, size: int) -> None:
        """Set the tile size in pixels."""
        self._tile_size = size
        self._radius = self._brush_size * size // 2
        self.update()

    def _update_pulse(self) -> None:
        """Update pulse animation phase."""
        self._pulse_phase += 0.05
        if self._pulse_phase > 2 * math.pi:
            self._pulse_phase -= 2 * math.pi
        self.update()

    def _update_geometry(self) -> None:
        """Update widget geometry based on center and radius."""
        margin = 50  # Extra margin for glow effects
        size = self._radius * 2 + margin * 2
        self.setGeometry(
            self._center.x() - size // 2,
            self._center.y() - size // 2,
            size,
            size
        )

    def paintEvent(self, event: object) -> None:
        """Paint the brush cursor overlay."""
        if not self._visible:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        center = QPointF(self.width() / 2, self.height() / 2)
        radius = float(self._radius)

        # Calculate pulse opacity
        pulse_opacity = 0.6 + 0.4 * math.sin(self._pulse_phase)

        # Draw fill preview
        fill_color = QColor(self._preview_color)
        fill_color.setAlphaF(fill_color.alphaF() * pulse_opacity)
        painter.setBrush(QBrush(fill_color))
        painter.setPen(Qt.PenStyle.NoPen)

        self._draw_shape(painter, center, radius)

        # Draw outer ring
        ring_color = QColor(self._primary_color)
        ring_color.setAlphaF(ring_color.alphaF() * pulse_opacity)

        pen = QPen(ring_color)
        pen.setWidth(2)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        self._draw_shape(painter, center, radius)

        # Draw inner dashed ring (rotating)
        dash_color = QColor(self._secondary_color)
        dash_pen = QPen(dash_color)
        dash_pen.setWidth(1)
        dash_pen.setStyle(Qt.PenStyle.DashLine)
        dash_pen.setDashOffset(self._pulse_phase * 10)  # Rotating dashes
        painter.setPen(dash_pen)

        self._draw_shape(painter, center, radius - 4)

        # Draw center crosshair
        crosshair_size = 8
        center_color = QColor(self._primary_color)
        center_color.setAlpha(200)
        painter.setPen(QPen(center_color, 2))

        painter.drawLine(
            QPointF(center.x() - crosshair_size, center.y()),
            QPointF(center.x() + crosshair_size, center.y())
        )
        painter.drawLine(
            QPointF(center.x(), center.y() - crosshair_size),
            QPointF(center.x(), center.y() + crosshair_size)
        )

        # Draw size text
        if self._brush_size > 1:
            painter.setPen(QPen(QColor(229, 229, 231), 1))
            font = painter.font()
            font.setPixelSize(10)
            font.setBold(True)
            painter.setFont(font)

            text = f"{self._brush_size}x{self._brush_size}"
            text_rect = QRectF(
                center.x() - 20,
                center.y() + radius + 5,
                40,
                15
            )
            painter.drawText(text_rect, Qt.AlignmentFlag.AlignCenter, text)

    def _draw_shape(
        self,
        painter: QPainter,
        center: QPointF,
        radius: float
    ) -> None:
        """Draw shape based on morph progress (square to circle)."""
        # Interpolate corner radius between 0 (square) and radius (circle)
        corner_radius = radius * self._shape_progress

        rect = QRectF(
            center.x() - radius,
            center.y() - radius,
            radius * 2,
            radius * 2
        )

        if corner_radius >= radius - 1:
            # Full circle
            painter.drawEllipse(rect)
        elif corner_radius <= 1:
            # Full square
            painter.drawRect(rect)
        else:
            # Rounded rectangle (morphing)
            painter.drawRoundedRect(rect, corner_radius, corner_radius)


class BrushPreviewOverlay(QWidget):
    """Preview overlay showing what will be painted.

    Shows a semi-transparent preview of the brush effect
    before the user clicks to paint.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._tiles: list[QRect] = []  # Tiles to preview
        self._preview_color = QColor(139, 92, 246, 60)
        self._border_color = QColor(139, 92, 246, 120)

        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

    def set_preview_tiles(self, tiles: list[QRect]) -> None:
        """Set tiles to show in preview."""
        self._tiles = tiles
        self.update()

    def clear_preview(self) -> None:
        """Clear the preview."""
        self._tiles.clear()
        self.update()

    def paintEvent(self, event: object) -> None:
        """Paint preview tiles."""
        if not self._tiles:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Fill
        painter.setBrush(QBrush(self._preview_color))
        painter.setPen(QPen(self._border_color, 1))

        for rect in self._tiles:
            painter.drawRect(rect)
