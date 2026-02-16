
import socket
import threading
import time
import pytest
from py_rme_canary.core.protocols.live_server import LiveServer
from py_rme_canary.core.protocols.live_packets import PacketType, NetworkHeader

def test_partial_packet_dos():
    """
    Test that a client sending partial packets DOES NOT block the server.
    This test should FAIL if the server is vulnerable to DoS.
    """
    # Start server on random port
    server = LiveServer(port=0)
    assert server.start()
    port = server.socket.getsockname()[1]

    server_thread = server.thread

    # Use context manager to ensure clean socket closing
    slow_sock = socket.socket()
    normal_sock = socket.socket()
    normal_sock.settimeout(2.0) # 2 seconds timeout

    try:
        # 1. Connect a "slow" client
        slow_sock.connect(('127.0.0.1', port))

        # Send just 1 byte of header and stop (simulating slowloris)
        slow_sock.send(b'\x01')

        # 2. Connect a normal client
        try:
            normal_sock.connect(('127.0.0.1', port))
        except TimeoutError:
            pytest.fail("Server blocked on accept? DoS successful.")

        # 3. Try to send login packet from normal client
        # Packet: Login (type 1)
        # Payload: "testuser\0password"
        payload = b"testuser\0password"
        header = NetworkHeader.pack(1, int(PacketType.LOGIN), len(payload))
        msg = header + payload

        normal_sock.sendall(msg)

        # 4. Wait for response (LOGIN_SUCCESS or ERROR)
        try:
            resp = normal_sock.recv(1024)
            if not resp:
                pytest.fail("Server closed connection unexpectedly")

            # If we received a response, it means the server processed our request
            # despite the slow client blocking the thread previously.
            if len(resp) >= 8:
                header = NetworkHeader.unpack(resp[:8])
                if header.packet_type == PacketType.LOGIN_SUCCESS:
                    print("Login success - server not blocked")
                else:
                    print(f"Login failed logic but server responded: {header.packet_type}")
            else:
                pytest.fail("Incomplete response form server")

        except TimeoutError:
            pytest.fail("Server blocked by partial packet! DoS vulnerability present.")

    finally:
        server.stop()
        slow_sock.close()
        normal_sock.close()
        # Ensure server thread stops
        if server_thread and server_thread.is_alive():
             server_thread.join(timeout=1.0)

if __name__ == "__main__":
    test_partial_packet_dos()
