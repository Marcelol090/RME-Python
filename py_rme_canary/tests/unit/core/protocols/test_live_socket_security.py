import struct
import pytest
from unittest.mock import MagicMock
from py_rme_canary.core.protocols.live_socket import LiveSocket
from py_rme_canary.core.protocols.live_packets import PacketType

class TestLiveSocketSecurity:
    def test_live_socket_dos_protection(self):
        """
        Verify DoS protection: LiveSocket rejects huge payloads.
        """
        mock_sock = MagicMock()
        live_socket = LiveSocket(sock=mock_sock)

        # Huge payload size (e.g., 20MB)
        HUGE_SIZE = 20 * 1024 * 1024
        # Header: version=1, type=MESSAGE, size=HUGE_SIZE
        header_data = struct.pack("<HHI", 1, PacketType.MESSAGE, HUGE_SIZE)

        # Mock recv behavior
        mock_sock.recv.side_effect = [header_data, b""]

        # Call recv_packet
        result = live_socket.recv_packet()

        # Verify result is None (rejected)
        assert result is None

        # Verify calls to recv
        calls = mock_sock.recv.mock_calls

        # First call: Read header (8 bytes)
        assert len(calls) >= 1
        assert calls[0].args[0] == 8

        # Verify that it did NOT attempt to read HUGE_SIZE bytes
        # Iterate over all calls and ensure none of them requested HUGE_SIZE
        for call in calls:
            requested_bytes = call.args[0]
            assert requested_bytes != HUGE_SIZE, f"Vulnerability exposed: Attempted to read {requested_bytes} bytes!"

        # Verify socket close was called
        mock_sock.close.assert_called()
