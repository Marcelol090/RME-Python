"""
Live Editing Server Implementation.

Ported from source/live_server.cpp
"""

import logging
import secrets
import select
import socket
import threading
import time
from collections.abc import Callable
from contextlib import suppress
from typing import TYPE_CHECKING, Any

from .live_packets import PacketType, decode_cursor, encode_chat
from .live_peer import LivePeer

if TYPE_CHECKING:
    pass

log = logging.getLogger(__name__)

# Security constants
MAX_MAP_REQUEST_AREA = 65536  # Max tiles per map request (e.g. 256x256)
MAX_PACKETS_PER_SECOND = 50   # Max packets/sec per client


def _decode_login_payload(payload: bytes) -> tuple[str, str]:
    if not payload:
        return "", ""
    name_bytes, sep, rest = payload.partition(b"\0")
    name = name_bytes.decode("utf-8", errors="ignore")
    password = rest.decode("utf-8", errors="ignore") if sep else ""
    return name, password


def _encode_client_list(clients: dict[socket.socket, LivePeer]) -> bytes:
    """Encode connected client list for broadcast."""
    import struct

    peers = list(clients.values())
    data = struct.pack("<H", len(peers))
    for peer in peers:
        client_id = int(peer.client_id)
        r, g, b = peer.get_color()
        name_bytes = (peer.name or "Unknown").encode("utf-8")[:64]
        data += struct.pack("<I BBB B", client_id, r, g, b, len(name_bytes))
        data += name_bytes
    return data


