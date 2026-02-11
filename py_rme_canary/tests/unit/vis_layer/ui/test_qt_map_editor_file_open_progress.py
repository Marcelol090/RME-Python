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


class _FakeProgress:
    created: list[_FakeProgress] = []
    cancel_at_step: int | None = None

    def __init__(self, *_args, **_kwargs) -> None:
        self.labels: list[str] = []
        self.values: list[int] = []
        self.closed = False
        self._cancel = False
        self.__class__.created.append(self)

    def setWindowTitle(self, *_args) -> None:
        return None

    def setWindowModality(self, *_args) -> None:
        return None

    def setAutoClose(self, *_args) -> None:
        return None

    def setMinimumDuration(self, *_args) -> None:
        return None

    def setLabelText(self, message: str) -> None:
        self.labels.append(str(message))

    def setValue(self, value: int) -> None:
        step = int(value)
        self.values.append(step)
        if self.cancel_at_step is not None and step >= int(self.cancel_at_step):
            self._cancel = True

    def wasCanceled(self) -> bool:
        return bool(self._cancel)

    def close(self) -> None:
        self.closed = True


def test_open_otbm_uses_progress_phases_and_refreshes_ui(app, monkeypatch) -> None:
    editor = _DummyEditor()
    _FakeProgress.created.clear()
    _FakeProgress.cancel_at_step = None

    gm = SimpleNamespace(load_report={"metadata": {"source": "otbm"}})
    loader = SimpleNamespace(
        last_otbm_path="C:/maps/resolved.otbm",
        last_id_mapper="mapper-ok",
        last_config=object(),
        load_with_detection=lambda _path: gm,
    )
    detection = SimpleNamespace(kind="otbm", reason="ok", engine="tfs")
    critical_calls: list[str] = []

    monkeypatch.setattr(file_module, "QProgressDialog", _FakeProgress)
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

    progress = _FakeProgress.created[-1]
    assert progress.closed
    assert progress.values == [0, 1, 2, 3, 4, 5, 6]
    assert "Detecting map format..." in progress.labels
    assert "Reading map file and translating IDs..." in progress.labels
    assert "Refreshing viewport and palettes..." in progress.labels


def test_open_otbm_reports_cancelation_when_progress_is_canceled(app, monkeypatch) -> None:
    editor = _DummyEditor()
    _FakeProgress.created.clear()
    _FakeProgress.cancel_at_step = 1

    critical_messages: list[str] = []

    monkeypatch.setattr(file_module, "QProgressDialog", _FakeProgress)
    monkeypatch.setattr(file_module.QFileDialog, "getOpenFileName", staticmethod(lambda *_a, **_k: ("C:/maps/a.otbm", "")))
    monkeypatch.setattr(file_module, "detect_map_file", lambda _path: (_ for _ in ()).throw(AssertionError("detect_map_file should not run")))
    monkeypatch.setattr(
        file_module.QMessageBox,
        "critical",
        staticmethod(lambda _parent, _title, text: critical_messages.append(str(text))),
    )

    editor._open_otbm()

    assert critical_messages
    assert "canceled" in critical_messages[0].lower()
    progress = _FakeProgress.created[-1]
    assert progress.closed
