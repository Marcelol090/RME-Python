"""Live Editing Client Implementation.

Ported from source/live_client.cpp

Includes auto-reconnect with exponential backoff to recover
from transient network failures without user intervention.
"""

from __future__ import annotations

import logging
import socket
import struct
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .live_packets import ConnectionState, PacketType, encode_cursor
from .live_socket import LiveSocket

log = logging.getLogger(__name__)


@dataclass
class ReconnectConfig:
    """Configuration for automatic reconnection.

    Attributes:
        enabled: Whether auto-reconnect is active.
        max_attempts: Maximum number of reconnect attempts (0 = unlimited).
        base_delay: Initial delay between attempts in seconds.
        max_delay: Maximum delay (cap for exponential growth).
        backoff_factor: Multiplier applied each failed attempt.
        jitter: Random factor added (0.0–1.0) to avoid thundering herd.
    """

    enabled: bool = True
    max_attempts: int = 10
    base_delay: float = 1.0
    max_delay: float = 30.0
    backoff_factor: float = 2.0
    jitter: float = 0.1


def _encode_login_payload(name: str, password: str) -> bytes:
    name_bytes = str(name or "").encode("utf-8")
    password_bytes = str(password or "").encode("utf-8")
    return name_bytes + b"\0" + password_bytes


