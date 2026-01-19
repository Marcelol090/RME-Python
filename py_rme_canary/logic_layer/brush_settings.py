"""Brush settings: size, shape, and tile offset calculations.

Mirrors legacy C++ BrushShape enum and brush_size from gui.cpp.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntEnum
from typing import Any, Callable, Iterator

from py_rme_canary.core.data.item import Position


class BrushShape(IntEnum):
    """Brush shape for multi-tile painting."""

    CIRCLE = 0
    SQUARE = 1


# Predefined brush sizes matching RME C++
# Size 0 = 1x1, Size 1 = 3x3, etc.
BRUSH_SIZE_DIMENSIONS = {
    0: 1,   # 1x1
    1: 3,   # 3x3
    2: 5,   # 5x5
    4: 7,   # 7x7
    6: 9,   # 9x9
    8: 11,  # 11x11
    11: 15, # 15x15
}


@dataclass(frozen=True, slots=True)
class BrushSettings:
    """Current brush painting settings.

    Attributes:
        size: Brush size index (0=1x1, 1=3x3, 2=5x5, etc.)
        shape: Brush shape (CIRCLE or SQUARE)
    """

    size: int = 0
    shape: BrushShape = BrushShape.SQUARE

    def get_radius(self) -> int:
        """Get brush radius in tiles.

        Returns:
            Radius (0 for 1x1, 1 for 3x3, etc.)
        """
        dimension = BRUSH_SIZE_DIMENSIONS.get(self.size, 1)
        return (dimension - 1) // 2

    def get_affected_positions(
        self,
        center: Position,
    ) -> Iterator[Position]:
        """Generate all positions affected by brush at center.

        For SQUARE shape: all tiles in square area.
        For CIRCLE shape: tiles within circular radius.

        Args:
            center: Center position of brush

        Yields:
            Position objects for each affected tile

        Example:
            >>> settings = BrushSettings(size=1, shape=BrushShape.SQUARE)
            >>> list(settings.get_affected_positions(Position(10, 10, 7)))
            [Position(9, 9, 7), Position(10, 9, 7), ...]
        """
        radius = self.get_radius()

        if radius == 0:
            yield center
            return

        cx, cy, cz = center.x, center.y, center.z

        if self.shape == BrushShape.SQUARE:
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    yield Position(x=cx + dx, y=cy + dy, z=cz)
        else:
            # CIRCLE shape - use distance check
            radius_sq = radius * radius
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if dx * dx + dy * dy <= radius_sq:
                        yield Position(x=cx + dx, y=cy + dy, z=cz)

    def get_preview_positions(
        self,
        center: Position,
    ) -> list[tuple[int, int]]:
        """Get (dx, dy) offsets for brush preview rendering.

        Returns only the offset pairs (dx, dy), not full positions.
        Useful for preview rendering where z is implied.
        """
        radius = self.get_radius()

        if radius == 0:
            return [(0, 0)]

        offsets: list[tuple[int, int]] = []

        if self.shape == BrushShape.SQUARE:
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    offsets.append((dx, dy))
        else:
            radius_sq = radius * radius
            for dy in range(-radius, radius + 1):
                for dx in range(-radius, radius + 1):
                    if dx * dx + dy * dy <= radius_sq:
                        offsets.append((dx, dy))

        return offsets


def apply_brush_with_size(
    brush_func: Callable[[Any, Position], list[Any]],
    game_map: Any,
    center: Position,
    settings: BrushSettings,
) -> list[Any]:
    """Apply a brush function across all positions in brush size.

    Args:
        brush_func: Function(game_map, pos) -> list of changes
        game_map: Target game map
        center: Center position
        settings: Brush size/shape settings

    Returns:
        Combined list of all changes
    """
    all_changes = []
    for pos in settings.get_affected_positions(center):
        changes = brush_func(game_map, pos)
        all_changes.extend(changes)
    return all_changes
