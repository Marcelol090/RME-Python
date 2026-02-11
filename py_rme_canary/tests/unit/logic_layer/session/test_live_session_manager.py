"""Tests for logic_layer.session.live_session_manager."""

from __future__ import annotations

from py_rme_canary.logic_layer.session.live_session_manager import (
    LiveSessionManager,
    SessionInfo,
    SessionMetrics,
    SessionState,
)

# --- SessionState ---


class TestSessionState:
    def test_all_states_exist(self) -> None:
        assert SessionState.IDLE is not None
        assert SessionState.CONNECTING is not None
        assert SessionState.CONNECTED is not None
        assert SessionState.AUTHENTICATED is not None
        assert SessionState.SYNCING is not None
        assert SessionState.ACTIVE is not None
        assert SessionState.RECONNECTING is not None
        assert SessionState.DISCONNECTING is not None
        assert SessionState.ERROR is not None

    def test_unique_values(self) -> None:
        values = [s.value for s in SessionState]
        assert len(values) == len(set(values))


# --- SessionMetrics ---


class TestSessionMetrics:
    def test_default_values(self) -> None:
        m = SessionMetrics()
        assert m.connected_at == 0.0
        assert m.reconnect_count == 0
        assert m.uptime_seconds == 0.0

    def test_uptime_with_connection(self) -> None:
        import time

        m = SessionMetrics(connected_at=time.time() - 10.0)
        assert m.uptime_seconds >= 9.0

    def test_uptime_with_disconnection(self) -> None:
        m = SessionMetrics(connected_at=100.0, disconnected_at=110.0)
        assert m.uptime_seconds == 10.0


# --- SessionInfo ---


class TestSessionInfo:
    def test_defaults(self) -> None:
        info = SessionInfo()
        assert info.host == ""
        assert info.port == 7171
        assert info.state == SessionState.IDLE
        assert info.connected_users == []


# --- LiveSessionManager ---


class TestLiveSessionManager:
    def test_initial_state(self) -> None:
        mgr = LiveSessionManager()
        assert mgr.state == SessionState.IDLE
        assert mgr.is_active is False

    def test_info_property(self) -> None:
        mgr = LiveSessionManager()
        assert isinstance(mgr.info, SessionInfo)

    def test_state_change_callback(self) -> None:
        mgr = LiveSessionManager()
        changes: list[tuple[SessionState, SessionState]] = []
        mgr.on_state_changed = lambda old, new: changes.append((old, new))

        # Force a state change through internal method
        mgr._set_state(SessionState.CONNECTING)
        assert len(changes) == 1
        assert changes[0] == (SessionState.IDLE, SessionState.CONNECTING)

    def test_no_duplicate_state_change(self) -> None:
        mgr = LiveSessionManager()
        changes: list[tuple[SessionState, SessionState]] = []
        mgr.on_state_changed = lambda old, new: changes.append((old, new))

        mgr._set_state(SessionState.CONNECTING)
        mgr._set_state(SessionState.CONNECTING)  # Same state again
        assert len(changes) == 1

    def test_connect_invalid_host_gives_error(self) -> None:
        mgr = LiveSessionManager()
        result = mgr.connect("192.0.2.1", 1, name="test")  # RFC 5737 TEST-NET
        assert result is False
        assert mgr.state == SessionState.ERROR

    def test_disconnect_from_idle(self) -> None:
        mgr = LiveSessionManager()
        mgr.disconnect()
        assert mgr.state == SessionState.IDLE

    def test_send_chat_when_not_active(self) -> None:
        mgr = LiveSessionManager()
        assert mgr.send_chat("hello") is False

    def test_update_cursor_when_not_active(self) -> None:
        mgr = LiveSessionManager()
        assert mgr.update_cursor(10, 20, 7) is False

    def test_get_cursor_overlays_empty(self) -> None:
        mgr = LiveSessionManager()
        assert mgr.get_cursor_overlays() == []

    def test_get_diagnostics(self) -> None:
        mgr = LiveSessionManager()
        diag = mgr.get_diagnostics()
        assert diag["state"] == "IDLE"
        assert diag["host"] == ""
        assert diag["port"] == 7171
        assert diag["users_online"] == 0

    def test_is_active_states(self) -> None:
        mgr = LiveSessionManager()
        inactive_states = [
            SessionState.IDLE,
            SessionState.CONNECTING,
            SessionState.RECONNECTING,
            SessionState.DISCONNECTING,
            SessionState.ERROR,
        ]
        for s in inactive_states:
            mgr._info.state = s
            assert mgr.is_active is False

        active_states = [
            SessionState.CONNECTED,
            SessionState.AUTHENTICATED,
            SessionState.SYNCING,
            SessionState.ACTIVE,
        ]
        for s in active_states:
            mgr._info.state = s
            assert mgr.is_active is True
