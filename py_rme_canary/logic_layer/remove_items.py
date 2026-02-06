from __future__ import annotations

from collections.abc import Callable, Mapping
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from py_rme_canary.core.data.gamemap import GameMap
from py_rme_canary.core.data.houses import House
from py_rme_canary.core.data.item import Item
from py_rme_canary.core.data.tile import Tile

if TYPE_CHECKING:
    from py_rme_canary.core.database.items_xml import ItemType
else:
    ItemType = Any


@dataclass(frozen=True, slots=True)
class RemoveItemsResult:
    removed: int


@dataclass(frozen=True, slots=True)
class ClearInvalidHousesResult:
    houses_removed: int
    tile_refs_cleared: int


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


def _clone_tile_with_items(*, tile: Tile, ground: Item | None, items: list[Item]) -> Tile:
    return Tile(
        x=int(tile.x),
        y=int(tile.y),
        z=int(tile.z),
        ground=ground,
        items=items,
        house_id=tile.house_id,
        map_flags=int(tile.map_flags),
        zones=tile.zones,
        modified=True,
        monsters=tile.monsters,
        npc=tile.npc,
        spawn_monster=tile.spawn_monster,
        spawn_npc=tile.spawn_npc,
    )


def _remove_matching_items_in_tile(*, tile: Tile, predicate: Callable[[Item], bool]) -> tuple[Tile, int]:
    removed = 0
    ground = tile.ground
    if ground is not None and predicate(ground):
        ground = None
        removed += 1

    new_items: list[Item] = []
    for it in tile.items:
        if predicate(it):
            removed += 1
            continue
        new_items.append(it)

    if removed <= 0:
        return tile, 0

    return _clone_tile_with_items(tile=tile, ground=ground, items=new_items), int(removed)


def _item_attr(item_type: ItemType | None, *keys: str) -> str:
    if item_type is None:
        return ""
    attrs = item_type.attributes or {}
    if not attrs:
        return ""
    lowered = {str(k).strip().lower(): str(v).strip() for k, v in attrs.items()}
    for key in keys:
        val = lowered.get(str(key).strip().lower(), "")
        if val:
            return val
    return ""


def _is_truthy_attr(raw: str) -> bool:
    return str(raw).strip().lower() in {"1", "true", "yes", "y", "on"}


def _is_corpse_item(item: Item, *, item_types: Mapping[int, ItemType] | None) -> bool:
    if _is_complex_item(item):
        return False
    if item_types is None:
        return False
    item_type = item_types.get(int(item.id))
    return bool(_item_attr(item_type, "corpseType", "corpse_type", "corpse"))


def _is_blocking_item(item: Item, *, item_types: Mapping[int, ItemType] | None) -> bool:
    if item_types is None:
        return False
    item_type = item_types.get(int(item.id))
    if item_type is None:
        return False
    return _is_truthy_attr(
        _item_attr(
            item_type,
            "blockSolid",
            "blocksolid",
            "blocking",
            "blockPathFind",
            "blockpathfind",
        )
    )


def _is_non_blocking_tile(tile: Tile, *, item_types: Mapping[int, ItemType] | None) -> bool:
    if tile.ground is not None and _is_blocking_item(tile.ground, item_types=item_types):
        return False
    for item in tile.items:
        if _is_blocking_item(item, item_types=item_types):
            return False
    return True


def _has_any_non_blocking_tile_in_area(
    *,
    non_blocking_tiles: set[tuple[int, int, int]],
    sx: int,
    ex: int,
    sy: int,
    ey: int,
    sz: int,
    ez: int,
) -> bool:
    for z in range(int(sz), int(ez) + 1):
        for y in range(int(sy), int(ey) + 1):
            for x in range(int(sx), int(ex) + 1):
                if (int(x), int(y), int(z)) in non_blocking_tiles:
                    return True
    return False


