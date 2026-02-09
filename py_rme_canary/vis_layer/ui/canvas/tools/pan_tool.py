"""Pan Tool Implementation."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor, QMouseEvent

from py_rme_canary.vis_layer.ui.canvas.tools.abstract_tool import AbstractTool


class PanTool(AbstractTool):
    """Tool for panning the canvas."""

    def __init__(self, canvas, editor):
        super().__init__(canvas, editor)
        self.mouse_down = False
        self.pan_anchor = None

    def cursor(self):
        return QCursor(Qt.CursorShape.OpenHandCursor)

    def mouse_press(self, event: QMouseEvent, tile_pos: tuple[int, int]) -> bool:
        if event.button() == Qt.MouseButton.MiddleButton or event.button() == Qt.MouseButton.LeftButton:
            self.mouse_down = True
            self.pan_anchor = (event.position().toPoint(), self.editor.viewport.origin_x, self.editor.viewport.origin_y)
            self.canvas.setCursor(QCursor(Qt.CursorShape.ClosedHandCursor))
            return True
        return False

    def mouse_move(self, event: QMouseEvent, tile_pos: tuple[int, int]) -> bool:
        if not self.mouse_down or self.pan_anchor is None:
            return False

        anchor_pt, ox, oy = self.pan_anchor
        cur = event.position().toPoint()
        dx_px = int(cur.x() - anchor_pt.x())
        dy_px = int(cur.y() - anchor_pt.y())
        dx_tiles = -dx_px // self.editor.viewport.tile_px
        dy_tiles = -dy_px // self.editor.viewport.tile_px
        self.editor.viewport.origin_x = max(0, int(ox + dx_tiles))
        self.editor.viewport.origin_y = max(0, int(oy + dy_tiles))
        self.canvas.request_render()
        return True

    def mouse_release(self, event: QMouseEvent, tile_pos: tuple[int, int]) -> bool:
        if event.button() == Qt.MouseButton.MiddleButton or event.button() == Qt.MouseButton.LeftButton:
            self.mouse_down = False
            self.pan_anchor = None
            self.canvas.setCursor(self.cursor())
            return True
        return False
