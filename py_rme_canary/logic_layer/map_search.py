"""Map search helpers (UI-free).

These utilities support menu actions like "Find Item" and "Find on Map"
without introducing any Qt dependencies.
"""

from __future__ import annotations

from collections.abc import Callable, Iterable
from functools import lru_cache

from py_rme_canary.core.data.gamemap import GameMap
from py_rme_canary.core.data.item import Item, Position

TileKey = tuple[int, int, int]


def _iter_item_tree(root: Item) -> Iterable[Item]:
    stack: list[Item] = [root]
    while stack:
        it = stack.pop()
        yield it
        children = getattr(it, "items", None) or ()
        # Depth-first; preserve order as much as possible.
        for child in reversed(tuple(children)):
            stack.append(child)


def _tile_contains_server_id(game_map: GameMap, *, x: int, y: int, z: int, server_id: int) -> bool:
    tile = game_map.get_tile(int(x), int(y), int(z))
    if tile is None:
        return False

    ground = getattr(tile, "ground", None)
    if ground is not None:
        for it in _iter_item_tree(ground):
            if int(it.id) == int(server_id):
                return True

    items = getattr(tile, "items", None) or []
    for top in items:
        for it in _iter_item_tree(top):
            if int(it.id) == int(server_id):
                return True

    return False


def _normalize_selection_tiles(selection_tiles: Iterable[tuple[int, int, int]] | None) -> set[TileKey]:
    if selection_tiles is None:
        return set()

    normalized: set[TileKey] = set()
    for value in selection_tiles:
        if not isinstance(value, tuple) or len(value) != 3:
            continue
        normalized.add((int(value[0]), int(value[1]), int(value[2])))
    return normalized


def _iter_tiles_in_scope(
    game_map: GameMap,
    selection_tiles: Iterable[tuple[int, int, int]] | None = None,
) -> Iterable[object]:
    selection_set = _normalize_selection_tiles(selection_tiles)
    if not selection_set:
        yield from game_map.iter_tiles()
        return

    for x, y, z in sorted(selection_set, key=lambda key: (int(key[2]), int(key[1]), int(key[0]))):
        tile = game_map.get_tile(int(x), int(y), int(z))
        if tile is not None:
            yield tile

    # Explicit return to satisfy mypy reachability checks
    return  # type: ignore[unreachable]


def _iter_tile_items(tile: object) -> Iterable[Item]:
    ground = getattr(tile, "ground", None)
    if ground is not None:
        for it in _iter_item_tree(ground):
            yield it

    items = getattr(tile, "items", None) or []
    for top in items:
        for it in _iter_item_tree(top):
            yield it


def _find_positions_by_item_predicate(
    game_map: GameMap,
    *,
    item_predicate: Callable[[Item], bool],
    z_filter: int | None = None,
    selection_tiles: Iterable[tuple[int, int, int]] | None = None,
    max_results: int = 5000,
) -> list[Position]:
    out: list[Position] = []
    seen: set[TileKey] = set()

    for tile in _iter_tiles_in_scope(game_map, selection_tiles):
        if z_filter is not None and int(getattr(tile, "z", -1)) != int(z_filter):
            continue

        key = (int(getattr(tile, "x", 0)), int(getattr(tile, "y", 0)), int(getattr(tile, "z", 0)))
        if key in seen:
            continue

        for item in _iter_tile_items(tile):
            if item_predicate(item):
                seen.add(key)
                out.append(Position(x=key[0], y=key[1], z=key[2]))
                break

        if len(out) >= int(max_results):
            break

    out.sort(key=lambda p: (int(p.z), int(p.y), int(p.x)))
    return out


def _to_bool(value: object) -> bool:
    return str(value or "").strip().casefold() in {"1", "true", "yes", "on"}


@lru_cache(maxsize=8192)
def _item_metadata(server_id: int) -> object | None:
    try:
        from py_rme_canary.logic_layer.asset_manager import AssetManager

        return AssetManager.instance().get_item_metadata(int(server_id))
    except Exception:
        return None


def _is_container_item(item: Item) -> bool:
    if bool(getattr(item, "items", ())):
        return True

    try:
        from py_rme_canary.logic_layer.item_type_detector import ItemCategory, ItemTypeDetector

        if ItemTypeDetector.get_category(item) == ItemCategory.CONTAINER:
            return True
    except Exception:
        pass

    metadata = _item_metadata(int(item.id))
    if metadata is None:
        return False

    kind = str(getattr(metadata, "kind", "") or "").strip().casefold()
    if kind in {"container", "backpack", "bag", "quiver"}:
        return True

    attrs = getattr(metadata, "attributes", None) or {}
    for key in ("container", "iscontainer"):
        if _to_bool(attrs.get(key)):
            return True
    return False


def _is_writeable_item(item: Item) -> bool:
    text = getattr(item, "text", None)
    if isinstance(text, str) and text.strip():
        return True

    metadata = _item_metadata(int(item.id))
    if metadata is None:
        return False

    if bool(getattr(metadata, "can_write_text", False)):
        return True

    attrs = getattr(metadata, "attributes", None) or {}
    for key in ("writeable", "writable", "canwritetext", "canWriteText"):
        if _to_bool(attrs.get(key)):
            return True
    return False


