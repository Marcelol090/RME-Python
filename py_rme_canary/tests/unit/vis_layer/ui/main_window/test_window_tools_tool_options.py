from __future__ import annotations

from py_rme_canary.vis_layer.ui.main_window.menubar.window import tools as window_tools
from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_docks import QtMapEditorDocksMixin


class _FakeToolOptions:
    def __init__(self) -> None:
        self.focus_calls = 0

    def setFocus(self) -> None:  # noqa: N802 - Qt method name parity for test double
        self.focus_calls += 1


class _FakePaletteDock:
    def __init__(self) -> None:
        self.show_calls = 0
        self.raise_calls = 0
        self.tool_options = _FakeToolOptions()

    def show(self) -> None:
        self.show_calls += 1

    def raise_(self) -> None:
        self.raise_calls += 1


class _DummyEditor(QtMapEditorDocksMixin):
    def __init__(self) -> None:
        self.dock_palette = _FakePaletteDock()


def test_open_tool_options_delegates_to_editor_method() -> None:
    class _Editor:
        def __init__(self) -> None:
            self.calls = 0

        def _show_tool_options_panel(self) -> None:
            self.calls += 1

    editor = _Editor()
    window_tools.open_tool_options(editor)
    assert editor.calls == 1


def test_show_tool_options_panel_shows_palette_and_focuses_tool_options() -> None:
    editor = _DummyEditor()
    editor._show_tool_options_panel()
    assert editor.dock_palette.show_calls == 1
    assert editor.dock_palette.raise_calls == 1
    assert editor.dock_palette.tool_options.focus_calls == 1
