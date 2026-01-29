from __future__ import annotations

from pathlib import Path

from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.core.data.houses import House
from py_rme_canary.core.data.item import Item, Position
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.core.io.otbm_saver import save_game_map_bundle_atomic
from py_rme_canary.logic_layer.operations.map_import import import_map_with_offset


def test_import_map_with_offset(tmp_path: Path) -> None:
    target_map = GameMap(header=MapHeader(otbm_version=2, width=10, height=10))
    target_map.set_tile(Tile(x=1, y=1, z=7, ground=Item(id=100)))

    source_map = GameMap(header=MapHeader(otbm_version=2, width=5, height=5, housefile="houses.xml"))
    source_map.set_tile(Tile(x=0, y=0, z=7, ground=Item(id=200), items=[Item(id=201)], house_id=1))
    source_map.houses[1] = House(id=1, name="ImportHouse", entry=Position(1, 1, 7), townid=1)

    source_path = tmp_path / "source_map.otbm"
    save_game_map_bundle_atomic(str(source_path), source_map, id_mapper=None)

    report = import_map_with_offset(
        target_map=target_map,
        source_path=source_path,
        offset=(2, 3, 0),
        import_tiles=True,
        import_houses=True,
        import_spawns=False,
        import_zones=False,
        merge_mode=0,
    )

    imported_tile = target_map.get_tile(2, 3, 7)
    assert imported_tile is not None
    assert imported_tile.ground is not None
    assert imported_tile.ground.id == 200
    assert len(imported_tile.items) == 1
    assert imported_tile.items[0].id == 201

    assert 1 in target_map.houses
    assert target_map.houses[1].entry == Position(3, 4, 7)
    assert report.tiles_imported == 1
    assert report.houses_imported == 1
