import pytest

pytest.importorskip("PyQt6.QtWidgets")

from py_rme_canary.tests.ui._editor_test_utils import show_editor_window, stabilize_editor_for_headless_tests
from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor  # noqa: E402


@pytest.fixture
def editor(qapp, qtbot):
    window = QtMapEditor()
    stabilize_editor_for_headless_tests(window)
    qtbot.addWidget(window)
    show_editor_window(qtbot, window)
    return window


def test_selection_mode_action_trigger_updates_editor_state(editor, qtbot):
    editor.act_selection_mode.setChecked(False)
    editor.act_selection_mode.trigger()
    qtbot.wait(5)
    assert editor.selection_mode is True


def test_selection_mode_toggle_cancels_pending_canvas_paint_gesture(editor, qtbot, monkeypatch):
    canvas = editor.canvas
    canvas._mouse_down = True
    canvas._selection_dragging = True

    calls = {"cancel_gesture": 0}
    session_type = type(editor.session)
    original_cancel = session_type.cancel_gesture

    def _wrapped_cancel_gesture(self) -> None:
        calls["cancel_gesture"] += 1
        original_cancel(self)

    monkeypatch.setattr(session_type, "cancel_gesture", _wrapped_cancel_gesture)

    editor.act_selection_mode.setChecked(True)
    editor._toggle_selection_mode()
    qtbot.wait(5)

    assert editor.selection_mode is True
    assert calls["cancel_gesture"] == 1
    assert canvas._mouse_down is False
    assert canvas._selection_dragging is False
