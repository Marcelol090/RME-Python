"""Flood Fill Tool for area filling.

This module implements flood fill (bucket) tool for the map editor.
Similar to paint bucket tool in image editors - fills connected areas.

Reference:
    - C++ Legacy: Similar to ground_brush.cpp fill mode
    - GAP_ANALYSIS.md: Advanced Tools

Features:
    - FloodFillConfig: Fill settings (mode, tolerance, limits)
    - FloodFillEngine: Core fill algorithm (BFS-based)
    - FillMode: Different fill strategies
    - FillResult: Statistics about filled area

Layer: logic_layer (no PyQt6 dependencies)
"""

from __future__ import annotations

import logging
from collections import deque
from collections.abc import Iterator
from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap
    from py_rme_canary.core.data.tile import Tile
    from py_rme_canary.logic_layer.brushes.base_brush import BaseBrush

logger = logging.getLogger(__name__)


class FillMode(Enum):
    """Fill algorithm mode."""

    CONTIGUOUS = auto()  # Fill only connected same-type tiles
    SAME_TYPE = auto()  # Fill all matching tiles in area (not connected)
    REPLACE_ALL = auto()  # Fill entire selection regardless of type
    BORDER_ONLY = auto()  # Fill only the border of the area


class FillDirection(Enum):
    """Connectivity for flood fill."""

    FOUR_WAY = 4  # Cardinal directions only (N,S,E,W)
    EIGHT_WAY = 8  # Include diagonals


@dataclass(slots=True)
class FillConfig:
    """Configuration for flood fill operation.

    Attributes:
        mode: Fill algorithm mode.
        direction: 4-way or 8-way connectivity.
        max_tiles: Maximum tiles to fill (safety limit).
        match_ground: Match ground item ID.
        match_items: Match all items on tile.
        single_floor: Fill only current floor.
        respect_borders: Stop at auto-border tiles.
        fill_empty: Allow filling empty tiles.
    """

    mode: FillMode = FillMode.CONTIGUOUS
    direction: FillDirection = FillDirection.FOUR_WAY
    max_tiles: int = 50000
    match_ground: bool = True
    match_items: bool = False
    single_floor: bool = True
    respect_borders: bool = True
    fill_empty: bool = True


@dataclass
class FillResult:
    """Result of a flood fill operation.

    Attributes:
        tiles_filled: Number of tiles that were filled.
        tiles_checked: Total tiles checked during operation.
        stopped_by_limit: Whether fill was stopped by max_tiles limit.
        bounds: Bounding box of filled area (min_x, min_y, max_x, max_y).
        error: Error message if operation failed.
    """

    tiles_filled: int = 0
    tiles_checked: int = 0
    stopped_by_limit: bool = False
    bounds: tuple[int, int, int, int] | None = None
    error: str | None = None

    @property
    def success(self) -> bool:
        return self.error is None and self.tiles_filled > 0


# Type alias for position
Position = tuple[int, int, int]  # (x, y, z)


