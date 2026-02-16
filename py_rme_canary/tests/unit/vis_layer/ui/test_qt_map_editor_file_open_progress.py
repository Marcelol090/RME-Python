from __future__ import annotations

from types import SimpleNamespace

import pytest

pytest.importorskip("PyQt6")

from py_rme_canary.vis_layer.ui.main_window import qt_map_editor_file as file_module
from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_file import QtMapEditorFileMixin


@pytest.fixture
def app():
    from PyQt6.QtWidgets import QApplication

    instance = QApplication.instance()
    if instance is None:
        instance = QApplication([])
    return instance


class _DummyEditor(QtMapEditorFileMixin):
    def __init__(self) -> None:
        self.current_path = None
        self.map = None
        self.session = None
        self.brush_mgr = object()
        self.viewport = SimpleNamespace(origin_x=99, origin_y=77)
        self.id_mapper = None
        self.context_payloads: list[dict] = []
        self.default_project_writes = 0
        self.status_messages: list[str] = []
        self.palette_refreshes = 0
        self.canvas_updates = 0
        self.apply_state_calls = 0
        self.palettes = SimpleNamespace(refresh_primary_list=self._refresh_palettes)
        self.canvas = SimpleNamespace(update=self._canvas_update)

    def _refresh_palettes(self) -> None:
        self.palette_refreshes += 1

    def _canvas_update(self) -> None:
        self.canvas_updates += 1

    def _on_tiles_changed(self, _changed) -> None:
        return None

    def apply_ui_state_to_session(self) -> None:
        self.apply_state_calls += 1

    def _set_id_mapper(self, mapper) -> None:
        self.id_mapper = mapper

    def _apply_detected_context(self, metadata: dict) -> None:
        self.context_payloads.append(dict(metadata or {}))

    def _maybe_write_default_project_json(self, *, opened_otbm_path: str, cfg: object) -> None:
        self.default_project_writes += 1
        self.status_messages.append(f"project:{opened_otbm_path}:{bool(cfg)}")

    def _update_status_capabilities(self, *, prefix: str) -> None:
        self.status_messages.append(str(prefix))


class _FakeLoadingDialog:
    created: list[_FakeLoadingDialog] = []

    def __init__(self, *_args, **_kwargs) -> None:
        self.messages: list[str] = []
        self.progress_values: list[int] = []
        self.closed = False
        self.__class__.created.append(self)

    def show(self) -> None:
        return None

    def set_message(self, message: str) -> None:
        self.messages.append(str(message))

    def set_progress(self, value: int, max_val: int = 100) -> None:
        _ = max_val
        self.progress_values.append(int(value))

    def close(self) -> None:
        self.closed = True


def test_open_otbm_uses_progress_phases_and_refreshes_ui(app, monkeypatch) -> None:
    editor = _DummyEditor()
    _FakeLoadingDialog.created.clear()

    gm = SimpleNamespace(load_report={"metadata": {"source": "otbm"}})
    loader = SimpleNamespace(
        last_otbm_path="C:/maps/resolved.otbm",
        last_id_mapper="mapper-ok",
        last_config=object(),
        load_with_detection=lambda _path: gm,
    )
    detection = SimpleNamespace(kind="otbm", reason="ok", engine="tfs")
    critical_calls: list[str] = []

    monkeypatch.setattr(file_module, "ModernLoadingDialog", _FakeLoadingDialog)
    monkeypatch.setattr(file_module.QFileDialog, "getOpenFileName", staticmethod(lambda *_a, **_k: ("C:/maps/a.otbm", "")))
    monkeypatch.setattr(file_module, "detect_map_file", lambda _path: detection)
    monkeypatch.setattr(file_module, "OTBMLoader", lambda: loader)
    monkeypatch.setattr(file_module, "EditorSession", lambda *args, **kwargs: SimpleNamespace(args=args, kwargs=kwargs))
    monkeypatch.setattr(file_module.QMessageBox, "critical", staticmethod(lambda *_a, **_k: critical_calls.append("critical")))

    editor._open_otbm()

    assert not critical_calls
    assert editor.current_path == "C:/maps/resolved.otbm"
    assert editor.id_mapper == "mapper-ok"
    assert editor.viewport.origin_x == 0
    assert editor.viewport.origin_y == 0
    assert editor.apply_state_calls == 1
    assert editor.default_project_writes == 1
    assert editor.palette_refreshes == 1
    assert editor.canvas_updates == 1
    assert editor.context_payloads == [{"source": "otbm"}]

    assert len(_FakeLoadingDialog.created) == 1
    progress = _FakeLoadingDialog.created[-1]
    assert progress.closed
    assert progress.progress_values == [16, 33, 50, 66, 83, 100]
    assert "Detecting map format..." in progress.messages
    assert "Reading map file and translating IDs..." in progress.messages
    assert "Refreshing viewport and palettes..." in progress.messages


def test_open_otbm_reports_error_and_closes_progress(app, monkeypatch) -> None:
    editor = _DummyEditor()
    _FakeLoadingDialog.created.clear()

    critical_messages: list[str] = []

    monkeypatch.setattr(file_module, "ModernLoadingDialog", _FakeLoadingDialog)
    monkeypatch.setattr(file_module.QFileDialog, "getOpenFileName", staticmethod(lambda *_a, **_k: ("C:/maps/a.otbm", "")))
    monkeypatch.setattr(file_module, "detect_map_file", lambda _path: (_ for _ in ()).throw(RuntimeError("boom")))
    monkeypatch.setattr(
        file_module.QMessageBox,
        "critical",
        staticmethod(lambda _parent, _title, text: critical_messages.append(str(text))),
    )

    editor._open_otbm()

    assert critical_messages
    assert "boom" in critical_messages[0].lower()
    progress = _FakeLoadingDialog.created[-1]
    assert progress.closed
