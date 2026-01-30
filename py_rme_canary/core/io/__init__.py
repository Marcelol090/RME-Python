"""Binary IO for core data structures.

Phase 3 focuses on OTBM streaming load/save.

This package provides:
- otbm/: Modular OTBM loader/saver implementation
"""

# Re-export new modular OTBM API
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
