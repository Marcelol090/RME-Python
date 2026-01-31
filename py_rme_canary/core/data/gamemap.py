# gamemap.py
from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field, replace
from typing import Any, TypedDict

from .houses import House
from .item import Position
from .spawns import MonsterSpawnArea, NpcSpawnArea
from .tile import Tile
from .towns import Town
from .zones import Zone


@dataclass(frozen=True, slots=True)
class MapHeader:
    """Minimal map header metadata.

    Mirrors the essential map-level fields from the C++ `Map` class:
    - width/height
    - description + external file references (spawns/houses/zones)

    `otbm_version` is carried to keep save/load decisions deterministic.
    """

    otbm_version: int
    width: int
    height: int

    description: str = ""
    spawnmonsterfile: str = ""
    spawnnpcfile: str = ""
    housefile: str = ""
    zonefile: str = ""


TileKey = tuple[int, int, int]


class LoadReport(TypedDict, total=False):
    warnings: list[Any]
    unknown_ids_count: int
    replaced_items: list[tuple[int, int, int, int]]
    metadata: dict[str, Any]
    dynamic_id_conversions: dict[str, int]


def _default_load_report() -> LoadReport:
    return {
        "warnings": [],
        "unknown_ids_count": 0,
        "replaced_items": [],
        "metadata": {},
    }


@dataclass(slots=True)
class GameMap:
    """Minimal container required for OTBM IO.

    Besides tiles and header metadata, this may also include persisted
    map-level structures that are part of the OTBM format (e.g. waypoints).

    Tiles are stored sparsely by (x, y, z).
    """

    header: MapHeader
    tiles: dict[TileKey, Tile] = field(default_factory=dict)
    # Persisted map-level structures (OTBM child nodes).
    waypoints: dict[str, Position] = field(default_factory=dict)
    towns: dict[int, Town] = field(default_factory=dict)
    # Persisted external structures (typically stored in XML referenced by header).
    monster_spawns: list[MonsterSpawnArea] = field(default_factory=list)
    npc_spawns: list[NpcSpawnArea] = field(default_factory=list)
    houses: dict[int, House] = field(default_factory=dict)
    zones: dict[int, Zone] = field(default_factory=dict)
    # Metadata injected by loaders; kept here so it works with `slots=True`.
    load_report: LoadReport = field(default_factory=_default_load_report)

    def get_tile(self, x: int, y: int, z: int) -> Tile | None:
        return self.tiles.get((int(x), int(y), int(z)))

    def set_tile(self, tile: Tile) -> None:
        self.tiles[(int(tile.x), int(tile.y), int(tile.z))] = tile

    def set_tile_at(self, x: int, y: int, z: int, tile: Tile) -> None:
        if (tile.x, tile.y, tile.z) != (x, y, z):
            tile = replace(tile, x=int(x), y=int(y), z=int(z))
        self.set_tile(tile)

    def ensure_tile(self, x: int, y: int, z: int) -> Tile:
        key = (int(x), int(y), int(z))
        tile = self.tiles.get(key)
        if tile is None:
            tile = Tile(x=key[0], y=key[1], z=key[2])
            self.tiles[key] = tile
        return tile

    def delete_tile(self, x: int, y: int, z: int) -> None:
        self.tiles.pop((int(x), int(y), int(z)), None)

    def iter_tiles(self) -> Iterator[Tile]:
        return iter(self.tiles.values())

    def iter_tile_positions(self) -> Iterable[TileKey]:
        return self.tiles.keys()

    def clear(self) -> None:
        self.tiles.clear()
