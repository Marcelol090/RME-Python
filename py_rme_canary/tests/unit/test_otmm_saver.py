from __future__ import annotations

from pathlib import Path

from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.core.data.houses import House
from py_rme_canary.core.data.item import Item, Position
from py_rme_canary.core.data.spawns import (
    MonsterSpawnArea,
    MonsterSpawnEntry,
    NpcSpawnArea,
    NpcSpawnEntry,
)
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.core.data.towns import Town
from py_rme_canary.core.io.otmm import load_otmm
from py_rme_canary.core.io.otmm_saver import serialize_otmm


def _sample_map() -> GameMap:
    header = MapHeader(otbm_version=1, width=256, height=256, description="otmm test")
    tile_items = Item(
        id=222,
        subtype=6,
        action_id=7,
        unique_id=9,
        text="hi",
        description="desc",
        items=(Item(id=333, text="child"),),
    )
    tile = Tile(
        x=100,
        y=200,
        z=7,
        ground=Item(id=111),
        items=[tile_items],
        map_flags=0x12,
    )
    house_tile = Tile(
        x=101,
        y=200,
        z=7,
        ground=Item(id=444),
        items=[],
        house_id=1,
    )

    town = Town(id=1, name="Town", temple_position=Position(x=100, y=200, z=7))
    house = House(
        id=1,
        name="House",
        entry=Position(x=101, y=200, z=7),
        rent=123,
        townid=1,
        beds=2,
    )

    monster_spawns = [
        MonsterSpawnArea(
            center=Position(x=100, y=200, z=7),
            radius=3,
            monsters=(MonsterSpawnEntry(name="rat", dx=1, dy=0, spawntime=30),),
        )
    ]
    npc_spawns = [
        NpcSpawnArea(
            center=Position(x=100, y=200, z=7),
            radius=1,
            npcs=(NpcSpawnEntry(name="npc", dx=0, dy=1),),
        )
    ]

    return GameMap(
        header=header,
        tiles={
            (tile.x, tile.y, tile.z): tile,
            (house_tile.x, house_tile.y, house_tile.z): house_tile,
        },
        towns={1: town},
        houses={1: house},
        monster_spawns=monster_spawns,
        npc_spawns=npc_spawns,
    )


def test_otmm_serialize_roundtrip(tmp_path: Path) -> None:
    gm = _sample_map()
    data = serialize_otmm(gm, otb_major=3, otb_minor=4)

    path = tmp_path / "roundtrip.otmm"
    path.write_bytes(data)

    loaded = load_otmm(path)

    assert loaded.header.description == "otmm test"
    tile = loaded.get_tile(100, 200, 7)
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
    assert item.items[0].id == 333

    house_tile = loaded.get_tile(101, 200, 7)
    assert house_tile is not None
    assert house_tile.house_id == 1

    assert 1 in loaded.towns
    assert loaded.towns[1].name == "Town"

    assert 1 in loaded.houses
    assert loaded.houses[1].name == "House"
    assert loaded.houses[1].rent == 123
    assert loaded.houses[1].beds == 2

    assert len(loaded.monster_spawns) == 1
    assert loaded.monster_spawns[0].monsters[0].name == "rat"

    assert len(loaded.npc_spawns) == 1
    assert loaded.npc_spawns[0].npcs[0].name == "npc"
