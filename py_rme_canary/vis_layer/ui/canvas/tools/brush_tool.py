"""Brush Tool Implementation."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor, QMouseEvent

from py_rme_canary.vis_layer.ui.canvas.tools.abstract_tool import AbstractTool


class BrushTool(AbstractTool):
    """Tool for painting on the map."""

    def __init__(self, canvas, editor):
        super().__init__(canvas, editor)
        self.mouse_down = False
        self.last_pos = None

    def cursor(self):
        """Use default cross or brush cursor."""
        return QCursor(Qt.CursorShape.CrossCursor)

    def mouse_press(self, event: QMouseEvent, tile_pos: tuple[int, int]) -> bool:
        if event.button() != Qt.MouseButton.LeftButton:
            return False

        self.mouse_down = True
        self.last_pos = tile_pos
        self._paint(tile_pos, alt=bool(event.modifiers() & Qt.KeyboardModifier.AltModifier))
        return True

    def mouse_move(self, event: QMouseEvent, tile_pos: tuple[int, int]) -> bool:
        if not self.mouse_down:
            return False

        if tile_pos != self.last_pos:
            self.last_pos = tile_pos
            self._paint(tile_pos, alt=bool(event.modifiers() & Qt.KeyboardModifier.AltModifier))
        return True

    def mouse_release(self, event: QMouseEvent, tile_pos: tuple[int, int]) -> bool:
        if event.button() == Qt.MouseButton.LeftButton and self.mouse_down:
            self.mouse_down = False
            self.editor.session.mouse_up()
            return True
        return False

    def _paint(self, tile_pos: tuple[int, int], alt: bool = False):
        """Perform painting action."""
        x, y = tile_pos
        z = self.editor.viewport.z
        try:
            # Delegate to existing session logic for now
            self.editor.session.mouse_down(x=x, y=y, z=z, alt=alt)
            # Trigger footprint painting in canvas
            self.canvas._paint_footprint_at(x, y, alt=alt)
        except Exception:
            pass
