"""Friends sidebar dock widgets for the PyQt6 editor."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor, QPainter, QPalette
from PyQt6.QtWidgets import (
    QComboBox,
    QFrame,
    QGroupBox,
    QHBoxLayout,
    QInputDialog,
    QLabel,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QVBoxLayout,
    QWidget,
)

from py_rme_canary.logic_layer.social import FriendEntry, FriendRequest, FriendsSnapshot


def _initials(name: str) -> str:
    parts = [token for token in str(name or "").split() if token]
    if not parts:
        return "?"
    if len(parts) == 1:
        token = parts[0][:2]
    else:
        token = f"{parts[0][:1]}{parts[1][:1]}"
    return token.upper()


class StatusDot(QWidget):
    """Small colored dot for online/offline state."""

    def __init__(self, *, status: str = "offline", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._status = "offline"
        self.setFixedSize(12, 12)
        self.set_status(status)

    def set_status(self, status: str) -> None:
        normalized = str(status or "").strip().lower()
        if normalized not in {"online", "idle", "dnd", "offline"}:
            normalized = "offline"
        self._status = normalized
        self.update()

    def _color(self) -> QColor:
        if self._status == "online":
            return QColor(76, 175, 80)
        if self._status == "idle":
            return QColor(255, 179, 0)
        if self._status == "dnd":
            return QColor(244, 67, 54)
        return QColor(128, 128, 128)

    def paintEvent(self, _event) -> None:  # noqa: N802
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(self._color())
        painter.drawEllipse(0, 0, self.width(), self.height())


class AvatarBadge(QLabel):
    """Simple circular avatar using user initials."""

    def __init__(self, name: str, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFixedSize(34, 34)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setText(_initials(name))
        self.setStyleSheet(
            """
            QLabel {
                border-radius: 17px;
                background-color: #3a3a52;
                color: #f5f5f9;
                font-weight: 700;
            }
            """
        )


@dataclass(slots=True)
class _RequestActions:
    accept: Callable[[int], None]
    reject: Callable[[int], None]


class FriendRequestCard(QFrame):
    """Single pending request card with accept/reject controls."""

    def __init__(
        self,
        request: FriendRequest,
        *,
        actions: _RequestActions,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._request = request
        self._actions = actions
        self._build()

    def _build(self) -> None:
        self.setFrameShape(QFrame.Shape.StyledPanel)
        self.setStyleSheet(
            """
            FriendRequestCard {
                background-color: #212131;
                border: 1px solid #343454;
                border-radius: 8px;
            }
            """
        )
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 8, 8, 8)
        layout.setSpacing(8)

        layout.addWidget(AvatarBadge(self._request.requester_name, self))

        identity = QVBoxLayout()
        name = QLabel(self._request.requester_name)
        name.setStyleSheet("font-weight: 600;")
        identity.addWidget(name)
        created = QLabel(self._request.created_at or "Pending request")
        created.setStyleSheet("color: #9ea0b4; font-size: 11px;")
        identity.addWidget(created)
        layout.addLayout(identity, 1)

        accept_button = QPushButton("Accept")
        accept_button.clicked.connect(lambda: self._actions.accept(int(self._request.id)))
        reject_button = QPushButton("Reject")
        reject_button.clicked.connect(lambda: self._actions.reject(int(self._request.id)))
        layout.addWidget(accept_button)
        layout.addWidget(reject_button)


class FriendCard(QFrame):
    """Single friend card with status + optional current map."""

    def __init__(
        self,
        friend: FriendEntry,
        *,
        on_view_map: Callable[[int], None],
        on_chat: Callable[[int], None] | None = None,
        on_more: Callable[[int], None] | None = None,
        parent: QWidget | None = None,
    ) -> None:
        super().__init__(parent)
        self._friend = friend
        self._on_view_map = on_view_map
        self._on_chat = on_chat
        self._on_more = on_more
        self._build()

    def _build(self) -> None:
        self.setFrameShape(QFrame.Shape.StyledPanel)
        from py_rme_canary.vis_layer.ui.theme import get_theme_manager

        tm = get_theme_manager()
        c = tm.tokens["color"]
        r = tm.tokens["radius"]

        self.setStyleSheet(
            f"""
            FriendCard {{
                background-color: {c["surface"]["secondary"]};
                border: 1px solid {c["border"]["default"]};
                border-radius: {r["md"]}px;
            }}
            QPushButton {{
                background-color: {c["surface"]["tertiary"]};
                border: none;
                border-radius: 4px;
                padding: 4px 8px;
                color: {c["text"]["secondary"]};
                font-size: 11px;
            }}
            QPushButton:hover {{
                background-color: {c["state"]["hover"]};
                color: {c["text"]["primary"]};
            }}
            """
        )

        root = QVBoxLayout(self)
        root.setContentsMargins(10, 10, 10, 10)
        root.setSpacing(6)

        top = QHBoxLayout()
        top.addWidget(AvatarBadge(self._friend.username, self))

        identity = QVBoxLayout()
        name = QLabel(self._friend.username)
        name.setStyleSheet(f"font-weight: 600; font-size: 13px; color: {c['text']['primary']};")
        identity.addWidget(name)
        status_text = QLabel(self._friend.status.capitalize())
        status_text.setStyleSheet(f"color: {c['text']['secondary']}; font-size: 11px;")
        identity.addWidget(status_text)
        top.addLayout(identity, 1)

        top.addWidget(StatusDot(status=self._friend.status, parent=self))
        root.addLayout(top)

        map_text = self._friend.current_map or "No shared map activity"
        map_label = QLabel(map_text)
        map_label.setStyleSheet(f"color: {c['text']['tertiary']}; font-size: 11px;")
        root.addWidget(map_label)

        actions = QHBoxLayout()
        actions.setSpacing(4)
        actions.addItem(QSpacerItem(10, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        if self._on_chat:
            chat_btn = QPushButton("Chat")
            chat_btn.clicked.connect(lambda: self._on_chat(int(self._friend.id)))
            actions.addWidget(chat_btn)

        view_button = QPushButton("View Map")
        view_button.setEnabled(bool(self._friend.current_map))
        view_button.clicked.connect(lambda: self._on_view_map(int(self._friend.id)))
        actions.addWidget(view_button)

        if self._on_more:
            more_btn = QPushButton("⋮")
            more_btn.setFixedSize(20, 20)
            more_btn.clicked.connect(lambda: self._on_more(int(self._friend.id)))
            actions.addWidget(more_btn)

        root.addLayout(actions)


class FriendsSidebar(QWidget):
    """Modern friends panel for the map editor."""

    request_friend = pyqtSignal(str)
    accept_request = pyqtSignal(int)
    reject_request = pyqtSignal(int)
    privacy_mode_changed = pyqtSignal(str)
    refresh_requested = pyqtSignal()
    view_map_requested = pyqtSignal(int)
    chat_requested = pyqtSignal(int)
    more_actions_requested = pyqtSignal(int)

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self._snapshot = FriendsSnapshot()
        self._build()

    def _build(self) -> None:
        root = QVBoxLayout(self)
        root.setContentsMargins(8, 8, 8, 8)
        root.setSpacing(8)

        header = QHBoxLayout()
        title = QLabel("Friends")
        title.setStyleSheet("font-size: 14px; font-weight: 700;")
        header.addWidget(title)
        header.addItem(QSpacerItem(10, 10, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))

        add_button = QPushButton("Add")
        add_button.clicked.connect(self._on_add_clicked)
        header.addWidget(add_button)

        refresh_button = QPushButton("Refresh")
        refresh_button.clicked.connect(self.refresh_requested.emit)
        header.addWidget(refresh_button)
        root.addLayout(header)

        privacy_layout = QHBoxLayout()
        privacy_layout.addWidget(QLabel("Privacy"))
        self._privacy_combo = QComboBox()
        self._privacy_combo.addItem("Friends only", "friends_only")
        self._privacy_combo.addItem("Private", "private")
        self._privacy_combo.addItem("Public", "public")
        self._privacy_combo.currentIndexChanged.connect(self._on_privacy_changed)
        privacy_layout.addWidget(self._privacy_combo, 1)
        root.addLayout(privacy_layout)

        self._status_label = QLabel("")
        self._status_label.setStyleSheet("color: #9ea0b4; font-size: 11px;")
        root.addWidget(self._status_label)

        self._pending_group = QGroupBox("Pending Requests (0)")
        self._pending_layout = QVBoxLayout(self._pending_group)
        self._pending_layout.setSpacing(6)
        root.addWidget(self._pending_group)

        self._scroll = QScrollArea()
        self._scroll.setWidgetResizable(True)
        self._scroll.setFrameShape(QFrame.Shape.NoFrame)

        self._content = QWidget(self._scroll)
        self._content_layout = QVBoxLayout(self._content)
        self._content_layout.setContentsMargins(0, 0, 0, 0)
        self._content_layout.setSpacing(8)

        self._online_group = QGroupBox("Online (0)")
        self._online_layout = QVBoxLayout(self._online_group)
        self._online_layout.setSpacing(6)
        self._content_layout.addWidget(self._online_group)

        self._offline_group = QGroupBox("Offline (0)")
        self._offline_layout = QVBoxLayout(self._offline_group)
        self._offline_layout.setSpacing(6)
        self._content_layout.addWidget(self._offline_group)
        self._content_layout.addItem(QSpacerItem(10, 10, QSizePolicy.Policy.Minimum, QSizePolicy.Policy.Expanding))

        self._scroll.setWidget(self._content)
        root.addWidget(self._scroll, 1)

    def _clear_layout(self, layout: QVBoxLayout) -> None:
        while layout.count():
            item = layout.takeAt(0)
            widget = item.widget()
            if widget is not None:
                widget.deleteLater()

    def _on_add_clicked(self) -> None:
        username, ok = QInputDialog.getText(self, "Add Friend", "Username")
        if not ok:
            return
        normalized = str(username or "").strip()
        if not normalized:
            return
        self.request_friend.emit(normalized)

    def _on_privacy_changed(self) -> None:
        value = str(self._privacy_combo.currentData() or "friends_only")
        self.privacy_mode_changed.emit(value)

    def set_privacy_mode(self, mode: str) -> None:
        target = str(mode or "").strip().lower()
        for index in range(self._privacy_combo.count()):
            if str(self._privacy_combo.itemData(index) or "").strip().lower() == target:
                self._privacy_combo.blockSignals(True)
                self._privacy_combo.setCurrentIndex(index)
                self._privacy_combo.blockSignals(False)
                return

    def set_status_message(self, message: str) -> None:
        self._status_label.setText(str(message or ""))

    def set_snapshot(self, snapshot: FriendsSnapshot) -> None:
        self._snapshot = snapshot
        self._pending_group.setTitle(f"Pending Requests ({len(snapshot.pending_requests)})")
        self._online_group.setTitle(f"Online ({len(snapshot.online)})")
        self._offline_group.setTitle(f"Offline ({len(snapshot.offline)})")

        self._clear_layout(self._pending_layout)
        self._clear_layout(self._online_layout)
        self._clear_layout(self._offline_layout)

        request_actions = _RequestActions(
            accept=lambda request_id: self.accept_request.emit(int(request_id)),
            reject=lambda request_id: self.reject_request.emit(int(request_id)),
        )
        for request in snapshot.pending_requests:
            self._pending_layout.addWidget(
                FriendRequestCard(request, actions=request_actions, parent=self._pending_group)
            )
        if not snapshot.pending_requests:
            self._pending_layout.addWidget(QLabel("No pending requests"))

        for friend in snapshot.online:
            self._online_layout.addWidget(
                FriendCard(
                    friend,
                    on_view_map=lambda friend_id: self.view_map_requested.emit(int(friend_id)),
                    on_chat=lambda friend_id: self.chat_requested.emit(int(friend_id)),
                    on_more=lambda friend_id: self.more_actions_requested.emit(int(friend_id)),
                    parent=self._online_group,
                )
            )
        if not snapshot.online:
            self._online_layout.addWidget(QLabel("No friends online"))

        for friend in snapshot.offline:
            self._offline_layout.addWidget(
                FriendCard(
                    friend,
                    on_view_map=lambda friend_id: self.view_map_requested.emit(int(friend_id)),
                    on_chat=lambda friend_id: self.chat_requested.emit(int(friend_id)),
                    on_more=lambda friend_id: self.more_actions_requested.emit(int(friend_id)),
                    parent=self._offline_group,
                )
            )
        if not snapshot.offline:
            self._offline_layout.addWidget(QLabel("No offline friends"))


class FriendsDock(QFrame):
    """Dock-friendly container for the friends sidebar."""

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setFrameShape(QFrame.Shape.NoFrame)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        self.sidebar = FriendsSidebar(self)
        layout.addWidget(self.sidebar)
        palette = self.palette()
        palette.setColor(QPalette.ColorRole.Window, QColor("#171725"))
        self.setAutoFillBackground(True)
        self.setPalette(palette)
