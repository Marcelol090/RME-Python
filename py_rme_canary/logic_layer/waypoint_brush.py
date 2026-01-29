"""Waypoint brush implementation for py_rme_canary.

Places navigation waypoints on tiles.
Reference: source/waypoint_brush.cpp (legacy C++)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from py_rme_canary.core.data.tile import Tile

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap
    from py_rme_canary.core.data.item import Position


@dataclass(frozen=True, slots=True)
class WaypointBrush:
    """Places navigation waypoints on tiles.

    Waypoints are named markers used for navigation and scripting.
    Each waypoint must have a unique name.

    Attributes:
        waypoint_name: Unique waypoint identifier

    Example:
        >>> brush = WaypointBrush(waypoint_name="temple_entrance")
        >>> if brush.can_draw(game_map, pos):
        ...     changes = brush.draw(game_map, pos)
    """

    waypoint_name: str

    def get_name(self) -> str:
        """Get brush name."""
        return f"Waypoint: {self.waypoint_name}"

    def can_draw(self, game_map: GameMap, pos: Position) -> bool:
        """Check if waypoint can be placed at position.

        Requirements:
        1. Tile exists
        2. Tile has ground

        Args:
            game_map: Target game map
            pos: Position to check

        Returns:
            True if waypoint can be placed, False otherwise
        """
        tile = game_map.get_tile(pos.x, pos.y, pos.z)
        if tile is None:
            return False

        # Require ground
        return tile.ground is not None

    def draw(
        self,
        game_map: GameMap,
        pos: Position,
    ) -> list[tuple[Position, Tile]]:
        """Place waypoint at position.

        Note: Waypoints are stored in game_map.waypoints dict.

        Args:
            game_map: Target game map
            pos: Position to place waypoint

        Returns:
            List of (position, new_tile) tuples for history system
        """
        tile = game_map.get_tile(pos.x, pos.y, pos.z)
        if tile is None or not self.can_draw(game_map, pos):
            return []

        # Add waypoint to map
        game_map.waypoints[self.waypoint_name] = pos

        # Return tile unchanged (waypoint is map metadata)
        return [(pos, tile)]

    def undraw(
        self,
        game_map: GameMap,
        pos: Position,
    ) -> list[tuple[Position, Tile]]:
        """Remove waypoint from position.

        Args:
            game_map: Target game map
            pos: Position to remove waypoint from

        Returns:
            List of (position, new_tile) tuples for history system
        """
        tile = game_map.get_tile(pos.x, pos.y, pos.z)
        if tile is None:
            return []

        # Remove waypoint if it matches this position
        if self.waypoint_name in game_map.waypoints:
            waypoint_pos = game_map.waypoints[self.waypoint_name]
            if waypoint_pos.x == pos.x and waypoint_pos.y == pos.y and waypoint_pos.z == pos.z:
                del game_map.waypoints[self.waypoint_name]

        # Return tile unchanged
        return [(pos, tile)]
