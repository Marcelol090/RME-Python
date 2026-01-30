"""Live Log Panel for collaborative editing.

Provides chat/log UI for live editing sessions:
- Message log with timestamps
- Chat input textbox
- Connected users list with colors

Layer: vis_layer (OK to use PyQt6)
Reference: legacy live_tab.cpp
"""

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING, Any

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor
from PyQt6.QtWidgets import (
    QDockWidget,
    QHBoxLayout,
    QHeaderView,
    QLabel,
    QLineEdit,
    QSplitter,
    QTableWidget,
    QTableWidgetItem,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    pass


class LiveLogPanel(QDockWidget):
    """Dock widget for live editing chat/log and user list.

    Signals:
        message_sent: Emitted when user sends a chat message
    """

    message_sent = pyqtSignal(str)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__("Live Log", parent)
        self.setAllowedAreas(Qt.DockWidgetArea.BottomDockWidgetArea | Qt.DockWidgetArea.TopDockWidgetArea)

        self._setup_ui()
        self._apply_style()

    def _setup_ui(self) -> None:
        """Initialize UI components."""
        container = QWidget()
        layout = QHBoxLayout(container)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(4)

        # Splitter for log + user list
        splitter = QSplitter(Qt.Orientation.Horizontal)

        # Left: Log + Input
        left_widget = QWidget()
        left_layout = QVBoxLayout(left_widget)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(4)

        # Message log table
        self.log_table = QTableWidget()
        self.log_table.setColumnCount(3)
        self.log_table.setHorizontalHeaderLabels(["Time", "User", "Message"])
        self.log_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.log_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.log_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.log_table.setColumnWidth(0, 70)
        self.log_table.setColumnWidth(1, 100)
        self.log_table.verticalHeader().setVisible(False)
        self.log_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.log_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        left_layout.addWidget(self.log_table)

        # Chat input
        self.input_box = QLineEdit()
        self.input_box.setPlaceholderText("Type a message...")
        self.input_box.returnPressed.connect(self._on_send_message)
        left_layout.addWidget(self.input_box)

        splitter.addWidget(left_widget)

        # Right: User list
        right_widget = QWidget()
        right_widget.setFixedWidth(200)
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(4)

        users_label = QLabel("Connected Users")
        users_label.setStyleSheet("font-weight: bold; color: #E5E5E7;")
        right_layout.addWidget(users_label)

        self.users_table = QTableWidget()
        self.users_table.setColumnCount(3)
        self.users_table.setHorizontalHeaderLabels(["", "#", "Name"])
        self.users_table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeMode.Fixed)
        self.users_table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeMode.Fixed)
        self.users_table.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeMode.Stretch)
        self.users_table.setColumnWidth(0, 24)
        self.users_table.setColumnWidth(1, 36)
        self.users_table.verticalHeader().setVisible(False)
        self.users_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        right_layout.addWidget(self.users_table)

        splitter.addWidget(right_widget)
        splitter.setSizes([400, 200])

        layout.addWidget(splitter)
        self.setWidget(container)

    def _apply_style(self) -> None:
        """Apply modern dark styling."""
        self.setStyleSheet("""
            QDockWidget {
                background: #1E1E2E;
                color: #E5E5E7;
            }
            QTableWidget {
                background: #1A1A2E;
                border: 1px solid #363650;
                color: #E5E5E7;
                gridline-color: #2A2A3E;
            }
            QTableWidget::item {
                padding: 4px;
            }
            QHeaderView::section {
                background: #2A2A3E;
                color: #A1A1AA;
                border: none;
                padding: 4px;
            }
            QLineEdit {
                background: #2A2A3E;
                border: 1px solid #363650;
                border-radius: 4px;
                padding: 6px;
                color: #E5E5E7;
            }
            QLineEdit:focus {
                border-color: #8B5CF6;
            }
        """)

    def _on_send_message(self) -> None:
        """Handle sending a chat message."""
        text = self.input_box.text().strip()
        if text:
            self.message_sent.emit(text)
            self.input_box.clear()

    def add_message(self, user: str, message: str, *, is_server: bool = False) -> None:
        """Add a message to the log."""
        row = self.log_table.rowCount()
        self.log_table.insertRow(row)

        # Time
        time_str = datetime.now().strftime("%H:%M:%S")
        time_item = QTableWidgetItem(time_str)
        time_item.setForeground(QColor("#A1A1AA"))
        self.log_table.setItem(row, 0, time_item)

        # User
        user_item = QTableWidgetItem(user)
        if is_server:
            user_item.setForeground(QColor("#8B5CF6"))
        else:
            user_item.setForeground(QColor("#4CAF50"))
        self.log_table.setItem(row, 1, user_item)

        # Message
        msg_item = QTableWidgetItem(message)
        self.log_table.setItem(row, 2, msg_item)

        # Scroll to bottom
        self.log_table.scrollToBottom()

    def add_server_message(self, message: str) -> None:
        """Add a server/system message."""
        self.add_message("Server", message, is_server=True)

    def update_user_list(self, peers: dict[int, Any] | list[dict[str, Any]]) -> None:
        """Update the connected users list."""
        self.users_table.setRowCount(0)

        if isinstance(peers, dict):
            entries = [(cid, peer) for cid, peer in sorted(peers.items())]
        else:
            entries = []
            for peer in peers:
                try:
                    cid = int(peer.get("client_id", 0))
                except Exception:
                    cid = 0
                entries.append((cid, peer))
            entries.sort(key=lambda e: int(e[0]))

        for client_id, peer in entries:
            row = self.users_table.rowCount()
            self.users_table.insertRow(row)

            # Color indicator
            color_item = QTableWidgetItem()
            try:
                if isinstance(peer, dict):
                    r, g, b = peer.get("color", (136, 136, 136))
                else:
                    r, g, b = peer.get_color()
                color_item.setBackground(QColor(r, g, b))
            except Exception:
                color_item.setBackground(QColor("#888888"))
            self.users_table.setItem(row, 0, color_item)

            # Client ID
            id_item = QTableWidgetItem(str(int(client_id)))
            self.users_table.setItem(row, 1, id_item)

            # Name
            if isinstance(peer, dict):
                name = str(peer.get("name", "")) or "Unknown"
            else:
                name = getattr(peer, "name", None) or "Unknown"
            name_item = QTableWidgetItem(str(name))
            self.users_table.setItem(row, 2, name_item)

    def clear_log(self) -> None:
        """Clear all messages."""
        self.log_table.setRowCount(0)

    def set_input_enabled(self, enabled: bool) -> None:
        """Enable or disable chat input."""
        self.input_box.setEnabled(enabled)
        if not enabled:
            self.input_box.setPlaceholderText("Disconnected")
        else:
            self.input_box.setPlaceholderText("Type a message...")
