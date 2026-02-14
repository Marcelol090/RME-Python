from __future__ import annotations

import pytest

pytest.importorskip("PyQt6")

from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_file import QtMapEditorFileMixin


class _DummyEvent:
    def __init__(self) -> None:
        self.ignored = 0

    def ignore(self) -> None:
        self.ignored += 1


class _DummyEditor(QtMapEditorFileMixin):
    def __init__(self) -> None:
        self._live_close_confirmed_for_exit = False
        self.confirm_calls: list[bool] = []
        self.confirm_result = True
        self.offline_calls = 0

    def _confirm_live_session_close(self, *, for_app_exit: bool = False) -> bool:
        self.confirm_calls.append(bool(for_app_exit))
        return bool(self.confirm_result)

    def _friends_mark_offline(self) -> None:
        self.offline_calls += 1


def test_window_close_request_blocks_when_live_confirmation_fails() -> None:
    editor = _DummyEditor()
    editor.confirm_result = False
    event = _DummyEvent()

    allowed = editor._handle_window_close_request(event)

    assert allowed is False
    assert editor.confirm_calls == [True]
    assert editor.offline_calls == 0
    assert event.ignored == 1


def test_window_close_request_uses_skip_flag_to_avoid_double_prompt() -> None:
    editor = _DummyEditor()
    editor._live_close_confirmed_for_exit = True
    event = _DummyEvent()

    allowed = editor._handle_window_close_request(event)

    assert allowed is True
    assert editor.confirm_calls == []
    assert editor.offline_calls == 1
    assert editor._live_close_confirmed_for_exit is False
    assert event.ignored == 0


def test_window_close_request_confirms_and_marks_offline_when_allowed() -> None:
    editor = _DummyEditor()
    editor.confirm_result = True
    event = _DummyEvent()

    allowed = editor._handle_window_close_request(event)

    assert allowed is True
    assert editor.confirm_calls == [True]
    assert editor.offline_calls == 1
    assert event.ignored == 0
