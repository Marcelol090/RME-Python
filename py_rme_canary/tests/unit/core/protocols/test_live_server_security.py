
import time
from unittest.mock import Mock, patch

from py_rme_canary.core.protocols.live_packets import PacketType
from py_rme_canary.core.protocols.live_server import LiveServer


class TestLiveServerSecurity:
    def _create_mock_peer(self):
        peer = Mock()
        peer.packet_count = 0
        peer.last_packet_reset = time.time()
        return peer

    def test_login_password_success(self):
        server = LiveServer()
        server.set_password("secret123")

        mock_client = Mock()
        mock_peer = self._create_mock_peer()
        mock_peer.client_id = 1
        mock_peer.packet_count = 0
        mock_peer.last_packet_reset = 0.0
        server.clients[mock_client] = mock_peer

        # Encode login payload: "user\0secret123"
        payload = b"user\0secret123"

        # Process login packet
        with patch.object(server, "broadcast_client_list"):
            server._process_packet(mock_client, PacketType.LOGIN, payload)

        # Should succeed
        mock_peer.send_packet.assert_called_with(PacketType.LOGIN_SUCCESS, (1).to_bytes(4, "little"))
        mock_peer.set_password.assert_called_with("secret123")

    def test_login_password_failure(self):
        server = LiveServer()
        server.set_password("secret123")

        mock_client = Mock()
        mock_peer = self._create_mock_peer()
        server.clients[mock_client] = mock_peer

        # Encode login payload: "user\0wrong"
        payload = b"user\0wrong"

        # Process login packet
        with patch.object(server, "_disconnect_client") as mock_disconnect:
            server._process_packet(mock_client, PacketType.LOGIN, payload)

            # Should fail
            mock_peer.send_packet.assert_called_with(PacketType.LOGIN_ERROR, b"Invalid password")
            mock_disconnect.assert_called_with(mock_client)

    def test_secrets_compare_digest_called(self):
        server = LiveServer()
        server.set_password("secret")

        mock_client = Mock()
        mock_peer = self._create_mock_peer()
        server.clients[mock_client] = mock_peer

        payload = b"user\0wrong"

        with patch(
            "py_rme_canary.core.protocols.live_server.secrets.compare_digest",
            return_value=False,
        ) as mock_compare:
            with patch.object(server, "_disconnect_client"):
                server._process_packet(mock_client, PacketType.LOGIN, payload)

            mock_compare.assert_called_once()
            # Verify arguments (note: order might vary but usually (a, b))
            args = mock_compare.call_args[0]
            assert "wrong" in args
            assert "secret" in args