def find_item_positions(
    game_map: GameMap,
    *,
    server_id: int,
    z_filter: int | None = None,
    selection_tiles: Iterable[tuple[int, int, int]] | None = None,
    max_results: int = 5000,
) -> list[Position]:
    """Return positions of tiles that contain an item with `server_id`.

    - Searches ground + stacked items, including container recursion.
    - Optionally filters by z.
    - Caps results to keep UI responsive.
    """

    server_id = int(server_id)
    if server_id <= 0:
        return []

    return _find_positions_by_item_predicate(
        game_map,
        item_predicate=lambda item: int(item.id) == int(server_id),
        z_filter=z_filter,
        selection_tiles=selection_tiles,
        max_results=max_results,
    )


def find_unique_item_positions(
    game_map: GameMap,
    *,
    unique_id: int | None = None,
    z_filter: int | None = None,
    selection_tiles: Iterable[tuple[int, int, int]] | None = None,
    max_results: int = 5000,
) -> list[Position]:
    target = int(unique_id) if unique_id is not None else None

    def _matches(item: Item) -> bool:
        value = getattr(item, "unique_id", None)
        if value is None:
            return False
        if target is None:
            return int(value) > 0
        return int(value) == target

    return _find_positions_by_item_predicate(
        game_map,
        item_predicate=_matches,
        z_filter=z_filter,
        selection_tiles=selection_tiles,
        max_results=max_results,
    )


def find_action_item_positions(
    game_map: GameMap,
    *,
    action_id: int | None = None,
    z_filter: int | None = None,
    selection_tiles: Iterable[tuple[int, int, int]] | None = None,
    max_results: int = 5000,
) -> list[Position]:
    target = int(action_id) if action_id is not None else None

    def _matches(item: Item) -> bool:
        value = getattr(item, "action_id", None)
        if value is None:
            return False
        if target is None:
            return int(value) > 0
        return int(value) == target

    return _find_positions_by_item_predicate(
        game_map,
        item_predicate=_matches,
        z_filter=z_filter,
        selection_tiles=selection_tiles,
        max_results=max_results,
    )


def find_container_item_positions(
    game_map: GameMap,
    *,
    z_filter: int | None = None,
    selection_tiles: Iterable[tuple[int, int, int]] | None = None,
    max_results: int = 5000,
) -> list[Position]:
    return _find_positions_by_item_predicate(
        game_map,
        item_predicate=_is_container_item,
        z_filter=z_filter,
        selection_tiles=selection_tiles,
        max_results=max_results,
    )


def find_writeable_item_positions(
    game_map: GameMap,
    *,
    z_filter: int | None = None,
    selection_tiles: Iterable[tuple[int, int, int]] | None = None,
    max_results: int = 5000,
) -> list[Position]:
    return _find_positions_by_item_predicate(
        game_map,
        item_predicate=_is_writeable_item,
        z_filter=z_filter,
        selection_tiles=selection_tiles,
        max_results=max_results,
    )


def find_waypoints(
    game_map: GameMap,
    *,
    query: str,
    max_results: int = 5000,
) -> list[tuple[str, Position]]:
    """Return (name, position) for waypoints matching `query`.

    Match behavior: case-insensitive substring match.
    If `query` is empty/whitespace, returns all waypoints.
    """

    q = str(query or "").strip().casefold()
    out: list[tuple[str, Position]] = []

    for name, pos in sorted(game_map.waypoints.items(), key=lambda kv: kv[0].casefold()):
        if q and q not in str(name).casefold():
            continue
        out.append((str(name), pos))
        if len(out) >= int(max_results):
            break

    return out


def find_houses(
    game_map: GameMap,
    *,
    query: str,
    max_results: int = 5000,
) -> list[tuple[str, Position]]:
    """Return (name, entry_position) for houses matching `query`."""
    q = str(query or "").strip().casefold()
    out: list[tuple[str, Position]] = []

    # Iterate sorted by name
    sorted_houses = sorted(game_map.houses.values(), key=lambda h: h.name.casefold())

    for house in sorted_houses:
        if q and q not in house.name.casefold():
            continue
        if house.entry:
            out.append((house.name, house.entry))

        if len(out) >= max_results:
            break

    return out


def find_monsters(
    game_map: GameMap,
    *,
    query: str,
    max_results: int = 5000,
) -> list[tuple[str, Position]]:
    """Return (monster_name, center_position) for monster spawns matching `query`.

    Searches within monster spawn areas. Returns the center of the spawn area.
    """
    q = str(query or "").strip().casefold()
    out: list[tuple[str, Position]] = []

    for spawn in game_map.monster_spawns:
        # Check if any monster in this spawn matches
        matches = False
        display_name = ""

        for monster in spawn.monsters:
            if not q or q in monster.name.casefold():
                matches = True
                display_name = monster.name  # Use the first matching monster name
                break

        if matches:
            # We return specific occurrences.
            # If multiple monsters match in same spawn, we presently just return the spawn center once per spawn area.
            # To be more precise, we could return each monster entry, but they share the same spawn center + dx/dy.
            # For "Find", jumping to the center is usually desired.
            out.append((f"{display_name} (Spawn)", spawn.center))

        if len(out) >= max_results:
            break

    return out


def find_npcs(
    game_map: GameMap,
    *,
    query: str,
    max_results: int = 5000,
) -> list[tuple[str, Position]]:
    """Return (npc_name, center_position) for npc spawns matching `query`."""
    q = str(query or "").strip().casefold()
    out: list[tuple[str, Position]] = []

    for spawn in game_map.npc_spawns:
        matches = False
        display_name = ""

        for npc in spawn.npcs:
            if not q or q in npc.name.casefold():
                matches = True
                display_name = npc.name
                break

        if matches:
            out.append((f"{display_name} (NPC Spawn)", spawn.center))

        if len(out) >= max_results:
            break

    return out
