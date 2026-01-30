"""Border group registry for auto-border processing."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field


@dataclass(slots=True)
class BorderGroupRegistry:
    """Track border group membership for item ids."""

    _items_by_group: dict[int, set[int]] = field(default_factory=dict)
    _group_by_item: dict[int, int] = field(default_factory=dict)

    def clear(self) -> None:
        self._items_by_group.clear()
        self._group_by_item.clear()

    def register_group(self, group_id: int, item_ids: Iterable[int]) -> None:
        gid = int(group_id)
        items = self._items_by_group.setdefault(gid, set())
        for item_id in item_ids:
            iid = int(item_id)
            if iid <= 0:
                continue
            items.add(iid)
            self._group_by_item[iid] = gid

    def group_for_item(self, item_id: int) -> int | None:
        return self._group_by_item.get(int(item_id))

    def items_for_group(self, group_id: int) -> frozenset[int]:
        return frozenset(self._items_by_group.get(int(group_id), set()))
