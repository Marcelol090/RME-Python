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


class _EditorStub(QtMapEditorBrushesMixin):
    def __init__(self) -> None:
        self.brush_shape = "square"
        self.shape_square = _ButtonStub()
        self.shape_circle = _ButtonStub()


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
