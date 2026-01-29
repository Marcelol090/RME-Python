from __future__ import annotations

from dataclasses import dataclass

from py_rme_canary.core.data.gamemap import GameMap
from py_rme_canary.core.data.item import Item
from py_rme_canary.core.data.tile import Tile


@dataclass(frozen=True, slots=True)
class RemoveItemsResult:
    removed: int


def _is_complex_item(item: Item) -> bool:
    """Best-effort approximation of legacy `Item::isComplex()`.

    Legacy reference:
    - `source/complexitem.h`: Container/Teleport/Door/Depot are specialized item
      subclasses and are considered "complex".
    - `source/map.h` `RemoveItemOnMap` explicitly skips complex items.

    The Python core model does not currently have access to item-type tables
    (items.otb) at runtime, so we conservatively treat items as "complex" when
    they carry any persisted extra structure/fields beyond a plain id.

    This preserves behavior for common complex items:
    - Container with contents (`items`)
    - Teleport (`destination`)
    - Depot/Door (`depot_id`, `house_door_id`)
    - Any item carrying extra attributes (`action_id`, `unique_id`, `text`, etc.)
    """

    if item.items:
        return True
    if item.destination is not None:
        return True
    if item.depot_id is not None:
        return True
    if item.house_door_id is not None:
        return True
    if item.attribute_map:
        return True
    if item.action_id is not None or item.unique_id is not None:
        return True
    return bool(item.text or item.description)


def remove_items_in_tile(*, tile: Tile, server_id: int) -> tuple[Tile, int]:
    """Remove non-complex items with `server_id` from a tile.

    Mirrors legacy `RemoveItemOnMap` behavior:
    - Only removes from `ground` and the top-level `items` stack.
    - Does not recurse into container contents.
    - Skips complex items.
    """

    sid = int(server_id)
    removed = 0

    ground = tile.ground
    if ground is not None and int(ground.id) == sid and not _is_complex_item(ground):
        ground = None
        removed += 1

    if not tile.items:
        if removed <= 0:
            return tile, 0
        return (
            Tile(
                x=int(tile.x),
                y=int(tile.y),
                z=int(tile.z),
                ground=ground,
                items=list(tile.items),
                house_id=tile.house_id,
                map_flags=int(tile.map_flags),
                zones=tile.zones,
                modified=True,
                monsters=tile.monsters,
                npc=tile.npc,
                spawn_monster=tile.spawn_monster,
                spawn_npc=tile.spawn_npc,
            ),
            removed,
        )

    new_items: list[Item] = []
    for it in tile.items:
        if int(it.id) == sid and not _is_complex_item(it):
            removed += 1
            continue
        new_items.append(it)

    if removed <= 0:
        return tile, 0

    return (
        Tile(
            x=int(tile.x),
            y=int(tile.y),
            z=int(tile.z),
            ground=ground,
            items=new_items,
            house_id=tile.house_id,
            map_flags=int(tile.map_flags),
            zones=tile.zones,
            modified=True,
            monsters=tile.monsters,
            npc=tile.npc,
            spawn_monster=tile.spawn_monster,
            spawn_npc=tile.spawn_npc,
        ),
        removed,
    )


def remove_items_in_map(
    game_map: GameMap,
    *,
    server_id: int,
    selection_only: bool = False,
    selection_tiles: set[tuple[int, int, int]] | None = None,
) -> tuple[dict[tuple[int, int, int], Tile], RemoveItemsResult]:
    """Compute removed tiles for a map.

    Mirrors legacy `RemoveItemOnMap(map, condition, selectedOnly)`:
    - Operates only on ground + top-level stack items.
    - Skips complex items.
    - When `selection_only=True`, only considers tiles in `selection_tiles`.

    Returns a dict of changed tiles and a summary.
    """

    if selection_only and not selection_tiles:
        return {}, RemoveItemsResult(removed=0)

    selection_set: set[tuple[int, int, int]] = set(selection_tiles) if selection_tiles is not None else set()

    sid = int(server_id)
    changed: dict[tuple[int, int, int], Tile] = {}
    removed_total = 0

    for key, tile in game_map.tiles.items():
        if selection_only and key not in selection_set:
            continue

        new_tile, removed = remove_items_in_tile(tile=tile, server_id=sid)
        if removed <= 0:
            continue

        changed[key] = new_tile
        removed_total += int(removed)

    return changed, RemoveItemsResult(removed=int(removed_total))


