"""OTMM map saver - serialize GameMap to OTMM binary format.

Legacy reference: source/iomap_otmm.cpp
"""

from __future__ import annotations

import struct
from collections.abc import Iterable

from py_rme_canary.core.constants import (
    ESCAPE_CHAR,
    MAGIC_OTMM,
    NODE_END,
    NODE_START,
    OTMM_ATTR_ACTION_ID,
    OTMM_ATTR_DEPOT_ID,
    OTMM_ATTR_DESC,
    OTMM_ATTR_DOOR_ID,
    OTMM_ATTR_SUBTYPE,
    OTMM_ATTR_TELE_DEST,
    OTMM_ATTR_TEXT,
    OTMM_ATTR_TILE_FLAGS,
    OTMM_ATTR_UNIQUE_ID,
    OTMM_DESCRIPTION,
    OTMM_EDITOR,
    OTMM_HOUSE,
    OTMM_HOUSE_DATA,
    OTMM_HOUSETILE,
    OTMM_ITEM,
    OTMM_MAP_DATA,
    OTMM_MONSTER,
    OTMM_NPC,
    OTMM_SPAWN_MONSTER_AREA,
    OTMM_SPAWN_MONSTER_DATA,
    OTMM_SPAWN_NPC_AREA,
    OTMM_SPAWN_NPC_DATA,
    OTMM_TILE,
    OTMM_TILE_DATA,
    OTMM_TOWN,
    OTMM_TOWN_DATA,
    OTMM_VERSION_1,
)
from py_rme_canary.core.data.gamemap import GameMap
from py_rme_canary.core.data.houses import House
from py_rme_canary.core.data.item import Item, Position
from py_rme_canary.core.data.spawns import MonsterSpawnArea, NpcSpawnArea
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.core.data.towns import Town

from .atomic_io import save_bytes_atomic


def _u8(v: int) -> int:
    if not (0 <= v <= 0xFF):
        raise ValueError(f"u8 out of range: {v}")
    return v


def _u16(v: int) -> int:
    if not (0 <= v <= 0xFFFF):
        raise ValueError(f"u16 out of range: {v}")
    return v


def _u32(v: int) -> int:
    if not (0 <= v <= 0xFFFFFFFF):
        raise ValueError(f"u32 out of range: {v}")
    return v


def _escape_bytes(data: bytes) -> bytes:
    out = bytearray()
    for b in data:
        if b in (NODE_START, NODE_END, ESCAPE_CHAR):
            out.append(ESCAPE_CHAR)
        out.append(b)
    return bytes(out)


def _node_bytes(node_type: int, payload: bytes, children: tuple[bytes, ...] = ()) -> bytes:
    out = bytearray()
    out.append(NODE_START)
    out.append(node_type & 0xFF)
    out += _escape_bytes(payload)
    for child in children:
        out += child
    out.append(NODE_END)
    return bytes(out)


def _string_payload(text: str) -> bytes:
    raw = (text or "").encode("utf-8", errors="replace")
    if len(raw) > 0xFFFF:
        raw = raw[:0xFFFF]
    return struct.pack("<H", _u16(len(raw))) + raw


def _is_simple_item(item: Item) -> bool:
    return (
        item.action_id is None
        and item.unique_id is None
        and not item.text
        and not item.description
        and item.destination is None
        and item.subtype is None
        and item.count is None
        and item.depot_id is None
        and item.house_door_id is None
        and not item.items
    )


