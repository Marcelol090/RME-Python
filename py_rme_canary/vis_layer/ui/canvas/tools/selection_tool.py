"""Selection Tool Implementation."""

from __future__ import annotations

from PyQt6.QtCore import Qt
from PyQt6.QtGui import QCursor, QMouseEvent

from py_rme_canary.vis_layer.ui.canvas.tools.abstract_tool import AbstractTool


class SelectionTool(AbstractTool):
    """Tool for selecting tiles."""

    def __init__(self, canvas, editor):
        super().__init__(canvas, editor)
        self.mouse_down = False
        self.drag_start = None

    def cursor(self):
        return QCursor(Qt.CursorShape.ArrowCursor)

    def mouse_press(self, event: QMouseEvent, tile_pos: tuple[int, int]) -> bool:
        if event.button() != Qt.MouseButton.LeftButton:
            return False

        self.mouse_down = True
        x, y = tile_pos
        z = self.editor.viewport.z

        mods = event.modifiers()
        shift = bool(mods & Qt.KeyboardModifier.ShiftModifier)
        ctrl = bool(mods & Qt.KeyboardModifier.ControlModifier)
        alt = bool(mods & Qt.KeyboardModifier.AltModifier)

        # Simplified selection logic for now
        if shift:
            self.editor.session.begin_box_selection(x=x, y=y, z=z)
        elif ctrl:
            self.editor.session.toggle_select_tile(x=x, y=y, z=z)
        else:
            self.editor.session.set_single_selection(x=x, y=y, z=z)

        self.canvas.update()
        return True

    def mouse_move(self, event: QMouseEvent, tile_pos: tuple[int, int]) -> bool:
        if not self.mouse_down:
            return False

        x, y = tile_pos
        z = self.editor.viewport.z

        # Update box selection if active
        if self.editor.session.get_selection_box() is not None:
             self.editor.session.update_box_selection(x=x, y=y, z=z)
             self.canvas.request_render()

        return True

    def mouse_release(self, event: QMouseEvent, tile_pos: tuple[int, int]) -> bool:
        if event.button() == Qt.MouseButton.LeftButton:
            self.mouse_down = False

            # Finish box selection
            if self.editor.session.get_selection_box() is not None:
                self.editor.session.finish_box_selection(
                    toggle_if_single=False, # Simplify for now
                    mode=None,
                    visible_floors=self.editor._visible_floors_for_selection()
                )

            self.canvas.request_render()
            return True
        return False
