from __future__ import annotations

from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.core.data.item import Item
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.core.database.id_mapper import IdMapper
from py_rme_canary.logic_layer.map_format_conversion import (
    analyze_map_format_conversion,
    apply_map_format_version,
)


def _make_map_with_items(item_ids: list[int]) -> GameMap:
    header = MapHeader(otbm_version=2, width=256, height=256)
    game_map = GameMap(header=header)
    for idx, item_id in enumerate(item_ids):
        tile = Tile(x=100 + idx, y=100, z=7, ground=Item(id=int(item_id)))
        game_map.set_tile(tile)
    return game_map


def test_analyze_clientid_missing_mapper() -> None:
    game_map = _make_map_with_items([100])
    report = analyze_map_format_conversion(game_map, target_version=5, id_mapper=None)
    assert report.id_mapper_missing is True
    assert report.ok is False


def test_analyze_clientid_missing_ids() -> None:
    game_map = _make_map_with_items([100, 200, 0])
    id_mapper = IdMapper(client_to_server={300: 100}, server_to_client={100: 300})
    report = analyze_map_format_conversion(game_map, target_version=5, id_mapper=id_mapper)
    assert report.id_mapper_missing is False
    assert report.placeholder_items == 1
    assert report.ok is False
    assert report.missing_mappings == (200,)


def test_apply_map_format_version() -> None:
    game_map = _make_map_with_items([100])
    apply_map_format_version(game_map, target_version=5)
    assert game_map.header.otbm_version == 5
