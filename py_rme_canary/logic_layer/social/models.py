from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal

PresenceStatus = Literal["online", "idle", "dnd", "offline"]
PrivacyMode = Literal["public", "friends_only", "private"]
FriendshipStatus = Literal["pending", "accepted", "rejected", "blocked"]


@dataclass(frozen=True, slots=True)
class UserProfile:
    """Basic user identity persisted in the friends database."""

    id: int
    username: str
    email: str
    avatar_url: str = ""
    created_at: str = ""


@dataclass(frozen=True, slots=True)
class FriendRequest:
    """Pending inbound friend request."""

    id: int
    requester_id: int
    requester_name: str
    requester_avatar: str = ""
    created_at: str = ""


@dataclass(frozen=True, slots=True)
class FriendEntry:
    """Accepted friend with presence metadata."""

    id: int
    username: str
    avatar_url: str
    status: PresenceStatus
    current_map: str | None = None
    privacy_mode: PrivacyMode = "friends_only"
    last_seen: str = ""


@dataclass(slots=True)
class FriendsSnapshot:
    """UI-friendly grouped state for the friends panel."""

    pending_requests: list[FriendRequest] = field(default_factory=list)
    online: list[FriendEntry] = field(default_factory=list)
    offline: list[FriendEntry] = field(default_factory=list)
