"""XML Spawns Loader for py_rme_canary.

Parses monsters.xml and npcs.xml to populate GameMap with spawn data.
"""

from __future__ import annotations

import os

from py_rme_canary.core.data.creature import Monster, Npc
from py_rme_canary.core.data.gamemap import GameMap
from py_rme_canary.core.data.item import Position
from py_rme_canary.core.data.spawns import (
    MonsterSpawnArea,
    NpcSpawnArea,
)
from py_rme_canary.core.io.xml.safe import Element, ParseError
from py_rme_canary.core.io.xml.safe import safe_etree as ET


def load_spawns_xml(game_map: GameMap, file_path: str, is_npc: bool) -> None:
    """Load monster or NPC spawns from XML and populate the map.

    Populates:
    - game_map.monster_spawns (or npc_spawns)
    - tile.spawn_monster (or spawn_npc) on the center tile
    - tile.monsters (or npc) on the target tiles (center + offset)

    Args:
        game_map: The map object to populate.
        file_path: Absolute path to the XML file.
        is_npc: If True, load NPCs; otherwise, load monsters.
    """
    if not os.path.exists(file_path):
        return

    try:
        tree = ET.parse(file_path)
        root = tree.getroot()
    except ParseError:
        return

    for spawn_node in root.findall("spawn"):
        _process_spawn_node(game_map, spawn_node, is_npc)


def _process_spawn_node(
    game_map: GameMap,
    spawn_node: Element,
    is_npc: bool,
) -> None:
    """Process a single spawn node from XML."""
    try:
        center_x = int(spawn_node.get("centerx", "0"))
        center_y = int(spawn_node.get("centery", "0"))
        center_z = int(spawn_node.get("centerz", "0"))
        radius = int(spawn_node.get("radius", "0"))

        center_pos = Position(x=center_x, y=center_y, z=center_z)

        # Create spawn area and register it
        if is_npc:
            npc_spawn_area = NpcSpawnArea(center=center_pos, radius=radius, npcs=())
            game_map.npc_spawns.append(npc_spawn_area)
            _mark_center_tile_npc(game_map, center_x, center_y, center_z, npc_spawn_area)
        else:
            monster_spawn_area = MonsterSpawnArea(center=center_pos, radius=radius, monsters=())
            game_map.monster_spawns.append(monster_spawn_area)
            _mark_center_tile_monster(game_map, center_x, center_y, center_z, monster_spawn_area)

        # Process children
        tag_name = "npc" if is_npc else "monster"
        for child in spawn_node.findall(tag_name):
            _process_creature_entry(game_map, child, center_x, center_y, center_z, is_npc)

    except (ValueError, TypeError):
        pass


def _mark_center_tile_npc(
    game_map: GameMap,
    cx: int,
    cy: int,
    cz: int,
    spawn_area: NpcSpawnArea,
) -> None:
    """Mark the center tile with NPC spawn marker."""
    tile = game_map.ensure_tile(cx, cy, cz)
    new_tile = type(tile)(
        x=tile.x,
        y=tile.y,
        z=tile.z,
        ground=tile.ground,
        items=tile.items,
        house_id=tile.house_id,
        map_flags=tile.map_flags,
        zones=tile.zones,
        modified=tile.modified,
        monsters=tile.monsters,
        npc=tile.npc,
        spawn_monster=tile.spawn_monster,
        spawn_npc=spawn_area,
    )
    game_map.set_tile(new_tile)


def _mark_center_tile_monster(
    game_map: GameMap,
    cx: int,
    cy: int,
    cz: int,
    spawn_area: MonsterSpawnArea,
) -> None:
    """Mark the center tile with Monster spawn marker."""
    tile = game_map.ensure_tile(cx, cy, cz)
    new_tile = type(tile)(
        x=tile.x,
        y=tile.y,
        z=tile.z,
        ground=tile.ground,
        items=tile.items,
        house_id=tile.house_id,
        map_flags=tile.map_flags,
        zones=tile.zones,
        modified=tile.modified,
        monsters=tile.monsters,
        npc=tile.npc,
        spawn_monster=spawn_area,
        spawn_npc=tile.spawn_npc,
    )
    game_map.set_tile(new_tile)


def _process_creature_entry(
    game_map: GameMap,
    child: Element,
    center_x: int,
    center_y: int,
    center_z: int,
    is_npc: bool,
) -> None:
    """Process a single creature (monster/npc) entry within a spawn."""
    name = child.get("name")
    if not name:
        return

    dx = int(child.get("x", "0"))
    dy = int(child.get("y", "0"))
    direction = int(child.get("direction", "2"))

    abs_x = center_x + dx
    abs_y = center_y + dy
    abs_z = center_z

    target_tile = game_map.ensure_tile(abs_x, abs_y, abs_z)

    if is_npc:
        npc_inst = Npc(name=name, direction=direction)
        updated_tile = type(target_tile)(
            x=target_tile.x,
            y=target_tile.y,
            z=target_tile.z,
            ground=target_tile.ground,
            items=target_tile.items,
            house_id=target_tile.house_id,
            map_flags=target_tile.map_flags,
            zones=target_tile.zones,
            modified=target_tile.modified,
            monsters=target_tile.monsters,
            npc=npc_inst,
            spawn_monster=target_tile.spawn_monster,
            spawn_npc=target_tile.spawn_npc,
        )
        game_map.set_tile(updated_tile)
    else:
        monster_inst = Monster(name=name, direction=direction)
        new_monsters = list(target_tile.monsters)
        new_monsters.append(monster_inst)
        updated_tile = type(target_tile)(
            x=target_tile.x,
            y=target_tile.y,
            z=target_tile.z,
            ground=target_tile.ground,
            items=target_tile.items,
            house_id=target_tile.house_id,
            map_flags=target_tile.map_flags,
            zones=target_tile.zones,
            modified=target_tile.modified,
            monsters=new_monsters,
            npc=target_tile.npc,
            spawn_monster=target_tile.spawn_monster,
            spawn_npc=target_tile.spawn_npc,
        )
        game_map.set_tile(updated_tile)
