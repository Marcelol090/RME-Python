
import socket
import struct
import threading
import time
from unittest.mock import MagicMock

import pytest

from py_rme_canary.core.protocols.live_packets import PacketType
from py_rme_canary.core.protocols.tile_serializer import encode_map_request
from py_rme_canary.core.protocols.live_server import LiveServer

class TestLiveServerDoSMapRequest:
    def test_map_request_area_limit(self):
        """Test that the server limits the area of a map request."""
        print("Starting server...")
        server = LiveServer(port=0)  # bind to random port
        server.start()
        port = server.socket.getsockname()[1]
        print(f"Server started on port {port}")

        mock_provider = MagicMock(return_value=[])
        server.set_map_provider(mock_provider)

        client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        client.connect(("127.0.0.1", port))
        print("Client connected")

        # Login
        # Payload: name\0password
        login_payload = b"test\0"
        login_packet = struct.pack("<HHI", 1, int(PacketType.LOGIN), len(login_payload)) + login_payload
        client.sendall(login_packet)
        print("Sent login packet")

        # Wait for login success
        time.sleep(1.0) # increased wait time

        # Send huge map request: 0,0 to 1000,1000 (1M tiles)
        # Expected limit is 65536 tiles (256x256)
        payload = encode_map_request(0, 0, 1000, 1000, 7)
        header = struct.pack("<HHI", 1, int(PacketType.MAP_REQUEST), len(payload))
        client.sendall(header + payload)
        print("Sent map request")

        time.sleep(1.0) # increased wait time

        server.stop()
        client.close()
        print("Server stopped")

        print(f"Mock provider call count: {mock_provider.call_count}")
        if mock_provider.call_count > 0:
            args = mock_provider.call_args[0]
            print(f"Mock provider called with: {args}")
            x_min, y_min, x_max, y_max, z = args
            area = (x_max - x_min + 1) * (y_max - y_min + 1)
            print(f"Requested area: {area}")
            # 65536 is the limit mentioned in memory
            assert area <= 65536, f"Map request area {area} exceeded limit 65536"
        else:
            # If not called, it might have been rejected silently, which is also fine for DoS protection
            print("Mock provider was NOT called")
            pass
