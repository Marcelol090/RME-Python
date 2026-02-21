"""Chat Dialog for Social Interactions.

Provides a 1-on-1 chat interface.
"""

from __future__ import annotations

import html
from datetime import datetime

from PyQt6.QtWidgets import (
    QHBoxLayout,
    QLineEdit,
    QPushButton,
    QTextEdit,
    QVBoxLayout,
    QWidget,
)

from py_rme_canary.vis_layer.ui.dialogs.base_modern import ModernDialog
from py_rme_canary.vis_layer.ui.theme import get_theme_manager


class ChatDialog(ModernDialog):
    """Modern chat dialog."""

    def __init__(self, parent: QWidget | None = None, friend_name: str = "Friend") -> None:
        super().__init__(parent, title=f"Chat with {friend_name}")
        self._friend_name = friend_name
        self.setMinimumSize(400, 500)
        self._populate_ui()

    def _populate_ui(self) -> None:
        layout = self.content_layout

        # Chat history
        self.history = QTextEdit()
        self.history.setReadOnly(True)
        layout.addWidget(self.history)

        # Input area
        input_layout = QHBoxLayout()
        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText("Type a message...")
        self.input_field.returnPressed.connect(self._send_message)
        input_layout.addWidget(self.input_field)

        self.send_btn = QPushButton("Send")
        self.send_btn.clicked.connect(self._send_message)
        input_layout.addWidget(self.send_btn)

        layout.addLayout(input_layout)

        self._apply_styles()

    def _apply_styles(self) -> None:
        tm = get_theme_manager()
        c = tm.tokens["color"]
        r = tm.tokens["radius"]

        self.history.setStyleSheet(f"""
            QTextEdit {{
                background-color: {c["surface"]["primary"]};
                border: 1px solid {c["border"]["default"]};
                border-radius: {r["md"]}px;
                color: {c["text"]["primary"]};
                padding: 8px;
            }}
        """)

        self.input_field.setStyleSheet(f"""
            QLineEdit {{
                background-color: {c["surface"]["secondary"]};
                border: 1px solid {c["border"]["default"]};
                border-radius: {r["sm"]}px;
                color: {c["text"]["primary"]};
                padding: 6px;
            }}
        """)

        self.send_btn.setStyleSheet(f"""
            QPushButton {{
                background-color: {c["brand"]["primary"]};
                color: {c["text"]["primary"]};
                border: none;
                border-radius: {r["sm"]}px;
                padding: 6px 12px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {c["brand"]["secondary"]};
            }}
        """)

    def _send_message(self) -> None:
        text = self.input_field.text().strip()
        if not text:
            return

        # Mock sending
        timestamp = datetime.now().strftime("%H:%M")
        self.append_message("You", text, timestamp)
        self.input_field.clear()

        # Mock reply (optional, can be removed)
        # self.append_message(self._friend_name, f"Echo: {text}", timestamp)

    def append_message(self, sender: str, text: str, timestamp: str) -> None:
        tm = get_theme_manager()
        c = tm.tokens["color"]

        color = c["brand"]["primary"] if sender == "You" else c["text"]["secondary"]
        escaped_sender = html.escape(sender)
        escaped_text = html.escape(text)
        self.history.append(f'<span style="color: {c["text"]["tertiary"]};">[{timestamp}]</span> <b style="color: {color};">{escaped_sender}:</b> {escaped_text}')
