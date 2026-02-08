"""Binary IO for core data structures.

Phase 3 focuses on OTBM streaming load/save.

This package provides:
- otbm/: Modular OTBM loader/saver implementation
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from .otbm import (
        LoadWarning,
        OTBMLoader,
        load_game_map,
        load_game_map_with_items_db,
        save_game_map_atomic,
        save_game_map_atomic_with_items_db,
        save_game_map_bundle_atomic,
        serialize,
    )

__all__ = [
    "LoadWarning",
    "OTBMLoader",
    "load_game_map",
    "load_game_map_with_items_db",
    "save_game_map_atomic",
    "save_game_map_atomic_with_items_db",
    "save_game_map_bundle_atomic",
    "serialize",
]


def __getattr__(name: str) -> Any:
    if name in {
        "LoadWarning",
        "OTBMLoader",
        "load_game_map",
        "load_game_map_with_items_db",
        "save_game_map_atomic",
        "save_game_map_atomic_with_items_db",
        "save_game_map_bundle_atomic",
        "serialize",
    }:
        from . import otbm as _otbm

        return getattr(_otbm, name)
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")


def __dir__() -> list[str]:
    return sorted(__all__)
