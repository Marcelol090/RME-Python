"""
Friends Sidebar implementation.
"""

from typing import List, Dict, Optional

from PyQt6.QtCore import Qt, pyqtSlot
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton,
    QScrollArea, QFrame, QInputDialog, QMessageBox
)

from py_rme_canary.vis_layer.ui.friends.widgets import (
    FriendItemWidget, FriendRequestWidget
)
from py_rme_canary.logic_layer.friends_client import FriendsClient


class CategoryWidget(QWidget):
    def __init__(self, title, parent=None):
        super().__init__(parent)
        self.layout = QVBoxLayout()
        self.layout.setContentsMargins(0, 10, 0, 5)
        self.layout.setSpacing(5)

        self.label = QLabel(title)
        self.label.setStyleSheet("color: #8E9297; font-size: 11px; font-weight: bold; text-transform: uppercase;")
        self.layout.addWidget(self.label)

        self.items_layout = QVBoxLayout()
        self.items_layout.setSpacing(2)
        self.layout.addLayout(self.items_layout)

        self.setLayout(self.layout)

    def add_widget(self, widget):
        self.items_layout.addWidget(widget)

    def clear(self):
        while self.items_layout.count():
            child = self.items_layout.takeAt(0)
            if child.widget():
                child.widget().deleteLater()


