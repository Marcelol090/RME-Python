from unittest.mock import Mock, patch

from py_rme_canary.core.protocols.live_packets import PacketType
from py_rme_canary.core.protocols.live_server import MAX_PACKETS_PER_SEC, LiveServer
from py_rme_canary.core.protocols.tile_serializer import encode_map_request


class TestLiveServerDoS:
    def _create_mock_peer(self) -> Mock:
        peer = Mock()
        peer.name = "TestUser"
        peer.address = ("127.0.0.1", 12345)
        peer.client_id = 1
        peer.is_authenticated = True
        peer.packet_count = 0
        peer.last_packet_reset = 0.0
        peer.process_incoming_data.return_value = []
        return peer

    def test_rate_limiting_disconnects_on_handle_client_data(self):
        """When the per-socket limit is exceeded, the client is disconnected."""
        server = LiveServer()
        mock_client = Mock()
        mock_peer = self._create_mock_peer()
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

    def test_map_request_limit_rejects_large_area(self):
        server = LiveServer()
        mock_client = Mock()
        mock_peer = self._create_mock_peer()
        server.clients[mock_client] = mock_peer

        payload = encode_map_request(0, 0, 300, 300, 7)
        mock_provider = Mock()
        server.set_map_provider(mock_provider)

        server._process_packet(mock_client, PacketType.MAP_REQUEST, payload)

        mock_provider.assert_not_called()
        mock_peer.send_packet.assert_called()
        assert mock_peer.send_packet.call_args[0][0] == PacketType.MAP_CHUNK

    def test_map_request_valid_calls_provider(self):
        server = LiveServer()
        mock_client = Mock()
        mock_peer = self._create_mock_peer()
        server.clients[mock_client] = mock_peer

        payload = encode_map_request(0, 0, 100, 100, 7)
        mock_provider = Mock(return_value=[])
        server.set_map_provider(mock_provider)

        server._process_packet(mock_client, PacketType.MAP_REQUEST, payload)

        mock_provider.assert_called_once_with(0, 0, 100, 100, 7)
