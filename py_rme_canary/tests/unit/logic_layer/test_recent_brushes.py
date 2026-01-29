from __future__ import annotations

from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.logic_layer.brush_definitions import BrushManager
from py_rme_canary.logic_layer.session.editor import EditorSession


def _make_session() -> EditorSession:
    game_map = GameMap(header=MapHeader(otbm_version=2, width=1, height=1))
    brush_mgr = BrushManager()
    return EditorSession(game_map=game_map, brush_manager=brush_mgr)


def test_recent_brushes_keep_most_recent_and_limit() -> None:
    session = _make_session()

    for sid in range(1, 26):
        session.set_selected_brush(int(sid))

    assert session.recent_brushes_max == 20
    assert len(session.recent_brushes) == 20
    assert session.recent_brushes[0] == 25
    assert session.recent_brushes[-1] == 6


def test_recent_brushes_dedupe_moves_to_front() -> None:
    session = _make_session()

    session.set_selected_brush(10)
    session.set_selected_brush(20)
    session.set_selected_brush(30)
    session.set_selected_brush(20)

    assert session.recent_brushes[:3] == [20, 30, 10]
