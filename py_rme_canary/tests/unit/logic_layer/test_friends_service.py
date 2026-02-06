from __future__ import annotations

import pytest

from py_rme_canary.logic_layer.social import FriendsService


def _service(tmp_path) -> FriendsService:
    db_path = tmp_path / "friends.db"
    return FriendsService.from_path(db_path)


def test_friend_request_acceptance_roundtrip(tmp_path) -> None:
    service = _service(tmp_path)
    alice = service.ensure_user(username="alice")
    bob = service.ensure_user(username="bob")

    request_id = service.send_friend_request(requester_id=alice.id, target_username="bob")
    snapshot_bob = service.snapshot(user_id=bob.id)
    assert len(snapshot_bob.pending_requests) == 1
    assert snapshot_bob.pending_requests[0].id == request_id
    assert snapshot_bob.pending_requests[0].requester_name == "alice"

    service.accept_request(user_id=bob.id, request_id=request_id)
    snapshot_alice = service.snapshot(user_id=alice.id)
    snapshot_bob_after = service.snapshot(user_id=bob.id)
    assert [friend.username for friend in snapshot_alice.offline] == ["bob"]
    assert [friend.username for friend in snapshot_bob_after.offline] == ["alice"]
    assert snapshot_bob_after.pending_requests == []


def test_sender_cannot_accept_own_request(tmp_path) -> None:
    service = _service(tmp_path)
    alice = service.ensure_user(username="alice")
    service.ensure_user(username="bob")
    request_id = service.send_friend_request(requester_id=alice.id, target_username="bob")

    with pytest.raises(ValueError, match="sender"):
        service.accept_request(user_id=alice.id, request_id=request_id)


def test_private_presence_hides_current_map_for_friends(tmp_path) -> None:
    service = _service(tmp_path)
    alice = service.ensure_user(username="alice")
    bob = service.ensure_user(username="bob")
    request_id = service.send_friend_request(requester_id=alice.id, target_username="bob")
    service.accept_request(user_id=bob.id, request_id=request_id)

    service.update_presence(
        user_id=bob.id,
        status="online",
        current_map="Cave Level -1",
        privacy_mode="friends_only",
    )
    snapshot = service.snapshot(user_id=alice.id)
    assert snapshot.online[0].username == "bob"
    assert snapshot.online[0].current_map == "Cave Level -1"

    service.update_presence(
        user_id=bob.id,
        status="online",
        current_map="Cave Level -1",
        privacy_mode="private",
    )
    snapshot_private = service.snapshot(user_id=alice.id)
    assert snapshot_private.online[0].username == "bob"
    assert snapshot_private.online[0].current_map is None


def test_sync_live_usernames_updates_friend_presence(tmp_path) -> None:
    service = _service(tmp_path)
    alice = service.ensure_user(username="alice")
    bob = service.ensure_user(username="bob")
    request_id = service.send_friend_request(requester_id=alice.id, target_username="bob")
    service.accept_request(user_id=bob.id, request_id=request_id)

    service.update_presence(user_id=bob.id, status="offline", current_map=None, privacy_mode="friends_only")
    snapshot_online = service.sync_live_usernames(user_id=alice.id, connected_usernames={"bob"})
    assert [friend.username for friend in snapshot_online.online] == ["bob"]
    assert snapshot_online.offline == []

    snapshot_offline = service.sync_live_usernames(user_id=alice.id, connected_usernames=set())
    assert [friend.username for friend in snapshot_offline.offline] == ["bob"]
