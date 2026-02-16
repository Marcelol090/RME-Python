from unittest.mock import Mock, patch

from py_rme_canary.core.protocols.live_server import MAX_PACKETS_PER_SEC, LiveServer


class TestLiveServerDoS:
    def test_rate_limiting_disconnects_on_handle_client_data(self):
        """When the per-socket limit is exceeded, the client is disconnected."""
        server = LiveServer()
        mock_client = Mock()
        mock_peer = Mock()
        mock_peer.name = "Flooder"
        mock_peer.process_incoming_data.return_value = []
        server.clients[mock_client] = mock_peer
        server._client_packet_rates[mock_client] = (1000.0, MAX_PACKETS_PER_SEC)

        with (
            patch("time.time", return_value=1000.5),
            patch.object(server, "_disconnect_client") as mock_disconnect,
        ):
            server._handle_client_data(mock_client)

        mock_disconnect.assert_called_once_with(mock_client)

    def test_rate_limit_reset_after_one_second(self):
        """Rate limiter resets count after one second and accepts the packet."""
        server = LiveServer()
        mock_client = Mock()
        server._client_packet_rates[mock_client] = (1000.0, MAX_PACKETS_PER_SEC)

        with patch("time.time", return_value=1001.1):
            allowed = server._check_rate_limit(mock_client)

        assert allowed is True
        assert server._client_packet_rates[mock_client] == (1001.1, 1)

    def test_rate_limit_blocks_packet_after_limit(self):
        """Exactly limit packets are allowed, the next one is rejected."""
        server = LiveServer()
        mock_client = Mock()
        server._client_packet_rates[mock_client] = (1000.0, 0)

        with patch("time.time", return_value=1000.2):
            for _ in range(MAX_PACKETS_PER_SEC):
                assert server._check_rate_limit(mock_client) is True
            assert server._check_rate_limit(mock_client) is False
