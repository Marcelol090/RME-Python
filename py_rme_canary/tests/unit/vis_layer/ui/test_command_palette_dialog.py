from __future__ import annotations

import pytest

pytest.importorskip("PyQt6")

from PyQt6.QtGui import QAction
from PyQt6.QtWidgets import QApplication, QMainWindow

from py_rme_canary.vis_layer.ui.dialogs.command_palette_dialog import CommandEntry, CommandPaletteDialog


@pytest.fixture
def app():
    app = QApplication.instance()
    if app is None:
        app = QApplication([])
    return app


def test_collect_from_editor_includes_menu_action(app) -> None:
    window = QMainWindow()
    file_menu = window.menuBar().addMenu("File")
    action = QAction("Open Map", window)
    file_menu.addAction(action)

    entries = CommandPaletteDialog.collect_from_editor(window)

    assert any(entry.label == "Open Map" and entry.path == "File" for entry in entries)


def test_dialog_filters_and_triggers_selected_action(app) -> None:
    window = QMainWindow()
    triggered = {"count": 0}

    action = QAction("Command Test", window)
    action.triggered.connect(lambda _checked=False: triggered.__setitem__("count", triggered["count"] + 1))

    dialog = CommandPaletteDialog(
        window,
        entries=[
            CommandEntry(action=action, label="Command Test", path="Edit", shortcut="Ctrl+K"),
            CommandEntry(action=QAction("Other Action", window), label="Other Action", path="File", shortcut=""),
        ],
    )

    dialog._apply_filter("command")
    assert dialog._list.count() == 1

    dialog._trigger_selected()
    assert triggered["count"] == 1
    assert dialog.last_executed == "Command Test"
