from __future__ import annotations

import struct
from pathlib import Path

from py_rme_canary.core.constants import (
    ESCAPE_CHAR,
    MAGIC_OTMM,
    NODE_END,
    NODE_START,
    OTMM_ATTR_ACTION_ID,
    OTMM_ATTR_DESC,
    OTMM_ATTR_SUBTYPE,
    OTMM_ATTR_TEXT,
    OTMM_ATTR_TILE_FLAGS,
    OTMM_ATTR_UNIQUE_ID,
    OTMM_DESCRIPTION,
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
)
from py_rme_canary.core.database.items_xml import ItemsXML
from py_rme_canary.core.io.otmm import load_otmm


def _escape_payload(data: bytes) -> bytes:
    out = bytearray()
    for b in data:
        if b in (NODE_START, NODE_END, ESCAPE_CHAR):
            out.append(ESCAPE_CHAR)
        out.append(b)
    return bytes(out)


def _pack_string(text: str) -> bytes:
    raw = text.encode("utf-8")
    return struct.pack("<H", len(raw)) + raw


def _node(node_type: int, payload: bytes = b"", children: bytes = b"") -> bytes:
    return bytes([NODE_START, node_type]) + _escape_payload(payload) + children + bytes([NODE_END])


def _build_sample_otmm() -> bytes:
    root_payload = struct.pack("<IHHII", 1, 512, 512, 3, 4)

    desc_node = _node(OTMM_DESCRIPTION, _pack_string("hello"))

    tile_payload = struct.pack("<HHB", 100, 200, 7)
    tile_payload += struct.pack("<H", 111)
    tile_payload += bytes([OTMM_ATTR_TILE_FLAGS]) + struct.pack("<I", 0x12)

    item_payload = struct.pack("<H", 222)
    item_payload += bytes([OTMM_ATTR_SUBTYPE]) + struct.pack("<H", 6)
    item_payload += bytes([OTMM_ATTR_ACTION_ID]) + struct.pack("<H", 7)
    item_payload += bytes([OTMM_ATTR_UNIQUE_ID]) + struct.pack("<H", 9)
    item_payload += bytes([OTMM_ATTR_TEXT]) + _pack_string("hi")
    item_payload += bytes([OTMM_ATTR_DESC]) + _pack_string("desc")

    child_payload = struct.pack("<H", 333)
    child_payload += bytes([OTMM_ATTR_TEXT]) + _pack_string("child")

    item_node = _node(OTMM_ITEM, item_payload, _node(OTMM_ITEM, child_payload))
    tile_node = _node(OTMM_TILE, tile_payload, item_node)
    tile_data_node = _node(OTMM_TILE_DATA, b"", tile_node)

    map_node = _node(OTMM_MAP_DATA, b"", desc_node + tile_data_node)
    root_node = _node(0, root_payload, map_node)

    return MAGIC_OTMM + root_node


def _build_house_u16_otmm() -> bytes:
    root_payload = struct.pack("<IHHII", 1, 64, 64, 0, 0)

    tile_payload = struct.pack("<HHB", 10, 20, 7)
    tile_payload += struct.pack("<I", 1)
    tile_payload += struct.pack("<H", 0)
    tile_node = _node(OTMM_HOUSETILE, tile_payload)
    tile_data_node = _node(OTMM_TILE_DATA, b"", tile_node)

    house_payload = struct.pack("<I", 1)
    house_payload += _pack_string("House")
    house_payload += struct.pack("<HHHHHB", 2, 100, 3, 30, 40, 7)
    house_node = _node(OTMM_HOUSE, house_payload)
    house_data_node = _node(OTMM_HOUSE_DATA, b"", house_node)

    map_node = _node(OTMM_MAP_DATA, b"", tile_data_node + house_data_node)
    root_node = _node(0, root_payload, map_node)

    return MAGIC_OTMM + root_node


