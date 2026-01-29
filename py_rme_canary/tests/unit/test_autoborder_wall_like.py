from __future__ import annotations

from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.core.data.item import Item
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.logic_layer.borders.processor import AutoBorderProcessor
from py_rme_canary.logic_layer.brush_definitions import BrushDefinition


class _DummyBrushManager:
    def __init__(self, brush_def: BrushDefinition) -> None:
        self._brush_def = brush_def

    def get_brush(self, _server_id: int) -> BrushDefinition | None:
        return self._brush_def


def _make_map() -> GameMap:
    return GameMap(header=MapHeader(otbm_version=2, width=10, height=10))


def _seed_tile(game_map: GameMap, x: int, y: int, z: int, items: list[Item]) -> None:
    game_map.set_tile(Tile(x=int(x), y=int(y), z=int(z), items=list(items)))


def _make_wall_like_brush(brush_type: str) -> BrushDefinition:
    return BrushDefinition(
        name=f"{brush_type} brush",
        server_id=100,
        brush_type=str(brush_type),
        borders={
            "EAST": 101,
            "WEST": 102,
            "SOLITARY": 100,
        },
    )


def test_carpet_updates_neighbors_and_keeps_top_items() -> None:
    game_map = _make_map()
    brush_def = _make_wall_like_brush("carpet")
    mgr = _DummyBrushManager(brush_def)

    _seed_tile(game_map, 0, 0, 7, [Item(id=100)])
    _seed_tile(game_map, 1, 0, 7, [Item(id=999), Item(id=100)])

    AutoBorderProcessor(game_map, mgr).update_positions([(0, 0, 7)], brush_id=100)

    left = game_map.get_tile(0, 0, 7)
    right = game_map.get_tile(1, 0, 7)
    assert left is not None
    assert right is not None
    assert [int(it.id) for it in left.items] == [101]
    assert [int(it.id) for it in right.items] == [102, 999]


def test_table_updates_neighbors_and_stacks_on_top() -> None:
    game_map = _make_map()
    brush_def = _make_wall_like_brush("table")
    mgr = _DummyBrushManager(brush_def)

    _seed_tile(game_map, 0, 0, 7, [Item(id=100)])
    _seed_tile(game_map, 1, 0, 7, [Item(id=999), Item(id=100)])

    AutoBorderProcessor(game_map, mgr).update_positions([(0, 0, 7)], brush_id=100)

    left = game_map.get_tile(0, 0, 7)
    right = game_map.get_tile(1, 0, 7)
    assert left is not None
    assert right is not None
    assert [int(it.id) for it in left.items] == [101]
    assert [int(it.id) for it in right.items] == [999, 102]
