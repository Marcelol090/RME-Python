from __future__ import annotations

from py_rme_canary.core.protocols.live_server import LiveServer


def test_live_server_banlist_list_unban_and_clear() -> None:
    server = LiveServer(host="127.0.0.1", port=7171)
    server._banned_hosts.update({"10.0.0.2", "10.0.0.1"})  # noqa: SLF001 - testing internal storage

    assert server.get_banned_hosts() == ["10.0.0.1", "10.0.0.2"]
    assert server.unban_host("10.0.0.2") is True
    assert server.get_banned_hosts() == ["10.0.0.1"]
    assert server.unban_host("10.0.0.99") is False
    assert server.clear_banned_hosts() == 1
    assert server.get_banned_hosts() == []
