"""Legacy compatibility wrapper.

The actions history dock implementation lives in `py_rme_canary.vis_layer.ui.docks`.
This module preserves the historical import path.
"""

from __future__ import annotations

from py_rme_canary.vis_layer.ui.docks.actions_history import ActionsHistoryDock

__all__ = ["ActionsHistoryDock"]
