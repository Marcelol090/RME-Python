"""Compatibility facade for legacy imports.

Historically, tests and UI imported OTBM saving from `py_rme_canary.core.io.otbm_saver`.
The implementation is modularized under `py_rme_canary.core.io.otbm`.

This module preserves the public API while delegating to the modular saver.
"""

from __future__ import annotations

from py_rme_canary.core.io.otbm.saver import (
    save_game_map_atomic,
    save_game_map_atomic_with_items_db,
    save_game_map_bundle_atomic,
    serialize,
)

__all__ = [
    "save_game_map_atomic",
    "save_game_map_atomic_with_items_db",
    "save_game_map_bundle_atomic",
    "serialize",
]
