from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING, cast

from PyQt6.QtCore import QTimer
from PyQt6.QtWidgets import QMessageBox

from py_rme_canary.logic_layer.social import FriendsService

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


class QtMapEditorFriendsMixin:
    """Friends sidebar integration for the editor window."""

    def _init_friends(self) -> None:
        editor = cast("QtMapEditor", self)
        sidebar = getattr(editor, "friends_sidebar", None)
        if sidebar is None:
            return

        service = FriendsService.from_default_path()
        editor.friends_service = service

        username = str(
            os.environ.get("RME_USERNAME") or os.environ.get("USERNAME") or os.environ.get("USER") or "mapper"
        ).strip()
        profile = service.ensure_user(username=username)
        editor.friends_local_user_id = int(profile.id)
        editor.friends_privacy_mode = "friends_only"

        sidebar.request_friend.connect(editor._friends_add_request)
        sidebar.accept_request.connect(editor._friends_accept_request)
        sidebar.reject_request.connect(editor._friends_reject_request)
        sidebar.privacy_mode_changed.connect(editor._friends_set_privacy_mode)
        sidebar.refresh_requested.connect(editor._refresh_friends_sidebar)
        sidebar.view_map_requested.connect(editor._friends_view_map)
        sidebar.chat_requested.connect(editor._friends_chat)

        editor._friends_update_presence(status="online")
        editor._refresh_friends_sidebar()

        editor._friends_timer = QTimer(editor)
        editor._friends_timer.setInterval(10_000)
        editor._friends_timer.timeout.connect(editor._friends_periodic_sync)
        editor._friends_timer.start()

    def _friends_current_map_name(self) -> str | None:
        editor = cast("QtMapEditor", self)
        current_path = str(getattr(editor, "current_path", "") or "").strip()
        if not current_path:
            return "Untitled Map"
        return Path(current_path).name or "Untitled Map"

    def _friends_update_presence(self, *, status: str = "online") -> None:
        editor = cast("QtMapEditor", self)
        service = getattr(editor, "friends_service", None)
        local_user_id = getattr(editor, "friends_local_user_id", None)
        if service is None or local_user_id is None:
            return
        service.update_presence(
            user_id=int(local_user_id),
            status=str(status),  # type: ignore[arg-type]
            current_map=editor._friends_current_map_name(),
            privacy_mode=str(getattr(editor, "friends_privacy_mode", "friends_only")),  # type: ignore[arg-type]
        )

    def _refresh_friends_sidebar(self) -> None:
        editor = cast("QtMapEditor", self)
        service = getattr(editor, "friends_service", None)
        local_user_id = getattr(editor, "friends_local_user_id", None)
        sidebar = getattr(editor, "friends_sidebar", None)
        if service is None or local_user_id is None or sidebar is None:
            return
        snapshot = service.snapshot(user_id=int(local_user_id))
        sidebar.set_snapshot(snapshot)
        sidebar.set_privacy_mode(str(getattr(editor, "friends_privacy_mode", "friends_only")))

    def _friends_add_request(self, username: str) -> None:
        editor = cast("QtMapEditor", self)
        service = getattr(editor, "friends_service", None)
        local_user_id = getattr(editor, "friends_local_user_id", None)
        if service is None or local_user_id is None:
            return

        try:
            service.send_friend_request(requester_id=int(local_user_id), target_username=str(username))
        except ValueError as exc:
            QMessageBox.warning(editor, "Friends", str(exc))
            return
        except Exception as exc:  # pragma: no cover - defensive path
            QMessageBox.critical(editor, "Friends", f"Unable to send friend request: {exc}")
            return

        editor.status.showMessage(f"Friend request sent to {username}")
        editor._refresh_friends_sidebar()

    def _friends_accept_request(self, request_id: int) -> None:
        editor = cast("QtMapEditor", self)
        service = getattr(editor, "friends_service", None)
        local_user_id = getattr(editor, "friends_local_user_id", None)
        if service is None or local_user_id is None:
            return
        try:
            service.accept_request(user_id=int(local_user_id), request_id=int(request_id))
        except Exception as exc:
            QMessageBox.warning(editor, "Friends", f"Unable to accept request: {exc}")
            return
        editor.status.showMessage("Friend request accepted")
        editor._refresh_friends_sidebar()

    def _friends_reject_request(self, request_id: int) -> None:
        editor = cast("QtMapEditor", self)
        service = getattr(editor, "friends_service", None)
        local_user_id = getattr(editor, "friends_local_user_id", None)
        if service is None or local_user_id is None:
            return
        try:
            service.reject_request(user_id=int(local_user_id), request_id=int(request_id))
        except Exception as exc:
            QMessageBox.warning(editor, "Friends", f"Unable to reject request: {exc}")
            return
        editor.status.showMessage("Friend request rejected")
        editor._refresh_friends_sidebar()

    def _friends_set_privacy_mode(self, mode: str) -> None:
        editor = cast("QtMapEditor", self)
        normalized = str(mode or "").strip().lower()
        if normalized not in {"public", "friends_only", "private"}:
            normalized = "friends_only"
        editor.friends_privacy_mode = normalized
        editor._friends_update_presence(status="online")
        editor._refresh_friends_sidebar()

    def _friends_view_map(self, friend_id: int) -> None:
        editor = cast("QtMapEditor", self)
        service = getattr(editor, "friends_service", None)
        local_user_id = getattr(editor, "friends_local_user_id", None)
        if service is None or local_user_id is None:
            return

        snapshot = service.snapshot(user_id=int(local_user_id))
        for friend in (*snapshot.online, *snapshot.offline):
            if int(friend.id) != int(friend_id):
                continue
            map_name = friend.current_map
            if map_name:
                QMessageBox.information(editor, "Friend Activity", f"{friend.username} is editing: {map_name}")
            else:
                QMessageBox.information(editor, "Friend Activity", f"{friend.username} has no shared map activity.")
            return

    def _friends_chat(self, friend_id: int) -> None:
        """Open chat dialog with friend."""
        editor = cast("QtMapEditor", self)
        service = getattr(editor, "friends_service", None)
        local_user_id = getattr(editor, "friends_local_user_id", None)
        if service is None or local_user_id is None:
            return

        snapshot = service.snapshot(user_id=int(local_user_id))
        target_name = "Unknown"
        for friend in (*snapshot.online, *snapshot.offline):
            if int(friend.id) == int(friend_id):
                target_name = friend.username
                break

        from py_rme_canary.vis_layer.ui.dialogs.chat_dialog import ChatDialog
        dlg = ChatDialog(parent=editor, friend_name=target_name)
        dlg.exec()

    def _friends_sync_live_clients(self, clients: list[dict[str, object]]) -> None:
        editor = cast("QtMapEditor", self)
        service = getattr(editor, "friends_service", None)
        local_user_id = getattr(editor, "friends_local_user_id", None)
        if service is None or local_user_id is None:
            return
        names = {
            str(entry.get("name") or entry.get("username") or "").strip()
            for entry in clients
            if isinstance(entry, dict)
        }
        names = {name for name in names if name}
        service.sync_live_usernames(user_id=int(local_user_id), connected_usernames=names)
        editor._refresh_friends_sidebar()

    def _friends_periodic_sync(self) -> None:
        editor = cast("QtMapEditor", self)
        editor._friends_update_presence(status="online")
        editor._refresh_friends_sidebar()

    def _friends_mark_offline(self) -> None:
        editor = cast("QtMapEditor", self)
        service = getattr(editor, "friends_service", None)
        local_user_id = getattr(editor, "friends_local_user_id", None)
        if service is None or local_user_id is None:
            return
        service.update_presence(
            user_id=int(local_user_id),
            status="offline",
            current_map=None,
            privacy_mode=str(getattr(editor, "friends_privacy_mode", "friends_only")),  # type: ignore[arg-type]
        )

    def closeEvent(self, event) -> None:  # noqa: N802
        editor = cast("QtMapEditor", self)
        editor._friends_mark_offline()
        parent_close_event = getattr(super(), "closeEvent", None)
        if callable(parent_close_event):
            parent_close_event(event)
