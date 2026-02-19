from __future__ import annotations

from dataclasses import dataclass

from py_rme_canary.logic_layer.hotkey_manager import Hotkey, HotkeyManager
from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_brushes import QtMapEditorBrushesMixin


class _StatusStub:
    def __init__(self) -> None:
        self.messages: list[str] = []

    def showMessage(self, msg: str, _timeout: int = 0) -> None:  # noqa: N802
        self.messages.append(str(msg))


class _SelectionActionStub:
    def __init__(self, editor: _EditorStub, *, checked: bool) -> None:
        self._editor = editor
        self._checked = bool(checked)

    def isChecked(self) -> bool:  # noqa: N802
        return bool(self._checked)

    def trigger(self) -> None:
        self._checked = not bool(self._checked)
        self._editor.selection_mode = bool(self._checked)


class _BrushEntryStub:
    def __init__(self, value: int) -> None:
        self._value = int(value)

    def value(self) -> int:  # noqa: D401
        return int(self._value)

    def setValue(self, value: int) -> None:  # noqa: N802
        self._value = int(value)

    def blockSignals(self, _block: bool) -> None:  # noqa: N802
        return


class _LabelStub:
    def __init__(self) -> None:
        self.text = ""

    def setText(self, text: str) -> None:  # noqa: N802
        self.text = str(text)


class _CanvasStub:
    def __init__(self) -> None:
        self.updates = 0

    def width(self) -> int:
        return 320

    def height(self) -> int:
        return 320

    def update(self) -> None:
        self.updates += 1


@dataclass
class _BrushDef:
    server_id: int
    name: str
    brush_type: str = "terrain"


class _BrushManagerStub:
    def __init__(self) -> None:
        self._brushes = {
            100: _BrushDef(server_id=100, name="Grass"),
            200: _BrushDef(server_id=200, name="Stone Wall"),
        }

    def get_brush(self, sid: int):  # noqa: ANN201
        return self._brushes.get(int(sid))

    def get_brush_any(self, sid: int):  # noqa: ANN201
        return self.get_brush(int(sid))


class _SessionStub:
    def __init__(self) -> None:
        self.selected: list[int] = []

    def set_selected_brush(self, sid: int) -> None:
        self.selected.append(int(sid))


class _ViewportStub:
    def __init__(self) -> None:
        self.origin_x = 10
        self.origin_y = 20
        self.z = 7
        self.tile_px = 32


class _EditorStub(QtMapEditorBrushesMixin):
    def __init__(self) -> None:
        self.status = _StatusStub()
        self.session = _SessionStub()
        self.hotkey_manager = HotkeyManager()
        self.brush_mgr = _BrushManagerStub()
        self.brush_id_entry = _BrushEntryStub(100)
        self.brush_label = _LabelStub()
        self.canvas = _CanvasStub()
        self.viewport = _ViewportStub()
        self.selection_mode = False
        self.map = type("MapStub", (), {"header": type("Header", (), {"width": 512, "height": 512})()})()
        self.centered: tuple[int, int, int, bool] | None = None
        self.act_selection_mode = _SelectionActionStub(self, checked=False)

    def center_view_on(self, x: int, y: int, z: int, *, push_history: bool = True) -> None:
        self.centered = (int(x), int(y), int(z), bool(push_history))


def test_assign_hotkey_in_drawing_mode_stores_brush_name() -> None:
    editor = _EditorStub()
    editor.selection_mode = False
    editor._assign_hotkey(1)

    hk = editor.hotkey_manager.get_hotkey(1)
    assert hk.is_brush is True
    assert hk.brush_name == "Grass"
    assert editor.status.messages[-1].startswith("Set hotkey 1: brush")


def test_assign_hotkey_in_selection_mode_stores_view_center_position() -> None:
    editor = _EditorStub()
    editor.selection_mode = True
    editor.act_selection_mode = _SelectionActionStub(editor, checked=True)
    editor._assign_hotkey(2)

    hk = editor.hotkey_manager.get_hotkey(2)
    assert hk.is_position is True
    assert hk.position.x == 15
    assert hk.position.y == 25
    assert hk.position.z == 7


def test_activate_brush_hotkey_switches_to_drawing_mode_and_selects_brush() -> None:
    editor = _EditorStub()
    editor.selection_mode = True
    editor.act_selection_mode = _SelectionActionStub(editor, checked=True)
    editor.hotkey_manager.set_hotkey(3, Hotkey.from_brush("Stone Wall"))

    editor._activate_hotkey(3)

    assert editor.selection_mode is False
    assert editor.brush_id_entry.value() == 200
    assert editor.session.selected[-1] == 200
    assert editor.status.messages[-1] == "Used hotkey 3"


def test_activate_position_hotkey_switches_to_selection_and_centers_view() -> None:
    editor = _EditorStub()
    editor.selection_mode = False
    editor.act_selection_mode = _SelectionActionStub(editor, checked=False)
    editor.hotkey_manager.set_hotkey(4, Hotkey.from_position(100, 140, 5))

    editor._activate_hotkey(4)

    assert editor.selection_mode is True
    assert editor.centered == (100, 140, 5, True)
    assert editor.status.messages[-1] == "Used hotkey 4"


def test_activate_unassigned_hotkey_reports_status() -> None:
    editor = _EditorStub()
    editor._activate_hotkey(7)
    assert editor.status.messages[-1] == "Unassigned hotkey 7"
