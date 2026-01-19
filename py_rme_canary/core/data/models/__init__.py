"""Data model modules (new structured location).

These modules exist to match ARCHITECTURE_PROPOSAL.md while keeping backward
compatibility with the existing `py_rme_canary.core.data.*` modules.
"""

from .house import House
from .item import Item, ItemAttribute
from .position import Position
from .spawn import MonsterSpawnArea, MonsterSpawnEntry, NpcSpawnArea, NpcSpawnEntry
from .tile import Tile
from .zone import Zone

__all__ = [
    "House",
    "Item",
    "ItemAttribute",
    "MonsterSpawnArea",
    "MonsterSpawnEntry",
    "NpcSpawnArea",
    "NpcSpawnEntry",
    "Position",
    "Tile",
    "Zone",
]
