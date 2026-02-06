from __future__ import annotations

import json
from pathlib import Path

from py_rme_canary.logic_layer.brush_definitions import BrushManager


def _write_brushes_json(tmp_path: Path) -> Path:
    payload = {
        "brushes": [
            {
                "name": "Stone Ground",
                "server_id": 100,
                "type": "ground",
                "borders": {"SOLITARY": 101},
                "transitions": [],
            }
        ]
    }
    path = tmp_path / "brushes.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_set_border_override_updates_family_index(tmp_path: Path) -> None:
    brushes_path = _write_brushes_json(tmp_path)
    mgr = BrushManager.from_json_file(str(brushes_path))

    assert mgr.get_brush_any(101) is not None

    changed = mgr.set_border_override(100, "end_north", 202)
    assert changed is True

    brush = mgr.get_brush(100)
    assert brush is not None
    assert brush.get_border("END_NORTH") == 202

    owner = mgr.get_brush_any(202)
    assert owner is not None
    assert int(owner.server_id) == 100


def test_border_overrides_save_and_load(tmp_path: Path) -> None:
    brushes_path = _write_brushes_json(tmp_path)
    overrides_path = tmp_path / "brushes.overrides.json"

    mgr = BrushManager.from_json_file(str(brushes_path))
    assert mgr.set_border_override(100, "END_SOUTH", 303) is True

    saved_path = mgr.save_border_overrides_file(str(overrides_path))
    assert saved_path == overrides_path
    assert overrides_path.exists()

    payload = json.loads(overrides_path.read_text(encoding="utf-8"))
    assert payload["borders"]["100"]["END_SOUTH"] == 303

    mgr_reloaded = BrushManager.from_json_file(str(brushes_path))
    changed = mgr_reloaded.load_border_overrides_file(str(overrides_path))
    assert changed == 1

    brush = mgr_reloaded.get_brush(100)
    assert brush is not None
    assert brush.get_border("END_SOUTH") == 303