class LiveServer:
    """
    Server for collaborative map editing.
    """

    def __init__(self, host: str = "127.0.0.1", port: int = 7171):
        self.host = host
        self.port = port
        self.socket: socket.socket | None = None
        self.clients: dict[socket.socket, LivePeer] = {}
        self._client_seq = 0
        self._running = False
        self.thread: threading.Thread | None = None
        self.name: str = "Live Server"
        self.password: str = ""
        self._banned_hosts: set[str] = set()
        self._incoming_queue: list[tuple[int, bytes]] = []
        self._queue_lock = threading.Lock()

        # Callback for map data requests: (x_min, y_min, x_max, y_max, z) -> list[tiles]
        self._map_provider: Callable[[int, int, int, int, int], Any] | None = None

    def set_map_provider(self, callback: Callable[[int, int, int, int, int], Any] | None) -> None:
        """Set callback to provide map data for sync requests."""
        self._map_provider = callback

    def set_name(self, name: str) -> None:
        self.name = str(name or "").strip() or "Live Server"

    def set_password(self, password: str) -> None:
        self.password = str(password or "")

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

    def pop_packet(self) -> tuple[int, bytes] | None:
        with self._queue_lock:
            if self._incoming_queue:
                return self._incoming_queue.pop(0)
        return None

    def broadcast_client_list(self) -> None:
        """Broadcast updated client list to all peers."""
        payload = _encode_client_list(self.clients)
        self.broadcast(PacketType.CLIENT_LIST, payload)
        with self._queue_lock:
            self._incoming_queue.append((int(PacketType.CLIENT_LIST), payload))

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
                        try:
                            if str(addr[0]) in self._banned_hosts:
                                log.info("Rejected banned host %s", addr[0])
                                client.close()
                                continue
                        except Exception:
                            pass
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
        peer = self.clients.get(client)
        if peer is None:
            return

        # Rate limiting logic
        current_time = time.time()
        # Reset counter if 1 second has passed
        if current_time - peer.last_packet_reset > 1.0:
            peer.packet_count = 0
            peer.last_packet_reset = current_time

        peer.packet_count += 1
        if peer.packet_count > MAX_PACKETS_PER_SECOND:
            log.warning(f"Rate limit exceeded for client {peer.name} ({peer.address})")
            self._disconnect_client(client)
            return

        if packet_type == PacketType.LOGIN:
            name, password = _decode_login_payload(payload)
            if self.password and not secrets.compare_digest(str(password), str(self.password)):
                peer.send_packet(PacketType.LOGIN_ERROR, b"Invalid password")
                self._disconnect_client(client)
                return
            peer.set_name(str(name))
            peer.set_password(str(password))
            peer.is_authenticated = True
            client_id = int(peer.client_id)
            peer.send_packet(PacketType.LOGIN_SUCCESS, client_id.to_bytes(4, "little", signed=False))
            # Broadcast updated client list
            self.broadcast_client_list()
            log.info(f"Client {name} logged in (id={client_id})")
            return

        if not peer.is_authenticated:
            log.warning(f"Unauthenticated packet {packet_type}")
            self._disconnect_client(client)
            return

        if packet_type == PacketType.CURSOR_UPDATE:
            # Decode and store cursor, then rebroadcast
            client_id, x, y, z = decode_cursor(payload)
            peer.set_cursor(x, y, z)
            self.broadcast(PacketType.CURSOR_UPDATE, payload, exclude=client)
            with self._queue_lock:
                self._incoming_queue.append((int(packet_type), payload))
            return

        if packet_type == PacketType.TILE_UPDATE:
            self.broadcast(PacketType.TILE_UPDATE, payload, exclude=client)
            with self._queue_lock:
                self._incoming_queue.append((int(packet_type), payload))
            return

        if packet_type == PacketType.MESSAGE:
            # Re-encode with client info for broadcast
            text = payload.decode("utf-8", errors="ignore")
            log.info(f"Chat from {peer.name}: {text}")
            broadcast_payload = encode_chat(peer.client_id, peer.name, text)
            self.broadcast(PacketType.MESSAGE, broadcast_payload)
            with self._queue_lock:
                self._incoming_queue.append((int(packet_type), broadcast_payload))
            return

        if packet_type == PacketType.MAP_REQUEST:
            # Handle map sync request
            self._handle_map_request(client, payload)
            return

    def _handle_map_request(self, client: socket.socket, payload: bytes) -> None:
        """Handle MAP_REQUEST from client."""
        from .tile_serializer import decode_map_request, encode_map_chunk

        peer = self.clients.get(client)
        if peer is None:
            return

        x_min, y_min, x_max, y_max, z = decode_map_request(payload)

        # Validate request size
        width = abs(x_max - x_min) + 1
        height = abs(y_max - y_min) + 1
        area = width * height

        if area > MAX_MAP_REQUEST_AREA:
            log.warning(f"Map request too large from {peer.name}: {area} tiles (max {MAX_MAP_REQUEST_AREA})")
            # Ignore request or maybe send error? For now, ignore.
            return

        log.info(f"Map request from {peer.name}: ({x_min},{y_min}) to ({x_max},{y_max}) z={z}")

        if self._map_provider is None:
            # No map provider, send empty response
            chunk = encode_map_chunk(0, 1, [], x_min=x_min, y_min=y_min, z=z)
            peer.send_packet(PacketType.MAP_CHUNK, chunk)
            return

        try:
            tiles = self._map_provider(x_min, y_min, x_max, y_max, z)
            if not tiles:
                tiles = []
        except Exception as e:
            log.error(f"Map provider error: {e}")
            tiles = []

        # Send tiles in chunks (max ~100 tiles per chunk)
        CHUNK_SIZE = 100
        tile_list = list(tiles)
        total_chunks = max(1, (len(tile_list) + CHUNK_SIZE - 1) // CHUNK_SIZE)

        for i in range(total_chunks):
            start = i * CHUNK_SIZE
            end = min(start + CHUNK_SIZE, len(tile_list))
            chunk_tiles = tile_list[start:end]
            chunk = encode_map_chunk(i, total_chunks, chunk_tiles, x_min=x_min, y_min=y_min, z=z)
            if not peer.send_packet(PacketType.MAP_CHUNK, chunk):
                break

    def _disconnect_client(self, client_sock: socket.socket) -> None:
        """Disconnects a client."""
        peer = self.clients.pop(client_sock, None)
        addr = peer.address if peer is not None else "Unknown"
        name = peer.name if peer is not None else "Unknown"
        with suppress(Exception):
            client_sock.close()
        log.info(f"Client {name} ({addr}) disconnected")
        # Broadcast updated client list
        if self.clients:
            self.broadcast_client_list()

    def kick_client(self, client_id: int, reason: str = "Disconnected by host") -> bool:
        """Kick a client by id."""
        for sock, peer in list(self.clients.items()):
            if int(peer.client_id) == int(client_id):
                with suppress(Exception):
                    peer.send_packet(PacketType.KICK, str(reason).encode("utf-8"))
                self._disconnect_client(sock)
                return True
        return False

    def ban_client(self, client_id: int, reason: str = "Banned by host") -> bool:
        """Ban a client by id and kick."""
        for sock, peer in list(self.clients.items()):
            if int(peer.client_id) == int(client_id):
                host = str(peer.address[0])
                if host:
                    self._banned_hosts.add(host)
                with suppress(Exception):
                    peer.send_packet(PacketType.KICK, str(reason).encode("utf-8"))
                self._disconnect_client(sock)
                return True
        return False
