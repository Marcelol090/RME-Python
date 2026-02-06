"""Live Chat Panel for Real-Time Collaboration.

Provides a chat interface for collaborative map editing sessions.
Displays chat messages, user list, and connection status.

Mirrors legacy C++ LiveLogTab from source/live_tab.cpp.

Reference:
    - C++ LiveLogTab: source/live_tab.cpp
    - LiveServer: core/protocols/live_server.py
    - GAP_ANALYSIS.md: P2 Live Collaboration
"""

from __future__ import annotations

import html
import logging
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QColor
from PyQt6.QtWidgets import (
    QDockWidget,
    QFrame,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QMenu,
    QPushButton,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class ChatMessage:
    """Represents a single chat message.

    Attributes:
        timestamp: When the message was sent.
        sender_id: Client ID of sender (0 for system messages).
        sender_name: Display name of sender.
        text: Message content.
        color: Sender's cursor color (for user identification).
        is_system: Whether this is a system notification.
    """

    timestamp: datetime
    sender_id: int
    sender_name: str
    text: str
    color: tuple[int, int, int] = (255, 255, 255)
    is_system: bool = False


@dataclass(slots=True)
class ConnectedUser:
    """Represents a connected user in live session.

    Attributes:
        client_id: Unique client identifier.
        name: Display name.
        color: Cursor color (RGB).
        is_local: Whether this is the local user.
    """

    client_id: int
    name: str
    color: tuple[int, int, int] = (255, 255, 255)
    is_local: bool = False


class UserListWidget(QFrame):
    """Widget displaying connected users in the live session."""

    user_selected = pyqtSignal(int)  # client_id
    kick_requested = pyqtSignal(int, str)  # client_id, reason
    ban_requested = pyqtSignal(int, str)  # client_id, reason

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._users: dict[int, ConnectedUser] = {}
        self._is_host = False
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        # Header
        header = QLabel("Connected Users")
        header.setStyleSheet(
            """
            font-weight: bold;
            color: #E5E5E7;
            padding: 8px;
            background: #2A2A3E;
            border-radius: 4px 4px 0 0;
        """
        )
        layout.addWidget(header)

        # User table
        self.table = QTableWidget()
        self.table.setColumnCount(3)
        self.table.setHorizontalHeaderLabels(["", "ID", "Name"])
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self._show_context_menu)

        # Column widths
        header_view = self.table.horizontalHeader()
        header_view.setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        header_view.setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        header_view.setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.table.setColumnWidth(0, 24)
        self.table.setColumnWidth(1, 40)

        self.table.verticalHeader().setVisible(False)
        self.table.setStyleSheet(
            """
            QTableWidget {
                background: #1A1A2E;
                border: 1px solid #363650;
                border-radius: 0 0 4px 4px;
                gridline-color: #2A2A3E;
            }
            QTableWidget::item {
                padding: 4px;
                color: #E5E5E7;
            }
            QTableWidget::item:selected {
                background: #8B5CF6;
            }
            QHeaderView::section {
                background: #2A2A3E;
                color: #A1A1AA;
                padding: 4px;
                border: none;
            }
        """
        )

        layout.addWidget(self.table)

    def set_is_host(self, is_host: bool) -> None:
        """Set whether local user is the host (enables kick/ban)."""
        self._is_host = is_host

    def update_users(self, users: list[ConnectedUser]) -> None:
        """Update the user list."""
        self._users = {u.client_id: u for u in users}
        self.table.setRowCount(len(users))

        for row, user in enumerate(users):
            # Color indicator
            color_item = QTableWidgetItem()
            r, g, b = user.color
            color_item.setBackground(QColor(r, g, b))
            self.table.setItem(row, 0, color_item)

            # Client ID
            id_item = QTableWidgetItem(str(user.client_id))
            id_item.setData(Qt.ItemDataRole.UserRole, user.client_id)
            self.table.setItem(row, 1, id_item)

            # Name (with local indicator)
            name = user.name
            if user.is_local:
                name = f"[Local] {name}"
            name_item = QTableWidgetItem(name)
            self.table.setItem(row, 2, name_item)

    def _show_context_menu(self, pos) -> None:
        """Show context menu for user actions."""
        if not self._is_host:
            return

        item = self.table.itemAt(pos)
        if item is None:
            return

        row = item.row()
        id_item = self.table.item(row, 1)
        if id_item is None:
            return

        client_id = id_item.data(Qt.ItemDataRole.UserRole)
        user = self._users.get(client_id)
        if user is None or user.is_local:
            return  # Can't kick/ban self

        menu = QMenu(self)
        menu.setStyleSheet(
            """
            QMenu {
                background: #1A1A2E;
                border: 1px solid #363650;
                color: #E5E5E7;
            }
            QMenu::item:selected {
                background: #8B5CF6;
            }
        """
        )

        kick_action = QAction(f"Kick {user.name}", self)
        kick_action.triggered.connect(lambda: self.kick_requested.emit(client_id, "Kicked by host"))
        menu.addAction(kick_action)

        ban_action = QAction(f"Ban {user.name}", self)
        ban_action.triggered.connect(lambda: self.ban_requested.emit(client_id, "Banned by host"))
        menu.addAction(ban_action)

        menu.exec(self.table.mapToGlobal(pos))


