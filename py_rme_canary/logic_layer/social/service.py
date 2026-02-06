from __future__ import annotations

import os
from pathlib import Path

from .models import FriendEntry, FriendsSnapshot, PresenceStatus, PrivacyMode, UserProfile
from .repository import FriendsRepository


class FriendsService:
    """Application-facing orchestration for friend relationships and presence."""

    def __init__(self, repository: FriendsRepository) -> None:
        self.repo = repository

    @classmethod
    def from_path(cls, db_path: Path | str) -> FriendsService:
        return cls(FriendsRepository(db_path))

    @classmethod
    def from_default_path(cls) -> FriendsService:
        override = str(os.environ.get("PY_RME_FRIENDS_DB", "")).strip()
        if override:
            return cls.from_path(Path(override))
        return cls.from_path(Path.home() / ".py_rme_canary" / "friends.db")

    def ensure_user(self, *, username: str, email: str = "", avatar_url: str = "") -> UserProfile:
        return self.repo.upsert_user(username=username, email=email, avatar_url=avatar_url)

    def send_friend_request(self, *, requester_id: int, target_username: str) -> int:
        target_name = str(target_username or "").strip()
        if not target_name:
            raise ValueError("target username is required")

        target = self.repo.get_user_by_username(target_name)
        if target is None:
            target = self.repo.upsert_user(username=target_name)

        return self.repo.send_friend_request(requester_id=int(requester_id), target_id=int(target.id))

    def accept_request(self, *, user_id: int, request_id: int) -> None:
        self.repo.respond_to_request(actor_user_id=int(user_id), friendship_id=int(request_id), accept=True)

    def reject_request(self, *, user_id: int, request_id: int) -> None:
        self.repo.respond_to_request(actor_user_id=int(user_id), friendship_id=int(request_id), accept=False)

    def update_presence(
        self,
        *,
        user_id: int,
        status: PresenceStatus,
        current_map: str | None = None,
        privacy_mode: PrivacyMode = "friends_only",
    ) -> None:
        self.repo.update_presence(
            user_id=int(user_id),
            status=status,
            current_map=current_map,
            privacy_mode=privacy_mode,
        )

    def update_presence_by_username(
        self,
        *,
        username: str,
        status: PresenceStatus,
        current_map: str | None = None,
        privacy_mode: PrivacyMode = "friends_only",
    ) -> None:
        user = self.repo.get_user_by_username(str(username).strip())
        if user is None:
            return
        self.update_presence(
            user_id=user.id,
            status=status,
            current_map=current_map,
            privacy_mode=privacy_mode,
        )

    def snapshot(self, *, user_id: int) -> FriendsSnapshot:
        pending = self.repo.list_pending_requests(user_id=int(user_id))
        friends = self.repo.list_friends(user_id=int(user_id))

        online: list[FriendEntry] = []
        offline: list[FriendEntry] = []
        for entry in friends:
            if entry.status in {"online", "idle", "dnd"}:
                online.append(entry)
            else:
                offline.append(entry)

        return FriendsSnapshot(
            pending_requests=pending,
            online=online,
            offline=offline,
        )

    def sync_live_usernames(
        self,
        *,
        user_id: int,
        connected_usernames: set[str] | list[str] | tuple[str, ...],
    ) -> FriendsSnapshot:
        normalized_connected = {str(name).strip().casefold() for name in connected_usernames if str(name).strip()}

        for entry in self.repo.list_friends(user_id=int(user_id)):
            expected_online = entry.username.casefold() in normalized_connected
            if expected_online and entry.status == "offline":
                self.repo.update_presence(
                    user_id=int(entry.id),
                    status="online",
                    current_map=entry.current_map,
                    privacy_mode=entry.privacy_mode,
                )
            elif not expected_online and entry.status != "offline":
                self.repo.update_presence(
                    user_id=int(entry.id),
                    status="offline",
                    current_map=None,
                    privacy_mode=entry.privacy_mode,
                )

        return self.snapshot(user_id=int(user_id))
