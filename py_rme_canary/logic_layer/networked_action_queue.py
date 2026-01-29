"""NetworkedActionQueue for live collaboration.

Extends the standard action queue to broadcast tile changes to connected
live editing clients/server.

Layer: logic_layer (no PyQt6 imports)
Reference: legacy live_action.cpp
"""
from __future__ import annotations

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from py_rme_canary.core.protocols.live_client import LiveClient
    from py_rme_canary.core.protocols.live_server import LiveServer

log = logging.getLogger(__name__)


class DirtyList:
    """Tracks tiles modified during an action for network broadcast."""

    __slots__ = ("owner", "positions")

    def __init__(self) -> None:
        self.owner: int = 0  # client_id that originated the change
        self.positions: set[tuple[int, int, int]] = set()

    def add(self, x: int, y: int, z: int) -> None:
        """Add a position to the dirty list."""
        self.positions.add((int(x), int(y), int(z)))

    def clear(self) -> None:
        """Clear all tracked positions."""
        self.positions.clear()
        self.owner = 0

    def __len__(self) -> int:
        return len(self.positions)


class NetworkedActionQueue:
    """Action queue that broadcasts tile changes over the network.

    This wraps around the standard action mechanism and adds network
    broadcast capability for live editing sessions.

    Usage:
        queue = NetworkedActionQueue(editor_session)
        queue.set_live_client(client)  # For client mode
        # or
        queue.set_live_server(server)  # For server mode

        # During actions, call:
        queue.mark_dirty(x, y, z)

        # After action completes:
        queue.broadcast_dirty()
    """

    def __init__(self, session: Any = None) -> None:
        self.session = session
        self._dirty = DirtyList()
        self._live_client: LiveClient | None = None
        self._live_server: LiveServer | None = None
        self._on_broadcast: Callable[[DirtyList], None] | None = None

    def set_live_client(self, client: LiveClient | None) -> None:
        """Set the live client for broadcasting."""
        self._live_client = client
        self._live_server = None

    def set_live_server(self, server: LiveServer | None) -> None:
        """Set the live server for broadcasting."""
        self._live_server = server
        self._live_client = None

    def set_broadcast_callback(self, callback: Callable[[DirtyList], None] | None) -> None:
        """Set a callback for custom broadcast handling."""
        self._on_broadcast = callback

    def mark_dirty(self, x: int, y: int, z: int, *, owner: int = 0) -> None:
        """Mark a tile position as modified."""
        self._dirty.add(x, y, z)
        if owner != 0:
            self._dirty.owner = int(owner)

    def clear_dirty(self) -> None:
        """Clear the dirty list without broadcasting."""
        self._dirty.clear()

    def broadcast_dirty(self) -> int:
        """Broadcast all dirty tiles to connected peers.

        Returns:
            Number of positions broadcast
        """
        count = len(self._dirty)
        if count == 0:
            return 0

        # Custom callback takes priority
        if self._on_broadcast is not None:
            try:
                self._on_broadcast(self._dirty)
            except Exception as e:
                log.error(f"Broadcast callback error: {e}")

        # Broadcast via live client
        elif self._live_client is not None:
            self._broadcast_to_server()

        # Broadcast via live server
        elif self._live_server is not None:
            self._broadcast_to_clients()

        self._dirty.clear()
        return count

    def _broadcast_to_server(self) -> None:
        """Send tile updates to the server."""
        from py_rme_canary.core.protocols.live_packets import PacketType

        client = self._live_client
        if client is None:
            return

        # Encode positions as simple payload
        payload = self._encode_positions()
        if payload:
            client.send_packet(PacketType.TILE_UPDATE, payload)

    def _broadcast_to_clients(self) -> None:
        """Broadcast tile updates to all connected clients."""
        from py_rme_canary.core.protocols.live_packets import PacketType

        server = self._live_server
        if server is None:
            return

        payload = self._encode_positions()
        if payload:
            server.broadcast(PacketType.TILE_UPDATE, payload)

    def _encode_positions(self) -> bytes:
        """Encode dirty positions as network payload.

        Format: <count:u32> + <x:i32><y:i32><z:u8> * count
        """
        import struct

        positions = list(self._dirty.positions)
        if not positions:
            return b""

        result = struct.pack("<I", len(positions))
        for x, y, z in positions:
            result += struct.pack("<iiB", int(x), int(y), int(z))
        return result


def decode_tile_positions(payload: bytes) -> list[tuple[int, int, int]]:
    """Decode tile positions from network payload.

    Returns:
        List of (x, y, z) positions
    """
    import struct

    if len(payload) < 4:
        return []

    count = struct.unpack("<I", payload[:4])[0]
    positions = []
    offset = 4
    for _ in range(count):
        if offset + 9 > len(payload):
            break
        x, y, z = struct.unpack("<iiB", payload[offset : offset + 9])
        positions.append((int(x), int(y), int(z)))
        offset += 9
    return positions