def remove_items_in_tile(*, tile: Tile, server_id: int) -> tuple[Tile, int]:
    """Remove non-complex items with `server_id` from a tile.

    Mirrors legacy `RemoveItemOnMap` behavior:
    - Only removes from `ground` and the top-level `items` stack.
    - Does not recurse into container contents.
    - Skips complex items.
    """

    sid = int(server_id)
    return _remove_matching_items_in_tile(
        tile=tile,
        predicate=lambda it: int(it.id) == sid and not _is_complex_item(it),
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


def remove_corpses_in_map(
    game_map: GameMap,
    *,
    item_types: Mapping[int, ItemType] | None = None,
    selection_only: bool = False,
    selection_tiles: set[tuple[int, int, int]] | None = None,
) -> tuple[dict[tuple[int, int, int], Tile], RemoveItemsResult]:
    """Remove corpse items from map (or selection), skipping complex items."""
    if selection_only and not selection_tiles:
        return {}, RemoveItemsResult(removed=0)

    selection_set = set(selection_tiles) if selection_tiles is not None else set()
    changed: dict[tuple[int, int, int], Tile] = {}
    removed_total = 0

    for key, tile in game_map.tiles.items():
        if selection_only and key not in selection_set:
            continue
        new_tile, removed = _remove_matching_items_in_tile(
            tile=tile,
            predicate=lambda it: _is_corpse_item(it, item_types=item_types),
        )
        if removed <= 0:
            continue
        changed[key] = new_tile
        removed_total += int(removed)

    return changed, RemoveItemsResult(removed=int(removed_total))


def remove_unreachable_tiles_in_map(
    game_map: GameMap,
    *,
    item_types: Mapping[int, ItemType] | None = None,
    ground_layer: int = 7,
    max_layer: int = 15,
    radius_x: int = 10,
    radius_y: int = 8,
    radius_z: int = 2,
) -> tuple[dict[tuple[int, int, int], None], RemoveItemsResult]:
    """Remove tiles that are unreachable by legacy non-blocking proximity rules."""

    non_blocking: set[tuple[int, int, int]] = set()
    for key, tile in game_map.tiles.items():
        if _is_non_blocking_tile(tile, item_types=item_types):
            non_blocking.add((int(key[0]), int(key[1]), int(key[2])))

    changed: dict[tuple[int, int, int], None] = {}
    removed = 0

    for key, tile in game_map.tiles.items():
        pos = (int(key[0]), int(key[1]), int(key[2]))
        if pos in non_blocking:
            continue

        x, y, z = int(tile.x), int(tile.y), int(tile.z)
        sx = max(int(x) - int(radius_x), 0)
        ex = min(int(x) + int(radius_x), 0xFFFF)
        sy = max(int(y) - int(radius_y), 0)
        ey = min(int(y) + int(radius_y), 0xFFFF)
        if int(z) <= int(ground_layer):
            sz, ez = 0, 9
        else:
            sz = max(int(z) - int(radius_z), int(ground_layer))
            ez = min(int(z) + int(radius_z), int(max_layer))

        if _has_any_non_blocking_tile_in_area(
            non_blocking_tiles=non_blocking,
            sx=sx,
            ex=ex,
            sy=sy,
            ey=ey,
            sz=sz,
            ez=ez,
        ):
            continue

        changed[pos] = None
        removed += 1

    return changed, RemoveItemsResult(removed=int(removed))


def compute_clear_invalid_house_tiles(
    game_map: GameMap,
) -> tuple[dict[int, House], dict[tuple[int, int, int], Tile], ClearInvalidHousesResult]:
    """Compute valid houses and tile updates for house refs with invalid town/house ids."""

    towns = getattr(game_map, "towns", None) or {}
    houses = getattr(game_map, "houses", None) or {}

    valid_houses: dict[int, House] = {}
    for hid, house in houses.items():
        town_id = int(getattr(house, "townid", 0) or 0)
        if town_id > 0 and int(town_id) not in towns:
            continue
        valid_houses[int(hid)] = house

    changed_tiles: dict[tuple[int, int, int], Tile] = {}
    for key, tile in game_map.tiles.items():
        house_id = getattr(tile, "house_id", None)
        if house_id is None:
            continue
        if int(house_id) in valid_houses:
            continue
        changed_tiles[(int(key[0]), int(key[1]), int(key[2]))] = Tile(
            x=int(tile.x),
            y=int(tile.y),
            z=int(tile.z),
            ground=tile.ground,
            items=list(tile.items),
            house_id=None,
            map_flags=int(tile.map_flags),
            zones=tile.zones,
            modified=True,
            monsters=tile.monsters,
            npc=tile.npc,
            spawn_monster=tile.spawn_monster,
            spawn_npc=tile.spawn_npc,
        )

    return (
        valid_houses,
        changed_tiles,
        ClearInvalidHousesResult(
            houses_removed=max(0, int(len(houses) - len(valid_houses))),
            tile_refs_cleared=int(len(changed_tiles)),
        ),
    )


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
