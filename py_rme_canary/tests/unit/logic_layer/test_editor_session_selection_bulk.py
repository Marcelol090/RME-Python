from __future__ import annotations

from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.core.data.item import Item
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.logic_layer.brush_definitions import BrushManager
from py_rme_canary.logic_layer.session.editor import EditorSession


def _make_map() -> GameMap:
    game_map = GameMap(header=MapHeader(otbm_version=2, width=32, height=32))
    game_map.set_tile(Tile(x=10, y=10, z=7, ground=Item(id=100)))
    return game_map


def test_set_selection_tiles_filters_empty_tiles_by_default() -> None:
    session = EditorSession(game_map=_make_map(), brush_manager=BrushManager())

    applied = session.set_selection_tiles([(10, 10, 7), (11, 11, 7)])

    assert applied == {(10, 10, 7)}
    assert session.get_selection_tiles() == {(10, 10, 7)}


def test_set_selection_tiles_can_keep_empty_tiles_when_requested() -> None:
    session = EditorSession(game_map=_make_map(), brush_manager=BrushManager())

    applied = session.set_selection_tiles([(10, 10, 7), (11, 11, 7)], filter_nonempty=False)

    assert applied == {(10, 10, 7), (11, 11, 7)}
    assert session.get_selection_tiles() == {(10, 10, 7), (11, 11, 7)}
