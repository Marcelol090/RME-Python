import pytest

pytest.importorskip("PyQt6.QtWidgets")

from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor  # noqa: E402


@pytest.fixture
def editor(qapp, qtbot):
    window = QtMapEditor()
    qtbot.addWidget(window)
    with qtbot.waitExposed(window, timeout=5000):
        window.show()
    return window


def test_backend_brush_size_updates_toolbar(editor, qtbot):
    editor._set_brush_size(5)
    qtbot.wait(5)
    assert getattr(editor.brush_toolbar, "_size", 0) == 5


def test_backend_brush_shape_updates_toolbar(editor, qtbot):
    editor._set_brush_shape("circle")
    qtbot.wait(5)
    assert getattr(editor.brush_toolbar, "_shape", "") == "circle"
    assert editor.act_brush_shape_circle.isChecked() is True
    assert editor.act_brush_shape_square.isChecked() is False


def test_menu_brush_actions_update_toolbar_and_backend(editor, qtbot):
    before = int(getattr(editor, "brush_size", 1) or 1)
    editor.act_brush_size_increase.trigger()
    qtbot.wait(5)
    after = int(getattr(editor, "brush_size", 1) or 1)
    assert after == min(11, before + 1)
    assert getattr(editor.brush_toolbar, "_size", 0) == after

    editor.act_brush_shape_square.trigger()
    qtbot.wait(5)
    assert getattr(editor, "brush_shape", "") == "square"
    assert getattr(editor.brush_toolbar, "_shape", "") == "square"


def test_brush_size_actions_follow_bounds(editor, qtbot):
    editor._set_brush_size(1)
    qtbot.wait(5)
    assert editor.act_brush_size_decrease.isEnabled() is False
    assert editor.act_brush_size_increase.isEnabled() is True

    editor._set_brush_size(11)
    qtbot.wait(5)
    assert editor.act_brush_size_decrease.isEnabled() is True
    assert editor.act_brush_size_increase.isEnabled() is False


def test_brush_offset_cache_updates_with_size_and_shape(editor, qtbot):
    editor._set_brush_size(5)
    editor._set_brush_shape("circle")
    qtbot.wait(5)

    offsets = editor._brush_offsets()
    border_offsets = editor._brush_border_offsets()

    assert isinstance(offsets, tuple)
    assert isinstance(border_offsets, tuple)
    assert len(offsets) > 0
    assert len(border_offsets) > 0


def test_toolbar_automagic_updates_action(editor, qtbot):
    editor.brush_toolbar.set_automagic(False)
    editor.brush_toolbar.automagic_changed.emit(False)
    qtbot.wait(5)
    assert editor.act_automagic.isChecked() is False
