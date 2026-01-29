"""Legacy compatibility wrapper.

The palette dock implementation lives in `py_rme_canary.vis_layer.ui.docks`.
This module preserves the historical import path.
"""

from __future__ import annotations

from py_rme_canary.vis_layer.ui.docks.palette import PaletteManager

__all__ = ["PaletteManager"]
