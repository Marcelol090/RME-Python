from __future__ import annotations

from py_rme_canary.logic_layer.session.editor import EditorSession


class _FakeServer:
    def __init__(self) -> None:
        self.banned_hosts = ["10.0.0.7", "10.0.0.8"]
        self.unbanned: list[str] = []
        self.cleared = 0

    def get_banned_hosts(self) -> list[str]:
        return list(self.banned_hosts)

    def unban_host(self, host: str) -> bool:
        normalized = str(host)
        if normalized not in self.banned_hosts:
            return False
        self.banned_hosts = [entry for entry in self.banned_hosts if entry != normalized]
        self.unbanned.append(normalized)
        return True

    def clear_banned_hosts(self) -> int:
        count = len(self.banned_hosts)
        self.banned_hosts = []
        self.cleared += 1
        return count


def _make_session(server: object | None) -> EditorSession:
    session = EditorSession.__new__(EditorSession)
    session._live_server = server  # type: ignore[attr-defined]
    return session


def test_editor_session_live_banlist_helpers_with_server() -> None:
    fake = _FakeServer()
    session = _make_session(fake)

    assert session.list_live_banned_hosts() == ["10.0.0.7", "10.0.0.8"]
    assert session.unban_live_host("10.0.0.7") is True
    assert fake.unbanned == ["10.0.0.7"]
    assert session.clear_live_banlist() == 1
    assert fake.cleared == 1


def test_editor_session_live_banlist_helpers_without_server() -> None:
    session = _make_session(None)

    assert session.list_live_banned_hosts() == []
    assert session.unban_live_host("10.0.0.1") is False
    assert session.clear_live_banlist() == 0
