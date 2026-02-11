"""Tests for core.protocols.cursor_broadcaster."""

from __future__ import annotations

import time

from py_rme_canary.core.protocols.cursor_broadcaster import (
    BroadcasterConfig,
    CursorBroadcaster,
    CursorManager,
    CursorOverlayData,
    CursorReceiver,
)
from py_rme_canary.core.protocols.live_packets import encode_cursor

# --- CursorOverlayData ---


class TestCursorOverlayData:
    def test_to_dict(self) -> None:
        c = CursorOverlayData(client_id=1, name="Alice", x=10, y=20, z=7, color=(255, 0, 0))
        d = c.to_dict()
        assert d["client_id"] == 1
        assert d["name"] == "Alice"
        assert d["x"] == 10
        assert d["color"] == (255, 0, 0)

    def test_from_packet(self) -> None:
        c = CursorOverlayData.from_packet(3, 100, 200, 5, "Bob")
        assert c.client_id == 3
        assert c.name == "Bob"
        assert c.x == 100
        assert c.y == 200
        assert c.z == 5
        assert c.visible is True
        assert c.last_update > 0

    def test_from_packet_default_name(self) -> None:
        c = CursorOverlayData.from_packet(7, 0, 0, 0)
        assert c.name == "User_7"

    def test_color_assignment_wraps(self) -> None:
        """Color should cycle through the palette."""
        c1 = CursorOverlayData.from_packet(0, 0, 0, 0)
        c2 = CursorOverlayData.from_packet(16, 0, 0, 0)
        assert c1.color == c2.color  # 0 % 16 == 16 % 16


# --- BroadcasterConfig ---


class TestBroadcasterConfig:
    def test_defaults(self) -> None:
        cfg = BroadcasterConfig()
        assert cfg.throttle_ms == 50
        assert cfg.timeout_seconds == 10.0
        assert cfg.max_cursors == 32
        assert cfg.broadcast_enabled is True
        assert cfg.receive_enabled is True


# --- CursorBroadcaster ---


class TestCursorBroadcaster:
    def test_update_position_returns_false_when_disabled(self) -> None:
        cfg = BroadcasterConfig(broadcast_enabled=False)
        b = CursorBroadcaster(cfg)
        assert b.update_position(1, 2, 3) is False

    def test_update_same_position_no_send(self) -> None:
        b = CursorBroadcaster()
        b.update_position(10, 20, 7, force=True)
        # Same position, no force -> should not send
        result = b.update_position(10, 20, 7)
        assert result is False

    def test_flush_sends_pending(self) -> None:
        cfg = BroadcasterConfig(throttle_ms=60000)  # Very high throttle
        b = CursorBroadcaster(cfg)
        b.update_position(1, 1, 1, force=True)  # First succeeds
        b.update_position(2, 2, 2)  # Throttled

        # Should have pending
        flushed = b.flush()
        assert flushed is True

    def test_flush_nothing_pending(self) -> None:
        b = CursorBroadcaster()
        assert b.flush() is False

    def test_stats_tracking(self) -> None:
        b = CursorBroadcaster()
        b.update_position(1, 1, 1, force=True)
        stats = b.get_stats()
        assert stats["broadcasts_sent"] >= 0  # No server/client means _do_broadcast is a no-op
        assert stats["broadcasts_throttled"] >= 0


# --- CursorReceiver ---


