import pytest
from unittest.mock import Mock, patch
from py_rme_canary.core.protocols.live_server import LiveServer
from py_rme_canary.core.protocols.live_packets import PacketType

class TestLiveServerAuthBypass:
    def test_unauthenticated_message_disconnects_client(self):
        """
        Verify that a message sent without login results in disconnection.
        """
        server = LiveServer()
        server.set_password("secret123")

        mock_client = Mock()
        mock_peer = Mock()
        mock_peer.client_id = 1
        mock_peer.name = "Attacker"
        mock_peer.is_authenticated = False # Explicitly False

        server.clients[mock_client] = mock_peer

        # Encode chat message
        payload = "I am inside!".encode("utf-8")

        # Mock broadcast and disconnect
        with patch.object(server, "broadcast") as mock_broadcast, \
             patch.object(server, "_disconnect_client") as mock_disconnect:

            # Send MESSAGE packet without logging in
            server._process_packet(mock_client, PacketType.MESSAGE, payload)

            # Assertion: verify broadcast IS NOT called
            mock_broadcast.assert_not_called()

            # Assertion: verify disconnect IS called
            mock_disconnect.assert_called_with(mock_client)

    def test_authenticated_message_is_processed(self):
        """
        Verify that a message sent AFTER login is processed.
        """
        server = LiveServer()
        server.set_password("secret123")

        mock_client = Mock()
        mock_peer = Mock()
        mock_peer.client_id = 1
        mock_peer.name = "User"
        mock_peer.is_authenticated = True # Authenticated

        server.clients[mock_client] = mock_peer

        payload = "Hello!".encode("utf-8")

        with patch.object(server, "broadcast") as mock_broadcast, \
             patch.object(server, "_disconnect_client") as mock_disconnect:

            server._process_packet(mock_client, PacketType.MESSAGE, payload)

            # Assertion: verify broadcast IS called
            mock_broadcast.assert_called()

            # Assertion: verify disconnect IS NOT called
            mock_disconnect.assert_not_called()
