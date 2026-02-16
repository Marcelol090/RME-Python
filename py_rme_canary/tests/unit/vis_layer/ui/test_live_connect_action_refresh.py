from __future__ import annotations

import pytest

pytest.importorskip("PyQt6")

from py_rme_canary.vis_layer.ui.main_window import live_connect


class _DockLiveLog:
    def __init__(self) -> None:
        self.input_states: list[bool] = []

    def set_input_enabled(self, value: bool) -> None:
        self.input_states.append(bool(value))


class _Session:
    def __init__(self) -> None:
        self.connect_calls: list[tuple[str, int, str, str]] = []
        self.host_calls: list[tuple[str, int, str, str]] = []
        self.disconnect_calls = 0
        self.stop_calls = 0
        self.connect_result = True
        self.host_result = True
        self.banned_hosts: list[str] = []
        self.unbanned_hosts: list[str] = []

    def connect_live(self, host: str, port: int, *, name: str = "", password: str = "") -> bool:
        self.connect_calls.append((str(host), int(port), str(name), str(password)))
        return bool(self.connect_result)

    def disconnect_live(self) -> None:
        self.disconnect_calls += 1

    def start_live_server(self, *, host: str = "", port: int = 0, name: str = "", password: str = "") -> bool:
        self.host_calls.append((str(host), int(port), str(name), str(password)))
        return bool(self.host_result)

    def stop_live_server(self) -> None:
        self.stop_calls += 1

    def list_live_banned_hosts(self) -> list[str]:
        return list(self.banned_hosts)

    def unban_live_host(self, host: str) -> bool:
        normalized = str(host)
        if normalized not in self.banned_hosts:
            return False
        self.banned_hosts = [entry for entry in self.banned_hosts if entry != normalized]
        self.unbanned_hosts.append(normalized)
        return True


class _Editor:
    def __init__(self) -> None:
        self.session = _Session()
        self.dock_live_log = _DockLiveLog()
        self.action_refreshes = 0

    def _update_action_enabled_states(self) -> None:
        self.action_refreshes += 1


class _ConnectDialogOk:
    def __init__(self, *_a, **_k) -> None:
        pass

    def exec(self) -> int:
        return 1

    def get_values(self) -> tuple[str, str, int, str]:
        return ("Alice", "127.0.0.1", 7171, "pw")


class _HostDialogOk:
    def __init__(self, *_a, **_k) -> None:
        pass

    def exec(self) -> int:
        return 1

    def get_values(self) -> tuple[str, str, int, str]:
        return ("Server", "0.0.0.0", 31313, "pw")


def test_open_connect_dialog_success_refreshes_live_action_states(monkeypatch: pytest.MonkeyPatch) -> None:
    editor = _Editor()
    monkeypatch.setattr(live_connect, "ConnectDialog", _ConnectDialogOk)
    monkeypatch.setattr(
        "py_rme_canary.vis_layer.ui.main_window.live_connect.QMessageBox.information",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr(
        "py_rme_canary.vis_layer.ui.main_window.live_connect.QMessageBox.critical",
        lambda *_a, **_k: None,
    )

    live_connect.open_connect_dialog(editor)  # type: ignore[arg-type]

    assert editor.session.connect_calls == [("127.0.0.1", 7171, "Alice", "pw")]
    assert editor.dock_live_log.input_states == [True]
    assert editor.action_refreshes == 1


def test_disconnect_and_stop_host_refresh_action_states(monkeypatch: pytest.MonkeyPatch) -> None:
    editor = _Editor()
    monkeypatch.setattr(
        "py_rme_canary.vis_layer.ui.main_window.live_connect.QMessageBox.information",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr(
        "py_rme_canary.vis_layer.ui.main_window.live_connect.QMessageBox.critical",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr(live_connect, "HostDialog", _HostDialogOk)

    live_connect.open_host_dialog(editor)  # type: ignore[arg-type]
    live_connect.stop_host(editor)  # type: ignore[arg-type]
    live_connect.disconnect_live(editor)  # type: ignore[arg-type]

    assert editor.session.host_calls == [("0.0.0.0", 31313, "Server", "pw")]
    assert editor.session.stop_calls == 1
    assert editor.session.disconnect_calls == 1
    assert editor.dock_live_log.input_states == [False]
    assert editor.action_refreshes == 3


def test_manage_ban_list_unbans_selected_host(monkeypatch: pytest.MonkeyPatch) -> None:
    editor = _Editor()
    editor.session.banned_hosts = ["10.0.0.8", "10.0.0.9"]

    monkeypatch.setattr(
        "py_rme_canary.vis_layer.ui.main_window.live_connect.QInputDialog.getItem",
        lambda *_a, **_k: ("10.0.0.9", True),
    )
    monkeypatch.setattr(
        "py_rme_canary.vis_layer.ui.main_window.live_connect.QMessageBox.question",
        lambda *_a, **_k: live_connect.QMessageBox.StandardButton.Yes,
    )
    monkeypatch.setattr(
        "py_rme_canary.vis_layer.ui.main_window.live_connect.QMessageBox.information",
        lambda *_a, **_k: None,
    )
    monkeypatch.setattr(
        "py_rme_canary.vis_layer.ui.main_window.live_connect.QMessageBox.warning",
        lambda *_a, **_k: None,
    )

    live_connect.manage_ban_list(editor)  # type: ignore[arg-type]

    assert editor.session.unbanned_hosts == ["10.0.0.9"]
    assert editor.session.banned_hosts == ["10.0.0.8"]