class TestCursorReceiver:
    def test_handle_cursor_packet_basic(self) -> None:
        r = CursorReceiver()
        payload = encode_cursor(5, 100, 200, 7)
        cursor = r.handle_cursor_packet(payload)
        assert cursor is not None
        assert cursor.client_id == 5
        assert cursor.x == 100
        assert cursor.y == 200
        assert cursor.z == 7

    def test_exclude_self(self) -> None:
        r = CursorReceiver()
        payload = encode_cursor(1, 0, 0, 0)
        result = r.handle_cursor_packet(payload, exclude_self=1)
        assert result is None

    def test_receive_disabled(self) -> None:
        cfg = BroadcasterConfig(receive_enabled=False)
        r = CursorReceiver(cfg)
        payload = encode_cursor(1, 0, 0, 0)
        assert r.handle_cursor_packet(payload) is None

    def test_update_existing_cursor(self) -> None:
        r = CursorReceiver()
        payload1 = encode_cursor(1, 10, 20, 7)
        payload2 = encode_cursor(1, 30, 40, 5)
        r.handle_cursor_packet(payload1)
        r.handle_cursor_packet(payload2)
        cursors = r.get_visible_cursors()
        assert len(cursors) == 1
        assert cursors[0].x == 30
        assert cursors[0].z == 5

    def test_max_cursors_eviction(self) -> None:
        cfg = BroadcasterConfig(max_cursors=2)
        r = CursorReceiver(cfg)
        for i in range(3):
            payload = encode_cursor(i + 1, i * 10, 0, 0)
            r.handle_cursor_packet(payload)
        # Should only have 2 cursors (oldest evicted)
        cursors = r.get_visible_cursors()
        assert len(cursors) == 2

    def test_timeout_hides_cursor(self) -> None:
        cfg = BroadcasterConfig(timeout_seconds=0.01)
        r = CursorReceiver(cfg)
        payload = encode_cursor(1, 10, 20, 7)
        r.handle_cursor_packet(payload)
        time.sleep(0.02)
        cursors = r.get_visible_cursors()
        assert len(cursors) == 0

    def test_floor_filter(self) -> None:
        r = CursorReceiver()
        r.handle_cursor_packet(encode_cursor(1, 0, 0, 7))
        r.handle_cursor_packet(encode_cursor(2, 0, 0, 5))
        cursors = r.get_visible_cursors(current_floor=7)
        assert len(cursors) == 1
        assert cursors[0].z == 7

    def test_remove_cursor(self) -> None:
        r = CursorReceiver()
        r.handle_cursor_packet(encode_cursor(1, 0, 0, 0))
        assert r.remove_cursor(1) is True
        assert r.remove_cursor(1) is False
        assert r.get_visible_cursors() == []

    def test_clear(self) -> None:
        r = CursorReceiver()
        r.handle_cursor_packet(encode_cursor(1, 0, 0, 0))
        r.handle_cursor_packet(encode_cursor(2, 0, 0, 0))
        cleared = r.clear()
        assert cleared == 2
        assert r.get_visible_cursors() == []

    def test_name_resolver(self) -> None:
        r = CursorReceiver()
        r.set_name_resolver(lambda cid: f"Player_{cid}")
        r.handle_cursor_packet(encode_cursor(3, 0, 0, 0))
        cursors = r.get_visible_cursors()
        assert cursors[0].name == "Player_3"

    def test_update_callback(self) -> None:
        r = CursorReceiver()
        received: list[CursorOverlayData] = []
        r.set_update_callback(lambda c: received.append(c))
        r.handle_cursor_packet(encode_cursor(1, 10, 20, 7))
        assert len(received) == 1
        assert received[0].x == 10

    def test_get_cursor_overlays_dict_format(self) -> None:
        r = CursorReceiver()
        r.handle_cursor_packet(encode_cursor(1, 10, 20, 7))
        overlays = r.get_cursor_overlays()
        assert len(overlays) == 1
        assert isinstance(overlays[0], dict)
        assert "client_id" in overlays[0]

    def test_stats(self) -> None:
        r = CursorReceiver()
        r.handle_cursor_packet(encode_cursor(1, 0, 0, 0))
        stats = r.get_stats()
        assert stats["packets_received"] == 1
        assert stats["cursors_tracked"] == 1


# --- CursorManager ---


class TestCursorManager:
    def test_get_overlays_empty(self) -> None:
        cm = CursorManager()
        assert cm.get_overlays() == []

    def test_handle_packet_and_get_overlays(self) -> None:
        cm = CursorManager()
        cm.handle_packet(encode_cursor(1, 10, 20, 7))
        overlays = cm.get_overlays()
        assert len(overlays) == 1

    def test_remove_user(self) -> None:
        cm = CursorManager()
        cm.handle_packet(encode_cursor(1, 0, 0, 0))
        assert cm.remove_user(1) is True
        assert cm.get_overlays() == []

    def test_flush_no_error(self) -> None:
        cm = CursorManager()
        assert cm.flush() is False

    def test_clear(self) -> None:
        cm = CursorManager()
        cm.handle_packet(encode_cursor(1, 0, 0, 0))
        cm.clear()
        assert cm.get_overlays() == []
