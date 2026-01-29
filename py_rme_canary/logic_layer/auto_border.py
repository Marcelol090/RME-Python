"""Compatibility wrapper for auto-border.

The architecture proposal moves the implementation to `logic_layer/borders/`.
This module keeps the legacy import path stable.
"""

from __future__ import annotations

from py_rme_canary.logic_layer.borders import *  # noqa: F403

# Legacy alias: older code imports `_replace_top_item` from this module.

# Re-export everything that borders/__init__.py exports + legacy alias.
__all__ = [name for name in globals() if not name.startswith("_") or name == "_replace_top_item"]
