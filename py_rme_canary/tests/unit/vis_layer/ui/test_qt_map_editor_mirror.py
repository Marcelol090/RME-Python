from __future__ import annotations

from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_mirror import QtMapEditorMirrorMixin


class _ActionStub:
    def __init__(self) -> None:
        self.checked = False

    def blockSignals(self, _block: bool) -> None:  # noqa: N802
        return

    def setChecked(self, checked: bool) -> None:  # noqa: N802
        self.checked = bool(checked)

    def isChecked(self) -> bool:  # noqa: N802
        return bool(self.checked)


class _StatusStub:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def showMessage(self, message: str) -> None:  # noqa: N802
        self.messages.append(str(message))


class _EditorStub(QtMapEditorMirrorMixin):
    def __init__(self) -> None:
        self.mirror_enabled = False
        self.mirror_axis = "x"
        self.mirror_axis_value = None
        self._last_hover_tile = (12, 34)
        self.act_toggle_mirror = _ActionStub()
        self.act_mirror_axis_x = _ActionStub()
        self.act_mirror_axis_y = _ActionStub()
        self.status = _StatusStub()


def test_set_mirror_axis_keeps_actions_exclusive() -> None:
    editor = _EditorStub()
    editor._set_mirror_axis("y")
    assert editor.mirror_axis == "y"
    assert editor.act_mirror_axis_y.isChecked() is True
    assert editor.act_mirror_axis_x.isChecked() is False


def test_set_mirror_axis_invalid_value_falls_back_to_x() -> None:
    editor = _EditorStub()
    editor._set_mirror_axis("invalid")
    assert editor.mirror_axis == "x"
    assert editor.act_mirror_axis_x.isChecked() is True
    assert editor.act_mirror_axis_y.isChecked() is False
