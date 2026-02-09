"""Live Cursor Broadcaster for collaborative editing.

This module provides cursor position broadcasting for live editing sessions.
Each connected user can see where others are working in real-time.

Reference:
    - GAP_ANALYSIS.md: P2 - Live Collaboration (Cursor Broadcasting)
    - Legacy: live_socket.cpp cursor handling

Architecture:
    - CursorBroadcaster: Manages outbound cursor updates
    - CursorReceiver: Processes incoming cursor positions
    - CursorOverlayData: Data for rendering remote cursors

Layer: core/protocols (no PyQt6 imports)
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from py_rme_canary.core.protocols.live_client import LiveClient
    from py_rme_canary.core.protocols.live_server import LiveServer

from .live_packets import PacketType, decode_cursor, encode_cursor

logger = logging.getLogger(__name__)


# Color palette for user cursors (up to 16 unique colors)
CURSOR_COLORS: list[tuple[int, int, int]] = [
    (255, 0, 0),  # Red
    (0, 255, 0),  # Green
    (0, 0, 255),  # Blue
    (255, 255, 0),  # Yellow
    (255, 0, 255),  # Magenta
    (0, 255, 255),  # Cyan
    (255, 128, 0),  # Orange
    (128, 0, 255),  # Purple
    (0, 255, 128),  # Spring Green
    (255, 0, 128),  # Rose
    (128, 255, 0),  # Lime
    (0, 128, 255),  # Azure
    (255, 128, 128),  # Light Red
    (128, 255, 128),  # Light Green
    (128, 128, 255),  # Light Blue
    (255, 255, 128),  # Light Yellow
]


@dataclass(slots=True)
class CursorOverlayData:
    """Data for rendering a remote user's cursor.

    Attributes:
        client_id: Unique identifier for the connected user.
        name: Display name of the user.
        x: Tile X coordinate.
        y: Tile Y coordinate.
        z: Floor level.
        color: RGB color tuple for this user.
        last_update: Timestamp of last position update.
        visible: Whether cursor should be rendered.
    """

    client_id: int
    name: str
    x: int
    y: int
    z: int
    color: tuple[int, int, int] = (255, 255, 255)
    last_update: float = 0.0
    visible: bool = True

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for rendering."""
        return {
            "client_id": self.client_id,
            "name": self.name,
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "color": self.color,
        }

    @classmethod
    def from_packet(cls, client_id: int, x: int, y: int, z: int, name: str = "") -> CursorOverlayData:
        """Create from decoded packet data."""
        color = CURSOR_COLORS[client_id % len(CURSOR_COLORS)]
        return cls(
            client_id=client_id,
            name=name or f"User_{client_id}",
            x=x,
            y=y,
            z=z,
            color=color,
            last_update=time.time(),
        )


@dataclass
class BroadcasterConfig:
    """Configuration for cursor broadcasting.

    Attributes:
        throttle_ms: Minimum time between broadcasts.
        timeout_seconds: Time before cursor is considered stale.
        max_cursors: Maximum remote cursors to track.
        broadcast_enabled: Whether to send own cursor.
        receive_enabled: Whether to show others' cursors.
    """

    throttle_ms: int = 50  # 20 FPS max broadcast rate
    timeout_seconds: float = 10.0
    max_cursors: int = 32
    broadcast_enabled: bool = True
    receive_enabled: bool = True