def _build_town_otmm() -> bytes:
    root_payload = struct.pack("<IHHII", 1, 32, 32, 0, 0)

    town_payload = struct.pack("<I", 5)
    town_payload += _pack_string("Alpha")
    town_payload += struct.pack("<HHB", 123, 321, 7)
    town_node = _node(OTMM_TOWN, town_payload)
    town_data_node = _node(OTMM_TOWN_DATA, b"", town_node)

    map_node = _node(OTMM_MAP_DATA, b"", town_data_node)
    root_node = _node(0, root_payload, map_node)

    return MAGIC_OTMM + root_node


def _build_spawn_otmm() -> bytes:
    root_payload = struct.pack("<IHHII", 1, 32, 32, 0, 0)

    mcx, mcy, mcz = 8, 9, 7
    monster_area_payload = struct.pack("<HHB", mcx, mcy, mcz)
    monster_area_payload += struct.pack("<I", 5)

    monster_payload = _pack_string("rat")
    monster_payload += struct.pack("<I", 30)
    monster_payload += struct.pack("<HHB", mcx + 2, mcy - 1, mcz)
    monster_node = _node(OTMM_MONSTER, monster_payload)
    monster_area_node = _node(OTMM_SPAWN_MONSTER_AREA, monster_area_payload, monster_node)
    monster_data_node = _node(OTMM_SPAWN_MONSTER_DATA, b"", monster_area_node)

    ncx, ncy, ncz = 10, 11, 7
    npc_area_payload = struct.pack("<HHB", ncx, ncy, ncz)
    npc_area_payload += struct.pack("<I", 3)

    npc_payload = _pack_string("npc")
    npc_payload += struct.pack("<HHB", ncx - 1, ncy + 1, ncz)
    npc_node = _node(OTMM_NPC, npc_payload)
    npc_area_node = _node(OTMM_SPAWN_NPC_AREA, npc_area_payload, npc_node)
    npc_data_node = _node(OTMM_SPAWN_NPC_DATA, b"", npc_area_node)

    map_node = _node(OTMM_MAP_DATA, b"", monster_data_node + npc_data_node)
    root_node = _node(0, root_payload, map_node)

    return MAGIC_OTMM + root_node


def _build_unknown_item_otmm() -> bytes:
    root_payload = struct.pack("<IHHII", 1, 16, 16, 0, 0)

    tile_payload = struct.pack("<HHB", 1, 2, 7)
    tile_payload += struct.pack("<H", 0)

    item_payload = struct.pack("<H", 9999)
    item_node = _node(OTMM_ITEM, item_payload)

    tile_node = _node(OTMM_TILE, tile_payload, item_node)
    tile_data_node = _node(OTMM_TILE_DATA, b"", tile_node)

    map_node = _node(OTMM_MAP_DATA, b"", tile_data_node)
    root_node = _node(0, root_payload, map_node)

    return MAGIC_OTMM + root_node


def _build_empty_nodes_otmm() -> bytes:
    root_payload = struct.pack("<IHHII", 1, 8, 8, 0, 0)

    tile_data_node = _node(OTMM_TILE_DATA, b"")
    spawn_monster_node = _node(OTMM_SPAWN_MONSTER_DATA, b"")
    spawn_npc_node = _node(OTMM_SPAWN_NPC_DATA, b"")
    town_data_node = _node(OTMM_TOWN_DATA, b"")
    house_data_node = _node(OTMM_HOUSE_DATA, b"")

    map_node = _node(
        OTMM_MAP_DATA,
        b"",
        tile_data_node + spawn_monster_node + spawn_npc_node + town_data_node + house_data_node,
    )
    root_node = _node(0, root_payload, map_node)

    return MAGIC_OTMM + root_node


