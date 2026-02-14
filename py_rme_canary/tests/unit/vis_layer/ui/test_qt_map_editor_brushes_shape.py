from __future__ import annotations

from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_brushes import QtMapEditorBrushesMixin


class _ButtonStub:
    def __init__(self) -> None:
        self.checked = False

    def blockSignals(self, _block: bool) -> None:  # noqa: N802
        return

    def setChecked(self, checked: bool) -> None:  # noqa: N802
        self.checked = bool(checked)

    def isChecked(self) -> bool:  # noqa: N802
        return bool(self.checked)


class _ActionStub(_ButtonStub):
    def __init__(self, data: int | None = None) -> None:
        super().__init__()
        self._data = data

    def data(self):  # noqa: ANN201
        return self._data


class _EditorStub(QtMapEditorBrushesMixin):
    def __init__(self) -> None:
        self.brush_size = 1
        self.brush_shape = "square"
        self.shape_square = _ButtonStub()
        self.shape_circle = _ButtonStub()
        self.act_brush_shape_square = _ActionStub()
        self.act_brush_shape_circle = _ActionStub()
        self.act_brush_size_actions = [
            _ActionStub(1),
            _ActionStub(3),
            _ActionStub(5),
        ]


def test_set_brush_shape_keeps_square_and_circle_exclusive() -> None:
    editor = _EditorStub()
    editor._set_brush_shape("circle")
    assert editor.brush_shape == "circle"
    assert editor.shape_circle.isChecked() is True
    assert editor.shape_square.isChecked() is False


def test_set_brush_shape_invalid_value_falls_back_to_square() -> None:
    editor = _EditorStub()
    editor._set_brush_shape("triangle")
    assert editor.brush_shape == "square"
    assert editor.shape_square.isChecked() is True
    assert editor.shape_circle.isChecked() is False
    assert editor.act_brush_shape_square.isChecked() is True
    assert editor.act_brush_shape_circle.isChecked() is False


def test_set_brush_size_updates_menu_actions() -> None:
    editor = _EditorStub()
    editor._set_brush_size(5)
    checked = [action.isChecked() for action in editor.act_brush_size_actions]
    assert checked == [False, False, True]
    assert hasattr(editor, "_brush_draw_offsets")
    assert hasattr(editor, "_brush_border_offsets")
    assert (5, 5) in editor._brush_draw_offsets
    assert (6, 6) in editor._brush_border_offsets


def test_set_brush_shape_rebuilds_cached_offsets() -> None:
    editor = _EditorStub()
    editor._set_brush_size(1)
    editor._set_brush_shape("circle")
    assert (1, 1) not in editor._brush_draw_offsets
    editor._set_brush_shape("square")
    assert (1, 1) in editor._brush_draw_offsets
