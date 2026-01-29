from __future__ import annotations

from dataclasses import dataclass

from py_rme_canary.core.data.gamemap import GameMap
from py_rme_canary.core.data.item import Item


@dataclass(frozen=True, slots=True)
class MapStatistics:
    total_tiles: int
    total_items: int
    unique_items: int

    total_monsters: int
    unique_monsters: int
    total_npcs: int
    unique_npcs: int

    total_spawns: int
    total_houses: int

    items_with_action_id: int
    items_with_unique_id: int

    teleport_count: int
    container_count: int
    depot_count: int
    door_count: int

    waypoint_count: int
    tiles_per_floor: tuple[int, ...]  # len 16


def _format_int(n: int) -> str:
    return f"{int(n):,}"


def compute_map_statistics(game_map: GameMap) -> MapStatistics:
    """Compute map statistics in the spirit of legacy RME.

    Legacy reference: `source/map_statistics_window.cpp`.

    Notes on differences vs legacy:
    - Legacy counts placed creatures and per-tile spawn flags. The Python port
      currently models spawns as external structures (`monster_spawns`/`npc_spawns`).
      We count spawn entries from those lists.
    - Legacy determines teleport/container/depot/door via item type tables.
      Here we infer using persisted fields when available.
    """

    unique_item_ids: set[int] = set()

    unique_monster_names: set[str] = set()
    unique_npc_names: set[str] = set()
    total_monsters = 0
    total_npcs = 0

    # Spawns are external structures in the Python port.
    for monster_area in game_map.monster_spawns:
        for m in monster_area.monsters:
            total_monsters += 1
            unique_monster_names.add(str(m.name))

    for npc_area in game_map.npc_spawns:
        for n in npc_area.npcs:
            total_npcs += 1
            unique_npc_names.add(str(n.name))

    total_spawns = int(len(game_map.monster_spawns) + len(game_map.npc_spawns))
    total_houses = len(game_map.houses)
    waypoint_count = len(game_map.waypoints)

    tiles_per_floor = [0] * 16
    total_tiles = 0
    total_items = 0
    items_with_action_id = 0
    items_with_unique_id = 0

    teleport_count = 0
    container_count = 0
    depot_count = 0
    door_count = 0

    def count_item_common(it: Item) -> None:
        nonlocal total_items, items_with_action_id, items_with_unique_id
        total_items += 1
        unique_item_ids.add(int(it.id))
        if it.action_id is not None and int(it.action_id) > 0:
            items_with_action_id += 1
        if it.unique_id is not None and int(it.unique_id) > 0:
            items_with_unique_id += 1

    def count_special(it: Item) -> None:
        nonlocal teleport_count, container_count, depot_count, door_count
        if it.destination is not None:
            teleport_count += 1
        # Best-effort inference: container nodes are represented by child items.
        if it.items:
            container_count += 1
        if it.depot_id is not None and int(it.depot_id) > 0:
            depot_count += 1
        if it.house_door_id is not None and int(it.house_door_id) > 0:
            door_count += 1

    for (x, y, z), tile in game_map.tiles.items():
        _ = (x, y)
        total_tiles += 1
        if 0 <= int(z) < 16:
            tiles_per_floor[int(z)] += 1

        if tile.ground is not None:
            count_item_common(tile.ground)

        for it in tile.items:
            count_item_common(it)
            count_special(it)

    return MapStatistics(
        total_tiles=int(total_tiles),
        total_items=int(total_items),
        unique_items=len(unique_item_ids),
        total_monsters=int(total_monsters),
        unique_monsters=len(unique_monster_names),
        total_npcs=int(total_npcs),
        unique_npcs=len(unique_npc_names),
        total_spawns=int(total_spawns),
        total_houses=int(total_houses),
        items_with_action_id=int(items_with_action_id),
        items_with_unique_id=int(items_with_unique_id),
        teleport_count=int(teleport_count),
        container_count=int(container_count),
        depot_count=int(depot_count),
        door_count=int(door_count),
        waypoint_count=int(waypoint_count),
        tiles_per_floor=tuple(int(v) for v in tiles_per_floor),
    )


def format_map_statistics_report(game_map: GameMap, stats: MapStatistics) -> str:
    lines: list[str] = []
    lines.append("Map Statistics Report")
    lines.append("=====================")
    lines.append("")
    lines.append(f"Map Name: {game_map.header.description}")
    lines.append(f"Map Size: {int(game_map.header.width)} x {int(game_map.header.height)}")
    lines.append("")
    lines.append("General Statistics:")
    lines.append(f"  Total Tiles: {_format_int(stats.total_tiles)}")
    lines.append(f"  Total Items: {_format_int(stats.total_items)} ({_format_int(stats.unique_items)} unique)")
    lines.append(
        f"  Monsters (spawns): {_format_int(stats.total_monsters)} ({_format_int(stats.unique_monsters)} unique)"
    )
    lines.append(f"  NPCs (spawns): {_format_int(stats.total_npcs)} ({_format_int(stats.unique_npcs)} unique)")
    lines.append(f"  Spawns (areas): {_format_int(stats.total_spawns)}")
    lines.append(f"  Houses: {_format_int(stats.total_houses)}")
    lines.append(f"  Waypoints: {_format_int(stats.waypoint_count)}")
    lines.append("")
    lines.append("Special Items:")
    lines.append(f"  Items with Action ID: {_format_int(stats.items_with_action_id)}")
    lines.append(f"  Items with Unique ID: {_format_int(stats.items_with_unique_id)}")
    lines.append(f"  Teleports: {_format_int(stats.teleport_count)}")
    lines.append(f"  Containers (best-effort): {_format_int(stats.container_count)}")
    lines.append(f"  Depots: {_format_int(stats.depot_count)}")
    lines.append(f"  Doors: {_format_int(stats.door_count)}")
    lines.append("")
    lines.append("Tiles per Floor:")
    for z, n in enumerate(stats.tiles_per_floor):
        if int(n) <= 0:
            continue
        lines.append(f"  Floor {z}: {_format_int(int(n))}")

    return "\n".join(lines) + "\n"
