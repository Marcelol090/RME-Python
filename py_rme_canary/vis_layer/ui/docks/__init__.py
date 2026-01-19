"""Dock widgets.

This package groups dock-related widgets. Legacy wrappers remain available at:
- `py_rme_canary.vis_layer.ui.minimap`
- `py_rme_canary.vis_layer.ui.palette`
- `py_rme_canary.vis_layer.ui.actions_history`
"""

from .actions_history import ActionsHistoryDock
from .minimap import MinimapWidget
from .palette import PaletteManager

__all__ = ["ActionsHistoryDock", "MinimapWidget", "PaletteManager"]
