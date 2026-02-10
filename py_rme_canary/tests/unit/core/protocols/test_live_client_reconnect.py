"""Tests for LiveClient auto-reconnect functionality."""

from __future__ import annotations

from py_rme_canary.core.protocols.live_client import LiveClient, ReconnectConfig
from py_rme_canary.core.protocols.live_packets import ConnectionState


class TestReconnectConfig:
    def test_defaults(self) -> None:
        cfg = ReconnectConfig()
        assert cfg.enabled is True
        assert cfg.max_attempts == 10
        assert cfg.base_delay == 1.0
        assert cfg.max_delay == 30.0
        assert cfg.backoff_factor == 2.0
        assert cfg.jitter == 0.1

    def test_disabled(self) -> None:
        cfg = ReconnectConfig(enabled=False)
        assert cfg.enabled is False

    def test_custom_values(self) -> None:
        cfg = ReconnectConfig(
            enabled=True,
            max_attempts=5,
            base_delay=0.5,
            max_delay=10.0,
            backoff_factor=1.5,
            jitter=0.0,
        )
        assert cfg.max_attempts == 5
        assert cfg.base_delay == 0.5


class TestLiveClientReconnect:
    def test_client_has_reconnect_config(self) -> None:
        client = LiveClient()
        assert client.reconnect_config is not None
        assert isinstance(client.reconnect_config, ReconnectConfig)

    def test_client_custom_config(self) -> None:
        cfg = ReconnectConfig(enabled=False, max_attempts=3)
        client = LiveClient(reconnect_config=cfg)
        assert client.reconnect_config.enabled is False
        assert client.reconnect_config.max_attempts == 3

    def test_set_reconnect_config(self) -> None:
        client = LiveClient()
        new_cfg = ReconnectConfig(max_attempts=99)
        client.reconnect_config = new_cfg
        assert client.reconnect_config.max_attempts == 99

    def test_initial_state_disconnected(self) -> None:
        client = LiveClient()
        assert client.state == ConnectionState.DISCONNECTED

    def test_connect_to_invalid_host_fails(self) -> None:
        client = LiveClient(host="192.0.2.1", port=1)  # RFC 5737 TEST-NET
        cfg = ReconnectConfig(enabled=False)
        client.reconnect_config = cfg
        result = client.connect()
        assert result is False
        assert client.state == ConnectionState.DISCONNECTED

    def test_disconnect_is_intentional(self) -> None:
        """After disconnect(), no auto-reconnect should be triggered."""
        client = LiveClient()
        client.disconnect()
        assert client._intentional_disconnect is True

    def test_lifecycle_callbacks_settable(self) -> None:
        client = LiveClient()
        connected_called: list[bool] = []
        disconnected_reasons: list[str] = []
        reconnecting_attempts: list[tuple[int, float]] = []

        client.set_connected_callback(lambda: connected_called.append(True))
        client.set_disconnected_callback(lambda r: disconnected_reasons.append(r))
        client.set_reconnecting_callback(lambda a, d: reconnecting_attempts.append((a, d)))

        assert client._on_connected is not None
        assert client._on_disconnected is not None
        assert client._on_reconnecting is not None

    def test_pop_packet_empty(self) -> None:
        client = LiveClient()
        assert client.pop_packet() is None

    def test_send_packet_when_disconnected(self) -> None:
        from py_rme_canary.core.protocols.live_packets import PacketType

        client = LiveClient()
        result = client.send_packet(PacketType.MESSAGE, b"hello")
        assert result is False