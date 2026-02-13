"""Live socket base helpers (legacy-inspired).

This module provides a minimal socket wrapper for the live-editing MVP.
It centralizes framing (NetworkHeader) and basic send/receive utilities.
"""

from __future__ import annotations

import logging
import socket
import threading
from contextlib import suppress

from .live_packets import NetworkHeader, PacketType

log = logging.getLogger(__name__)

# Max payload size to prevent OOM attacks (16MB)
MAX_PAYLOAD_SIZE = 16 * 1024 * 1024


class LiveSocket:
    """Shared helpers for live client/server sockets."""

    def __init__(self, sock: socket.socket | None = None) -> None:
        self.socket: socket.socket | None = sock
        self.name: str = ""
        self.password: str = ""
        self.last_error: str = ""
        self._lock = threading.Lock()

    def set_name(self, name: str) -> bool:
        self.name = str(name)
        return True

    def set_password(self, password: str) -> bool:
        self.password = str(password)
        return True

    def set_last_error(self, error: str) -> None:
        self.last_error = str(error)

    def get_host_name(self) -> str:
        sock = self.socket
        if sock is None:
            return ""
        try:
            host, _port = sock.getpeername()
            return str(host)
        except OSError:
            try:
                host, _port = sock.getsockname()
                return str(host)
            except OSError:
                return ""

    def close(self) -> None:
        sock = self.socket
        self.socket = None
        if sock is None:
            return
        with suppress(OSError):
            sock.close()

    def send_packet(self, packet_type: PacketType, payload: bytes) -> bool:
        """Send a framed packet over the socket."""

        sock = self.socket
        if sock is None:
            return False

        header = NetworkHeader.pack(1, int(packet_type), len(payload))
        msg = header + payload
        try:
            with self._lock:
                sock.sendall(msg)
            return True
        except OSError as exc:
            self.set_last_error(str(exc))
            log.error("LiveSocket send failed: %s", exc)
            return False

    def recv_packet(self) -> tuple[int, bytes] | None:
        """Receive a single packet (blocking)."""

        sock = self.socket
        if sock is None:
            return None

        header_size = 8
        header_data = self._read_n_bytes(header_size)
        if not header_data:
            return None

        header = NetworkHeader.unpack(header_data)

        if header.size > MAX_PAYLOAD_SIZE:
            log.warning(f"Packet too large: {header.size} > {MAX_PAYLOAD_SIZE}. Disconnecting.")
            self.close()
            return None

        payload = self._read_n_bytes(int(header.size))
        if payload is None:
            return None

        return int(header.packet_type), payload

    def _read_n_bytes(self, n: int) -> bytes | None:
        sock = self.socket
        if sock is None:
            return None
        data = b""
        while len(data) < n:
            try:
                chunk = sock.recv(n - len(data))
            except OSError:
                return None
            if not chunk:
                return None
            data += chunk
        return data
