"""Live peer wrapper for server-side connections (legacy-inspired)."""

from __future__ import annotations

import socket
from dataclasses import dataclass

from .live_packets import PacketType, encode_cursor
from .live_socket import LiveSocket

# Color palette for client cursors (similar to legacy RME)
PEER_COLORS: list[tuple[int, int, int]] = [
    (255, 0, 0),  # Red
    (0, 255, 0),  # Green
    (0, 0, 255),  # Blue
    (255, 255, 0),  # Yellow
    (255, 0, 255),  # Magenta
    (0, 255, 255),  # Cyan
    (255, 128, 0),  # Orange
    (128, 0, 255),  # Purple
]


@dataclass(slots=True)
class LivePeer(LiveSocket):
    """Represents a connected live-editing client on the server."""

    server: object | None
    address: tuple[str, int]
    client_id: int
    cursor_x: int = 0
    cursor_y: int = 0
    cursor_z: int = 0
    is_authenticated: bool = False
    packet_count: int = 0
    last_packet_reset: float = 0.0

    def __init__(
        self,
        *,
        server: object | None,
        sock: socket.socket,
        address: tuple[str, int],
        client_id: int,
    ) -> None:
        super().__init__(sock)
        self.server = server
        self.address = (str(address[0]), int(address[1]))
        self.client_id = int(client_id)
        self.cursor_x = 0
        self.cursor_y = 0
        self.cursor_z = 0
        self.is_authenticated = False
        self.packet_count = 0
        self.last_packet_reset = 0.0

    def get_color(self) -> tuple[int, int, int]:
        """Get assigned color for this peer based on client_id."""
        idx = (self.client_id - 1) % len(PEER_COLORS)
        return PEER_COLORS[idx]

    def set_cursor(self, x: int, y: int, z: int) -> None:
        """Update cursor position."""
        self.cursor_x = int(x)
        self.cursor_y = int(y)
        self.cursor_z = int(z)

    def send_cursor(self, payload: bytes) -> bool:
        """Send cursor update packet."""
        return self.send_packet(PacketType.CURSOR_UPDATE, payload)

    def broadcast_cursor(self) -> bool:
        """Broadcast current cursor position."""
        payload = encode_cursor(self.client_id, self.cursor_x, self.cursor_y, self.cursor_z)
        return self.send_cursor(payload)
