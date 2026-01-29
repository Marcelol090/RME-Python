"""Compatibility module for `MapHeader`.

Architecture proposal split `MapHeader` into its own module.
For now, the canonical definition remains in `py_rme_canary.core.data.gamemap`.
"""

from __future__ import annotations

from .gamemap import MapHeader

__all__ = ["MapHeader"]
