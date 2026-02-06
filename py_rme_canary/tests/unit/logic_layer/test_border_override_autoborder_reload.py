from __future__ import annotations

import json
from pathlib import Path

from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.core.data.item import Item
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.logic_layer.borders.processor import AutoBorderProcessor
from py_rme_canary.logic_layer.brush_definitions import BrushManager


def _write_wall_brush(tmp_path: Path) -> Path:
    payload = {
        "brushes": [
            {
                "name": "Wall Brush",
                "server_id": 100,
                "type": "wall",
                "borders": {
                    "SOLITARY": 100,
                    "END_WEST": 101,
                    "END_EAST": 102,
                },
                "transitions": [],
            }
        ]
    }
    path = tmp_path / "brushes.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _make_map() -> GameMap:
    game_map = GameMap(header=MapHeader(otbm_version=2, width=8, height=8))
    game_map.set_tile(Tile(x=0, y=0, z=7, items=[Item(id=100)]))
    game_map.set_tile(Tile(x=1, y=0, z=7, items=[Item(id=100)]))
    return game_map


def test_runtime_border_override_changes_autoborder_result(tmp_path: Path) -> None:
    mgr = BrushManager.from_json_file(str(_write_wall_brush(tmp_path)))

    game_map = _make_map()
    AutoBorderProcessor(game_map, mgr).update_positions([(0, 0, 7)], brush_id=100)

    first_pass = game_map.get_tile(0, 0, 7)
    assert first_pass is not None
    assert first_pass.items
    assert int(first_pass.items[-1].id) == 101

    assert mgr.set_border_override(100, "END_WEST", 777) is True

    game_map = _make_map()
    AutoBorderProcessor(game_map, mgr).update_positions([(0, 0, 7)], brush_id=100)

    second_pass = game_map.get_tile(0, 0, 7)
    assert second_pass is not None
    assert second_pass.items
    assert int(second_pass.items[-1].id) == 777