class LiveClient(LiveSocket):
    """Handles connection to a Live Server for collaborative editing.

    Supports automatic reconnection with exponential backoff
    when the connection is lost unexpectedly.
    """

    def __init__(
        self,
        host: str = "localhost",
        port: int = 7171,
        *,
        reconnect_config: ReconnectConfig | None = None,
    ) -> None:
        super().__init__(None)
        self.host = host
        self.port = port
        self.state = ConnectionState.DISCONNECTED
        self.thread: threading.Thread | None = None
        self._running = False
        self._on_packet_received: Callable[[int, bytes], None] | None = None
        self._incoming_queue: list[tuple[int, bytes]] = []
        self._queue_lock = threading.Lock()
        self.client_id: int | None = None

        # Auto-reconnect
        self._reconnect_cfg = reconnect_config or ReconnectConfig()
        self._reconnect_attempt: int = 0
        self._reconnect_thread: threading.Thread | None = None
        self._intentional_disconnect: bool = False

        # Connection event callbacks
        self._on_connected: Callable[[], None] | None = None
        self._on_disconnected: Callable[[str], None] | None = None
        self._on_reconnecting: Callable[[int, float], None] | None = None

        # Callbacks for specific events
        self._on_cursor_update: Callable[[int, int, int, int], None] | None = None
        self._on_chat_message: Callable[[int, str, str], None] | None = None
        self._on_client_list: Callable[[list[dict[str, Any]]], None] | None = None
        self._on_map_chunk: Callable[[dict[str, Any]], None] | None = None
        self._on_tile_update: Callable[[bytes], None] | None = None

        # Map chunk reception
        self._map_chunks: dict[int, dict[str, Any]] = {}
        self._expected_chunks: int = 0

    def set_cursor_callback(self, callback: Callable[[int, int, int, int], None] | None) -> None:
        """Set callback for cursor updates: (client_id, x, y, z)."""
        self._on_cursor_update = callback

    def set_chat_callback(self, callback: Callable[[int, str, str], None] | None) -> None:
        """Set callback for chat messages: (client_id, name, message)."""
        self._on_chat_message = callback

    def set_client_list_callback(self, callback: Callable[[list[dict[str, Any]]], None] | None) -> None:
        """Set callback for client list updates."""
        self._on_client_list = callback

    def set_map_chunk_callback(self, callback: Callable[[dict[str, Any]], None] | None) -> None:
        """Set callback for map chunks."""
        self._on_map_chunk = callback

    def set_tile_update_callback(self, callback: Callable[[bytes], None] | None) -> None:
        """Set callback for tile updates."""
        self._on_tile_update = callback

    # --- Connection lifecycle callbacks ---

    def set_connected_callback(self, callback: Callable[[], None] | None) -> None:
        """Set callback invoked after a successful (re)connection."""
        self._on_connected = callback

    def set_disconnected_callback(self, callback: Callable[[str], None] | None) -> None:
        """Set callback invoked on disconnection. Receives reason string."""
        self._on_disconnected = callback

    def set_reconnecting_callback(
        self, callback: Callable[[int, float], None] | None
    ) -> None:
        """Set callback invoked before each reconnect attempt.

        Receives (attempt_number, delay_seconds).
        """
        self._on_reconnecting = callback

    @property
    def reconnect_config(self) -> ReconnectConfig:
        """Return the current reconnect configuration."""
        return self._reconnect_cfg

    @reconnect_config.setter
    def reconnect_config(self, cfg: ReconnectConfig) -> None:
        self._reconnect_cfg = cfg

    def pop_packet(self) -> tuple[int, bytes] | None:
        """Pop the next available packet from the queue (thread-safe enough for lists)."""
        with self._queue_lock:
            if self._incoming_queue:
                return self._incoming_queue.pop(0)
            return None

    def connect(self) -> bool:
        """Initiates connection to the server.

        Resets the intentional-disconnect flag so that auto-reconnect
        can kick in if the connection drops unexpectedly.
        """
        self._intentional_disconnect = False
        self._reconnect_attempt = 0
        return self._try_connect()

    def _try_connect(self) -> bool:
        """Low-level connection attempt (no flag reset)."""
        try:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(10.0)
            sock.connect((self.host, self.port))
            sock.settimeout(None)
            self.socket = sock
            self.state = ConnectionState.CONNECTED

            self._running = True
            self.thread = threading.Thread(target=self._receive_loop, daemon=True)
            self.thread.start()

            payload = _encode_login_payload(self.name, self.password)
            if not super().send_packet(PacketType.LOGIN, payload):
                log.error("Failed to send login packet")
                self.disconnect()
                return False

            log.info("Connected to Live Server at %s:%s", self.host, self.port)
            self._reconnect_attempt = 0

            if self._on_connected:
                try:
                    self._on_connected()
                except Exception:
                    pass

            return True
        except Exception as e:
            log.error("Failed to connect to %s:%s: %s", self.host, self.port, e)
            self.state = ConnectionState.DISCONNECTED
            return False

    def disconnect(self) -> None:
        """Terminates the connection intentionally (no auto-reconnect)."""
        self._intentional_disconnect = True
        self._do_disconnect("User requested disconnect")

    def _do_disconnect(self, reason: str = "Connection lost") -> None:
        """Internal disconnect handler."""
        was_connected = self.state >= ConnectionState.CONNECTED
        self._running = False
        self.close()
        self.state = ConnectionState.DISCONNECTED
        log.info("Disconnected from Live Server: %s", reason)

        if was_connected and self._on_disconnected:
            try:
                self._on_disconnected(reason)
            except Exception:
                pass

        # Trigger auto-reconnect if the disconnect was NOT intentional
        if was_connected and not self._intentional_disconnect:
            self._schedule_reconnect()

    def _schedule_reconnect(self) -> None:
        """Start the reconnection loop in a background thread."""
        cfg = self._reconnect_cfg
        if not cfg.enabled:
            return

        if cfg.max_attempts > 0 and self._reconnect_attempt >= cfg.max_attempts:
            log.warning(
                "Auto-reconnect exhausted (%d attempts), giving up",
                self._reconnect_attempt,
            )
            return

        # Don't start a second reconnect thread
        if self._reconnect_thread and self._reconnect_thread.is_alive():
            return

        self._reconnect_thread = threading.Thread(
            target=self._reconnect_loop, daemon=True
        )
        self._reconnect_thread.start()

    def _reconnect_loop(self) -> None:
        """Exponential backoff reconnection loop."""
        import random

        cfg = self._reconnect_cfg
        success = False

        while not self._intentional_disconnect:
            self._reconnect_attempt += 1

            if cfg.max_attempts > 0 and self._reconnect_attempt > cfg.max_attempts:
                log.warning("Max reconnect attempts reached (%d)", cfg.max_attempts)
                break

            # Calculate delay with exponential backoff + jitter
            delay = min(
                cfg.base_delay * (cfg.backoff_factor ** (self._reconnect_attempt - 1)),
                cfg.max_delay,
            )
            if cfg.jitter > 0:
                delay += random.uniform(0, cfg.jitter * delay)  # noqa: S311

            log.info(
                "Reconnect attempt %d in %.1fs ...",
                self._reconnect_attempt,
                delay,
            )

            if self._on_reconnecting:
                try:
                    self._on_reconnecting(self._reconnect_attempt, delay)
                except Exception:
                    pass

            time.sleep(delay)

            if self._try_connect():
                log.info(
                    "Reconnected successfully after %d attempt(s)",
                    self._reconnect_attempt,
                )
                success = True
                break

        if not success:
            log.info("Reconnection loop ended")

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

    def send_cursor_update(self, x: int, y: int, z: int) -> bool:
        """Send cursor position update."""
        if self.client_id is None:
            return False
        payload = encode_cursor(self.client_id, x, y, z)
        return self.send_packet(PacketType.CURSOR_UPDATE, payload)

    def send_chat_message(self, message: str) -> bool:
        """Send a chat message."""
        payload = str(message or "").encode("utf-8")
        return self.send_packet(PacketType.MESSAGE, payload)

    def request_map(self, x_min: int, y_min: int, x_max: int, y_max: int, z: int) -> bool:
        """Request map data from server."""
        from .tile_serializer import encode_map_request

        payload = encode_map_request(x_min, y_min, x_max, y_max, z)
        self._map_chunks.clear()
        self._expected_chunks = 0
        return self.send_packet(PacketType.MAP_REQUEST, payload)

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
                log.error("Receive loop error: %s", e)
                break

        # Use _do_disconnect so auto-reconnect can kick in
        if not self._intentional_disconnect:
            self._do_disconnect("Connection lost")

    def _handle_packet(self, packet_type: int, payload: bytes) -> None:
        """Queue received packet for polling on the main thread."""
        with self._queue_lock:
            self._incoming_queue.append((int(packet_type), payload))
        log.debug("Queued packet %s with %s bytes", int(packet_type), len(payload))

    def _handle_client_list(self, payload: bytes) -> None:
        """Parse and dispatch client list update."""
        if len(payload) < 2:
            return
        if self._on_client_list:
            try:
                count = struct.unpack("<H", payload[:2])[0]
                _ = count  # keep legacy code path available if callbacks are used.
            except Exception:
                return

    def _handle_map_chunk(self, payload: bytes) -> None:
        """Handle incoming map chunk."""
        from .tile_serializer import decode_map_chunk

        chunk = decode_map_chunk(payload)
        chunk_id = int(chunk.get("chunk_id", 0))
        total = int(chunk.get("total_chunks", 1))

        self._expected_chunks = total
        self._map_chunks[chunk_id] = chunk

        if self._on_map_chunk:
            self._on_map_chunk(chunk)

        log.debug("Received map chunk %d/%d with %d tiles", chunk_id + 1, total, len(chunk.get("tiles", [])))
