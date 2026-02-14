
import pytest
import time
import struct
from unittest.mock import Mock, patch
from py_rme_canary.core.protocols.live_server import LiveServer, MAX_MAP_REQUEST_AREA, MAX_PACKETS_PER_SECOND
from py_rme_canary.core.protocols.live_packets import PacketType

class TestLiveServerDoS:
    def _create_mock_peer(self):
        peer = Mock()
        peer.packet_count = 0
        peer.last_packet_reset = time.time()
        peer.is_authenticated = True
        peer.name = "TestUser"
        peer.address = ("127.0.0.1", 12345)
        peer.client_id = 1
        return peer

    def test_map_request_limit(self):
        server = LiveServer()
        mock_client = Mock()
        mock_peer = self._create_mock_peer()
        server.clients[mock_client] = mock_peer

        # Create payload for a huge map request: 0,0 to 300,300 (area 90601 > 65536)
        # Format: <x_min:i32><y_min:i32><x_max:i32><y_max:i32><z:u8>
        x_min, y_min = 0, 0
        x_max, y_max = 300, 300
        z = 7
        payload = struct.pack("<iiiiB", x_min, y_min, x_max, y_max, z)

        # Process map request
        # Mock map provider to ensure it's NOT called
        mock_provider = Mock()
        server.set_map_provider(mock_provider)

        server._process_packet(mock_client, PacketType.MAP_REQUEST, payload)

        # Provider should NOT be called
        mock_provider.assert_not_called()

        # Peer should NOT receive MAP_CHUNK
        # (send_packet shouldn't be called with MAP_CHUNK)
        # We iterate over all calls to send_packet and ensure none are MAP_CHUNK
        for call in mock_peer.send_packet.call_args_list:
            assert call.args[0] != PacketType.MAP_CHUNK

    def test_map_request_valid(self):
        server = LiveServer()
        mock_client = Mock()
        mock_peer = self._create_mock_peer()
        server.clients[mock_client] = mock_peer

        # Valid request: 0,0 to 100,100 (area 10201 <= 65536)
        x_min, y_min = 0, 0
        x_max, y_max = 100, 100
        z = 7
        payload = struct.pack("<iiiiB", x_min, y_min, x_max, y_max, z)

        mock_provider = Mock(return_value=[])
        server.set_map_provider(mock_provider)

        server._process_packet(mock_client, PacketType.MAP_REQUEST, payload)

        # Provider SHOULD be called
        mock_provider.assert_called_with(x_min, y_min, x_max, y_max, z)

    def test_rate_limit_exceeded(self):
        server = LiveServer()
        mock_client = Mock()
        mock_peer = self._create_mock_peer()
        server.clients[mock_client] = mock_peer

        # Send MAX_PACKETS_PER_SECOND + 1 packets
        with patch.object(server, "_disconnect_client") as mock_disconnect:
            # Send 50 packets (allowed)
            for _ in range(MAX_PACKETS_PER_SECOND):
                server._process_packet(mock_client, PacketType.CURSOR_UPDATE, b"payload")
                mock_disconnect.assert_not_called()

            # Send 51st packet (should trigger disconnect)
            server._process_packet(mock_client, PacketType.CURSOR_UPDATE, b"payload")

            mock_disconnect.assert_called_with(mock_client)

    def test_rate_limit_reset(self):
        server = LiveServer()
        mock_client = Mock()
        mock_peer = self._create_mock_peer()
        # Set last reset to > 1 second ago
        mock_peer.last_packet_reset = time.time() - 1.5
        mock_peer.packet_count = MAX_PACKETS_PER_SECOND # Should be reset

        server.clients[mock_client] = mock_peer

        with patch.object(server, "_disconnect_client") as mock_disconnect:
            server._process_packet(mock_client, PacketType.CURSOR_UPDATE, b"payload")

            mock_disconnect.assert_not_called()
            # Verify reset happened
            assert mock_peer.packet_count == 1
            # last_packet_reset should be updated to roughly now
            assert abs(mock_peer.last_packet_reset - time.time()) < 0.1
