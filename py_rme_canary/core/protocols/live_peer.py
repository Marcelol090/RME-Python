"""Live peer wrapper for server-side connections (legacy-inspired)."""

from __future__ import annotations

import socket
from dataclasses import dataclass

from .live_packets import PacketType
from .live_socket import LiveSocket


@dataclass(slots=True)
class LivePeer(LiveSocket):
    """Represents a connected live-editing client on the server."""

    server: object | None
    address: tuple[str, int]
    client_id: int

    def __init__(self, *, server: object | None, sock: socket.socket, address: tuple[str, int], client_id: int) -> None:
        super().__init__(sock)
        self.server = server
        self.address = (str(address[0]), int(address[1]))
        self.client_id = int(client_id)

    def send_cursor(self, payload: bytes) -> bool:
        return self.send_packet(PacketType.CURSOR_UPDATE, payload)