class FloodFillEngine:
    """Engine for performing flood fill operations.

    Uses breadth-first search (BFS) for efficient contiguous fill.

    Example:
        engine = FloodFillEngine(game_map)
        result = engine.fill(
            start=(100, 100, 7),
            brush=ground_brush,
            config=FillConfig()
        )
        print(f"Filled {result.tiles_filled} tiles")
    """

    # Direction offsets for 4-way connectivity
    DIRECTIONS_4 = [(0, -1), (1, 0), (0, 1), (-1, 0)]  # N, E, S, W

    # Additional diagonal directions for 8-way
    DIAGONALS = [(-1, -1), (1, -1), (-1, 1), (1, 1)]  # NW, NE, SW, SE

    def __init__(self, game_map: GameMap) -> None:
        """Initialize the flood fill engine.

        Args:
            game_map: The map to perform fills on.
        """
        self._map = game_map
        self._brush: BaseBrush | None = None
        self._config = FillConfig()

        # Tracking
        self._visited: set[Position] = set()
        self._to_fill: set[Position] = set()
        self._reference_tile: Tile | None = None

    def fill(
        self,
        start: Position,
        brush: BaseBrush,
        config: FillConfig | None = None,
    ) -> FillResult:
        """Perform flood fill starting from a position.

        Args:
            start: Starting position (x, y, z).
            brush: Brush to apply to filled tiles.
            config: Fill configuration (uses default if None).

        Returns:
            FillResult with statistics about the operation.
        """
        self._brush = brush
        self._config = config or FillConfig()
        self._visited.clear()
        self._to_fill.clear()

        x, y, z = start

        # Validate start position
        if not self._is_valid_position(x, y, z):
            return FillResult(error="Invalid start position")

        # Get reference tile for matching
        self._reference_tile = self._map.get_tile(x, y, z)

        # Perform fill based on mode
        if self._config.mode == FillMode.CONTIGUOUS:
            result = self._contiguous_fill(start)
        elif self._config.mode == FillMode.SAME_TYPE:
            result = self._same_type_fill(start)
        elif self._config.mode == FillMode.REPLACE_ALL:
            result = self._replace_all_fill(start)
        elif self._config.mode == FillMode.BORDER_ONLY:
            result = self._border_fill(start)
        else:
            return FillResult(error=f"Unknown fill mode: {self._config.mode}")

        # Apply brush to collected tiles
        if self._to_fill:
            self._apply_brush_to_tiles()

        return result

    def _contiguous_fill(self, start: Position) -> FillResult:
        """BFS-based contiguous flood fill.

        Fills only tiles that are connected to the start position
        and match the reference tile.
        """
        queue: deque[Position] = deque([start])
        self._visited.add(start)

        directions = self._get_directions()

        min_x = max_x = start[0]
        min_y = max_y = start[1]
        checked = 0

        while queue:
            if len(self._to_fill) >= self._config.max_tiles:
                return FillResult(
                    tiles_filled=len(self._to_fill),
                    tiles_checked=checked,
                    stopped_by_limit=True,
                    bounds=(min_x, min_y, max_x, max_y),
                )

            x, y, z = queue.popleft()
            checked += 1

            # Check if tile matches
            if self._matches_reference(x, y, z):
                self._to_fill.add((x, y, z))

                # Update bounds
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)

                # Add neighbors
                for dx, dy in directions:
                    nx, ny = x + dx, y + dy
                    nz = z if self._config.single_floor else z
                    pos = (nx, ny, nz)

                    if pos not in self._visited and self._is_valid_position(nx, ny, nz):
                        self._visited.add(pos)
                        queue.append(pos)

        return FillResult(
            tiles_filled=len(self._to_fill),
            tiles_checked=checked,
            bounds=(min_x, min_y, max_x, max_y) if self._to_fill else None,
        )

    def _same_type_fill(self, start: Position) -> FillResult:
        """Fill all tiles of the same type in a bounded area.

        Fills ALL matching tiles within max_tiles distance,
        regardless of connectivity.
        """
        x, y, z = start
        radius = int(self._config.max_tiles**0.5)  # Square root for area

        checked = 0
        min_x = max_x = x
        min_y = max_y = y

        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if len(self._to_fill) >= self._config.max_tiles:
                    return FillResult(
                        tiles_filled=len(self._to_fill),
                        tiles_checked=checked,
                        stopped_by_limit=True,
                        bounds=(min_x, min_y, max_x, max_y),
                    )

                nx, ny = x + dx, y + dy
                nz = z
                checked += 1

                if self._is_valid_position(nx, ny, nz) and self._matches_reference(nx, ny, nz):
                    self._to_fill.add((nx, ny, nz))
                    min_x = min(min_x, nx)
                    max_x = max(max_x, nx)
                    min_y = min(min_y, ny)
                    max_y = max(max_y, ny)

        return FillResult(
            tiles_filled=len(self._to_fill),
            tiles_checked=checked,
            bounds=(min_x, min_y, max_x, max_y) if self._to_fill else None,
        )

    def _replace_all_fill(self, start: Position) -> FillResult:
        """Replace all tiles in current selection or visible viewport."""
        # For now, use same_type logic but without matching
        x, y, z = start
        radius = int(self._config.max_tiles**0.5) // 2

        checked = 0
        for dx in range(-radius, radius + 1):
            for dy in range(-radius, radius + 1):
                if len(self._to_fill) >= self._config.max_tiles:
                    break

                nx, ny = x + dx, y + dy
                checked += 1

                if self._is_valid_position(nx, ny, z):
                    self._to_fill.add((nx, ny, z))

        return FillResult(
            tiles_filled=len(self._to_fill),
            tiles_checked=checked,
            bounds=None,
        )

    def _border_fill(self, start: Position) -> FillResult:
        """Fill only the border of a contiguous region.

        First finds the contiguous region, then fills only tiles
        that have at least one non-matching neighbor.
        """
        # First do contiguous fill to find all matching tiles
        contiguous_result = self._contiguous_fill(start)

        if not self._to_fill:
            return contiguous_result

        # Now filter to only border tiles
        directions = self._get_directions()
        border_tiles: set[Position] = set()

        for pos in self._to_fill:
            x, y, z = pos
            is_border = False

            for dx, dy in directions:
                nx, ny = x + dx, y + dy
                neighbor_pos = (nx, ny, z)

                if neighbor_pos not in self._to_fill:
                    is_border = True
                    break

            if is_border:
                border_tiles.add(pos)

        self._to_fill = border_tiles

        return FillResult(
            tiles_filled=len(self._to_fill),
            tiles_checked=contiguous_result.tiles_checked,
            bounds=contiguous_result.bounds,
        )

    def _get_directions(self) -> list[tuple[int, int]]:
        """Get direction offsets based on config."""
        if self._config.direction == FillDirection.EIGHT_WAY:
            return self.DIRECTIONS_4 + self.DIAGONALS
        return self.DIRECTIONS_4

    def _is_valid_position(self, x: int, y: int, z: int) -> bool:
        """Check if position is within map bounds."""
        return (
            0 <= x < self._map.width and 0 <= y < self._map.height and 0 <= z < 16  # Standard Z range
        )

    def _matches_reference(self, x: int, y: int, z: int) -> bool:
        """Check if tile at position matches the reference tile."""
        tile = self._map.get_tile(x, y, z)

        # Handle empty tiles
        if tile is None:
            if self._reference_tile is None:
                return self._config.fill_empty
            return False

        if self._reference_tile is None:
            return self._config.fill_empty

        # Check ground match
        if self._config.match_ground:
            ref_ground = self._reference_tile.ground
            tile_ground = tile.ground

            ref_id = ref_ground.id if ref_ground else 0
            tile_id = tile_ground.id if tile_ground else 0

            if ref_id != tile_id:
                return False

        # Check items match (if enabled)
        if self._config.match_items:
            ref_items = frozenset(item.id for item in self._reference_tile.items)
            tile_items = frozenset(item.id for item in tile.items)

            if ref_items != tile_items:
                return False

        # Check borders (if respect_borders enabled)
        if self._config.respect_borders:
            # Check if tile has auto-border items (usually have specific flags)
            for item in tile.items:
                if hasattr(item, "is_border") and item.is_border:
                    return False

        return True

    def _apply_brush_to_tiles(self) -> None:
        """Apply the brush to all collected tiles."""
        if self._brush is None:
            return

        for x, y, z in self._to_fill:
            try:
                # Get or create tile
                tile = self._map.get_tile(x, y, z)
                if tile is None:
                    tile = self._map.create_tile(x, y, z)

                # Apply brush (implementation depends on brush type)
                if hasattr(self._brush, "apply"):
                    self._brush.apply(tile, self._map)
                elif hasattr(self._brush, "draw"):
                    self._brush.draw(tile, self._map)

            except Exception as e:
                logger.warning("Failed to apply brush at (%d, %d, %d): %s", x, y, z, e)

    def preview_fill(
        self,
        start: Position,
        brush: BaseBrush,
        config: FillConfig | None = None,
    ) -> Iterator[Position]:
        """Generate preview of fill without applying changes.

        Yields positions that would be filled, for overlay rendering.

        Args:
            start: Starting position.
            brush: Brush that would be applied.
            config: Fill configuration.

        Yields:
            Positions that would be affected.
        """
        self._brush = brush
        self._config = config or FillConfig()
        self._visited.clear()
        self._to_fill.clear()

        # Run fill logic without applying
        original_brush = self._brush
        self._brush = None  # Prevent application

        x, y, z = start
        if not self._is_valid_position(x, y, z):
            return

        self._reference_tile = self._map.get_tile(x, y, z)
        self._contiguous_fill(start)

        self._brush = original_brush

        yield from self._to_fill


def create_fill_engine(game_map: GameMap) -> FloodFillEngine:
    """Factory function to create a FloodFillEngine.

    Args:
        game_map: The map instance.

    Returns:
        Configured FloodFillEngine.
    """
    return FloodFillEngine(game_map)
