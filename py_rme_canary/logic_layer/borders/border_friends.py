"""Friend/enemy relationships between terrain brushes."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from typing import Protocol

FRIEND_ALL = 0xFFFFFFFF


def friend_of(*, friends: Iterable[int], hate_friends: bool, other_id: int) -> bool:
    ids = {int(x) for x in friends}
    if int(FRIEND_ALL) in ids:
        return not bool(hate_friends)
    if int(other_id) in ids:
        return not bool(hate_friends)
    return bool(hate_friends)


class SupportsFriends(Protocol):
    server_id: int
    friends: tuple[int, ...]
    hate_friends: bool


@dataclass(frozen=True, slots=True)
class FriendMatch:
    first_to_second: bool
    second_to_first: bool

    @property
    def is_friend(self) -> bool:
        return bool(self.first_to_second or self.second_to_first)


def brushes_are_friends(first: SupportsFriends, second: SupportsFriends) -> FriendMatch:
    return FriendMatch(
        first_to_second=friend_of(
            friends=first.friends,
            hate_friends=first.hate_friends,
            other_id=int(second.server_id),
        ),
        second_to_first=friend_of(
            friends=second.friends,
            hate_friends=second.hate_friends,
            other_id=int(first.server_id),
        ),
    )