class ChatLogWidget(QTextEdit):
    """Widget displaying chat message history."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setReadOnly(True)
        self.setAcceptRichText(True)
        self._messages: list[ChatMessage] = []

        self.setStyleSheet(
            """
            QTextEdit {
                background: #1A1A2E;
                border: 1px solid #363650;
                border-radius: 4px;
                color: #E5E5E7;
                font-family: 'Segoe UI', 'SF Pro Text', sans-serif;
                font-size: 13px;
                padding: 8px;
            }
        """
        )

    def add_message(self, msg: ChatMessage) -> None:
        """Add a message to the chat log."""
        self._messages.append(msg)

        # Format timestamp
        time_str = msg.timestamp.strftime("%H:%M:%S")

        # Build HTML
        if msg.is_system:
            html_line = f'<span style="color: #A1A1AA;">[{time_str}] [system] {html.escape(msg.text)}</span>'
        else:
            r, g, b = msg.color
            name_color = f"rgb({r},{g},{b})"
            html_line = (
                f'<span style="color: #A1A1AA;">[{time_str}]</span> '
                f'<span style="color: {name_color}; font-weight: bold;">{html.escape(msg.sender_name)}:</span> '
                f'<span style="color: #E5E5E7;">{html.escape(msg.text)}</span>'
            )

        self.append(html_line)

        # Auto-scroll to bottom
        scrollbar = self.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def add_system_message(self, text: str) -> None:
        """Add a system notification message."""
        msg = ChatMessage(
            timestamp=datetime.now(),
            sender_id=0,
            sender_name="System",
            text=text,
            is_system=True,
        )
        self.add_message(msg)

    def clear_log(self) -> None:
        """Clear all messages."""
        self._messages.clear()
        self.clear()


class ChatInputWidget(QFrame):
    """Widget for composing and sending chat messages."""

    message_sent = pyqtSignal(str)  # message text

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._enabled = True
        self._setup_ui()

    def _setup_ui(self) -> None:
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        self.input = QLineEdit()
        self.input.setPlaceholderText("Type a message...")
        self.input.returnPressed.connect(self._send_message)
        self.input.setStyleSheet(
            """
            QLineEdit {
                background: #2A2A3E;
                border: 1px solid #363650;
                border-radius: 4px;
                color: #E5E5E7;
                padding: 8px 12px;
                font-size: 13px;
            }
            QLineEdit:focus {
                border-color: #8B5CF6;
            }
            QLineEdit:disabled {
                background: #1A1A2E;
                color: #6B7280;
            }
        """
        )
        layout.addWidget(self.input)

        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self._send_message)
        self.send_btn.setStyleSheet(
            """
            QPushButton {
                background: #8B5CF6;
                border: none;
                border-radius: 4px;
                color: white;
                padding: 8px 16px;
                font-weight: bold;
            }
            QPushButton:hover {
                background: #7C3AED;
            }
            QPushButton:pressed {
                background: #6D28D9;
            }
            QPushButton:disabled {
                background: #4B5563;
            }
        """
        )
        layout.addWidget(self.send_btn)

    def _send_message(self) -> None:
        """Send the current message."""
        text = self.input.text().strip()
        if text and self._enabled:
            self.message_sent.emit(text)
            self.input.clear()

    def set_enabled(self, enabled: bool) -> None:
        """Enable or disable input."""
        self._enabled = enabled
        self.input.setEnabled(enabled)
        self.send_btn.setEnabled(enabled)
        if not enabled:
            self.input.setPlaceholderText("Disconnected")
        else:
            self.input.setPlaceholderText("Type a message...")


class LiveChatPanel(QDockWidget):
    """Dock widget for live collaboration chat.

    Provides:
    - Chat message log with timestamps
    - User list with color indicators
    - Message input with send button
    - Host controls (kick/ban)

    Mirrors legacy C++ LiveLogTab from source/live_tab.cpp.

    Signals:
        message_sent: Emitted when user sends a chat message.
        kick_requested: Emitted when host requests to kick a user.
        ban_requested: Emitted when host requests to ban a user.

    Example:
        >>> panel = LiveChatPanel(parent)
        >>> panel.message_sent.connect(on_message)
        >>> panel.add_chat_message(msg)
        >>> panel.update_user_list(users)
    """

    message_sent = pyqtSignal(str)
    kick_requested = pyqtSignal(int, str)
    ban_requested = pyqtSignal(int, str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Live Chat", parent)
        self._host_name = "Disconnected"
        self._is_connected = False
        self._is_host = False

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI components."""
        # Main widget
        main_widget = QWidget()
        self.setWidget(main_widget)

        layout = QVBoxLayout(main_widget)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        # Header with connection status
        self.header = QLabel("Live Chat - Disconnected")
        self.header.setStyleSheet(
            """
            font-size: 14px;
            font-weight: bold;
            color: #E5E5E7;
            padding: 4px;
        """
        )
        layout.addWidget(self.header)

        # Splitter for chat log and user list
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left side - Chat log
        chat_container = QWidget()
        chat_layout = QVBoxLayout(chat_container)
        chat_layout.setContentsMargins(0, 0, 0, 0)
        chat_layout.setSpacing(8)

        self.chat_log = ChatLogWidget()
        chat_layout.addWidget(self.chat_log, 1)

        self.chat_input = ChatInputWidget()
        self.chat_input.message_sent.connect(self._on_message_sent)
        self.chat_input.set_enabled(False)
        chat_layout.addWidget(self.chat_input)

        splitter.addWidget(chat_container)

        # Right side - User list
        self.user_list = UserListWidget()
        self.user_list.kick_requested.connect(self._on_kick_requested)
        self.user_list.ban_requested.connect(self._on_ban_requested)
        splitter.addWidget(self.user_list)

        # Set splitter sizes (chat gets more space)
        splitter.setSizes([400, 200])
        splitter.setCollapsible(0, False)
        splitter.setCollapsible(1, False)

        layout.addWidget(splitter, 1)

    def _apply_style(self) -> None:
        """Apply dark theme styling."""
        self.setStyleSheet(
            """
            QDockWidget {
                background: #0F0F1A;
                color: #E5E5E7;
            }
            QDockWidget::title {
                background: #1A1A2E;
                padding: 8px;
                text-align: left;
            }
        """
        )

    def _on_message_sent(self, text: str) -> None:
        """Handle local message send."""
        self.message_sent.emit(text)

    def _on_kick_requested(self, client_id: int, reason: str) -> None:
        """Handle kick request."""
        self.kick_requested.emit(client_id, reason)

    def _on_ban_requested(self, client_id: int, reason: str) -> None:
        """Handle ban request."""
        self.ban_requested.emit(client_id, reason)

    def connect_to_session(self, host_name: str, is_host: bool = False) -> None:
        """Called when connecting to a live session.

        Args:
            host_name: Display name for the session host.
            is_host: Whether local user is the session host.
        """
        self._host_name = host_name
        self._is_connected = True
        self._is_host = is_host

        self.header.setText(f"Live Chat - {host_name}")
        self.chat_input.set_enabled(True)
        self.user_list.set_is_host(is_host)

        role = "Host" if is_host else "Client"
        self.chat_log.add_system_message(f"Connected to {host_name} as {role}")

    def disconnect_from_session(self) -> None:
        """Called when disconnecting from session."""
        self._is_connected = False
        self._is_host = False

        self.header.setText("Live Chat - Disconnected")
        self.chat_input.set_enabled(False)
        self.user_list.set_is_host(False)
        self.chat_log.add_system_message("Disconnected from session")

    def add_chat_message(self, msg: ChatMessage) -> None:
        """Add a chat message to the log.

        Args:
            msg: The chat message to display.
        """
        self.chat_log.add_message(msg)

    def add_system_message(self, text: str) -> None:
        """Add a system notification.

        Args:
            text: The notification text.
        """
        self.chat_log.add_system_message(text)

    def update_user_list(self, users: list[ConnectedUser]) -> None:
        """Update the connected users list.

        Args:
            users: List of connected users.
        """
        self.user_list.update_users(users)

    def clear_chat(self) -> None:
        """Clear all chat messages."""
        self.chat_log.clear_log()

    @property
    def is_connected(self) -> bool:
        """Check if currently connected to a session."""
        return self._is_connected

    @property
    def is_host(self) -> bool:
        """Check if local user is the session host."""
        return self._is_host


def create_live_chat_dock(parent: QWidget | None = None) -> LiveChatPanel:
    """Factory function to create a LiveChatPanel.

    Args:
        parent: Parent widget.

    Returns:
        Configured LiveChatPanel instance.
    """
    panel = LiveChatPanel(parent)
    panel.setAllowedAreas(
        Qt.DockWidgetArea.LeftDockWidgetArea
        | Qt.DockWidgetArea.RightDockWidgetArea
        | Qt.DockWidgetArea.BottomDockWidgetArea
    )
    panel.setMinimumSize(400, 300)
    return panel


__all__ = [
    "LiveChatPanel",
    "ChatMessage",
    "ConnectedUser",
    "create_live_chat_dock",
]
