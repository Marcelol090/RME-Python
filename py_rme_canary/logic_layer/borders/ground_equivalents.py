"""Ground-equivalent mapping for border items."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field

from py_rme_canary.core.data.tile import Tile


@dataclass(slots=True)
class GroundEquivalentRegistry:
    _by_item: dict[int, int] = field(default_factory=dict)
    _items_by_ground: dict[int, set[int]] = field(default_factory=dict)

    def clear(self) -> None:
        self._by_item.clear()
        self._items_by_ground.clear()

    def register(self, item_id: int, ground_id: int) -> None:
        iid = int(item_id)
        gid = int(ground_id)
        if iid <= 0 or gid <= 0:
            return
        self._by_item[iid] = gid
        self._items_by_ground.setdefault(gid, set()).add(iid)

    def register_many(self, ground_id: int, item_ids: Iterable[int]) -> None:
        for item_id in item_ids:
            self.register(int(item_id), int(ground_id))

    def ground_for_item(self, item_id: int) -> int | None:
        return self._by_item.get(int(item_id))

    def items_for_ground(self, ground_id: int) -> frozenset[int]:
        return frozenset(self._items_by_ground.get(int(ground_id), set()))

    def resolve_ground_id(self, tile: Tile | None) -> int | None:
        if tile is None:
            return None
        if tile.ground is not None:
            return int(tile.ground.id)
        for item in tile.items:
            gid = self._by_item.get(int(item.id))
            if gid:
                return int(gid)
        return None
