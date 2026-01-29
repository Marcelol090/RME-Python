"""Selection-based operations for py_rme_canary.

Provides operations that work on selected areas of the map:
- Search items within selection
- Remove items within selection
- Count monsters/NPCs within selection
- Remove duplicate items within selection
- Find specific creatures within selection
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap
    from py_rme_canary.core.data.item import Item
    from py_rme_canary.core.data.tile import Tile

TileKey = tuple[int, int, int]


@dataclass(frozen=True, slots=True)
class SelectionSearchResult:
    """Result of searching items within selection."""

    item_id: int
    positions: list[TileKey]
    count: int


@dataclass(frozen=True, slots=True)
class MonsterCountResult:
    """Result of counting monsters within selection."""

    total_monsters: int
    total_npcs: int
    unique_monsters: dict[str, int]  # monster_name -> count
    unique_npcs: dict[str, int]  # npc_name -> count
    monster_positions: dict[str, list[TileKey]]  # monster_name -> positions
    npc_positions: dict[str, list[TileKey]]  # npc_name -> positions


@dataclass(frozen=True, slots=True)
class RemoveDuplicatesResult:
    """Result of removing duplicate items."""

    removed_count: int
    tiles_modified: int


@dataclass(frozen=True, slots=True)
class CreatureSearchResult:
    """Result of finding specific creatures."""

    creature_name: str
    creature_type: str  # "monster" or "npc"
    positions: list[TileKey]


def search_items_in_selection(
    game_map: GameMap,
    *,
    item_id: int,
    selection_tiles: set[TileKey],
) -> SelectionSearchResult:
    """Search for items within the selected area only."""
    positions: list[TileKey] = []

    for tile_key in selection_tiles:
        tile = game_map.get_tile(*tile_key)
        if tile is None:
            continue

        # Check ground
        if tile.ground and tile.ground.id == item_id:
            positions.append(tile_key)
            continue

        # Check items
        for item in tile.items:
            if item.id == item_id:
                positions.append(tile_key)
                break

    return SelectionSearchResult(
        item_id=item_id, positions=positions, count=len(positions)
    )


def count_monsters_in_selection(
    game_map: GameMap, *, selection_tiles: set[TileKey]
) -> MonsterCountResult:
    """Count monsters and NPCs within the selected area."""
    total_monsters = 0
    total_npcs = 0
    unique_monsters: dict[str, int] = {}
    unique_npcs: dict[str, int] = {}
    monster_positions: dict[str, list[TileKey]] = {}
    npc_positions: dict[str, list[TileKey]] = {}

    for tile_key in selection_tiles:
        tile = game_map.get_tile(*tile_key)
        if tile is None:
            continue

        # Count monsters on tile
        for monster in tile.monsters:
            total_monsters += 1
            name = monster.name
            unique_monsters[name] = unique_monsters.get(name, 0) + 1
            if name not in monster_positions:
                monster_positions[name] = []
            monster_positions[name].append(tile_key)

        # Count NPC on tile
        if tile.npc:
            total_npcs += 1
            name = tile.npc.name
            unique_npcs[name] = unique_npcs.get(name, 0) + 1
            if name not in npc_positions:
                npc_positions[name] = []
            npc_positions[name].append(tile_key)

    return MonsterCountResult(
        total_monsters=total_monsters,
        total_npcs=total_npcs,
        unique_monsters=unique_monsters,
        unique_npcs=unique_npcs,
        monster_positions=monster_positions,
        npc_positions=npc_positions,
    )


def remove_duplicates_in_selection(
    game_map: GameMap, *, selection_tiles: set[TileKey]
) -> tuple[dict[TileKey, Tile], RemoveDuplicatesResult]:
    """Remove duplicate items within the selected area.

    Keeps only one instance of each item ID per tile.
    """
    from py_rme_canary.core.data.tile import Tile

    changed_tiles: dict[TileKey, Tile] = {}
    removed_total = 0
    tiles_modified = 0

    for tile_key in selection_tiles:
        tile = game_map.get_tile(*tile_key)
        if tile is None or not tile.items:
            continue

        # Count item IDs
        seen_ids: set[int] = set()
        new_items: list[Item] = []

        for item in tile.items:
            if item.id not in seen_ids:
                seen_ids.add(item.id)
                new_items.append(item)
            else:
                removed_total += 1

        # Only create new tile if something was removed
        if len(new_items) < len(tile.items):
            new_tile = Tile(
                x=tile.x,
                y=tile.y,
                z=tile.z,
                ground=tile.ground,
                items=new_items,
                house_id=tile.house_id,
                map_flags=tile.map_flags,
                zones=tile.zones,
                modified=True,
                monsters=tile.monsters,
                npc=tile.npc,
                spawn_monster=tile.spawn_monster,
                spawn_npc=tile.spawn_npc,
            )
            changed_tiles[tile_key] = new_tile
            tiles_modified += 1

    return changed_tiles, RemoveDuplicatesResult(
        removed_count=removed_total, tiles_modified=tiles_modified
    )
