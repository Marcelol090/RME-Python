from __future__ import annotations

import pytest

pytest.importorskip("PyQt6")

from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.core.data.item import Item, Position
from py_rme_canary.core.data.spawns import MonsterSpawnArea, MonsterSpawnEntry
from py_rme_canary.core.data.tile import Tile
from py_rme_canary.vis_layer.ui.dialogs.map_validator_dialog import ValidationWorker


def _build_invalid_map() -> GameMap:
    game_map = GameMap(
        header=MapHeader(
            otbm_version=2,
            width=32,
            height=32,
        )
    )

    # House reference that does not exist + invalid item id.
    game_map.set_tile(
        Tile(
            x=1,
            y=1,
            z=7,
            items=[Item(id=0)],
            house_id=99,
        )
    )

    # Out-of-bounds waypoint.
    game_map.waypoints["bad_wp"] = Position(x=500, y=500, z=7)

    # Invalid spawn area.
    game_map.monster_spawns = [
        MonsterSpawnArea(
            center=Position(x=500, y=500, z=7),
            radius=-1,
            monsters=(MonsterSpawnEntry(name="", dx=0, dy=0),),
        )
    ]

    return game_map


def test_validation_worker_collects_real_issues() -> None:
    worker = ValidationWorker(_build_invalid_map())
    captured: dict[str, list[dict[str, str]]] = {}
    worker.finished.connect(lambda issues: captured.setdefault("issues", issues))

    worker.run()

    issues = captured["issues"]
    assert any("spawn" in issue["message"].lower() for issue in issues)
    assert any("house" in issue["message"].lower() for issue in issues)
    assert any("waypoint" in issue["message"].lower() for issue in issues)
    assert any("invalid or unknown IDs" in issue["message"] for issue in issues)


def test_validation_worker_handles_missing_map() -> None:
    worker = ValidationWorker(None)
    captured: dict[str, list[dict[str, str]]] = {}
    worker.finished.connect(lambda issues: captured.setdefault("issues", issues))

    worker.run()

    assert captured["issues"][0]["message"] == "No map loaded"
