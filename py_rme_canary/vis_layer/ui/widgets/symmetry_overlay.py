"""Symmetry overlay widget for visual axis rendering.

Draws symmetry axis lines on the map canvas with draggable handles.

Layer: vis_layer (uses PyQt6)
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import QPointF, QRectF, Qt, pyqtSignal
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget

if TYPE_CHECKING:
    from py_rme_canary.logic_layer.symmetry_manager import SymmetryManager


class SymmetryOverlay(QWidget):
    """Transparent overlay widget that draws symmetry axis lines.

    This widget should be overlaid on top of the map canvas.

    Signals:
        axis_dragged: Emitted when an axis is moved (axis_type, new_world_pos)
    """

    axis_dragged = pyqtSignal(str, int)  # "vertical" or "horizontal", new position

    # Colors
    LINE_COLOR = QColor(0, 150, 255, 200)  # Blue with alpha
    HANDLE_COLOR = QColor(255, 255, 255, 230)  # White
    HANDLE_BORDER_COLOR = QColor(0, 150, 255, 255)

    # Sizes
    HANDLE_SIZE = 10
    LINE_WIDTH = 2
    DASH_PATTERN = [8, 4]  # 8px solid, 4px gap

    def __init__(
        self,
        parent: QWidget | None = None,
        symmetry_manager: SymmetryManager | None = None,
    ) -> None:
        super().__init__(parent)
        self._symmetry_manager = symmetry_manager

        # Camera/viewport conversion (set by parent)
        self._tile_size: int = 32
        self._camera_x: int = 0
        self._camera_y: int = 0

        # Drag state
        self._dragging_axis: str | None = None
        self._drag_start_pos: QPointF | None = None

        # Make transparent and pass mouse events
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground, True)
        self.setMouseTracking(True)

    def set_symmetry_manager(self, manager: SymmetryManager) -> None:
        """Set the symmetry manager to observe."""
        self._symmetry_manager = manager
        manager.add_state_listener(self._on_state_changed)
        self.update()

    def set_camera(self, x: int, y: int, tile_size: int) -> None:
        """Update camera position for coordinate conversion."""
        self._camera_x = int(x)
        self._camera_y = int(y)
        self._tile_size = max(1, int(tile_size))
        self.update()

    def world_to_screen_x(self, world_x: int) -> float:
        """Convert world X to screen X."""
        return float((world_x - self._camera_x) * self._tile_size)

    def world_to_screen_y(self, world_y: int) -> float:
        """Convert world Y to screen Y."""
        return float((world_y - self._camera_y) * self._tile_size)

    def screen_to_world_x(self, screen_x: float) -> int:
        """Convert screen X to world X."""
        return int(self._camera_x + screen_x / self._tile_size)

    def screen_to_world_y(self, screen_y: float) -> int:
        """Convert screen Y to world Y."""
        return int(self._camera_y + screen_y / self._tile_size)

    def paintEvent(self, event: Any) -> None:
        """Draw symmetry axis lines."""
        if self._symmetry_manager is None:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Set up dashed pen
        pen = QPen(self.LINE_COLOR)
        pen.setWidth(self.LINE_WIDTH)
        pen.setDashPattern(self.DASH_PATTERN)

        if self._symmetry_manager.vertical_enabled:
            self._draw_vertical_axis(painter, pen)

        if self._symmetry_manager.horizontal_enabled:
            self._draw_horizontal_axis(painter, pen)

        painter.end()

    def _draw_vertical_axis(self, painter: QPainter, pen: QPen) -> None:
        """Draw vertical symmetry axis."""
        if self._symmetry_manager is None:
            return

        screen_x = self.world_to_screen_x(self._symmetry_manager.center_x)
        height = float(self.height())

        # Draw line
        painter.setPen(pen)
        painter.drawLine(QPointF(screen_x, 0), QPointF(screen_x, height))

        # Draw handle at top
        handle_rect = QRectF(
            screen_x - self.HANDLE_SIZE / 2,
            10,
            self.HANDLE_SIZE,
            self.HANDLE_SIZE,
        )
        painter.setPen(QPen(self.HANDLE_BORDER_COLOR, 2))
        painter.setBrush(QBrush(self.HANDLE_COLOR))
        painter.drawRect(handle_rect)

    def _draw_horizontal_axis(self, painter: QPainter, pen: QPen) -> None:
        """Draw horizontal symmetry axis."""
        if self._symmetry_manager is None:
            return

        screen_y = self.world_to_screen_y(self._symmetry_manager.center_y)
        width = float(self.width())

        # Draw line
        painter.setPen(pen)
        painter.drawLine(QPointF(0, screen_y), QPointF(width, screen_y))

        # Draw handle at left
        handle_rect = QRectF(
            10,
            screen_y - self.HANDLE_SIZE / 2,
            self.HANDLE_SIZE,
            self.HANDLE_SIZE,
        )
        painter.setPen(QPen(self.HANDLE_BORDER_COLOR, 2))
        painter.setBrush(QBrush(self.HANDLE_COLOR))
        painter.drawRect(handle_rect)

    def mousePressEvent(self, event: Any) -> None:
        """Check if user clicked on a handle."""
        if self._symmetry_manager is None:
            event.ignore()
            return

        pos = event.position()
        mx, my = pos.x(), pos.y()

        # Check vertical handle
        if self._symmetry_manager.vertical_enabled:
            screen_x = self.world_to_screen_x(self._symmetry_manager.center_x)
            if abs(mx - screen_x) < self.HANDLE_SIZE and 10 <= my <= 10 + self.HANDLE_SIZE:
                self._dragging_axis = "vertical"
                self._drag_start_pos = pos
                self.setCursor(Qt.CursorShape.SizeHorCursor)
                event.accept()
                return

        # Check horizontal handle
        if self._symmetry_manager.horizontal_enabled:
            screen_y = self.world_to_screen_y(self._symmetry_manager.center_y)
            if abs(my - screen_y) < self.HANDLE_SIZE and 10 <= mx <= 10 + self.HANDLE_SIZE:
                self._dragging_axis = "horizontal"
                self._drag_start_pos = pos
                self.setCursor(Qt.CursorShape.SizeVerCursor)
                event.accept()
                return

        event.ignore()

    def mouseMoveEvent(self, event: Any) -> None:
        """Handle axis dragging."""
        if self._symmetry_manager is None:
            event.ignore()
            return

        pos = event.position()
        mx, my = pos.x(), pos.y()

        if self._dragging_axis == "vertical":
            new_world_x = self.screen_to_world_x(mx)
            self._symmetry_manager.center_x = new_world_x
            self.axis_dragged.emit("vertical", new_world_x)
            self.update()
            event.accept()
            return

        if self._dragging_axis == "horizontal":
            new_world_y = self.screen_to_world_y(my)
            self._symmetry_manager.center_y = new_world_y
            self.axis_dragged.emit("horizontal", new_world_y)
            self.update()
            event.accept()
            return

        # Update cursor when hovering handles
        if self._symmetry_manager.vertical_enabled:
            screen_x = self.world_to_screen_x(self._symmetry_manager.center_x)
            if abs(mx - screen_x) < self.HANDLE_SIZE and 10 <= my <= 10 + self.HANDLE_SIZE:
                self.setCursor(Qt.CursorShape.SizeHorCursor)
                return

        if self._symmetry_manager.horizontal_enabled:
            screen_y = self.world_to_screen_y(self._symmetry_manager.center_y)
            if abs(my - screen_y) < self.HANDLE_SIZE and 10 <= mx <= 10 + self.HANDLE_SIZE:
                self.setCursor(Qt.CursorShape.SizeVerCursor)
                return

        self.setCursor(Qt.CursorShape.ArrowCursor)
        event.ignore()

    def mouseReleaseEvent(self, event: Any) -> None:
        """End axis dragging."""
        if self._dragging_axis:
            self._dragging_axis = None
            self._drag_start_pos = None
            self.setCursor(Qt.CursorShape.ArrowCursor)
            event.accept()
            return
        event.ignore()

    def _on_state_changed(self) -> None:
        """Called when symmetry manager state changes."""
        self.update()