class FriendsSidebar(QWidget):
    def __init__(self, client: FriendsClient, parent=None):
        super().__init__(parent)
        self.client = client
        self.setup_ui()
        self.connect_signals()

    def setup_ui(self):
        self.main_layout = QVBoxLayout()
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # 1. Header
        header = QWidget()
        header.setStyleSheet("background-color: #2F3136; border-bottom: 1px solid #202225;")
        header_layout = QHBoxLayout()
        header_layout.setContentsMargins(10, 10, 10, 10)

        title = QLabel("Friends")
        title.setStyleSheet("font-weight: bold; font-size: 14px; color: #FFF;")

        add_btn = QPushButton("+")
        add_btn.setFixedSize(24, 24)
        add_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        add_btn.setStyleSheet("""
            QPushButton { background-color: #43B581; color: white; border-radius: 4px; border: none; }
            QPushButton:hover { background-color: #3CA374; }
        """)
        add_btn.clicked.connect(self.show_add_friend_dialog)

        settings_btn = QPushButton("⚙")
        settings_btn.setFixedSize(24, 24)
        settings_btn.setCursor(Qt.CursorShape.PointingHandCursor)
        settings_btn.setStyleSheet("background-color: transparent; color: #B9BBBE; border: none;")

        header_layout.addWidget(title)
        header_layout.addStretch()
        header_layout.addWidget(add_btn)
        header_layout.addWidget(settings_btn)
        header.setLayout(header_layout)

        self.main_layout.addWidget(header)

        # 2. Pending Requests (Collapsible)
        self.pending_widget = QWidget()
        self.pending_layout = QVBoxLayout()
        self.pending_layout.setContentsMargins(10, 5, 10, 5)

        self.pending_header = QPushButton("Pending Requests (0)")
        self.pending_header.setCheckable(True)
        self.pending_header.setChecked(True)
        self.pending_header.setStyleSheet("""
            QPushButton { text-align: left; background: transparent; color: #FFF; font-weight: bold; border: none; }
            QPushButton:checked { color: #FFF; }
        """)
        self.pending_header.clicked.connect(self.toggle_pending)

        self.requests_container = QWidget()
        self.requests_list_layout = QVBoxLayout()
        self.requests_list_layout.setContentsMargins(0, 5, 0, 5)
        self.requests_container.setLayout(self.requests_list_layout)

        self.pending_layout.addWidget(self.pending_header)
        self.pending_layout.addWidget(self.requests_container)
        self.pending_widget.setLayout(self.pending_layout)
        self.pending_widget.setVisible(False) # Hidden by default if empty

        self.main_layout.addWidget(self.pending_widget)

        # 3. Friends List (Scroll Area)
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setStyleSheet("QScrollArea { border: none; background-color: #2F3136; }")

        self.friends_container = QWidget()
        self.friends_container.setStyleSheet("background-color: #2F3136;")
        self.friends_layout = QVBoxLayout()
        self.friends_layout.setContentsMargins(10, 0, 10, 0)
        self.friends_layout.addStretch() # Spacer at bottom

        self.online_category = CategoryWidget("Online — 0")
        self.offline_category = CategoryWidget("Offline — 0")

        self.friends_layout.insertWidget(0, self.online_category)
        self.friends_layout.insertWidget(1, self.offline_category)

        self.friends_container.setLayout(self.friends_layout)
        self.scroll_area.setWidget(self.friends_container)

        self.main_layout.addWidget(self.scroll_area)

        self.setLayout(self.main_layout)
        self.setStyleSheet("background-color: #2F3136;")

    def connect_signals(self):
        self.client.friends_list_received.connect(self.populate_friends_list)
        self.client.friend_status_changed.connect(self.update_friend_status)
        self.client.friend_activity_changed.connect(self.update_friend_activity)
        self.client.friend_request_received.connect(self.add_pending_request)
        self.client.friend_request_accepted.connect(self.on_request_accepted_remote)

    def show_add_friend_dialog(self):
        text, ok = QInputDialog.getText(self, "Add Friend", "Enter username:")
        if ok and text:
            self.client.send_friend_request(text)
            QMessageBox.information(self, "Request Sent", f"Friend request sent to {text}")

    def toggle_pending(self):
        self.requests_container.setVisible(self.pending_header.isChecked())

    @pyqtSlot(list)
    def populate_friends_list(self, friends: List[Dict]):
        # Clear existing
        self.online_category.clear()
        self.offline_category.clear()

        online_count = 0
        offline_count = 0

        # Sort: Online first, then alphabetical
        friends.sort(key=lambda x: (0 if x['status'] != 'offline' else 1, x['username']))

        for friend in friends:
            w = FriendItemWidget(friend)
            if friend['status'] == 'offline':
                self.offline_category.add_widget(w)
                offline_count += 1
            else:
                self.online_category.add_widget(w)
                online_count += 1

        self.online_category.label.setText(f"Online — {online_count}")
        self.offline_category.label.setText(f"Offline — {offline_count}")

    @pyqtSlot(dict)
    def add_pending_request(self, request_data: Dict):
        w = FriendRequestWidget(request_data)
        w.accepted.connect(self.client.accept_friend_request)
        w.rejected.connect(self.client.reject_friend_request)
        w.accepted.connect(lambda rid: w.deleteLater()) # Remove from UI optimistically
        w.rejected.connect(lambda rid: w.deleteLater())

        self.requests_list_layout.addWidget(w)
        self.pending_widget.setVisible(True)
        self.update_pending_count()

    def update_pending_count(self):
        count = self.requests_list_layout.count()
        self.pending_header.setText(f"Pending Requests ({count})")
        if count == 0:
            self.pending_widget.setVisible(False)

    @pyqtSlot(dict)
    def update_friend_status(self, data: Dict):
        # Full refresh for simplicity in this prototype,
        # normally we'd find the specific widget and move it
        # but since we don't store a map of ID -> Widget here yet:
        pass
        # To do this properly, we need to request the full list again or maintain state
        # For now, let's just log it. The mock client only sends partial updates.
        # We would need to update the internal model.
        print(f"Status update: {data}")
        # In a real app, we'd update the specific widget's data and move it between categories.

    @pyqtSlot(dict)
    def update_friend_activity(self, data: Dict):
        # Same as above, would find widget and call w.update_data(data)
        print(f"Activity update: {data}")

    @pyqtSlot(dict)
    def on_request_accepted_remote(self, friend_data: Dict):
        # Add to list
        w = FriendItemWidget(friend_data)
        if friend_data.get('status') == 'offline':
            self.offline_category.add_widget(w)
        else:
            self.online_category.add_widget(w)

        self.update_counts()

    def update_counts(self):
        # Helper to update label counts
        pass