def remove_monsters_in_map(
    game_map: GameMap,
    *,
    selection_only: bool = False,
    selection_tiles: set[tuple[int, int, int]] | None = None,
) -> tuple[dict[tuple[int, int, int], Tile], RemoveItemsResult]:
    """Remove all monsters from the map (or selection).

    Mirrors legacy `RemoveMonstersOnMap`:
    - Clears `tile.monsters` for target tiles.
    - Preserves `tile.npc`, `tile.spawn_monster`, `tile.spawn_npc`.
    - Preserves `tile.items`.
    """
    if selection_only and not selection_tiles:
        return {}, RemoveItemsResult(removed=0)

    selection_set = set(selection_tiles) if selection_tiles is not None else set()
    changed: dict[tuple[int, int, int], Tile] = {}
    removed_total = 0

    for key, tile in game_map.tiles.items():
        if selection_only and key not in selection_set:
            continue

        if not tile.monsters:
            continue

        count = len(tile.monsters)
        removed_total += count

        # Create new tile with empty monsters list, preserving everything else
        new_tile = Tile(
            x=tile.x,
            y=tile.y,
            z=tile.z,
            ground=tile.ground,
            items=tile.items,
            house_id=tile.house_id,
            map_flags=tile.map_flags,
            zones=tile.zones,
            modified=True,
            monsters=[],  # Clear monsters
            npc=tile.npc,
            spawn_monster=tile.spawn_monster,
            spawn_npc=tile.spawn_npc,
        )
        changed[key] = new_tile

    return changed, RemoveItemsResult(removed=removed_total)


@dataclass(frozen=True, slots=True)
class ReplaceItemsResult:
    """Result of replace items operation."""

    replaced: int


def replace_items_in_tile(
    *,
    tile: Tile,
    source_id: int,
    target_id: int,
) -> tuple[Tile, int]:
    """Replace items with `source_id` to `target_id` in a tile.

    Mirrors legacy `ReplaceItemOnMap` behavior:
    - Replaces in `ground` and top-level `items` stack.
    - Does not recurse into container contents.
    - Skips complex items.
    """
    sid = int(source_id)
    tid = int(target_id)
    replaced = 0

    ground = tile.ground
    if ground is not None and int(ground.id) == sid and not _is_complex_item(ground):
        ground = Item(id=tid)
        replaced += 1

    if not tile.items:
        if replaced <= 0:
            return tile, 0
        return (
            Tile(
                x=int(tile.x),
                y=int(tile.y),
                z=int(tile.z),
                ground=ground,
                items=list(tile.items),
                house_id=tile.house_id,
                map_flags=int(tile.map_flags),
                zones=tile.zones,
                modified=True,
                monsters=tile.monsters,
                npc=tile.npc,
                spawn_monster=tile.spawn_monster,
                spawn_npc=tile.spawn_npc,
            ),
            replaced,
        )

    new_items: list[Item] = []
    for it in tile.items:
        if int(it.id) == sid and not _is_complex_item(it):
            new_items.append(Item(id=tid))
            replaced += 1
        else:
            new_items.append(it)

    if replaced <= 0:
        return tile, 0

    return (
        Tile(
            x=int(tile.x),
            y=int(tile.y),
            z=int(tile.z),
            ground=ground,
            items=new_items,
            house_id=tile.house_id,
            map_flags=int(tile.map_flags),
            zones=tile.zones,
            modified=True,
            monsters=tile.monsters,
            npc=tile.npc,
            spawn_monster=tile.spawn_monster,
            spawn_npc=tile.spawn_npc,
        ),
        replaced,
    )


def replace_items_in_map(
    game_map: GameMap,
    *,
    source_id: int,
    target_id: int,
    selection_only: bool = False,
    selection_tiles: set[tuple[int, int, int]] | None = None,
) -> tuple[dict[tuple[int, int, int], Tile], ReplaceItemsResult]:
    """Replace items on map.

    Mirrors legacy `ReplaceItemOnMap(map, sourceId, targetId, selectedOnly)`:
    - Operates on ground + top-level stack items.
    - Skips complex items.
    - When `selection_only=True`, only considers tiles in `selection_tiles`.

    Returns a dict of changed tiles and a summary.
    """
    if selection_only and not selection_tiles:
        return {}, ReplaceItemsResult(replaced=0)

    selection_set = set(selection_tiles) if selection_tiles is not None else set()
    sid = int(source_id)
    tid = int(target_id)
    changed: dict[tuple[int, int, int], Tile] = {}
    replaced_total = 0

    for key, tile in game_map.tiles.items():
        if selection_only and key not in selection_set:
            continue

        new_tile, replaced = replace_items_in_tile(
            tile=tile,
            source_id=sid,
            target_id=tid,
        )
        if replaced <= 0:
            continue

        changed[key] = new_tile
        replaced_total += int(replaced)

    return changed, ReplaceItemsResult(replaced=int(replaced_total))


def find_items_in_map(
    game_map: GameMap,
    *,
    server_id: int,
    selection_only: bool = False,
    selection_tiles: set[tuple[int, int, int]] | None = None,
) -> list[tuple[int, int, int]]:
    """Find all positions containing item with given server_id.

    Args:
        game_map: Target game map
        server_id: Item ID to search for
        selection_only: Limit to selection
        selection_tiles: Selection tile positions

    Returns:
        List of (x, y, z) tuples where item was found
    """
    if selection_only and not selection_tiles:
        return []

    selection_set = set(selection_tiles) if selection_tiles is not None else set()
    sid = int(server_id)
    results: list[tuple[int, int, int]] = []

    for key, tile in game_map.tiles.items():
        if selection_only and key not in selection_set:
            continue

        # Check ground
        if tile.ground is not None and int(tile.ground.id) == sid:
            results.append(key)
            continue

        # Check items
        for item in tile.items:
            if int(item.id) == sid:
                results.append(key)
                break

    return results