def _build_item_payload(item: Item) -> bytes:
    if int(item.id) == 0:
        raise ValueError("Refusing to serialize Item with server id 0")

    payload = bytearray(struct.pack("<H", _u16(int(item.id))))

    subtype = item.subtype
    if subtype is None and item.count is not None:
        subtype = int(item.count)

    if subtype is not None and int(subtype) > 0:
        payload += struct.pack("<BH", _u8(OTMM_ATTR_SUBTYPE), _u16(int(subtype) & 0xF))

    if item.action_id is not None and int(item.action_id) > 0:
        payload += struct.pack("<BH", _u8(OTMM_ATTR_ACTION_ID), _u16(int(item.action_id)))

    if item.unique_id is not None and int(item.unique_id) > 0:
        payload += struct.pack("<BH", _u8(OTMM_ATTR_UNIQUE_ID), _u16(int(item.unique_id)))

    if item.text:
        payload += struct.pack("<B", _u8(OTMM_ATTR_TEXT)) + _string_payload(item.text)

    if item.description:
        payload += struct.pack("<B", _u8(OTMM_ATTR_DESC)) + _string_payload(item.description)

    if item.destination is not None:
        dest = item.destination
        payload += struct.pack(
            "<BHHB",
            _u8(OTMM_ATTR_TELE_DEST),
            _u16(int(dest.x)),
            _u16(int(dest.y)),
            _u8(int(dest.z)),
        )

    if item.depot_id is not None and int(item.depot_id) >= 0:
        payload += struct.pack("<BH", _u8(OTMM_ATTR_DEPOT_ID), _u16(int(item.depot_id)))

    if item.house_door_id is not None and int(item.house_door_id) > 0:
        payload += struct.pack("<BB", _u8(OTMM_ATTR_DOOR_ID), _u8(int(item.house_door_id)))

    return bytes(payload)


def _build_item_node(item: Item) -> bytes:
    payload = _build_item_payload(item)
    children: tuple[bytes, ...] = ()
    if item.items:
        children = tuple(_build_item_node(child) for child in item.items)
    return _node_bytes(OTMM_ITEM, payload, children)


def _build_tile_node(tile: Tile) -> bytes:
    payload = bytearray(struct.pack("<HHB", _u16(int(tile.x)), _u16(int(tile.y)), _u8(int(tile.z))))

    if tile.house_id is not None:
        payload += struct.pack("<I", _u32(int(tile.house_id)))

    # ground_id MUST come before tile attributes (loader reads ground_id first)
    ground_nodes: list[bytes] = []
    ground_id = 0
    if tile.ground is not None:
        if _is_simple_item(tile.ground):
            ground_id = int(tile.ground.id)
        else:
            ground_nodes.append(_build_item_node(tile.ground))

    payload += struct.pack("<H", _u16(int(ground_id)))

    # tile flags attribute comes AFTER ground_id
    if int(tile.map_flags) != 0:
        payload += struct.pack("<BI", _u8(OTMM_ATTR_TILE_FLAGS), _u32(int(tile.map_flags)))

    item_nodes = [_build_item_node(item) for item in tile.items]
    children = tuple(ground_nodes + item_nodes)
    node_type = OTMM_HOUSETILE if tile.house_id is not None else OTMM_TILE
    return _node_bytes(node_type, bytes(payload), children)


def _build_spawn_monster_data(spawns: Iterable[MonsterSpawnArea]) -> bytes:
    area_nodes: list[bytes] = []
    for area in spawns:
        center = area.center
        payload = bytearray(struct.pack("<HHB", _u16(int(center.x)), _u16(int(center.y)), _u8(int(center.z))))
        payload += struct.pack("<I", _u32(int(area.radius)))

        monster_nodes: list[bytes] = []
        for entry in area.monsters:
            mx = int(center.x) + int(entry.dx)
            my = int(center.y) + int(entry.dy)
            mz = int(center.z)
            m_payload = bytearray(_string_payload(str(entry.name)))
            m_payload += struct.pack("<I", _u32(int(entry.spawntime)))
            m_payload += struct.pack("<HHB", _u16(mx), _u16(my), _u8(mz))
            monster_nodes.append(_node_bytes(OTMM_MONSTER, bytes(m_payload)))

        area_nodes.append(_node_bytes(OTMM_SPAWN_MONSTER_AREA, bytes(payload), tuple(monster_nodes)))

    return _node_bytes(OTMM_SPAWN_MONSTER_DATA, b"", tuple(area_nodes))


