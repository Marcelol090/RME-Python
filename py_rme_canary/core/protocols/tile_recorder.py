from __future__ import annotations

from typing import Protocol

from py_rme_canary.core.data.tile import Tile

TileKey = tuple[int, int, int]


class TileChangeRecorder(Protocol):
    """Minimal protocol for recording tile diffs.

    Used by history/undo systems to record (before, after) tile mutations.
    """

    def record_tile_change(self, key: TileKey, before: Tile | None, after: Tile | None) -> None: ...
