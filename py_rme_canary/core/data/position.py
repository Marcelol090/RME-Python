"""Compatibility module for `Position`.

Architecture proposal split `Position` into its own module.
For now, the canonical definition remains in `py_rme_canary.core.data.item`.
"""

from __future__ import annotations

from py_rme_canary.core.data.models.position import Position

__all__ = ["Position"]