class CursorBroadcaster:
    """Manages broadcasting local cursor position to live peers.

    This class throttles cursor updates to prevent network flooding
    while maintaining responsive feedback for remote users.

    Usage:
        broadcaster = CursorBroadcaster(config)
        broadcaster.set_server(live_server)

        # On mouse move:
        broadcaster.update_position(x, y, z)
    """

    def __init__(self, config: BroadcasterConfig | None = None) -> None:
        self._config = config or BroadcasterConfig()
        self._lock = threading.Lock()

        # Connection references
        self._server: LiveServer | None = None
        self._client: LiveClient | None = None

        # Throttling state
        self._last_broadcast_time: float = 0.0
        self._last_position: tuple[int, int, int] = (0, 0, 0)
        self._pending_broadcast = False

        # Stats
        self._broadcasts_sent: int = 0
        self._broadcasts_throttled: int = 0

    @property
    def config(self) -> BroadcasterConfig:
        return self._config

    def set_server(self, server: LiveServer | None) -> None:
        """Set the live server for broadcasting (server mode)."""
        with self._lock:
            self._server = server
            self._client = None

    def set_client(self, client: LiveClient | None) -> None:
        """Set the live client for broadcasting (client mode)."""
        with self._lock:
            self._client = client
            self._server = None

    def update_position(self, x: int, y: int, z: int, *, force: bool = False) -> bool:
        """Update and potentially broadcast cursor position.

        The broadcast is throttled to respect the configured interval.

        Args:
            x, y, z: Tile coordinates.
            force: Bypass throttling.

        Returns:
            True if broadcast was sent.
        """
        if not self._config.broadcast_enabled:
            return False

        now = time.time()
        throttle_seconds = self._config.throttle_ms / 1000.0

        with self._lock:
            new_pos = (int(x), int(y), int(z))

            # Check if position changed
            if new_pos == self._last_position and not force:
                return False

            self._last_position = new_pos

            # Check throttle
            if not force and (now - self._last_broadcast_time) < throttle_seconds:
                self._pending_broadcast = True
                self._broadcasts_throttled += 1
                return False

            # Broadcast
            self._do_broadcast(new_pos)
            self._last_broadcast_time = now
            self._pending_broadcast = False
            self._broadcasts_sent += 1

        return True

    def flush(self) -> bool:
        """Force broadcast of pending position update.

        Returns:
            True if there was a pending update to send.
        """
        with self._lock:
            if not self._pending_broadcast:
                return False

            self._do_broadcast(self._last_position)
            self._pending_broadcast = False
            self._broadcasts_sent += 1
            self._last_broadcast_time = time.time()

        return True

    def _do_broadcast(self, pos: tuple[int, int, int]) -> None:
        """Send cursor update packet."""
        x, y, z = pos

        if self._server is not None:
            # Server mode: broadcast to all clients
            try:
                payload = encode_cursor(0, x, y, z)  # 0 = server
                self._server.broadcast(PacketType.CURSOR_UPDATE, payload)
            except Exception as e:
                logger.debug("Cursor broadcast failed (server): %s", e)

        elif self._client is not None:
            # Client mode: send to server
            try:
                client_id = getattr(self._client, "client_id", 0)
                payload = encode_cursor(client_id, x, y, z)
                # Corrected method: send_packet instead of send
                self._client.send_packet(PacketType.CURSOR_UPDATE, payload)
            except Exception as e:
                logger.debug("Cursor broadcast failed (client): %s", e)

    def get_stats(self) -> dict[str, int]:
        """Get broadcasting statistics."""
        with self._lock:
            return {
                "broadcasts_sent": self._broadcasts_sent,
                "broadcasts_throttled": self._broadcasts_throttled,
            }


