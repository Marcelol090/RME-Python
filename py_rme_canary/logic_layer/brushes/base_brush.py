from __future__ import annotations

from typing import TYPE_CHECKING, Protocol

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap
    from py_rme_canary.core.data.tile import Tile


class BaseBrush(Protocol):
    """Protocol for brushes that can be used with fill tool."""

    def apply(self, tile: Tile, game_map: GameMap) -> None:
        ...

    def draw(self, tile: Tile, game_map: GameMap) -> None:
        ...
