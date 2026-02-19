import time
import unittest
from unittest.mock import MagicMock

from py_rme_canary.core.protocols.live_packets import NetworkHeader, PacketType
from py_rme_canary.core.protocols.live_server import MAX_PACKETS_PER_SEC, LiveServer
from py_rme_canary.core.protocols.live_socket import MAX_PAYLOAD_SIZE, LiveSocket
from py_rme_canary.core.protocols.tile_serializer import encode_map_request


class TestLiveSocketSecurity(unittest.TestCase):
    def test_recv_packet_payload_limit(self):
        """Test that LiveSocket rejects payloads larger than MAX_PAYLOAD_SIZE."""
        mock_sock = MagicMock()
        ls = LiveSocket(mock_sock)

        # Mock header with size > MAX_PAYLOAD_SIZE + 1
        oversized = MAX_PAYLOAD_SIZE + 1
        header_bytes = NetworkHeader.pack(1, PacketType.MESSAGE, oversized)

        # recv returns header bytes
        mock_sock.recv.side_effect = [header_bytes]

        # Should return None (and log warning)
        with self.assertLogs("py_rme_canary.core.protocols.live_socket", level="WARNING") as cm:
            result = ls.recv_packet()
            self.assertIsNone(result)
            self.assertIn("Packet too large", cm.output[0])


class TestLiveServerSecurity(unittest.TestCase):
    def setUp(self):
        self.server = LiveServer()
        self.mock_client_sock = MagicMock()
        self.server.clients[self.mock_client_sock] = MagicMock()
        # Initialize rate limit for mock client
        self.server._client_packet_rates[self.mock_client_sock] = (time.time(), 0)

    def test_rate_limiting(self):
        """Test that clients are disconnected if they exceed rate limit."""
        # Simulate packets in < 1 second up to configured limit
        for _ in range(MAX_PACKETS_PER_SEC):
            allowed = self.server._check_rate_limit(self.mock_client_sock)
            self.assertTrue(allowed)

        # Next packet should be rejected
        allowed = self.server._check_rate_limit(self.mock_client_sock)
        self.assertFalse(allowed)

    def test_map_request_area_limit(self):
        """Test that massive map requests are rejected."""
        # Setup map provider
        self.server.set_map_provider(MagicMock(return_value=[]))

        # Create a massive request (e.g. 1000x1000)
        # MAX_MAP_REQUEST_AREA is 65536
        x_min, y_min = 0, 0
        x_max, y_max = 1000, 1000  # 1,000,000 tiles
        payload = encode_map_request(x_min, y_min, x_max, y_max, 7)

        peer = self.server.clients[self.mock_client_sock]
        peer.name = "TestClient"

        with self.assertLogs('py_rme_canary.core.protocols.live_server', level='WARNING') as cm:
            self.server._handle_map_request(self.mock_client_sock, payload)
            self.assertIn("Rejected massive map request", cm.output[0])

        # Ensure provider was NOT called
        self.server._map_provider.assert_not_called()

    def test_secure_password_comparison(self):
        """Test password verification."""
        self.server.set_password("secret123")
        peer = self.server.clients[self.mock_client_sock]
        # Configure peer mock for broadcast_client_list
        peer.get_color.return_value = (255, 255, 255)
        peer.client_id = 1
        peer.name = "User"

        # Test incorrect password
        payload_wrong = b"User\0wrongpass"
        self.server._process_packet(self.mock_client_sock, PacketType.LOGIN, payload_wrong)
        peer.send_packet.assert_called_with(PacketType.LOGIN_ERROR, b"Invalid password")

        # Reset mock and re-add peer (it was disconnected)
        peer.send_packet.reset_mock()
        self.server.clients[self.mock_client_sock] = peer
        self.server._client_packet_rates[self.mock_client_sock] = (time.time(), 0)

        # Test correct password
        payload_correct = b"User\0secret123"
        self.server._process_packet(self.mock_client_sock, PacketType.LOGIN, payload_correct)

        # Should have called LOGIN_SUCCESS first
        self.assertTrue(peer.send_packet.called)

        # Check first call arguments
        first_call = peer.send_packet.mock_calls[0]
        self.assertEqual(first_call.args[0], PacketType.LOGIN_SUCCESS)

if __name__ == '__main__':
    unittest.main()
