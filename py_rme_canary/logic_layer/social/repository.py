from __future__ import annotations

import sqlite3
from pathlib import Path

from .models import FriendEntry, FriendRequest, PresenceStatus, PrivacyMode, UserProfile

_ALLOWED_PRESENCE: set[str] = {"online", "idle", "dnd", "offline"}
_ALLOWED_PRIVACY: set[str] = {"public", "friends_only", "private"}

_SCHEMA_SQL = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE,
    email TEXT NOT NULL UNIQUE,
    password_hash TEXT NOT NULL DEFAULT '',
    avatar_url TEXT NOT NULL DEFAULT '',
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS friendships (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user1_id INTEGER NOT NULL,
    user2_id INTEGER NOT NULL,
    status TEXT NOT NULL CHECK(status IN ('pending', 'accepted', 'rejected', 'blocked')),
    requested_by INTEGER NOT NULL,
    created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user1_id) REFERENCES users(id),
    FOREIGN KEY (user2_id) REFERENCES users(id),
    FOREIGN KEY (requested_by) REFERENCES users(id),
    UNIQUE(user1_id, user2_id),
    CHECK(user1_id < user2_id)
);

CREATE TABLE IF NOT EXISTS user_presence (
    user_id INTEGER PRIMARY KEY,
    status TEXT NOT NULL CHECK(status IN ('online', 'idle', 'dnd', 'offline')) DEFAULT 'offline',
    current_map TEXT,
    privacy_mode TEXT NOT NULL CHECK(privacy_mode IN ('public', 'friends_only', 'private')) DEFAULT 'friends_only',
    last_seen TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX IF NOT EXISTS idx_friendships_user1_status ON friendships(user1_id, status);
CREATE INDEX IF NOT EXISTS idx_friendships_user2_status ON friendships(user2_id, status);
CREATE INDEX IF NOT EXISTS idx_friendships_requested_by ON friendships(requested_by, status);
"""


def _canonical_pair(first_id: int, second_id: int) -> tuple[int, int]:
    a = int(first_id)
    b = int(second_id)
    return (a, b) if a < b else (b, a)


class FriendsRepository:
    """SQLite-backed repository for friend graph + presence."""

    def __init__(self, db_path: Path | str) -> None:
        self._db_path = Path(db_path)
        self._db_path.parent.mkdir(parents=True, exist_ok=True)
        self.init_schema()

    @property
    def db_path(self) -> Path:
        return self._db_path

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(str(self._db_path), timeout=30.0)
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        return conn

    def init_schema(self) -> None:
        with self._connect() as conn:
            conn.executescript(_SCHEMA_SQL)
            conn.commit()

    def upsert_user(
        self,
        *,
        username: str,
        email: str = "",
        password_hash: str = "",
        avatar_url: str = "",
    ) -> UserProfile:
        normalized_username = str(username).strip()
        if not normalized_username:
            raise ValueError("username is required")

        normalized_email = str(email).strip() or f"{normalized_username.lower()}@local.invalid"
        normalized_avatar = str(avatar_url or "").strip()

        with self._connect() as conn:
            existing = conn.execute(
                "SELECT id, username, email, avatar_url, created_at FROM users WHERE username = ?",
                (normalized_username,),
            ).fetchone()

            if existing is None:
                conn.execute(
                    """
                    INSERT INTO users (username, email, password_hash, avatar_url)
                    VALUES (?, ?, ?, ?)
                    """,
                    (normalized_username, normalized_email, str(password_hash or ""), normalized_avatar),
                )
            else:
                conn.execute(
                    """
                    UPDATE users
                    SET email = ?, avatar_url = ?
                    WHERE id = ?
                    """,
                    (
                        normalized_email or str(existing["email"] or ""),
                        normalized_avatar or str(existing["avatar_url"] or ""),
                        int(existing["id"]),
                    ),
                )

            row = conn.execute(
                "SELECT id, username, email, avatar_url, created_at FROM users WHERE username = ?",
                (normalized_username,),
            ).fetchone()

            if row is None:
                raise RuntimeError("failed to upsert user")

            return UserProfile(
                id=int(row["id"]),
                username=str(row["username"] or ""),
                email=str(row["email"] or ""),
                avatar_url=str(row["avatar_url"] or ""),
                created_at=str(row["created_at"] or ""),
            )

    def get_user_by_id(self, user_id: int) -> UserProfile | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, username, email, avatar_url, created_at FROM users WHERE id = ?",
                (int(user_id),),
            ).fetchone()
            if row is None:
                return None
            return UserProfile(
                id=int(row["id"]),
                username=str(row["username"] or ""),
                email=str(row["email"] or ""),
                avatar_url=str(row["avatar_url"] or ""),
                created_at=str(row["created_at"] or ""),
            )

    def get_user_by_username(self, username: str) -> UserProfile | None:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT id, username, email, avatar_url, created_at FROM users WHERE username = ?",
                (str(username).strip(),),
            ).fetchone()
            if row is None:
                return None
            return UserProfile(
                id=int(row["id"]),
                username=str(row["username"] or ""),
                email=str(row["email"] or ""),
                avatar_url=str(row["avatar_url"] or ""),
                created_at=str(row["created_at"] or ""),
            )

    def search_users(
        self,
        query: str,
        *,
        limit: int = 20,
        exclude_user_id: int | None = None,
    ) -> list[UserProfile]:
        normalized_query = str(query or "").strip()
        pattern = f"%{normalized_query}%"

        sql = """
            SELECT id, username, email, avatar_url, created_at
            FROM users
            WHERE (? = '' OR username LIKE ? COLLATE NOCASE)
        """
        params: list[object] = [normalized_query, pattern]
        if exclude_user_id is not None:
            sql += " AND id != ?"
            params.append(int(exclude_user_id))
        sql += " ORDER BY username ASC LIMIT ?"
        params.append(max(1, int(limit)))

        with self._connect() as conn:
            rows = conn.execute(sql, tuple(params)).fetchall()

        return [
            UserProfile(
                id=int(row["id"]),
                username=str(row["username"] or ""),
                email=str(row["email"] or ""),
                avatar_url=str(row["avatar_url"] or ""),
                created_at=str(row["created_at"] or ""),
            )
            for row in rows
        ]

    def send_friend_request(self, *, requester_id: int, target_id: int) -> int:
        requester = int(requester_id)
        target = int(target_id)
        if requester == target:
            raise ValueError("cannot befriend yourself")

        user1_id, user2_id = _canonical_pair(requester, target)
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, status, requested_by
                FROM friendships
                WHERE user1_id = ? AND user2_id = ?
                """,
                (user1_id, user2_id),
            ).fetchone()

            if row is None:
                cursor = conn.execute(
                    """
                    INSERT INTO friendships (user1_id, user2_id, status, requested_by)
                    VALUES (?, ?, 'pending', ?)
                    """,
                    (user1_id, user2_id, requester),
                )
                return int(cursor.lastrowid)

            status = str(row["status"] or "")
            row_id = int(row["id"])
            existing_requester = int(row["requested_by"])

            if status == "accepted":
                raise ValueError("users are already friends")
            if status == "blocked":
                raise ValueError("friendship is blocked")
            if status == "pending" and existing_requester == requester:
                raise ValueError("friend request already pending")

            conn.execute(
                """
                UPDATE friendships
                SET status = 'pending',
                    requested_by = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (requester, row_id),
            )
            return row_id

    def respond_to_request(self, *, actor_user_id: int, friendship_id: int, accept: bool) -> None:
        actor = int(actor_user_id)
        request_id = int(friendship_id)
        with self._connect() as conn:
            row = conn.execute(
                """
                SELECT id, user1_id, user2_id, status, requested_by
                FROM friendships
                WHERE id = ?
                """,
                (request_id,),
            ).fetchone()

            if row is None:
                raise ValueError("friend request not found")

            status = str(row["status"] or "")
            if status != "pending":
                raise ValueError("friend request is not pending")

            user1_id = int(row["user1_id"])
            user2_id = int(row["user2_id"])
            requested_by = int(row["requested_by"])
            if actor not in {user1_id, user2_id}:
                raise ValueError("request does not belong to user")
            if actor == requested_by:
                raise ValueError("request sender cannot accept/reject own request")

            next_status = "accepted" if bool(accept) else "rejected"
            conn.execute(
                """
                UPDATE friendships
                SET status = ?,
                    updated_at = CURRENT_TIMESTAMP
                WHERE id = ?
                """,
                (next_status, request_id),
            )

    def list_pending_requests(self, *, user_id: int) -> list[FriendRequest]:
        uid = int(user_id)
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    f.id AS friendship_id,
                    u.id AS requester_id,
                    u.username AS requester_name,
                    u.avatar_url AS requester_avatar,
                    f.created_at AS created_at
                FROM friendships f
                JOIN users u ON u.id = f.requested_by
                WHERE f.status = 'pending'
                  AND (f.user1_id = ? OR f.user2_id = ?)
                  AND f.requested_by != ?
                ORDER BY f.created_at ASC
                """,
                (uid, uid, uid),
            ).fetchall()

        return [
            FriendRequest(
                id=int(row["friendship_id"]),
                requester_id=int(row["requester_id"]),
                requester_name=str(row["requester_name"] or ""),
                requester_avatar=str(row["requester_avatar"] or ""),
                created_at=str(row["created_at"] or ""),
            )
            for row in rows
        ]

    def list_friends(self, *, user_id: int) -> list[FriendEntry]:
        uid = int(user_id)
        with self._connect() as conn:
            rows = conn.execute(
                """
                SELECT
                    u.id AS friend_id,
                    u.username AS username,
                    u.avatar_url AS avatar_url,
                    COALESCE(p.status, 'offline') AS status,
                    p.current_map AS current_map,
                    COALESCE(p.privacy_mode, 'friends_only') AS privacy_mode,
                    COALESCE(p.last_seen, '') AS last_seen
                FROM friendships f
                JOIN users u ON u.id = CASE
                    WHEN f.user1_id = ? THEN f.user2_id
                    ELSE f.user1_id
                END
                LEFT JOIN user_presence p ON p.user_id = u.id
                WHERE f.status = 'accepted'
                  AND (f.user1_id = ? OR f.user2_id = ?)
                ORDER BY
                    CASE COALESCE(p.status, 'offline')
                        WHEN 'online' THEN 0
                        WHEN 'idle' THEN 1
                        WHEN 'dnd' THEN 2
                        ELSE 3
                    END,
                    LOWER(u.username) ASC
                """,
                (uid, uid, uid),
            ).fetchall()

        entries: list[FriendEntry] = []
        for row in rows:
            status = str(row["status"] or "offline").lower()
            if status not in _ALLOWED_PRESENCE:
                status = "offline"

            privacy_mode = str(row["privacy_mode"] or "friends_only").lower()
            if privacy_mode not in _ALLOWED_PRIVACY:
                privacy_mode = "friends_only"

            current_map_raw = row["current_map"]
            current_map = str(current_map_raw) if current_map_raw is not None else None
            if privacy_mode == "private":
                current_map = None

            entries.append(
                FriendEntry(
                    id=int(row["friend_id"]),
                    username=str(row["username"] or ""),
                    avatar_url=str(row["avatar_url"] or ""),
                    status=status,  # type: ignore[arg-type]
                    current_map=current_map,
                    privacy_mode=privacy_mode,  # type: ignore[arg-type]
                    last_seen=str(row["last_seen"] or ""),
                )
            )
        return entries

    def update_presence(
        self,
        *,
        user_id: int,
        status: PresenceStatus,
        current_map: str | None = None,
        privacy_mode: PrivacyMode = "friends_only",
    ) -> None:
        uid = int(user_id)
        normalized_status = str(status).lower()
        normalized_privacy = str(privacy_mode).lower()
        if normalized_status not in _ALLOWED_PRESENCE:
            normalized_status = "offline"
        if normalized_privacy not in _ALLOWED_PRIVACY:
            normalized_privacy = "friends_only"

        map_value = str(current_map).strip() if current_map else None
        if normalized_privacy == "private":
            map_value = None

        with self._connect() as conn:
            conn.execute(
                """
                INSERT INTO user_presence (user_id, status, current_map, privacy_mode, last_seen)
                VALUES (?, ?, ?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(user_id) DO UPDATE SET
                    status = excluded.status,
                    current_map = excluded.current_map,
                    privacy_mode = excluded.privacy_mode,
                    last_seen = CURRENT_TIMESTAMP
                """,
                (uid, normalized_status, map_value, normalized_privacy),
            )
