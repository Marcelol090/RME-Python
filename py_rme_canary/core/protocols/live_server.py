"""
Live Editing Server Implementation.

Ported from source/live_server.cpp
"""

import logging
import select
import socket
import threading

from .live_packets import PacketType
from .live_peer import LivePeer

log = logging.getLogger(__name__)


class LiveServer:
    """
    Server for collaborative map editing.
    """

    def __init__(self, host: str = "0.0.0.0", port: int = 7171):
        self.host = host
        self.port = port
        self.socket: socket.socket | None = None
        self.clients: dict[socket.socket, LivePeer] = {}
        self._client_seq = 0
        self._running = False
        self.thread: threading.Thread | None = None

    def start(self) -> bool:
        """Starts the server listener."""
        try:
            self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            self.socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            self.socket.bind((self.host, self.port))
            self.socket.listen(5)

            self._running = True
            self.thread = threading.Thread(target=self._accept_loop, daemon=True)
            self.thread.start()

            log.info(f"Live Server started on {self.host}:{self.port}")
            return True
        except Exception as e:
            log.error(f"Failed to start server: {e}")
            return False

    def stop(self) -> None:
        """Stops the server."""
        self._running = False
        if self.socket:
            self.socket.close()

        # Disconnect all clients
        for client_sock in list(self.clients.keys()):
            self._disconnect_client(client_sock)

        log.info("Live Server stopped")

    def broadcast(self, packet_type: PacketType, payload: bytes, exclude: socket.socket | None = None) -> None:
        """Broadcasts a packet to all connected clients."""
        for peer in list(self.clients.values()):
            sock = peer.socket
            if sock is None:
                continue
            if sock == exclude:
                continue
            if not peer.send_packet(packet_type, payload):
                self._disconnect_client(sock)

    def _accept_loop(self) -> None:
        """Main loop to accept connections and handle data."""
        if not self.socket:
            return

        while self._running:
            try:
                # Use select for non-blocking check
                readable, _, _ = select.select([self.socket] + list(self.clients.keys()), [], [], 1.0)

                for sock in readable:
                    if sock is self.socket:
                        client, addr = self.socket.accept()
                        log.info(f"Accepted connection from {addr}")
                        self._client_seq += 1
                        peer = LivePeer(
                            server=self, sock=client, address=(str(addr[0]), int(addr[1])), client_id=self._client_seq
                        )
                        self.clients[client] = peer
                    else:
                        self._handle_client_data(sock)

            except Exception as e:
                log.error(f"Server loop error: {e}")

    def _handle_client_data(self, client_sock: socket.socket) -> None:
        """Reads data from a client socket."""
        try:
            peer = self.clients.get(client_sock)
            if peer is None:
                self._disconnect_client(client_sock)
                return
            pkt = peer.recv_packet()
            if not pkt:
                self._disconnect_client(client_sock)
                return
            packet_type, payload = pkt
            self._process_packet(client_sock, int(packet_type), payload)

        except Exception:
            self._disconnect_client(client_sock)

    def _process_packet(self, client: socket.socket, packet_type: int, payload: bytes) -> None:
        """Business logic for handling packets."""
        # For now, just echo/broadcast to others
        # Example: Cursor update
        if packet_type == PacketType.CURSOR_UPDATE or packet_type == PacketType.TILE_UPDATE:
            self.broadcast(PacketType(packet_type), payload, exclude=client)
        elif packet_type == PacketType.MESSAGE:
            peer = self.clients.get(client)
            who = peer.address if peer is not None else "Unknown"
            log.info(f"Chat from {who}: {payload.decode('utf-8', errors='ignore')}")
            self.broadcast(PacketType.MESSAGE, payload, exclude=client)

    def _disconnect_client(self, client_sock: socket.socket) -> None:
        """Disconnects a client."""
        peer = self.clients.pop(client_sock, None)
        addr = peer.address if peer is not None else "Unknown"
        try:
            client_sock.close()
        except Exception:
            pass
        log.info(f"Client {addr} disconnected")
