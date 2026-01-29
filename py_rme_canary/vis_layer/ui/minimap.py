"""Legacy compatibility wrapper.

The minimap dock widget implementation lives in `py_rme_canary.vis_layer.ui.docks`.
This module preserves the historical import path:

    from py_rme_canary.vis_layer.ui.minimap import MinimapWidget
"""

from __future__ import annotations

from py_rme_canary.vis_layer.ui.docks.minimap import MinimapWidget

__all__ = ["MinimapWidget"]
