from __future__ import annotations

from dataclasses import dataclass

from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.core.data.houses import House
from py_rme_canary.core.data.item import Item, Position
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.core.data.towns import Town
from py_rme_canary.logic_layer.brush_definitions import BrushManager
from py_rme_canary.logic_layer.remove_items import (
    compute_clear_invalid_house_tiles,
    remove_corpses_in_map,
    remove_unreachable_tiles_in_map,
)
from py_rme_canary.logic_layer.session.action_queue import ActionType
from py_rme_canary.logic_layer.session.editor import EditorSession


@dataclass(frozen=True, slots=True)
class _FakeItemType:
    server_id: int
    attributes: dict[str, str]


@dataclass(slots=True)
class _FakeItemsXML:
    items_by_server_id: dict[int, _FakeItemType]


def _make_map(*, width: int = 1024, height: int = 1024) -> GameMap:
    return GameMap(header=MapHeader(otbm_version=2, width=int(width), height=int(height)))


def _make_session(game_map: GameMap) -> EditorSession:
    return EditorSession(game_map=game_map, brush_manager=BrushManager())


def test_remove_corpses_in_map_skips_complex_items() -> None:
    game_map = _make_map()
    game_map.set_tile(Tile(x=10, y=10, z=7, ground=Item(id=500)))
    game_map.set_tile(Tile(x=11, y=10, z=7, items=[Item(id=500, action_id=100)]))
    game_map.set_tile(Tile(x=12, y=10, z=7, items=[Item(id=501)]))

    item_types = {
        500: _FakeItemType(server_id=500, attributes={"corpseType": "blood"}),
        501: _FakeItemType(server_id=501, attributes={}),
    }
    changed, result = remove_corpses_in_map(game_map, item_types=item_types)

    assert result.removed == 1
    assert list(changed.keys()) == [(10, 10, 7)]
    assert changed[(10, 10, 7)].ground is None


def test_remove_unreachable_tiles_in_map() -> None:
    game_map = _make_map()
    game_map.set_tile(Tile(x=100, y=100, z=7, ground=Item(id=101)))
    game_map.set_tile(Tile(x=101, y=100, z=7, ground=Item(id=100)))
    game_map.set_tile(Tile(x=500, y=500, z=7, ground=Item(id=100)))

    item_types = {
        100: _FakeItemType(server_id=100, attributes={"blockSolid": "1"}),
        101: _FakeItemType(server_id=101, attributes={}),
    }
    changed, result = remove_unreachable_tiles_in_map(game_map, item_types=item_types)

    assert result.removed == 1
    assert (500, 500, 7) in changed
    assert (101, 100, 7) not in changed


def test_compute_clear_invalid_house_tiles() -> None:
    game_map = _make_map()
    game_map.towns[1] = Town(id=1, name="Thais", temple_position=Position(x=100, y=100, z=7))
    game_map.houses[10] = House(id=10, name="Valid", townid=1)
    game_map.houses[20] = House(id=20, name="InvalidTown", townid=99)

    game_map.set_tile(Tile(x=20, y=20, z=7, house_id=10))
    game_map.set_tile(Tile(x=21, y=20, z=7, house_id=20))
    game_map.set_tile(Tile(x=22, y=20, z=7, house_id=30))

    valid_houses, changed_tiles, result = compute_clear_invalid_house_tiles(game_map)

    assert set(valid_houses) == {10}
    assert result.houses_removed == 1
    assert result.tile_refs_cleared == 2
    assert changed_tiles[(21, 20, 7)].house_id is None
    assert changed_tiles[(22, 20, 7)].house_id is None


def test_session_clear_invalid_house_tiles_is_undoable() -> None:
    game_map = _make_map()
    game_map.towns[1] = Town(id=1, name="Carlin", temple_position=Position(x=50, y=50, z=7))
    game_map.houses[10] = House(id=10, name="Valid", townid=1)
    game_map.houses[20] = House(id=20, name="InvalidTown", townid=99)
    game_map.set_tile(Tile(x=30, y=30, z=7, house_id=20))

    session = _make_session(game_map)
    result, action = session.clear_invalid_house_tiles()

    assert action is not None
    assert result.houses_removed == 1
    assert result.tile_refs_cleared == 1
    assert set(game_map.houses) == {10}
    assert game_map.get_tile(30, 30, 7).house_id is None
    latest = session.action_queue.latest()
    assert latest is not None
    assert latest.type == ActionType.CLEAR_INVALID_HOUSE_TILES

    session.undo()
    assert set(game_map.houses) == {10, 20}
    assert game_map.get_tile(30, 30, 7).house_id == 20

    session.redo()
    assert set(game_map.houses) == {10}
    assert game_map.get_tile(30, 30, 7).house_id is None


def test_session_remove_corpses_and_unreachable_tiles() -> None:
    game_map = _make_map()
    game_map.set_tile(Tile(x=10, y=10, z=7, ground=Item(id=500)))
    game_map.set_tile(Tile(x=11, y=10, z=7, items=[Item(id=500, action_id=9)]))
    game_map.set_tile(Tile(x=100, y=100, z=7, ground=Item(id=101)))
    game_map.set_tile(Tile(x=500, y=500, z=7, ground=Item(id=100)))

    session = _make_session(game_map)
    session._items_xml = _FakeItemsXML(
        items_by_server_id={
            100: _FakeItemType(server_id=100, attributes={"blockSolid": "1"}),
            101: _FakeItemType(server_id=101, attributes={"blockSolid": "0"}),
            500: _FakeItemType(server_id=500, attributes={"corpseType": "blood"}),
        }
    )

    removed_corpses, corpses_action = session.remove_corpses()
    assert removed_corpses == 1
    assert corpses_action is not None
    assert game_map.get_tile(10, 10, 7).ground is None
    assert len(game_map.get_tile(11, 10, 7).items) == 1
    latest = session.action_queue.latest()
    assert latest is not None
    assert latest.type == ActionType.REMOVE_CORPSES

    removed_unreachable, unreachable_action = session.remove_unreachable_tiles()
    assert removed_unreachable == 1
    assert unreachable_action is not None
    assert game_map.get_tile(500, 500, 7) is None
    latest = session.action_queue.latest()
    assert latest is not None
    assert latest.type == ActionType.REMOVE_UNREACHABLE_TILES

    session.undo()
    assert game_map.get_tile(500, 500, 7) is not None
