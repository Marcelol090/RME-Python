"""Tool Manager for managing active tools."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtCore import QObject, pyqtSignal

from py_rme_canary.vis_layer.ui.canvas.tools.brush_tool import BrushTool
from py_rme_canary.vis_layer.ui.canvas.tools.pan_tool import PanTool
from py_rme_canary.vis_layer.ui.canvas.tools.selection_tool import SelectionTool

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.canvas.tools.abstract_tool import AbstractTool
    from py_rme_canary.vis_layer.ui.canvas.widget import MapCanvasWidget
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


class ToolManager(QObject):
    """Manages active tool and delegates events."""

    tool_changed = pyqtSignal(object)  # Emits new active tool

    def __init__(self, canvas: MapCanvasWidget, editor: QtMapEditor) -> None:
        super().__init__()
        self.canvas = canvas
        self.editor = editor

        self.tools: dict[str, AbstractTool] = {
            "brush": BrushTool(canvas, editor),
            "selection": SelectionTool(canvas, editor),
            "pan": PanTool(canvas, editor),
        }

        self._active_tool: AbstractTool | None = self.tools["brush"]
        self._active_tool_name = "brush"

        if self._active_tool:
            self._active_tool.activate()

    @property
    def active_tool(self) -> AbstractTool | None:
        return self._active_tool

    def set_tool(self, name: str) -> None:
        """Switch active tool."""
        if name not in self.tools:
            return

        if self._active_tool:
            self._active_tool.deactivate()

        self._active_tool = self.tools[name]
        self._active_tool_name = name

        if self._active_tool:
            self._active_tool.activate()
            self.tool_changed.emit(self._active_tool)

    def get_tool(self, name: str) -> AbstractTool | None:
        return self.tools.get(name)