def _build_spawn_npc_data(spawns: Iterable[NpcSpawnArea]) -> bytes:
    area_nodes: list[bytes] = []
    for area in spawns:
        center = area.center
        payload = bytearray(struct.pack("<HHB", _u16(int(center.x)), _u16(int(center.y)), _u8(int(center.z))))
        payload += struct.pack("<I", _u32(int(area.radius)))

        npc_nodes: list[bytes] = []
        for entry in area.npcs:
            nx = int(center.x) + int(entry.dx)
            ny = int(center.y) + int(entry.dy)
            nz = int(center.z)
            n_payload = bytearray(_string_payload(str(entry.name)))
            n_payload += struct.pack("<HHB", _u16(nx), _u16(ny), _u8(nz))
            npc_nodes.append(_node_bytes(OTMM_NPC, bytes(n_payload)))

        area_nodes.append(_node_bytes(OTMM_SPAWN_NPC_AREA, bytes(payload), tuple(npc_nodes)))

    return _node_bytes(OTMM_SPAWN_NPC_DATA, b"", tuple(area_nodes))


def _build_town_data(towns: Iterable[Town]) -> bytes:
    town_nodes: list[bytes] = []
    for town in towns:
        payload = bytearray(struct.pack("<I", _u32(int(town.id))))
        payload += _string_payload(str(town.name))
        pos = town.temple_position
        payload += struct.pack("<HHB", _u16(int(pos.x)), _u16(int(pos.y)), _u8(int(pos.z)))
        town_nodes.append(_node_bytes(OTMM_TOWN, bytes(payload)))

    return _node_bytes(OTMM_TOWN_DATA, b"", tuple(town_nodes))


def _build_house_data(houses: Iterable[House]) -> bytes:
    house_nodes: list[bytes] = []
    for house in houses:
        entry = house.entry or Position(x=0, y=0, z=7)
        payload = bytearray(struct.pack("<I", _u32(int(house.id))))
        payload += _string_payload(str(house.name))
        payload += struct.pack("<H", _u16(int(house.townid)))
        payload += struct.pack("<H", _u16(int(house.rent)))
        payload += struct.pack("<H", _u16(int(house.beds)))
        payload += struct.pack("<HHB", _u16(int(entry.x)), _u16(int(entry.y)), _u8(int(entry.z)))
        house_nodes.append(_node_bytes(OTMM_HOUSE, bytes(payload)))

    return _node_bytes(OTMM_HOUSE_DATA, b"", tuple(house_nodes))


def serialize_otmm(
    game_map: GameMap,
    *,
    otb_major: int = 0,
    otb_minor: int = 0,
) -> bytes:
    header = game_map.header
    root_payload = struct.pack(
        "<IHHII",
        _u32(int(OTMM_VERSION_1)),
        _u16(int(header.width)),
        _u16(int(header.height)),
        _u32(int(otb_major)),
        _u32(int(otb_minor)),
    )

    editor_node = _node_bytes(OTMM_EDITOR, _string_payload("Saved with py_rme_canary"))
    desc_node = _node_bytes(OTMM_DESCRIPTION, _string_payload(header.description))

    tiles_sorted = sorted(game_map.tiles.values(), key=lambda t: (t.z, t.y, t.x))
    tile_nodes = [_build_tile_node(tile) for tile in tiles_sorted if tile.ground is not None or tile.items]
    tile_data_node = _node_bytes(OTMM_TILE_DATA, b"", tuple(tile_nodes))

    spawn_monster_node = _build_spawn_monster_data(game_map.monster_spawns)
    spawn_npc_node = _build_spawn_npc_data(game_map.npc_spawns)
    town_data_node = _build_town_data(game_map.towns.values())
    house_data_node = _build_house_data(game_map.houses.values())

    map_children = (
        editor_node,
        desc_node,
        tile_data_node,
        spawn_monster_node,
        spawn_npc_node,
        town_data_node,
        house_data_node,
    )
    map_node = _node_bytes(OTMM_MAP_DATA, b"", map_children)
    root_node = _node_bytes(0, root_payload, (map_node,))

    return MAGIC_OTMM + root_node


def save_otmm_atomic(
    path: str,
    game_map: GameMap,
    *,
    otb_major: int = 0,
    otb_minor: int = 0,
) -> None:
    save_bytes_atomic(path, serialize_otmm(game_map, otb_major=otb_major, otb_minor=otb_minor))
