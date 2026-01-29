from __future__ import annotations

from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.logic_layer.brush_definitions import (
    BrushDefinition,
    BrushManager,
    TableBrushSpec,
    TableItemChoice,
)
from py_rme_canary.logic_layer.transactional_brush import HistoryManager, TransactionalBrushStroke


def _make_map() -> GameMap:
    return GameMap(header=MapHeader(otbm_version=2, width=6, height=6))


def _make_table_spec(server_id: int) -> TableBrushSpec:
    return TableBrushSpec(
        name="test table",
        server_id=int(server_id),
        items_by_alignment={
            "north": (TableItemChoice(id=101, chance=10),),
            "south": (TableItemChoice(id=102, chance=10),),
            "east": (TableItemChoice(id=103, chance=10),),
            "west": (TableItemChoice(id=104, chance=10),),
            "horizontal": (TableItemChoice(id=105, chance=10),),
            "vertical": (TableItemChoice(id=106, chance=10),),
            "alone": (TableItemChoice(id=107, chance=10),),
        },
    )


def _make_table_brush(server_id: int) -> BrushDefinition:
    spec = _make_table_spec(server_id)
    return BrushDefinition(
        name="table brush",
        server_id=int(server_id),
        brush_type="table",
        borders={},
        transition_borders={},
        table_spec=spec,
    )


def _make_manager(brush_def: BrushDefinition) -> BrushManager:
    mgr = BrushManager()
    mgr._brushes[int(brush_def.server_id)] = brush_def
    for fid in brush_def.family_ids:
        mgr._family_index.setdefault(int(fid), int(brush_def.server_id))
    return mgr


def _tile_item_id(game_map: GameMap, x: int, y: int, z: int) -> int:
    tile = game_map.get_tile(int(x), int(y), int(z))
    assert tile is not None
    assert tile.items
    return int(tile.items[0].id)


def test_table_brush_single_tile_uses_alone_alignment() -> None:
    game_map = _make_map()
    brush_def = _make_table_brush(200)
    mgr = _make_manager(brush_def)
    history = HistoryManager()

    stroke = TransactionalBrushStroke(game_map=game_map, brush_manager=mgr, history=history)
    stroke.begin(x=2, y=2, z=7, selected_server_id=200)
    stroke.end()

    assert _tile_item_id(game_map, 2, 2, 7) == 107


def test_table_brush_row_aligns_edges_and_center() -> None:
    game_map = _make_map()
    brush_def = _make_table_brush(300)
    mgr = _make_manager(brush_def)
    history = HistoryManager()

    stroke = TransactionalBrushStroke(game_map=game_map, brush_manager=mgr, history=history)
    stroke.begin(x=1, y=2, z=7, selected_server_id=300)
    stroke.paint(x=2, y=2, z=7, selected_server_id=300)
    stroke.paint(x=3, y=2, z=7, selected_server_id=300)
    stroke.end()

    assert _tile_item_id(game_map, 1, 2, 7) == 104
    assert _tile_item_id(game_map, 2, 2, 7) == 105
    assert _tile_item_id(game_map, 3, 2, 7) == 103