def test_otmm_loader_reads_tiles_and_items(tmp_path: Path) -> None:
    p = tmp_path / "sample.otmm"
    p.write_bytes(_build_sample_otmm())

    gm = load_otmm(p)

    assert gm.header.width == 512
    assert gm.header.height == 512
    assert gm.header.description == "hello"

    tile = gm.get_tile(100, 200, 7)
    assert tile is not None
    assert tile.ground is not None
    assert tile.ground.id == 111
    assert tile.map_flags == 0x12

    assert len(tile.items) == 1
    item = tile.items[0]
    assert item.id == 222
    assert item.subtype == 6
    assert item.action_id == 7
    assert item.unique_id == 9
    assert item.text == "hi"
    assert item.description == "desc"

    assert len(item.items) == 1
    child = item.items[0]
    assert child.id == 333
    assert child.text == "child"


def test_otmm_loader_reads_house_payload_u16(tmp_path: Path) -> None:
    p = tmp_path / "house_u16.otmm"
    p.write_bytes(_build_house_u16_otmm())

    gm = load_otmm(p)

    tile = gm.get_tile(10, 20, 7)
    assert tile is not None
    assert tile.house_id == 1

    assert 1 in gm.houses
    house = gm.houses[1]
    assert house.name == "House"
    assert house.townid == 2
    assert house.rent == 100
    assert house.beds == 3
    assert house.entry is not None
    assert (house.entry.x, house.entry.y, house.entry.z) == (30, 40, 7)


def test_otmm_loader_reads_town_data(tmp_path: Path) -> None:
    p = tmp_path / "town.otmm"
    p.write_bytes(_build_town_otmm())

    gm = load_otmm(p)

    assert 5 in gm.towns
    town = gm.towns[5]
    assert town.name == "Alpha"
    assert (town.temple_position.x, town.temple_position.y, town.temple_position.z) == (123, 321, 7)


def test_otmm_loader_reads_spawn_data(tmp_path: Path) -> None:
    p = tmp_path / "spawns.otmm"
    p.write_bytes(_build_spawn_otmm())

    gm = load_otmm(p)

    assert len(gm.monster_spawns) == 1
    area = gm.monster_spawns[0]
    assert (area.center.x, area.center.y, area.center.z) == (8, 9, 7)
    assert area.radius == 5
    assert len(area.monsters) == 1
    monster = area.monsters[0]
    assert monster.name == "rat"
    assert monster.spawntime == 30
    assert (monster.dx, monster.dy) == (2, -1)

    assert len(gm.npc_spawns) == 1
    npc_area = gm.npc_spawns[0]
    assert (npc_area.center.x, npc_area.center.y, npc_area.center.z) == (10, 11, 7)
    assert npc_area.radius == 3
    assert len(npc_area.npcs) == 1
    npc = npc_area.npcs[0]
    assert npc.name == "npc"
    assert (npc.dx, npc.dy) == (-1, 1)


def test_otmm_loader_handles_unknown_item_placeholder(tmp_path: Path) -> None:
    p = tmp_path / "unknown.otmm"
    p.write_bytes(_build_unknown_item_otmm())

    items_db = ItemsXML.from_string(
        '<items><item id="111" name="ground"><attribute key="type" value="ground"/></item></items>'
    )
    gm = load_otmm(p, items_db=items_db)

    tile = gm.get_tile(1, 2, 7)
    assert tile is not None
    assert len(tile.items) == 1
    item = tile.items[0]
    assert item.id == 0
    assert item.raw_unknown_id == 9999

    report = gm.load_report
    assert report is not None
    assert report["unknown_ids_count"] == 1
    assert report["replaced_items"] == [(1, 2, 7, 9999)]


def test_otmm_loader_handles_empty_nodes(tmp_path: Path) -> None:
    p = tmp_path / "empty_nodes.otmm"
    p.write_bytes(_build_empty_nodes_otmm())

    gm = load_otmm(p)

    assert gm.tiles == {}
    assert gm.towns == {}
    assert gm.houses == {}
    assert gm.monster_spawns == []
    assert gm.npc_spawns == []
