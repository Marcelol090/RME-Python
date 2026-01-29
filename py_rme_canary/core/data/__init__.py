"""Core data structures (GUI-agnostic).

Phase 1 focuses on `Item`, `Tile`, and `GameMap` with only the fields required
for OTBM load/save and basic map manipulation.
"""

from .gamemap import GameMap, MapHeader
from .item import Item, Position
from .tile import Tile
from .towns import Town

__all__ = [
    "GameMap",
    "Item",
    "MapHeader",
    "Position",
    "Tile",
    "Town",
]
