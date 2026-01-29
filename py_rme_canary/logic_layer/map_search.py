"""Map search helpers (UI-free).

These utilities support menu actions like "Find Item" and "Find on Map"
without introducing any Qt dependencies.
"""

from __future__ import annotations

from collections.abc import Iterable

from py_rme_canary.core.data.gamemap import GameMap
from py_rme_canary.core.data.item import Item, Position


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


def find_item_positions(
    game_map: GameMap,
    *,
    server_id: int,
    z_filter: int | None = None,
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

    out: list[Position] = []
    seen: set[tuple[int, int, int]] = set()

    for t in game_map.iter_tiles():
        if z_filter is not None and int(t.z) != int(z_filter):
            continue
        key = (int(t.x), int(t.y), int(t.z))
        if key in seen:
            continue

        if _tile_contains_server_id(game_map, x=key[0], y=key[1], z=key[2], server_id=server_id):
            seen.add(key)
            out.append(Position(x=key[0], y=key[1], z=key[2]))
            if len(out) >= int(max_results):
                break

    out.sort(key=lambda p: (int(p.z), int(p.y), int(p.x)))
    return out


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
