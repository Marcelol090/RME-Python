"""Drag Shadow Overlay.

Visual feedback when dragging tile selections.
Shows a semi-transparent preview of where selection will be moved.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import QPoint, QRect, Qt
from PyQt6.QtGui import QBrush, QColor, QPainter, QPen
from PyQt6.QtWidgets import QWidget

if TYPE_CHECKING:
    pass


class DragShadowOverlay(QWidget):
    """Overlay showing drag preview for selections.

    Displays semi-transparent shadow showing where the dragged
    selection will land when the mouse button is released.

    Features:
    - Distinct visual from paste preview (different color)
    - Shows original positions with reduced opacity
    - Shows target positions with full preview
    - Handles multi-tile selections

    Example:
        >>> overlay = DragShadowOverlay(parent_canvas)
        >>> overlay.start_drag([(10, 10, 7), (11, 10, 7)])
        >>> overlay.update_drag_offset(5, 3)  # +5x, +3y
        >>> overlay.end_drag()
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        """Initialize drag shadow overlay.

        Args:
            parent: Parent widget (usually the map canvas)
        """
        super().__init__(parent)

        # Drag state
        self._is_dragging: bool = False
        self._original_positions: list[tuple[int, int, int]] = []
        self._drag_offset_x: int = 0
        self._drag_offset_y: int = 0

        # Visual settings
        self._origin: QPoint = QPoint(0, 0)
        self._tile_size: int = 32

        # Colors
        self._source_fill = QColor(100, 100, 100, 30)  # Gray, very faint
        self._source_border = QColor(100, 100, 100, 80)  # Gray border
        self._target_fill = QColor(59, 130, 246, 60)  # Blue fill
        self._target_border = QColor(59, 130, 246, 200)  # Blue border

        # Setup
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.hide()

    def start_drag(self, positions: list[tuple[int, int, int]]) -> None:
        """Start dragging selection.

        Args:
            positions: Original (x, y, z) tile positions being dragged
        """
        self._is_dragging = True
        self._original_positions = positions
        self._drag_offset_x = 0
        self._drag_offset_y = 0
        self.show()
        self.update()

    def update_drag_offset(self, offset_x: int, offset_y: int) -> None:
        """Update drag offset.

        Args:
            offset_x: Horizontal tile offset from original position
            offset_y: Vertical tile offset from original position
        """
        if not self._is_dragging:
            return

        self._drag_offset_x = offset_x
        self._drag_offset_y = offset_y
        self.update()

    def end_drag(self) -> None:
        """End dragging and hide overlay."""
        self._is_dragging = False
        self._original_positions.clear()
        self._drag_offset_x = 0
        self._drag_offset_y = 0
        self.hide()

    def set_origin(self, origin: QPoint) -> None:
        """Set the map origin for coordinate conversion.

        Args:
            origin: Screen position of map origin (world 0,0)
        """
        self._origin = origin
        if self._is_dragging:
            self.update()

    def set_tile_size(self, size: int) -> None:
        """Set tile render size.

        Args:
            size: Tile size in pixels (typically 32)
        """
        self._tile_size = size
        if self._is_dragging:
            self.update()

    def is_dragging(self) -> bool:
        """Check if currently dragging."""
        return self._is_dragging

    def paintEvent(self, event: object) -> None:
        """Paint drag shadow."""
        if not self._is_dragging or not self._original_positions:
            return

        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        # Draw original positions (faint gray)
        painter.setBrush(QBrush(self._source_fill))
        painter.setPen(QPen(self._source_border, 1, Qt.PenStyle.DotLine))

        for x, y, _z in self._original_positions:
            screen_x = self._origin.x() + x * self._tile_size
            screen_y = self._origin.y() + y * self._tile_size

            rect = QRect(screen_x, screen_y, self._tile_size, self._tile_size)
            painter.drawRect(rect)

        # Draw target positions (blue preview)
        target_positions = [
            (x + self._drag_offset_x, y + self._drag_offset_y, z) for x, y, z in self._original_positions
        ]

        painter.setBrush(QBrush(self._target_fill))
        painter.setPen(QPen(self._target_border, 2))

        for x, y, _z in target_positions:
            screen_x = self._origin.x() + x * self._tile_size
            screen_y = self._origin.y() + y * self._tile_size

            rect = QRect(screen_x, screen_y, self._tile_size, self._tile_size)
            painter.drawRect(rect)

        # Draw bounding box for target area
        if len(target_positions) > 1:
            min_x = min(p[0] for p in target_positions)
            max_x = max(p[0] for p in target_positions)
            min_y = min(p[1] for p in target_positions)
            max_y = max(p[1] for p in target_positions)

            bounding = QRect(
                self._origin.x() + min_x * self._tile_size,
                self._origin.y() + min_y * self._tile_size,
                (max_x - min_x + 1) * self._tile_size,
                (max_y - min_y + 1) * self._tile_size,
            )

            painter.setBrush(Qt.BrushStyle.NoBrush)
            painter.setPen(QPen(self._target_border, 3, Qt.PenStyle.DashLine))
            painter.drawRect(bounding)
