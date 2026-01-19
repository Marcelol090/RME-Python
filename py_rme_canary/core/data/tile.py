"""Core data model: tiles.

This module ports the persisted parts of the legacy C++ `Tile` model
(`source/tile.h`) required for strict OTBM I/O.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from .creature import Monster, Npc
from .item import Item
from .spawns import MonsterSpawnArea, NpcSpawnArea


@dataclass(frozen=True, slots=True)
class Tile:
    """A single map tile with ground + stacked items.

    Stack order:
    - `ground` is separate.
    - `items` is bottom -> top (borders are typically inserted at the bottom).
    """

    x: int
    y: int
    z: int

    ground: Item | None = None
    items: list[Item] = field(default_factory=list)

    # OTBM tile metadata
    house_id: int | None = None
    map_flags: int = 0

    # Runtime-only: whether this tile has been modified since load.
    # Not persisted in OTBM.
    modified: bool = False

    # Optional zone markers (not currently written into OTBM nodes).
    zones: frozenset[int] = frozenset()

    # Creatures (Legacy Parity)
    monsters: list[Monster] = field(default_factory=list)
    npc: Npc | None = None

    # Spawn Markers (Legacy Parity - center points)
    spawn_monster: MonsterSpawnArea | None = None
    spawn_npc: NpcSpawnArea | None = None

    def all_items(self) -> list[Item]:
        if self.ground is None:
            return list(self.items)
        return [self.ground, *self.items]

    def add_item(self, item: Item) -> Tile:
        """Append an item to the top of the stack (most common behavior)."""

        return self.add_item_top(item)

    def add_item_top(self, item: Item) -> Tile:
        """Add `item` to the top of the current stack."""

        new_items = list(self.items)
        new_items.append(item)
        return Tile(
            x=self.x,
            y=self.y,
            z=self.z,
            ground=self.ground,
            items=new_items,
            house_id=self.house_id,
            map_flags=self.map_flags,
            zones=self.zones,
            modified=self.modified,
            monsters=list(self.monsters),
            npc=self.npc,
            spawn_monster=self.spawn_monster,
            spawn_npc=self.spawn_npc,
        )

    def add_item_bottom(self, item: Item) -> Tile:
        """Insert `item` at the bottom of the stack (below other non-ground items)."""

        new_items = list(self.items)
        new_items.insert(0, item)
        return Tile(
            x=self.x,
            y=self.y,
            z=self.z,
            ground=self.ground,
            items=new_items,
            house_id=self.house_id,
            map_flags=self.map_flags,
            zones=self.zones,
            modified=self.modified,
            monsters=list(self.monsters),
            npc=self.npc,
            spawn_monster=self.spawn_monster,
            spawn_npc=self.spawn_npc,
        )

    def add_border_item(self, item: Item) -> Tile:
        """Legacy-compatible helper: borders are inserted at the bottom of `items`."""

        return self.add_item_bottom(item)

    def with_ground(self, ground: Item | None) -> Tile:
        return Tile(
            x=self.x,
            y=self.y,
            z=self.z,
            ground=ground,
            items=list(self.items),
            house_id=self.house_id,
            map_flags=self.map_flags,
            zones=self.zones,
            modified=self.modified,
            monsters=list(self.monsters),
            npc=self.npc,
            spawn_monster=self.spawn_monster,
            spawn_npc=self.spawn_npc,
        )

    def with_zones(self, zones: frozenset[int]) -> Tile:
        """Return a copy with updated `zones`."""

        return Tile(
            x=self.x,
            y=self.y,
            z=self.z,
            ground=self.ground,
            items=list(self.items),
            house_id=self.house_id,
            map_flags=self.map_flags,
            zones=frozenset(int(z) for z in zones if int(z) != 0),
            modified=self.modified,
            monsters=list(self.monsters),
            npc=self.npc,
            spawn_monster=self.spawn_monster,
            spawn_npc=self.spawn_npc,
        )
