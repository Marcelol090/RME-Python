from __future__ import annotations

from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.core.data.item import Item
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.logic_layer.session.selection import SelectionApplyMode, SelectionManager
from py_rme_canary.logic_layer.session.selection_modes import SelectionDepthMode


def _map_with_tiles() -> GameMap:
    game_map = GameMap(header=MapHeader(otbm_version=2, width=10, height=10))
    for z in (7, 8, 9):
        game_map.set_tile(Tile(x=1, y=1, z=z, ground=Item(id=100)))
    return game_map


def test_selection_default_depth_mode_is_compensate() -> None:
    selection = SelectionManager(game_map=_map_with_tiles())
    assert selection.selection_mode == SelectionDepthMode.COMPENSATE


def test_selection_visible_mode_filters_floors() -> None:
    selection = SelectionManager(game_map=_map_with_tiles())
    selection.selection_mode = SelectionDepthMode.VISIBLE
    selection.begin_box_selection(x=1, y=1, z=7)
    selection.update_box_selection(x=1, y=1, z=9)
    selection.finish_box_selection(
        mode=SelectionApplyMode.REPLACE,
        visible_floors=[7, 9],
    )
    assert selection.get_selection_tiles() == {(1, 1, 7), (1, 1, 9)}
