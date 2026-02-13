from __future__ import annotations

from py_rme_canary.vis_layer.ui.main_window.qt_map_editor_session import QtMapEditorSessionMixin


class _Status:
    def __init__(self) -> None:
        self.messages: list[tuple[str, int]] = []
        self._current = ""

    def showMessage(self, message: str, timeout: int = 0) -> None:  # noqa: N802
        self._current = str(message)
        self.messages.append((self._current, int(timeout)))

    def currentMessage(self) -> str:  # noqa: N802
        return str(self._current)


class _EditorStub(QtMapEditorSessionMixin):
    def __init__(self) -> None:
        self.status = _Status()
        self._ui_backend_contract_signature = 0
        self._ui_backend_contract_last_repairs_key = ""
        self._ui_backend_contract_last_repairs_signature = 0


def test_verify_contract_status_is_deduplicated(monkeypatch) -> None:
    editor = _EditorStub()
    results = iter(
        [
            (["show_grid_sync", "show_grid_sync", "show_tooltips_sync"], 11),
            (["show_tooltips_sync", "show_grid_sync"], 12),
        ]
    )

    def _fake_verify(_editor, *, last_signature: int):
        assert isinstance(last_signature, int)
        return next(results)

    monkeypatch.setattr(
        "py_rme_canary.vis_layer.ui.main_window.ui_backend_contract.verify_and_repair_ui_backend_contract",
        _fake_verify,
    )

    editor._verify_ui_backend_contract()
    editor._verify_ui_backend_contract()

    assert len(editor.status.messages) == 1
    assert editor.status.messages[0][1] == 3000
    assert "show_grid_sync" in editor.status.messages[0][0]
    assert "show_tooltips_sync" in editor.status.messages[0][0]


def test_verify_contract_status_resets_after_clean_cycle(monkeypatch) -> None:
    editor = _EditorStub()
    results = iter(
        [
            (["show_grid_sync"], 21),
            ([], 22),
            (["show_grid_sync"], 23),
        ]
    )

    def _fake_verify(_editor, *, last_signature: int):
        assert isinstance(last_signature, int)
        return next(results)

    monkeypatch.setattr(
        "py_rme_canary.vis_layer.ui.main_window.ui_backend_contract.verify_and_repair_ui_backend_contract",
        _fake_verify,
    )

    editor._verify_ui_backend_contract()
    editor._verify_ui_backend_contract()
    editor._verify_ui_backend_contract()

    assert len(editor.status.messages) == 2
    assert editor._ui_backend_contract_last_repairs_key == "show_grid_sync"
    assert editor._ui_backend_contract_last_repairs_signature > 0


def test_verify_contract_does_not_override_operational_status(monkeypatch) -> None:
    editor = _EditorStub()
    editor.status.showMessage("Map cleanup: removed 3 invalid item(s)", 3000)
    results = iter(
        [
            (["show_grid_sync"], 31),
            (["show_grid_sync"], 32),
        ]
    )

    def _fake_verify(_editor, *, last_signature: int):
        assert isinstance(last_signature, int)
        return next(results)

    monkeypatch.setattr(
        "py_rme_canary.vis_layer.ui.main_window.ui_backend_contract.verify_and_repair_ui_backend_contract",
        _fake_verify,
    )

    editor._verify_ui_backend_contract()
    assert len(editor.status.messages) == 1
    assert editor.status.currentMessage().startswith("Map cleanup:")

    editor.status._current = ""
    editor._verify_ui_backend_contract()
    assert len(editor.status.messages) == 2
    assert editor.status.messages[-1][0].startswith("UI contract auto-repair:")