class CursorReceiver:
    """Receives and manages remote cursor positions.

    This class tracks cursor positions from all connected users
    and provides data for rendering cursor overlays.

    Usage:
        receiver = CursorReceiver(config)
        receiver.set_name_resolver(lambda cid: get_user_name(cid))

        # When packet received:
        receiver.handle_cursor_packet(payload)

        # For rendering:
        cursors = receiver.get_visible_cursors()
    """

    def __init__(self, config: BroadcasterConfig | None = None) -> None:
        self._config = config or BroadcasterConfig()
        self._lock = threading.Lock()

        # Remote cursors: client_id -> CursorOverlayData
        self._cursors: dict[int, CursorOverlayData] = {}

        # Name resolver callback
        self._name_resolver: Callable[[int], str] | None = None

        # Update callback
        self._on_cursor_update: Callable[[CursorOverlayData], None] | None = None

        # Stats
        self._packets_received: int = 0

    def set_name_resolver(self, resolver: Callable[[int], str]) -> None:
        """Set callback to resolve client_id to display name."""
        self._name_resolver = resolver

    def set_update_callback(self, callback: Callable[[CursorOverlayData], None]) -> None:
        """Set callback for cursor position updates."""
        self._on_cursor_update = callback

    def handle_cursor_packet(self, payload: bytes, *, exclude_self: int = -1) -> CursorOverlayData | None:
        """Process an incoming cursor update packet.

        Args:
            payload: Raw packet data.
            exclude_self: Client ID to ignore (own cursor).

        Returns:
            Updated cursor data, or None if ignored.
        """
        if not self._config.receive_enabled:
            return None

        client_id, x, y, z = decode_cursor(payload)

        if client_id == exclude_self:
            return None

        with self._lock:
            self._packets_received += 1

            # Check limit
            if client_id not in self._cursors and len(self._cursors) >= self._config.max_cursors:
                # Remove oldest cursor
                oldest_id = min(self._cursors.keys(), key=lambda k: self._cursors[k].last_update)
                del self._cursors[oldest_id]

            # Get or create cursor data
            if client_id in self._cursors:
                cursor = self._cursors[client_id]
                cursor.x = x
                cursor.y = y
                cursor.z = z
                cursor.last_update = time.time()
                cursor.visible = True
            else:
                name = ""
                if self._name_resolver:
                    try:
                        name = self._name_resolver(client_id)
                    except Exception:
                        pass

                cursor = CursorOverlayData.from_packet(client_id, x, y, z, name)
                self._cursors[client_id] = cursor

        # Notify callback
        if self._on_cursor_update:
            try:
                self._on_cursor_update(cursor)
            except Exception:
                pass

        return cursor

    def remove_cursor(self, client_id: int) -> bool:
        """Remove a cursor (e.g., when user disconnects).

        Args:
            client_id: ID of cursor to remove.

        Returns:
            True if cursor existed and was removed.
        """
        with self._lock:
            if client_id in self._cursors:
                del self._cursors[client_id]
                return True
        return False

    def get_visible_cursors(self, current_floor: int | None = None) -> list[CursorOverlayData]:
        """Get list of visible remote cursors.

        Args:
            current_floor: If provided, only return cursors on this floor.

        Returns:
            List of cursor data for rendering.
        """
        now = time.time()
        timeout = self._config.timeout_seconds
        result: list[CursorOverlayData] = []

        with self._lock:
            for cursor in self._cursors.values():
                # Check timeout
                if (now - cursor.last_update) > timeout:
                    cursor.visible = False
                    continue

                # Check floor filter
                if current_floor is not None and cursor.z != current_floor:
                    continue

                if cursor.visible:
                    result.append(cursor)

        return result

    def get_cursor_overlays(self, current_floor: int | None = None) -> list[dict[str, Any]]:
        """Get cursor data in dict format for rendering.

        Args:
            current_floor: If provided, only return cursors on this floor.

        Returns:
            List of dicts ready for MapDrawer.
        """
        return [c.to_dict() for c in self.get_visible_cursors(current_floor)]

    def clear(self) -> int:
        """Remove all tracked cursors.

        Returns:
            Number of cursors cleared.
        """
        with self._lock:
            count = len(self._cursors)
            self._cursors.clear()
        return count

    def get_stats(self) -> dict[str, int]:
        """Get receiver statistics."""
        with self._lock:
            return {
                "packets_received": self._packets_received,
                "cursors_tracked": len(self._cursors),
            }


class CursorManager:
    """Combined manager for cursor broadcasting and receiving.

    This is a convenience class that wraps both broadcaster and
    receiver into a single interface.

    Usage:
        manager = CursorManager()
        manager.set_server(live_server)

        # Update own cursor:
        manager.update_position(x, y, z)

        # Get cursors for rendering:
        overlays = manager.get_overlays(current_floor=7)
    """

    def __init__(self, config: BroadcasterConfig | None = None) -> None:
        self._config = config or BroadcasterConfig()
        self.broadcaster = CursorBroadcaster(self._config)
        self.receiver = CursorReceiver(self._config)

    def set_server(self, server: LiveServer | None) -> None:
        """Set live server for both broadcasting and receiving."""
        self.broadcaster.set_server(server)

    def set_client(self, client: LiveClient | None) -> None:
        """Set live client for both broadcasting and receiving."""
        self.broadcaster.set_client(client)

    def update_position(self, x: int, y: int, z: int, *, force: bool = False) -> bool:
        """Update and broadcast own cursor position."""
        return self.broadcaster.update_position(x, y, z, force=force)

    def handle_packet(self, payload: bytes, exclude_self: int = -1) -> CursorOverlayData | None:
        """Handle incoming cursor packet."""
        return self.receiver.handle_cursor_packet(payload, exclude_self=exclude_self)

    def get_overlays(self, current_floor: int | None = None) -> list[dict[str, Any]]:
        """Get cursor overlay data for rendering."""
        return self.receiver.get_cursor_overlays(current_floor)

    def remove_user(self, client_id: int) -> bool:
        """Remove cursor for disconnected user."""
        return self.receiver.remove_cursor(client_id)

    def flush(self) -> bool:
        """Flush pending broadcast."""
        return self.broadcaster.flush()

    def clear(self) -> None:
        """Clear all state."""
        self.receiver.clear()
