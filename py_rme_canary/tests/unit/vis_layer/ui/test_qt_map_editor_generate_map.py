from __future__ import annotations

import pytest

pytest.importorskip("PyQt6")

from types import SimpleNamespace

from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_file import QtMapEditorFileMixin


def test_generate_map_routes_to_new_map_flow() -> None:
    class _GenerateEditor(QtMapEditorFileMixin):
        def __init__(self) -> None:
            self.calls = 0
            self.status_messages: list[str] = []
            self.status = SimpleNamespace(showMessage=lambda msg: self.status_messages.append(str(msg)))

        def _new_map(self) -> None:
            self.calls += 1

    editor = _GenerateEditor()
    editor._generate_map()

    assert editor.calls == 1
    assert any("Generate Map" in msg for msg in editor.status_messages)
