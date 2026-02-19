from __future__ import annotations

from types import SimpleNamespace

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QMessageBox

from py_rme_canary.core.data.gamemap import GameMap, MapHeader
from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_file import QtMapEditorFileMixin


class _DummyStatus:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def showMessage(self, value: str) -> None:  # noqa: N802
        self.messages.append(str(value))


class _DummyCanvas:
    def __init__(self) -> None:
        self.updates = 0

    def update(self) -> None:
        self.updates += 1


class _DummyLiveLog:
    def __init__(self) -> None:
        self.input_states: list[bool] = []

    def set_input_enabled(self, value: bool) -> None:
        self.input_states.append(bool(value))


class _Session:
    def __init__(self, *, live_client: bool = False, live_server: bool = False) -> None:
        self._live_client = bool(live_client)
        self._live_server = bool(live_server)
        self.disconnect_calls = 0
        self.stop_calls = 0

    def is_live_client(self) -> bool:
        return bool(self._live_client)

    def is_live_server(self) -> bool:
        return bool(self._live_server)

    def disconnect_live(self) -> None:
        self.disconnect_calls += 1
        self._live_client = False

    def stop_live_server(self) -> None:
        self.stop_calls += 1
        self._live_server = False


class _DummyEditor(QtMapEditorFileMixin):
    def __init__(self, session: _Session) -> None:
        self.session = session
        self.map = GameMap(header=MapHeader(otbm_version=2, width=32, height=32))
        self.brush_mgr = object()
        self.current_path = "city.otbm"
        self._current_file_path = "city.otbm"
        self._dirty = False
        self.status = _DummyStatus()
        self.canvas = _DummyCanvas()
        self.dock_live_log = _DummyLiveLog()
        self._apply_ui_state_calls = 0
        self._action_state_calls = 0
        self._window_titles: list[str] = []

    def _on_tiles_changed(self, *_a, **_k) -> None:
        return

    def apply_ui_state_to_session(self) -> None:
        self._apply_ui_state_calls += 1

    def _update_action_enabled_states(self) -> None:
        self._action_state_calls += 1

    def setWindowTitle(self, title: str) -> None:  # noqa: N802
        self._window_titles.append(str(title))


def test_close_map_cancels_when_live_close_confirmation_rejected(monkeypatch: pytest.MonkeyPatch) -> None:
    editor = _DummyEditor(_Session(live_client=True))
    created_sessions: list[object] = []

    class _StubEditorSession:
        def __init__(self, *_a, **_k) -> None:
            created_sessions.append(self)

    monkeypatch.setattr(
        "py_rme_canary.vis_layer.ui.main_window.qt_map_editor_file.EditorSession",
        _StubEditorSession,
    )
    monkeypatch.setattr(
        "py_rme_canary.vis_layer.ui.main_window.qt_map_editor_file.QMessageBox.question",
        lambda *_a, **_k: QMessageBox.StandardButton.Cancel,
    )

    editor._close_map()

    assert editor.session.disconnect_calls == 0
    assert editor.session.stop_calls == 0
    assert editor.current_path == "city.otbm"
    assert created_sessions == []
    assert editor.status.messages == []


def test_close_map_disconnects_live_client_and_resets_map(monkeypatch: pytest.MonkeyPatch) -> None:
    editor = _DummyEditor(_Session(live_client=True))
    previous_session = editor.session
    created_sessions: list[tuple[tuple[object, ...], dict[str, object]]] = []

    class _StubEditorSession:
        def __init__(self, *args, **kwargs) -> None:
            created_sessions.append((args, kwargs))

    monkeypatch.setattr(
        "py_rme_canary.vis_layer.ui.main_window.qt_map_editor_file.EditorSession",
        _StubEditorSession,
    )
    monkeypatch.setattr(
        "py_rme_canary.vis_layer.ui.main_window.qt_map_editor_file.QMessageBox.question",
        lambda *_a, **_k: QMessageBox.StandardButton.Ok,
    )

    editor._close_map()

    assert previous_session.disconnect_calls == 1
    assert editor.current_path is None
    assert editor._current_file_path is None
    assert editor._apply_ui_state_calls == 1
    assert editor.canvas.updates == 1
    assert editor.dock_live_log.input_states == [False]
    assert editor._action_state_calls >= 1
    assert editor.status.messages[-1] == "Map closed."
    assert len(created_sessions) == 1
    args, kwargs = created_sessions[0]
    assert len(args) == 2
    assert kwargs.get("on_tiles_changed") == editor._on_tiles_changed


def test_close_map_stops_live_server_when_hosting(monkeypatch: pytest.MonkeyPatch) -> None:
    editor = _DummyEditor(_Session(live_server=True))
    previous_session = editor.session
    monkeypatch.setattr(
        "py_rme_canary.vis_layer.ui.main_window.qt_map_editor_file.EditorSession",
        lambda *_a, **_k: SimpleNamespace(),
    )
    monkeypatch.setattr(
        "py_rme_canary.vis_layer.ui.main_window.qt_map_editor_file.QMessageBox.question",
        lambda *_a, **_k: QMessageBox.StandardButton.Ok,
    )

    editor._close_map()

    assert previous_session.stop_calls == 1
    assert editor.status.messages[-1] == "Map closed."
