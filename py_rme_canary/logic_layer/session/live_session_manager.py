"""Live Session Manager for collaborative editing.

Orchestrates the complete live editing lifecycle:
- Connection/disconnection with auto-reconnect
- Cursor broadcasting integration
- Chat message routing
- Connection state machine with event notifications
- Session metrics and diagnostics

Layer: logic_layer (no PyQt6 imports)
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

logger = logging.getLogger(__name__)


class SessionState(Enum):
    """Live session connection states."""

    IDLE = auto()
    CONNECTING = auto()
    CONNECTED = auto()
    AUTHENTICATED = auto()
    SYNCING = auto()
    ACTIVE = auto()
    RECONNECTING = auto()
    DISCONNECTING = auto()
    ERROR = auto()


@dataclass
class SessionMetrics:
    """Metrics for a live editing session.

    Attributes:
        connected_at: Timestamp when connected (0 if never).
        disconnected_at: Last disconnect time.
        reconnect_count: Total reconnection attempts.
        packets_sent: Total outbound packets.
        packets_received: Total inbound packets.
        bytes_sent: Total bytes sent.
        bytes_received: Total bytes received.
        last_latency_ms: Last measured round-trip latency.
    """

    connected_at: float = 0.0
    disconnected_at: float = 0.0
    reconnect_count: int = 0
    packets_sent: int = 0
    packets_received: int = 0
    bytes_sent: int = 0
    bytes_received: int = 0
    last_latency_ms: float = 0.0

    @property
    def uptime_seconds(self) -> float:
        """Seconds since connection was established."""
        if self.connected_at <= 0:
            return 0.0
        end = self.disconnected_at if self.disconnected_at > self.connected_at else time.time()
        return end - self.connected_at


@dataclass
class SessionInfo:
    """Information about the current live session.

    Attributes:
        host: Server hostname or IP.
        port: Server port.
        name: Local user display name.
        is_host: Whether we are hosting.
        server_name: Remote server display name.
        client_id: Assigned client ID (set after auth).
        state: Current session state.
        metrics: Session metrics.
        connected_users: List of connected user info dicts.
    """

    host: str = ""
    port: int = 7171
    name: str = ""
    is_host: bool = False
    server_name: str = ""
    client_id: int = 0
    state: SessionState = SessionState.IDLE
    metrics: SessionMetrics = field(default_factory=SessionMetrics)
    connected_users: list[dict[str, Any]] = field(default_factory=list)


class LiveSessionManager:
    """High-level manager for live editing sessions.

    Provides a clean event-driven API for the UI layer to observe
    connection state changes without polling.

    Usage::

        manager = LiveSessionManager()
        manager.on_state_changed = my_callback
        manager.on_chat_received = my_chat_handler

        manager.connect("127.0.0.1", 7171, name="Editor1")
        # ... later ...
        manager.disconnect()
    """

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._info = SessionInfo()

        # Event callbacks (set by UI layer)
        self.on_state_changed: Callable[[SessionState, SessionState], None] | None = None
        self.on_chat_received: Callable[[int, str, str], None] | None = None
        self.on_cursor_updated: Callable[[int, int, int, int], None] | None = None
        self.on_client_list_updated: Callable[[list[dict[str, Any]]], None] | None = None
        self.on_error: Callable[[str], None] | None = None

        # Internal references (set during connect)
        self._client: Any = None  # LiveClient
        self._server: Any = None  # LiveServer
        self._cursor_manager: Any = None  # CursorManager

    @property
    def info(self) -> SessionInfo:
        """Read-only access to current session information."""
        return self._info

    @property
    def state(self) -> SessionState:
        """Current session state."""
        return self._info.state

    @property
    def is_active(self) -> bool:
        """Whether the session is connected and usable."""
        return self._info.state in (
            SessionState.CONNECTED,
            SessionState.AUTHENTICATED,
            SessionState.SYNCING,
            SessionState.ACTIVE,
        )

    def _set_state(self, new_state: SessionState) -> None:
        """Update state and fire callback."""
        old = self._info.state
        if old == new_state:
            return
        self._info.state = new_state
        logger.info("Session state: %s -> %s", old.name, new_state.name)
        if self.on_state_changed:
            try:
                self.on_state_changed(old, new_state)
            except Exception:
                pass

    def connect(
        self,
        host: str,
        port: int,
        *,
        name: str = "",
        password: str = "",
    ) -> bool:
        """Connect to a remote live editing server.

        Args:
            host: Server address.
            port: Server port.
            name: Display name for this user.
            password: Server password (if required).

        Returns:
            True if the initial connection succeeded.
        """
        from py_rme_canary.core.protocols.live_client import LiveClient, ReconnectConfig
        from py_rme_canary.core.protocols.cursor_broadcaster import CursorManager

        with self._lock:
            if self.is_active:
                self.disconnect()

            self._set_state(SessionState.CONNECTING)
            self._info.host = str(host)
            self._info.port = int(port)
            self._info.name = str(name or "")
            self._info.is_host = False

            client = LiveClient(
                host=str(host),
                port=int(port),
                reconnect_config=ReconnectConfig(enabled=True),
            )
            if name:
                client.set_name(str(name))
            if password:
                client.set_password(str(password))

            # Wire up lifecycle callbacks
            client.set_connected_callback(self._on_client_connected)
            client.set_disconnected_callback(self._on_client_disconnected)
            client.set_reconnecting_callback(self._on_client_reconnecting)

            self._client = client

            # Set up cursor manager
            cm = CursorManager()
            cm.set_client(client)
            self._cursor_manager = cm

            ok = client.connect()
            if not ok:
                self._set_state(SessionState.ERROR)
                self._info.metrics.disconnected_at = time.time()
                return False

            self._info.metrics.connected_at = time.time()
            self._set_state(SessionState.CONNECTED)
            return True

    def host_server(
        self,
        *,
        host: str = "127.0.0.1",
        port: int = 7171,
        name: str = "",
        password: str = "",
    ) -> bool:
        """Start hosting a live editing server.

        Args:
            host: Bind address.
            port: Port to listen on.
            name: Server display name.
            password: Server password.

        Returns:
            True if the server started successfully.
        """
        from py_rme_canary.core.protocols.live_server import LiveServer
        from py_rme_canary.core.protocols.cursor_broadcaster import CursorManager

        with self._lock:
            if self._server is not None:
                return True

            self._set_state(SessionState.CONNECTING)
            self._info.host = str(host)
            self._info.port = int(port)
            self._info.name = str(name or "Host")
            self._info.server_name = str(name or "Live Server")
            self._info.is_host = True

            server = LiveServer(host=str(host), port=int(port))
            if name:
                server.set_name(str(name))
            if password:
                server.set_password(str(password))

            self._server = server

            cm = CursorManager()
            cm.set_server(server)
            self._cursor_manager = cm

            ok = server.start()
            if not ok:
                self._set_state(SessionState.ERROR)
                self._server = None
                return False

            self._info.metrics.connected_at = time.time()
            self._set_state(SessionState.ACTIVE)
            return True

    def disconnect(self) -> None:
        """Disconnect from session (client or server)."""
        with self._lock:
            self._set_state(SessionState.DISCONNECTING)

            if self._client:
                self._client.disconnect()
                self._client = None

            if self._server:
                self._server.stop()
                self._server = None

            if self._cursor_manager:
                self._cursor_manager.clear()
                self._cursor_manager = None

            self._info.metrics.disconnected_at = time.time()
            self._info.connected_users.clear()
            self._set_state(SessionState.IDLE)

    def send_chat(self, message: str) -> bool:
        """Send a chat message to the session."""
        if self._client and self.is_active:
            return bool(self._client.send_chat_message(str(message)))
        return False

    def update_cursor(self, x: int, y: int, z: int) -> bool:
        """Broadcast local cursor position."""
        if self._cursor_manager:
            return bool(self._cursor_manager.update_position(int(x), int(y), int(z)))
        return False

    def get_cursor_overlays(self, current_floor: int | None = None) -> list[dict[str, Any]]:
        """Get remote cursor data for rendering."""
        if self._cursor_manager:
            return list(self._cursor_manager.get_overlays(current_floor))
        return []

    def get_diagnostics(self) -> dict[str, Any]:
        """Get session diagnostics for the status bar / debug panel."""
        info = self._info
        return {
            "state": info.state.name,
            "host": info.host,
            "port": info.port,
            "name": info.name,
            "is_host": info.is_host,
            "client_id": info.client_id,
            "uptime": info.metrics.uptime_seconds,
            "reconnect_count": info.metrics.reconnect_count,
            "users_online": len(info.connected_users),
        }

    # --- Internal callbacks ---

    def _on_client_connected(self) -> None:
        """Called when the LiveClient (re)connects."""
        self._info.metrics.connected_at = time.time()
        self._set_state(SessionState.CONNECTED)

    def _on_client_disconnected(self, reason: str) -> None:
        """Called when the LiveClient disconnects."""
        self._info.metrics.disconnected_at = time.time()
        if self._info.state != SessionState.DISCONNECTING:
            logger.warning("Unexpected disconnect: %s", reason)
            if self.on_error:
                try:
                    self.on_error("Connection lost: " + str(reason))
                except Exception:
                    pass

    def _on_client_reconnecting(self, attempt: int, delay: float) -> None:
        """Called before each reconnect attempt."""
        self._info.metrics.reconnect_count += 1
        self._set_state(SessionState.RECONNECTING)
        logger.info("Reconnecting (attempt %d, delay %.1fs)...", attempt, delay)