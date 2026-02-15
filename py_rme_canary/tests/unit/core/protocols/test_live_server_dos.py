
import pytest
import time
from unittest.mock import Mock, patch
from py_rme_canary.core.protocols.live_server import LiveServer
from py_rme_canary.core.protocols.live_packets import PacketType

class TestLiveServerDoS:
    def test_rate_limiting(self):
        """Verify that sending too many packets per second disconnects the client."""
        server = LiveServer()
        mock_client = Mock()
        mock_peer = Mock()
        mock_peer.client_id = 1
        mock_peer.is_authenticated = True
        # Initialize rate limiting attributes (simulating what we will add)
        mock_peer.packet_count = 0
        mock_peer.last_packet_reset = time.time()

        server.clients[mock_client] = mock_peer

        # We need to patch time to control the "second"
        with patch("time.time", return_value=1000.0):
            # Send 50 packets (allowed limit)
            for _ in range(50):
                server._process_packet(mock_client, PacketType.MESSAGE, b"hello")

            assert mock_peer.packet_count == 50
            # Client should still be connected
            assert mock_client in server.clients

            # Send the 51st packet
            with patch.object(server, "_disconnect_client") as mock_disconnect:
                server._process_packet(mock_client, PacketType.MESSAGE, b"spam")

                # Should be disconnected
                mock_disconnect.assert_called_with(mock_client)

    def test_rate_limit_reset(self):
        """Verify that packet count resets after a second."""
        server = LiveServer()
        mock_client = Mock()
        mock_peer = Mock()
        mock_peer.client_id = 1
        mock_peer.is_authenticated = True
        mock_peer.packet_count = 50
        mock_peer.last_packet_reset = 1000.0

        server.clients[mock_client] = mock_peer

        # Advance time by 1.1 seconds
        with patch("time.time", return_value=1001.1):
            server._process_packet(mock_client, PacketType.MESSAGE, b"hello")

            # Should reset count to 1 (current packet)
            assert mock_peer.packet_count == 1
            assert mock_peer.last_packet_reset == 1001.1

            # Client should still be connected
            assert mock_client in server.clients
