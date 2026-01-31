"""Paste Preview Overlay.

Visual overlay showing where paste will occur.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import QPoint, QRect, Qt
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget

if TYPE_CHECKING:
    pass


class PastePreviewOverlay(QWidget):
    """Overlay showing paste preview.

    Displays a semi-transparent preview of the tiles
    that will be affected by a paste operation.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._positions: list[tuple[int, int, int]] = []
        self._origin: QPoint = QPoint(0, 0)
        self._tile_size: int = 32
        self._visible: bool = False
        self._color: QColor | None = None

        # Colors
        from py_rme_canary.vis_layer.ui.theme.colors import get_theme_color

        self._fill_color = get_theme_color("primary", 50)  # Light purple
        self._border_color = get_theme_color("primary", 180)  # Purple
        self._cut_fill_color = get_theme_color("secondary", 50)  # Light pink
        self._cut_border_color = get_theme_color("secondary", 180)  # Pink
        self._is_cut = False

        # Setup
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.hide()

    def set_preview_positions(self, positions: list[tuple[int, int, int]], is_cut: bool = False) -> None:
        """Set the tile positions to preview.

        Args:
            positions: List of (x, y, z) tile positions
            is_cut: True if this is a cut operation (different color)
        """
        self._positions = positions
        self._is_cut = is_cut
        self._color = self._cut_border_color if is_cut else self._border_color
        self.update()

    def set_origin(self, origin: QPoint) -> None:
        """Set the origin point for coordinate conversion.

        Args:
            origin: Screen position of map origin
        """
        self._origin = origin
        self.update()

    def set_tile_size(self, size: int) -> None:
        """Set the tile size in pixels.

        Args:
            size: Tile size in pixels
        """
        self._tile_size = size
        self.update()

    def set_visible(self, visible: bool) -> None:
        """Show or hide the preview."""
        self._visible = visible
        if visible:
            self.show()
        else:
            self.hide()

    def clear_preview(self) -> None:
        """Clear the preview."""
        self._positions.clear()
        self.update()

    def paintEvent(self, event: object) -> None:
        """Paint the paste preview."""
        if not self._visible or not self._positions:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Choose colors based on cut/copy
        if self._is_cut:
            fill = self._cut_fill_color
            border = self._cut_border_color
        else:
            fill = self._fill_color
            border = self._border_color

        painter.setBrush(QBrush(fill))
        painter.setPen(QPen(border, 2))

        # Draw each tile
        for x, y, _z in self._positions:
            screen_x = self._origin.x() + x * self._tile_size
            screen_y = self._origin.y() + y * self._tile_size

            rect = QRect(screen_x, screen_y, self._tile_size, self._tile_size)
            painter.drawRect(rect)

        # Draw bounding box
        if len(self._positions) > 1:
            min_x = min(p[0] for p in self._positions)
            max_x = max(p[0] for p in self._positions)
            min_y = min(p[1] for p in self._positions)
            max_y = max(p[1] for p in self._positions)

            bounding = QRect(
                self._origin.x() + min_x * self._tile_size,
                self._origin.y() + min_y * self._tile_size,
                (max_x - min_x + 1) * self._tile_size,
                (max_y - min_y + 1) * self._tile_size,
            )

            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(border, 3, Qt.PenStyle.DashLine))
            painter.drawRect(bounding)


class SelectionOverlay(QWidget):
    """Overlay showing current selection.

    Displays marching ants border around selected tiles.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)

        self._selection_rects: list[QRect] = []
        self._march_offset: int = 0
        self._rect: QRect | None = None
        self._visible: bool = False

        # Colors
        from py_rme_canary.vis_layer.ui.theme.colors import get_theme_color

        self._selection_color = get_theme_color("info", 100)  # Blue
        self._border_color = get_theme_color("info", 255)

        # Setup
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        # Marching ants timer
        from PyQt6.QtCore import QTimer

        self._march_timer = QTimer()
        self._march_timer.timeout.connect(self._update_march)
        self._march_timer.setInterval(50)
        self.hide()

    def set_rect(self, rect: QRect) -> None:
        """Set a single selection rectangle."""
        self._rect = rect
        self._selection_rects = [rect]
        if rect:
            self._march_timer.start()
            self.set_visible(True)
        else:
            self._march_timer.stop()
            self.set_visible(False)
        self.update()

    def set_visible(self, visible: bool) -> None:
        """Show or hide the overlay."""
        self._visible = visible
        if visible:
            self.show()
        else:
            self.hide()

    def set_selection(self, rects: list[QRect]) -> None:
        """Set selection rectangles in screen coordinates.

        Args:
            rects: List of QRect in screen coordinates
        """
        self._selection_rects = rects

        if rects:
            self._march_timer.start()
        else:
            self._march_timer.stop()

        self.update()

    def clear_selection(self) -> None:
        """Clear the selection."""
        self._selection_rects.clear()
        self._march_timer.stop()
        self.update()

    def _update_march(self) -> None:
        """Update marching ants animation."""
        self._march_offset = (self._march_offset + 1) % 16
        self.update()

    def paintEvent(self, event: object) -> None:
        """Paint the selection overlay."""
        if not self._selection_rects:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Fill
        painter.setBrush(QBrush(self._selection_color))
        painter.setPen(Qt.PenStyle.NoPen)

        for rect in self._selection_rects:
            painter.drawRect(rect)

        # Marching ants border
        pen = QPen(self._border_color, 2, Qt.PenStyle.CustomDashLine)
        pen.setDashPattern([4, 4])
        pen.setDashOffset(self._march_offset)
        painter.setPen(pen)
        painter.setBrush(Qt.BrushStyle.NoBrush)

        for rect in self._selection_rects:
            painter.drawRect(rect)
