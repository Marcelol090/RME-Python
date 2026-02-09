"""Abstract Tool Definition for Map Canvas Interaction."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

from PyQt6.QtGui import QMouseEvent, QPainter

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.canvas.widget import MapCanvasWidget
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


class AbstractTool:
    """Base class for all canvas tools."""

    def __init__(self, canvas: MapCanvasWidget, editor: QtMapEditor) -> None:
        self.canvas = canvas
        self.editor = editor
        self.active = False

    def activate(self) -> None:
        """Called when the tool becomes active."""
        self.active = True

    def deactivate(self) -> None:
        """Called when the tool becomes inactive."""
        self.active = False
        self.canvas.setCursor(self.cursor())

    def cursor(self) -> Any:
        """Return the cursor for this tool."""
        return None

    def mouse_press(self, event: QMouseEvent, tile_pos: tuple[int, int]) -> bool:
        """Handle mouse press event. Return True if handled."""
        return False

    def mouse_move(self, event: QMouseEvent, tile_pos: tuple[int, int]) -> bool:
        """Handle mouse move event. Return True if handled."""
        return False

    def mouse_release(self, event: QMouseEvent, tile_pos: tuple[int, int]) -> bool:
        """Handle mouse release event. Return True if handled."""
        return False

    def paint_overlay(self, painter: QPainter) -> None:
        """Draw tool-specific overlay."""
        pass

    def cancel(self) -> None:
        """Cancel current operation."""
        pass
