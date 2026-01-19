"""
Live Editing Client Implementation.

Ported from source/live_client.cpp
"""

import logging
import socket
import threading
from collections.abc import Callable

from .live_packets import ConnectionState, PacketType
from .live_socket import LiveSocket

log = logging.getLogger(__name__)


class LiveClient(LiveSocket):
    """
    Handles connection to a Live Server for collaborative editing.
    """

    def __init__(self, host: str = "localhost", port: int = 7171):
        super().__init__(None)
        self.host = host
        self.port = port
        self.state = ConnectionState.DISCONNECTED
        self.thread: threading.Thread | None = None
        self._running = False
        self._on_packet_received: Callable[[int, bytes], None] | None = None
        self._incoming_queue: list[tuple[int, bytes]] = []

    def pop_packet(self) -> tuple[int, bytes] | None:
        """Pop the next available packet from the queue (thread-safe enough for lists)."""
        if self._incoming_queue:
            return self._incoming_queue.pop(0)
        return None

    def connect(self) -> bool:
        """Initiates connection to the server."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.connect((self.host, self.port))
            self.socket = sock
            self.state = ConnectionState.CONNECTED

            self._running = True
            self.thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.thread.start()

            log.info(f"Connected to Live Server at {self.host}:{self.port}")
            return True
        except Exception as e:
            log.error(f"Failed to connect to {self.host}:{self.port}: {e}")
            self.state = ConnectionState.DISCONNECTED
            return False

    def disconnect(self) -> None:
        """Terminates the connection."""
        self._running = False
        self.close()
        self.state = ConnectionState.DISCONNECTED
        log.info("Disconnected from Live Server")

    def send_packet(self, packet_type: PacketType, payload: bytes) -> bool:
        """Sends a packet to the server."""
        if self.state < ConnectionState.CONNECTED or not self.socket:
            log.warning("Cannot send packet: Not connected")
            return False

        if not super().send_packet(packet_type, payload):
            log.error("Error sending packet")
            self.disconnect()
            return False
        return True

    def _receive_loop(self) -> None:
        """Background loop to handle incoming data."""
        if not self.socket:
            return

        while self._running:
            try:
                pkt = self.recv_packet()
                if not pkt:
                    break
                packet_type, payload = pkt
                self._handle_packet(int(packet_type), payload)

            except Exception as e:
                log.error(f"Receive loop error: {e}")
                break

        self.disconnect()

    def _handle_packet(self, packet_type: int, payload: bytes) -> None:
        """Dispatches received packet."""
        self._incoming_queue.append((packet_type, payload))
        if self._on_packet_received:
            self._on_packet_received(packet_type, payload)
        else:
            log.debug(f"Received packet {packet_type} with {len(payload)} bytes")
