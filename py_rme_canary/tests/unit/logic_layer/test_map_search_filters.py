from __future__ import annotations

from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.core.data.item import Item
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.logic_layer.map_search import (
    find_action_item_positions,
    find_container_item_positions,
    find_unique_item_positions,
    find_writeable_item_positions,
)


def _make_map() -> GameMap:
    game_map = GameMap(header=MapHeader(otbm_version=2, width=128, height=128))
    game_map.set_tile(Tile(x=1, y=1, z=7, items=[Item(id=1000, unique_id=9001)]))
    game_map.set_tile(Tile(x=2, y=2, z=7, items=[Item(id=1001, action_id=4500)]))
    game_map.set_tile(Tile(x=3, y=3, z=7, items=[Item(id=1987)]))  # Known container-like ID
    game_map.set_tile(Tile(x=4, y=4, z=7, items=[Item(id=1002, text="hello world")]))
    return game_map


def test_unique_and_action_filters() -> None:
    game_map = _make_map()

    unique_positions = find_unique_item_positions(game_map)
    action_positions = find_action_item_positions(game_map)

    assert [(pos.x, pos.y, pos.z) for pos in unique_positions] == [(1, 1, 7)]
    assert [(pos.x, pos.y, pos.z) for pos in action_positions] == [(2, 2, 7)]


def test_container_and_writeable_filters() -> None:
    game_map = _make_map()

    container_positions = find_container_item_positions(game_map)
    writeable_positions = find_writeable_item_positions(game_map)

    assert [(pos.x, pos.y, pos.z) for pos in container_positions] == [(3, 3, 7)]
    assert [(pos.x, pos.y, pos.z) for pos in writeable_positions] == [(4, 4, 7)]


def test_filters_respect_selection_scope() -> None:
    game_map = _make_map()
    selection_tiles = {(2, 2, 7)}

    scoped_action_positions = find_action_item_positions(game_map, selection_tiles=selection_tiles)
    scoped_unique_positions = find_unique_item_positions(game_map, selection_tiles=selection_tiles)

    assert [(pos.x, pos.y, pos.z) for pos in scoped_action_positions] == [(2, 2, 7)]
    assert scoped_unique_positions == []
