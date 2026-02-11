from __future__ import annotations

import sys
import types
from types import SimpleNamespace

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtWidgets import QMessageBox

_find_item_stub = types.ModuleType("py_rme_canary.vis_layer.ui.main_window.find_item")
_find_item_stub.open_find_item = lambda *_a, **_k: None
sys.modules.setdefault("py_rme_canary.vis_layer.ui.main_window.find_item", _find_item_stub)


def _load_dialogs_mixin():
    from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_dialogs import QtMapEditorDialogsMixin

    return QtMapEditorDialogsMixin


QtMapEditorDialogsMixin = _load_dialogs_mixin()


class _DummyStatus:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def showMessage(self, value: str) -> None:  # noqa: N802 - Qt naming parity
        self.messages.append(str(value))


class _DummyCanvas:
    def __init__(self) -> None:
        self.updates = 0

    def update(self) -> None:
        self.updates += 1


class _DummyEditor(QtMapEditorDialogsMixin):
    def __init__(self) -> None:
        self.status = _DummyStatus()
        self.canvas = _DummyCanvas()
        self.quick_replace_source_id = None
        self.quick_replace_target_id = None
        self.session = SimpleNamespace(clear_invalid_tiles=lambda selection_only=False: (0, None))
        self._action_state_updates = 0

    def _update_action_enabled_states(self) -> None:
        self._action_state_updates += 1


def test_map_cleanup_cancel_does_nothing(monkeypatch: pytest.MonkeyPatch) -> None:
    editor = _DummyEditor()
    calls = {"helper": 0, "session": 0}

    def _helper(*, confirm: bool = True) -> None:
        calls["helper"] += 1

    def _session_cleanup(*, selection_only: bool = False):
        calls["session"] += 1
        return (5, object())

    editor._map_clear_invalid_tiles = _helper  # type: ignore[attr-defined]
    editor.session = SimpleNamespace(clear_invalid_tiles=_session_cleanup)

    monkeypatch.setattr(
        "py_rme_canary.vis_layer.ui.main_window.qt_map_editor_dialogs.QMessageBox.question",
        lambda *_a, **_k: QMessageBox.StandardButton.No,
    )

    editor._map_cleanup()

    assert calls == {"helper": 0, "session": 0}
    assert editor.canvas.updates == 0
    assert editor.status.messages == []


def test_map_cleanup_delegates_to_map_clear_invalid_tiles_when_available(monkeypatch: pytest.MonkeyPatch) -> None:
    editor = _DummyEditor()
    helper_calls: list[bool] = []

    def _helper(*, confirm: bool = True) -> None:
        helper_calls.append(bool(confirm))

    editor._map_clear_invalid_tiles = _helper  # type: ignore[attr-defined]

    monkeypatch.setattr(
        "py_rme_canary.vis_layer.ui.main_window.qt_map_editor_dialogs.QMessageBox.question",
        lambda *_a, **_k: QMessageBox.StandardButton.Yes,
    )

    editor._map_cleanup()

    assert helper_calls == [False]


def test_map_cleanup_fallback_uses_session_and_no_id_mapper_needed(monkeypatch: pytest.MonkeyPatch) -> None:
    editor = _DummyEditor()
    calls: list[bool] = []

    def _session_cleanup(*, selection_only: bool = False):
        calls.append(bool(selection_only))
        return (7, object())

    editor.session = SimpleNamespace(clear_invalid_tiles=_session_cleanup)
    editor.id_mapper = None

    monkeypatch.setattr(
        "py_rme_canary.vis_layer.ui.main_window.qt_map_editor_dialogs.QMessageBox.question",
        lambda *_a, **_k: QMessageBox.StandardButton.Yes,
    )

    editor._map_cleanup()

    assert calls == [False]
    assert editor.canvas.updates == 1
    assert editor._action_state_updates == 1
    assert any("removed 7" in msg for msg in editor.status.messages)


def test_map_cleanup_fallback_reports_no_changes(monkeypatch: pytest.MonkeyPatch) -> None:
    editor = _DummyEditor()
    editor.session = SimpleNamespace(clear_invalid_tiles=lambda selection_only=False: (0, None))

    monkeypatch.setattr(
        "py_rme_canary.vis_layer.ui.main_window.qt_map_editor_dialogs.QMessageBox.question",
        lambda *_a, **_k: QMessageBox.StandardButton.Yes,
    )

    editor._map_cleanup()

    assert editor.canvas.updates == 0
    assert editor._action_state_updates == 0
    assert editor.status.messages[-1] == "Map cleanup: no changes"
