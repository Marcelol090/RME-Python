"""Legacy compatibility wrapper.

The map canvas implementation lives in `py_rme_canary.vis_layer.ui.canvas`.
This module preserves the historical import path:

    from py_rme_canary.vis_layer.ui.map_canvas import MapCanvasWidget
"""

from __future__ import annotations

from py_rme_canary.vis_layer.ui.canvas.widget import MapCanvasWidget

__all__ = ["MapCanvasWidget"]
