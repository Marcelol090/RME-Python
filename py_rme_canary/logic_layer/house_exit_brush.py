"""House exit brush implementation for py_rme_canary.

Marks tile as house exit/entry point and updates house entry position.
Reference: source/house_exit_brush.cpp (legacy C++)
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from py_rme_canary.core.data.item import Position
from py_rme_canary.core.data.tile import Tile

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap


@dataclass(frozen=True, slots=True)
class HouseExitBrush:
    """Marks tiles as house exit/entry points.

    HouseExitBrush sets the house's entry position to the painted tile.
    This is used to mark where players spawn when entering the house.

    Requirements:
    - Tile must belong to the house (house_id must match)
    - Tile must have ground

    Attributes:
        house_id: Unique house identifier
        house_name: Human-readable house name

    Example:
        >>> brush = HouseExitBrush(house_id=1001, house_name="Fibula House")
        >>> if brush.can_draw(game_map, pos):
        ...     changes = brush.draw(game_map, pos)
    """

    house_id: int
    house_name: str

    def get_name(self) -> str:
        """Get brush name."""
        return f"House Exit {self.house_id}: {self.house_name}"

    def can_draw(self, game_map: GameMap, pos: Position) -> bool:
        """Check if house exit can be painted at position.

        Requirements:
        1. Tile exists
        2. Tile has ground
        3. Tile belongs to this house

        Args:
            game_map: Target game map
            pos: Position to check

        Returns:
            True if house exit can be painted, False otherwise
        """
        tile = game_map.get_tile(pos.x, pos.y, pos.z)
        if tile is None:
            return False

        # Require ground
        if tile.ground is None:
            return False

        # Require tile to be part of this house
        return tile.house_id == self.house_id

    def draw(
        self,
        game_map: GameMap,
        pos: Position,
    ) -> list[tuple[Position, Tile]]:
        """Paint house exit at position.

        Actions:
        1. Update house entry position to this tile

        Note: This modifies the house object in game_map.houses dict.

        Args:
            game_map: Target game map
            pos: Position to paint house exit

        Returns:
            List of (position, new_tile) tuples for history system
        """
        tile = game_map.get_tile(pos.x, pos.y, pos.z)
        if tile is None or tile.ground is None:
            return []
        if tile.house_id is not None and tile.house_id != self.house_id:
            return []

        # Update house entry position
        house = game_map.houses.get(self.house_id)
        if house is not None:
            new_house = replace(house, entry=Position(x=pos.x, y=pos.y, z=pos.z))
            game_map.houses[self.house_id] = new_house

        # Return tile unchanged (exit brush only modifies house metadata)
        return [(pos, tile)]

    def undraw(
        self,
        game_map: GameMap,
        pos: Position,
    ) -> list[tuple[Position, Tile]]:
        """Remove house exit from position.

        Actions:
        1. Clear house entry if it matches this position

        Args:
            game_map: Target game map
            pos: Position to remove house exit from

        Returns:
            List of (position, new_tile) tuples for history system
        """
        tile = game_map.get_tile(pos.x, pos.y, pos.z)
        if tile is None:
            return []

        # Clear house entry if it matches this position
        house = game_map.houses.get(self.house_id)
        if (
            house is not None
            and house.entry is not None
            and (house.entry.x == pos.x and house.entry.y == pos.y and house.entry.z == pos.z)
        ):
            new_house = replace(house, entry=None)
            game_map.houses[self.house_id] = new_house

        # Return tile unchanged
        return [(pos, tile)]
