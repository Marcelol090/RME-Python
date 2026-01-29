"""Symmetry/Mirroring Manager for map editing.

Provides Aseprite-style symmetry functionality where drawing operations
are automatically mirrored across vertical/horizontal axes.

Layer: logic_layer (no PyQt6 imports)
"""
from __future__ import annotations

from collections.abc import Callable
from contextlib import suppress
from dataclasses import dataclass
from enum import IntEnum


class Direction(IntEnum):
    """Cardinal directions for items."""

    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3


@dataclass
class MirroredPosition:
    """Represents a mirrored position with optional direction transformation."""

    x: int
    y: int
    z: int
    mirror_type: str  # "vertical", "horizontal", or "both"
    direction_transform: dict[Direction, Direction] | None = None


class SymmetryManager:
    """Manages symmetry/mirroring state for map editing.

    Usage:
        manager = SymmetryManager()
        manager.set_center(1024, 1024)  # Center of 2048x2048 map

        manager.vertical_enabled = True
        positions = manager.calculate_mirrored_positions(100, 500, 7)
        # Returns: [MirroredPosition(1948, 500, 7, "vertical", ...)]
    """

    # Direction transforms for mirroring
    VERTICAL_DIRECTION_MAP: dict[Direction, Direction] = {
        Direction.NORTH: Direction.NORTH,
        Direction.SOUTH: Direction.SOUTH,
        Direction.EAST: Direction.WEST,
        Direction.WEST: Direction.EAST,
    }

    HORIZONTAL_DIRECTION_MAP: dict[Direction, Direction] = {
        Direction.NORTH: Direction.SOUTH,
        Direction.SOUTH: Direction.NORTH,
        Direction.EAST: Direction.EAST,
        Direction.WEST: Direction.WEST,
    }

    BOTH_DIRECTION_MAP: dict[Direction, Direction] = {
        Direction.NORTH: Direction.SOUTH,
        Direction.SOUTH: Direction.NORTH,
        Direction.EAST: Direction.WEST,
        Direction.WEST: Direction.EAST,
    }

    def __init__(self) -> None:
        self._vertical_enabled: bool = False
        self._horizontal_enabled: bool = False
        self._center_x: int = 0
        self._center_y: int = 0
        self._dragging_axis: str | None = None  # "vertical", "horizontal", or None

        # Callbacks for state changes
        self._on_state_changed: list[Callable[[], None]] = []

    # Properties
    @property
    def vertical_enabled(self) -> bool:
        return self._vertical_enabled

    @vertical_enabled.setter
    def vertical_enabled(self, value: bool) -> None:
        if self._vertical_enabled != bool(value):
            self._vertical_enabled = bool(value)
            self._notify_state_changed()

    @property
    def horizontal_enabled(self) -> bool:
        return self._horizontal_enabled

    @horizontal_enabled.setter
    def horizontal_enabled(self, value: bool) -> None:
        if self._horizontal_enabled != bool(value):
            self._horizontal_enabled = bool(value)
            self._notify_state_changed()

    @property
    def center_x(self) -> int:
        return self._center_x

    @center_x.setter
    def center_x(self, value: int) -> None:
        self._center_x = int(value)
        self._notify_state_changed()

    @property
    def center_y(self) -> int:
        return self._center_y

    @center_y.setter
    def center_y(self, value: int) -> None:
        self._center_y = int(value)
        self._notify_state_changed()

    @property
    def is_active(self) -> bool:
        """True if any symmetry mode is enabled."""
        return self._vertical_enabled or self._horizontal_enabled

    @property
    def dragging_axis(self) -> str | None:
        return self._dragging_axis

    @dragging_axis.setter
    def dragging_axis(self, value: str | None) -> None:
        self._dragging_axis = value

    # Public methods
    def set_center(self, x: int, y: int) -> None:
        """Set the center point for symmetry axes."""
        self._center_x = int(x)
        self._center_y = int(y)
        self._notify_state_changed()

    def toggle_vertical(self) -> bool:
        """Toggle vertical symmetry. Returns new state."""
        self.vertical_enabled = not self._vertical_enabled
        return self._vertical_enabled

    def toggle_horizontal(self) -> bool:
        """Toggle horizontal symmetry. Returns new state."""
        self.horizontal_enabled = not self._horizontal_enabled
        return self._horizontal_enabled

    def add_state_listener(self, callback: Callable[[], None]) -> None:
        """Add a listener for state changes."""
        if callback not in self._on_state_changed:
            self._on_state_changed.append(callback)

    def remove_state_listener(self, callback: Callable[[], None]) -> None:
        """Remove a state change listener."""
        if callback in self._on_state_changed:
            self._on_state_changed.remove(callback)

    def calculate_mirrored_positions(
        self, x: int, y: int, z: int
    ) -> list[MirroredPosition]:
        """Calculate all mirrored positions for a given coordinate.

        Args:
            x: Original X coordinate
            y: Original Y coordinate
            z: Z level (not mirrored)

        Returns:
            List of MirroredPosition objects (excludes original position)
        """
        result: list[MirroredPosition] = []

        if self._vertical_enabled:
            # Mirror across vertical axis (X changes)
            distance_x = x - self._center_x
            mirrored_x = self._center_x - distance_x
            result.append(
                MirroredPosition(
                    x=int(mirrored_x),
                    y=int(y),
                    z=int(z),
                    mirror_type="vertical",
                    direction_transform=self.VERTICAL_DIRECTION_MAP,
                )
            )

        if self._horizontal_enabled:
            # Mirror across horizontal axis (Y changes)
            distance_y = y - self._center_y
            mirrored_y = self._center_y - distance_y
            result.append(
                MirroredPosition(
                    x=int(x),
                    y=int(mirrored_y),
                    z=int(z),
                    mirror_type="horizontal",
                    direction_transform=self.HORIZONTAL_DIRECTION_MAP,
                )
            )

        if self._vertical_enabled and self._horizontal_enabled:
            # Diagonal mirror (both X and Y change)
            distance_x = x - self._center_x
            distance_y = y - self._center_y
            mirrored_x = self._center_x - distance_x
            mirrored_y = self._center_y - distance_y
            result.append(
                MirroredPosition(
                    x=int(mirrored_x),
                    y=int(mirrored_y),
                    z=int(z),
                    mirror_type="both",
                    direction_transform=self.BOTH_DIRECTION_MAP,
                )
            )

        return result

    def mirror_direction(
        self, direction: Direction | int, mirror_type: str
    ) -> Direction:
        """Get the mirrored direction for an item.

        Args:
            direction: Original direction
            mirror_type: "vertical", "horizontal", or "both"

        Returns:
            Transformed direction
        """
        dir_val = Direction(int(direction)) if not isinstance(direction, Direction) else direction

        if mirror_type == "vertical":
            return self.VERTICAL_DIRECTION_MAP.get(dir_val, dir_val)
        elif mirror_type == "horizontal":
            return self.HORIZONTAL_DIRECTION_MAP.get(dir_val, dir_val)
        elif mirror_type == "both":
            return self.BOTH_DIRECTION_MAP.get(dir_val, dir_val)
        return dir_val

    def filter_visible_positions(
        self,
        positions: list[MirroredPosition],
        viewport_x_min: int,
        viewport_y_min: int,
        viewport_x_max: int,
        viewport_y_max: int,
    ) -> list[MirroredPosition]:
        """Filter mirrored positions to only those visible in viewport.

        Optimization for large maps.
        """
        return [
            p
            for p in positions
            if viewport_x_min <= p.x <= viewport_x_max
            and viewport_y_min <= p.y <= viewport_y_max
        ]

    def _notify_state_changed(self) -> None:
        """Notify all listeners of state change."""
        for callback in self._on_state_changed:
            with suppress(Exception):
                callback()


# Singleton instance for global access
_symmetry_manager: SymmetryManager | None = None


def get_symmetry_manager() -> SymmetryManager:
    """Get the global symmetry manager instance."""
    global _symmetry_manager
    if _symmetry_manager is None:
        _symmetry_manager = SymmetryManager()
    return _symmetry_manager
