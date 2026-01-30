from __future__ import annotations

from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.logic_layer.brush_definitions import (
    BrushDefinition,
    BrushManager,
    CarpetBrushSpec,
    CarpetItemChoice,
)
from py_rme_canary.logic_layer.transactional_brush import HistoryManager, TransactionalBrushStroke


def _make_map() -> GameMap:
    return GameMap(header=MapHeader(otbm_version=2, width=6, height=6))


def _make_carpet_spec(server_id: int) -> CarpetBrushSpec:
    return CarpetBrushSpec(
        name="test carpet",
        server_id=int(server_id),
        items_by_alignment={
            "center": (CarpetItemChoice(id=201, chance=10),),
            "northeast": (CarpetItemChoice(id=202, chance=10),),
        },
    )


def _make_carpet_brush(server_id: int) -> BrushDefinition:
    spec = _make_carpet_spec(server_id)
    return BrushDefinition(
        name="carpet brush",
        server_id=int(server_id),
        brush_type="carpet",
        borders={},
        transition_borders={},
        carpet_spec=spec,
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


def test_carpet_brush_single_tile_uses_center_alignment() -> None:
    game_map = _make_map()
    brush_def = _make_carpet_brush(400)
    mgr = _make_manager(brush_def)
    history = HistoryManager()

    stroke = TransactionalBrushStroke(game_map=game_map, brush_manager=mgr, history=history)
    stroke.begin(x=2, y=2, z=7, selected_server_id=400)
    stroke.end()

    assert _tile_item_id(game_map, 2, 2, 7) == 201


def test_carpet_brush_northeast_alignment() -> None:
    game_map = _make_map()
    brush_def = _make_carpet_brush(500)
    mgr = _make_manager(brush_def)
    history = HistoryManager()

    stroke = TransactionalBrushStroke(game_map=game_map, brush_manager=mgr, history=history)
    stroke.begin(x=2, y=2, z=7, selected_server_id=500)
    stroke.paint(x=2, y=1, z=7, selected_server_id=500)
    stroke.paint(x=3, y=2, z=7, selected_server_id=500)
    stroke.end()

    assert _tile_item_id(game_map, 2, 2, 7) == 202
