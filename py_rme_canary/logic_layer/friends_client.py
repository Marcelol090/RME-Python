"""
Friends Client for handling social interactions and real-time status.

This module implements the client-side logic for the Friends System,
including WebSocket communication (mocked for now) and signal handling.
"""

import json
import logging
from typing import Any, Dict, List, Optional

from PyQt6.QtCore import QObject, QTimer, pyqtSignal

log = logging.getLogger(__name__)


class FriendsClient(QObject):
    """
    Client for the Friends System.

    Handles connection to the presence server, manages the local friend list state,
    and emits signals when updates occur.
    """

    # Signals
    connected = pyqtSignal()
    disconnected = pyqtSignal()
    friends_list_received = pyqtSignal(list)  # List[Dict]
    friend_status_changed = pyqtSignal(dict)  # {friend_id, status, ...}
    friend_activity_changed = pyqtSignal(dict)  # {friend_id, current_map, ...}
    friend_request_received = pyqtSignal(dict)  # Request data
    friend_request_accepted = pyqtSignal(dict)  # Friend data
    error_occurred = pyqtSignal(str)

    def __init__(self, token: Optional[str] = None):
        super().__init__()
        self._token = token
        self._is_connected = False
        self._mock_timer = QTimer()
        self._mock_timer.timeout.connect(self._process_mock_events)
        self._event_queue: List[Dict[str, Any]] = []

    def connect_to_server(self):
        """Initiate connection to the friends server."""
        log.info("Connecting to friends server...")
        # Simulate network delay
        QTimer.singleShot(1000, self._on_mock_connected)

    def disconnect_from_server(self):
        """Disconnect from the friends server."""
        log.info("Disconnecting from friends server...")
        self._is_connected = False
        self._mock_timer.stop()
        self.disconnected.emit()

    def send_friend_request(self, username: str):
        """Send a friend request to a user."""
        log.info(f"Sending friend request to {username}")
        # Mock response: Request sent successfully (no UI feedback needed usually unless error)

    def accept_friend_request(self, request_id: int):
        """Accept a pending friend request."""
        log.info(f"Accepting friend request {request_id}")
        # Mock: Server would confirm and send 'friend_request_accepted'
        # We simulate this response after a delay
        QTimer.singleShot(500, lambda: self._mock_accept_event(request_id))

    def reject_friend_request(self, request_id: int):
        """Reject a pending friend request."""
        log.info(f"Rejecting friend request {request_id}")

    def update_my_activity(self, map_name: Optional[str], privacy_mode: str = "friends_only"):
        """Update local user's activity status."""
        log.info(f"Updating activity: map={map_name}, privacy={privacy_mode}")
        # In a real app, this sends a frame to the server

    # --- Mock Logic for Demonstration ---

    def _on_mock_connected(self):
        self._is_connected = True
        self.connected.emit()
        log.info("Connected to friends server (Mock)")

        # 1. Send initial friend list
        friends_list = [
            {
                "id": 2,
                "username": "CunhaLuiz",
                "avatar_url": "https://avatars.githubusercontent.com/u/1000?v=4",
                "status": "online",
                "current_map": "Cave Level -1",
                "privacy_mode": "friends_only"
            },
            {
                "id": 5,
                "username": "Qatari",
                "avatar_url": "https://avatars.githubusercontent.com/u/2000?v=4",
                "status": "idle",
                "current_map": None,
                "privacy_mode": "friends_only"
            },
             {
                "id": 8,
                "username": "Maria",
                "avatar_url": "https://avatars.githubusercontent.com/u/3000?v=4",
                "status": "offline",
                "current_map": None,
                "privacy_mode": "private"
            }
        ]
        self.friends_list_received.emit(friends_list)

        # 2. Simulate a pending request coming in
        QTimer.singleShot(2000, self._mock_incoming_request)

        # 3. Simulate friend status change
        QTimer.singleShot(5000, self._mock_status_change)

        # 4. Simulate friend activity change
        QTimer.singleShot(8000, self._mock_activity_change)

    def _mock_incoming_request(self):
        req = {
            "id": 20,
            "requester_id": 99,
            "requester_name": "NewUser123",
            "requester_avatar": "https://avatars.githubusercontent.com/u/4000?v=4"
        }
        self.friend_request_received.emit(req)

    def _mock_status_change(self):
        # Maria comes online
        update = {
            "friend_id": 8,
            "status": "online",
            "current_map": None
        }
        self.friend_status_changed.emit(update)

    def _mock_activity_change(self):
        # CunhaLuiz changes map
        update = {
            "friend_id": 2,
            "current_map": "Dragon Lair",
            "privacy_mode": "friends_only"
        }
        self.friend_activity_changed.emit(update)

    def _mock_accept_event(self, request_id: int):
        # Simulate the server telling us the new friendship is active
        # In this mock, we just hardcode a 'NewFriend' for demo purposes
        new_friend = {
            "id": 99,
            "username": "NewUser123",
            "avatar_url": "https://avatars.githubusercontent.com/u/4000?v=4",
            "status": "online",
            "current_map": None,
            "privacy_mode": "friends_only"
        }
        self.friend_request_accepted.emit(new_friend)

    def _process_mock_events(self):
        pass
