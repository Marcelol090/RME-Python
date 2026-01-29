"""Lasso Selection Module for RME.

Provides polygon/freehand selection for advanced tile selection.

Layer: logic_layer (no PyQt6 imports)
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field
from typing import Any

log = logging.getLogger(__name__)


@dataclass
class LassoSelection:
    """Manages freehand/polygon selection state.

    Usage:
        lasso = LassoSelection()
        lasso.start(x, y)
        lasso.add_point(x2, y2)
        ...
        lasso.close()
        tiles = lasso.get_selected_tiles(current_z)
    """

    points: list[tuple[int, int]] = field(default_factory=list)
    is_active: bool = False
    z_level: int = 7

    def start(self, x: int, y: int, z: int = 7) -> None:
        """Start a new lasso selection."""
        self.points = [(int(x), int(y))]
        self.is_active = True
        self.z_level = int(z)
        log.debug("Lasso started at (%d, %d, %d)", x, y, z)

    def add_point(self, x: int, y: int) -> None:
        """Add a point to the current selection."""
        if self.is_active:
            self.points.append((int(x), int(y)))

    def close(self) -> None:
        """Close the polygon (connect last point to first)."""
        self.is_active = False
        log.debug("Lasso closed with %d points", len(self.points))

    def cancel(self) -> None:
        """Cancel current selection."""
        self.points.clear()
        self.is_active = False
        log.debug("Lasso cancelled")

    def clear(self) -> None:
        """Clear selection data."""
        self.points.clear()
        self.is_active = False

    @property
    def point_count(self) -> int:
        return len(self.points)

    def get_bounding_box(self) -> tuple[int, int, int, int] | None:
        """Get bounding box (min_x, min_y, max_x, max_y)."""
        if len(self.points) < 2:
            return None

        xs = [p[0] for p in self.points]
        ys = [p[1] for p in self.points]
        return (min(xs), min(ys), max(xs), max(ys))

    def point_in_polygon(self, x: int, y: int) -> bool:
        """Check if point is inside the polygon using ray casting."""
        if len(self.points) < 3:
            return False

        n = len(self.points)
        inside = False

        p1x, p1y = self.points[0]
        for i in range(1, n + 1):
            p2x, p2y = self.points[i % n]
            if y > min(p1y, p2y):
                if y <= max(p1y, p2y):
                    if x <= max(p1x, p2x):
                        if p1y != p2y:
                            xinters = (y - p1y) * (p2x - p1x) / (p2y - p1y) + p1x
                        if p1x == p2x or x <= xinters:
                            inside = not inside
            p1x, p1y = p2x, p2y

        return inside

    def get_selected_tiles(self, z: int | None = None) -> list[tuple[int, int, int]]:
        """Get all tile positions inside the polygon.

        Args:
            z: Z-level to use (defaults to selection z_level)

        Returns:
            List of (x, y, z) tuples for selected tiles
        """
        if len(self.points) < 3:
            return []

        bbox = self.get_bounding_box()
        if not bbox:
            return []

        min_x, min_y, max_x, max_y = bbox
        z_val = z if z is not None else self.z_level
        tiles: list[tuple[int, int, int]] = []

        for y in range(min_y, max_y + 1):
            for x in range(min_x, max_x + 1):
                if self.point_in_polygon(x, y):
                    tiles.append((x, y, z_val))

        log.debug("Lasso selected %d tiles", len(tiles))
        return tiles


class LassoTool:
    """Tool for using lasso selection in the editor.

    Tracks mouse movement and builds a polygon selection path.
    """

    def __init__(self) -> None:
        self._selection = LassoSelection()
        self._sample_distance: int = 2  # Min pixels between samples

    @property
    def is_active(self) -> bool:
        return self._selection.is_active

    @property
    def points(self) -> list[tuple[int, int]]:
        return self._selection.points

    @property
    def selection(self) -> LassoSelection:
        return self._selection

    def start(self, world_x: int, world_y: int, z: int = 7) -> None:
        """Start lasso at world coordinates."""
        self._selection.start(world_x, world_y, z)

    def add_point(self, world_x: int, world_y: int) -> bool:
        """Add point if far enough from last point.

        Returns True if point was added.
        """
        if not self.is_active:
            return False

        if len(self._selection.points) > 0:
            last_x, last_y = self._selection.points[-1]
            dist_sq = (world_x - last_x) ** 2 + (world_y - last_y) ** 2
            if dist_sq < self._sample_distance**2:
                return False

        self._selection.add_point(world_x, world_y)
        return True

    def finish(self) -> list[tuple[int, int, int]]:
        """Complete the selection and return selected tiles."""
        if not self.is_active:
            return []

        self._selection.close()
        return self._selection.get_selected_tiles()

    def cancel(self) -> None:
        """Cancel current selection."""
        self._selection.cancel()


# Singleton for global access
_lasso_tool: LassoTool | None = None


def get_lasso_tool() -> LassoTool:
    """Get the global lasso tool instance."""
    global _lasso_tool
    if _lasso_tool is None:
        _lasso_tool = LassoTool()
    return _lasso_tool
