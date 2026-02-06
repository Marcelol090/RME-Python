"""Map Region/Chunk System.

This module provides a chunk-based organization of map data for:
- Efficient viewport culling
- Incremental loading/streaming
- Region-based operations
- Memory optimization

Reference:
    - C++ Legacy: map_region.cpp
    - Minecraft chunk system
    - Quadtree spatial partitioning

Features:
    - MapRegion: A rectangular chunk of the map
    - RegionManager: Manages regions and queries
    - Spatial indexing for fast lookups
    - Dirty tracking for incremental updates

Layer: core (no UI dependencies)
"""

from __future__ import annotations

import logging
import math
import weakref
from collections.abc import Callable, Iterator
from dataclasses import dataclass
from enum import Enum, auto
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap
    from py_rme_canary.core.data.tile import Tile

logger = logging.getLogger(__name__)


# Position type alias
Position = tuple[int, int, int]  # (x, y, z)
RegionCoord = tuple[int, int, int]  # (rx, ry, z) - region coordinates


class RegionState(Enum):
    """State of a region."""

    UNLOADED = auto()  # Region not loaded
    LOADING = auto()  # Currently loading
    LOADED = auto()  # Fully loaded
    DIRTY = auto()  # Has unsaved changes
    MODIFIED = auto()  # Modified since last render


@dataclass(slots=True)
class RegionBounds:
    """Bounds of a region in tile coordinates.

    Attributes:
        min_x: Minimum X coordinate.
        min_y: Minimum Y coordinate.
        max_x: Maximum X coordinate (inclusive).
        max_y: Maximum Y coordinate (inclusive).
        z: Floor level.
    """

    min_x: int
    min_y: int
    max_x: int
    max_y: int
    z: int

    @property
    def width(self) -> int:
        return self.max_x - self.min_x + 1

    @property
    def height(self) -> int:
        return self.max_y - self.min_y + 1

    @property
    def tile_count(self) -> int:
        return self.width * self.height

    def contains(self, x: int, y: int) -> bool:
        """Check if position is within bounds."""
        return self.min_x <= x <= self.max_x and self.min_y <= y <= self.max_y

    def intersects(self, other: RegionBounds) -> bool:
        """Check if this region intersects another."""
        if self.z != other.z:
            return False
        return not (
            self.max_x < other.min_x or self.min_x > other.max_x or self.max_y < other.min_y or self.min_y > other.max_y
        )

    def intersection(self, other: RegionBounds) -> RegionBounds | None:
        """Get intersection with another region."""
        if not self.intersects(other):
            return None
        return RegionBounds(
            min_x=max(self.min_x, other.min_x),
            min_y=max(self.min_y, other.min_y),
            max_x=min(self.max_x, other.max_x),
            max_y=min(self.max_y, other.max_y),
            z=self.z,
        )


@dataclass
class RegionStats:
    """Statistics about a region.

    Attributes:
        tile_count: Number of tiles in region.
        item_count: Total items in region.
        ground_count: Tiles with ground.
        empty_count: Empty tiles.
        house_tiles: Tiles belonging to houses.
        spawn_count: Spawn points in region.
    """

    tile_count: int = 0
    item_count: int = 0
    ground_count: int = 0
    empty_count: int = 0
    house_tiles: int = 0
    spawn_count: int = 0

    def merge(self, other: RegionStats) -> None:
        """Merge another stats into this one."""
        self.tile_count += other.tile_count
        self.item_count += other.item_count
        self.ground_count += other.ground_count
        self.empty_count += other.empty_count
        self.house_tiles += other.house_tiles
        self.spawn_count += other.spawn_count


class MapRegion:
    """A rectangular chunk of the map.

    Regions provide:
    - Spatial grouping of tiles
    - Dirty tracking for rendering
    - Stats caching
    - Memory management hints

    Example:
        region = MapRegion(
            coord=(0, 0, 7),  # Region at origin, floor 7
            bounds=RegionBounds(0, 0, 63, 63, 7),
            game_map=map_instance
        )

        # Check if modified
        if region.is_dirty:
            renderer.update_region(region)
            region.mark_clean()
    """

    __slots__ = (
        "_coord",
        "_bounds",
        "_map_ref",
        "_state",
        "_dirty_tiles",
        "_stats",
        "_last_access",
        "_version",
    )

    def __init__(
        self,
        coord: RegionCoord,
        bounds: RegionBounds,
        game_map: GameMap,
    ) -> None:
        """Initialize a map region.

        Args:
            coord: Region coordinates (rx, ry, z).
            bounds: Tile bounds.
            game_map: Parent map (stored as weak reference).
        """
        self._coord = coord
        self._bounds = bounds
        self._map_ref = weakref.ref(game_map)
        self._state = RegionState.LOADED
        self._dirty_tiles: set[Position] = set()
        self._stats: RegionStats | None = None
        self._last_access = 0.0
        self._version = 0

    @property
    def coord(self) -> RegionCoord:
        """Region coordinates."""
        return self._coord

    @property
    def bounds(self) -> RegionBounds:
        """Region bounds."""
        return self._bounds

    @property
    def state(self) -> RegionState:
        """Current region state."""
        return self._state

    @property
    def is_dirty(self) -> bool:
        """Check if region has uncommitted changes."""
        return self._state in (RegionState.DIRTY, RegionState.MODIFIED) or len(self._dirty_tiles) > 0

    @property
    def version(self) -> int:
        """Version counter (increments on changes)."""
        return self._version

    def get_map(self) -> GameMap | None:
        """Get the parent map (may be None if collected)."""
        return self._map_ref()

    def mark_dirty(self, x: int, y: int, z: int) -> None:
        """Mark a tile as dirty.

        Args:
            x: Tile X coordinate.
            y: Tile Y coordinate.
            z: Floor level.
        """
        if self._bounds.contains(x, y) and z == self._bounds.z:
            self._dirty_tiles.add((x, y, z))
            self._state = RegionState.DIRTY
            self._version += 1
            self._stats = None  # Invalidate cache

    def mark_clean(self) -> None:
        """Mark region as clean (no pending changes)."""
        self._dirty_tiles.clear()
        self._state = RegionState.LOADED

    def get_dirty_tiles(self) -> set[Position]:
        """Get set of dirty tile positions."""
        return self._dirty_tiles.copy()

    def get_stats(self, force_recalc: bool = False) -> RegionStats:
        """Get statistics about this region.

        Args:
            force_recalc: Force recalculation of stats.

        Returns:
            RegionStats for this region.
        """
        if self._stats is not None and not force_recalc:
            return self._stats

        game_map = self.get_map()
        if game_map is None:
            return RegionStats()

        stats = RegionStats()
        z = self._bounds.z

        for y in range(self._bounds.min_y, self._bounds.max_y + 1):
            for x in range(self._bounds.min_x, self._bounds.max_x + 1):
                tile = game_map.get_tile(x, y, z)

                if tile is None:
                    stats.empty_count += 1
                    continue

                stats.tile_count += 1

                if tile.ground:
                    stats.ground_count += 1

                stats.item_count += len(list(tile.items))

                house_id = getattr(tile, "house_id", 0)
                if house_id:
                    stats.house_tiles += 1

                # Check for spawns
                for item in tile.items:
                    if hasattr(item, "spawn") and item.spawn:
                        stats.spawn_count += 1

        self._stats = stats
        return stats

    def iter_tiles(self) -> Iterator[Tile]:
        """Iterate over all tiles in this region.

        Yields:
            Tile objects (non-empty only).
        """
        game_map = self.get_map()
        if game_map is None:
            return

        z = self._bounds.z
        for y in range(self._bounds.min_y, self._bounds.max_y + 1):
            for x in range(self._bounds.min_x, self._bounds.max_x + 1):
                tile = game_map.get_tile(x, y, z)
                if tile is not None:
                    yield tile

    def iter_positions(self) -> Iterator[Position]:
        """Iterate over all positions in this region.

        Yields:
            Position tuples (x, y, z).
        """
        z = self._bounds.z
        for y in range(self._bounds.min_y, self._bounds.max_y + 1):
            for x in range(self._bounds.min_x, self._bounds.max_x + 1):
                yield (x, y, z)

    def contains(self, x: int, y: int, z: int) -> bool:
        """Check if position is within this region."""
        return z == self._bounds.z and self._bounds.contains(x, y)

    def __repr__(self) -> str:
        return f"MapRegion({self._coord}, {self._bounds.width}x{self._bounds.height})"


class RegionManager:
    """Manager for map regions.

    Provides:
    - Region creation and lookup
    - Viewport queries
    - Dirty region tracking
    - Memory management

    Example:
        manager = RegionManager(game_map, chunk_size=64)

        # Get region at position
        region = manager.get_region_at(100, 100, 7)

        # Get visible regions for a viewport
        visible = manager.get_regions_in_view(
            viewport_x=50, viewport_y=50,
            viewport_width=800, viewport_height=600,
            floor=7
        )

        # Mark tile as dirty
        manager.mark_dirty(100, 100, 7)

        # Get all dirty regions
        dirty = manager.get_dirty_regions()
    """

    def __init__(
        self,
        game_map: GameMap,
        chunk_size: int = 64,
    ) -> None:
        """Initialize the region manager.

        Args:
            game_map: The map to manage.
            chunk_size: Size of each region in tiles.
        """
        self._map = game_map
        self._chunk_size = chunk_size
        self._regions: dict[RegionCoord, MapRegion] = {}
        self._dirty_regions: set[RegionCoord] = set()

        # Calculate grid dimensions
        self._grid_width = math.ceil(game_map.width / chunk_size)
        self._grid_height = math.ceil(game_map.height / chunk_size)

        # On-change callback
        self._on_region_dirty: Callable[[MapRegion], None] | None = None

    @property
    def chunk_size(self) -> int:
        """Size of each region in tiles."""
        return self._chunk_size

    @property
    def region_count(self) -> int:
        """Number of loaded regions."""
        return len(self._regions)

    def set_dirty_callback(self, callback: Callable[[MapRegion], None]) -> None:
        """Set callback for when a region becomes dirty."""
        self._on_region_dirty = callback

    def pos_to_region_coord(self, x: int, y: int, z: int) -> RegionCoord:
        """Convert tile position to region coordinates.

        Args:
            x: Tile X.
            y: Tile Y.
            z: Floor level.

        Returns:
            Region coordinates (rx, ry, z).
        """
        rx = x // self._chunk_size
        ry = y // self._chunk_size
        return (rx, ry, z)

    def get_region_at(self, x: int, y: int, z: int) -> MapRegion:
        """Get or create region containing a position.

        Args:
            x: Tile X.
            y: Tile Y.
            z: Floor level.

        Returns:
            MapRegion containing the position.
        """
        coord = self.pos_to_region_coord(x, y, z)
        return self.get_region(coord)

    def get_region(self, coord: RegionCoord) -> MapRegion:
        """Get or create a region by coordinates.

        Args:
            coord: Region coordinates (rx, ry, z).

        Returns:
            MapRegion instance.
        """
        if coord in self._regions:
            return self._regions[coord]

        # Create new region
        rx, ry, z = coord
        bounds = RegionBounds(
            min_x=rx * self._chunk_size,
            min_y=ry * self._chunk_size,
            max_x=min((rx + 1) * self._chunk_size - 1, self._map.width - 1),
            max_y=min((ry + 1) * self._chunk_size - 1, self._map.height - 1),
            z=z,
        )

        region = MapRegion(coord, bounds, self._map)
        self._regions[coord] = region
        return region

    def mark_dirty(self, x: int, y: int, z: int) -> None:
        """Mark a tile as dirty.

        Args:
            x: Tile X.
            y: Tile Y.
            z: Floor level.
        """
        region = self.get_region_at(x, y, z)
        region.mark_dirty(x, y, z)
        self._dirty_regions.add(region.coord)

        if self._on_region_dirty:
            self._on_region_dirty(region)

    def get_dirty_regions(self) -> list[MapRegion]:
        """Get all regions with pending changes.

        Returns:
            List of dirty MapRegion instances.
        """
        return [self._regions[coord] for coord in self._dirty_regions if coord in self._regions]

    def clear_dirty(self) -> None:
        """Clear all dirty flags."""
        for coord in self._dirty_regions:
            if coord in self._regions:
                self._regions[coord].mark_clean()
        self._dirty_regions.clear()

    def get_regions_in_view(
        self,
        viewport_x: int,
        viewport_y: int,
        viewport_width: int,
        viewport_height: int,
        floor: int,
        padding: int = 0,
    ) -> list[MapRegion]:
        """Get all regions visible in a viewport.

        Args:
            viewport_x: Viewport left edge in tiles.
            viewport_y: Viewport top edge in tiles.
            viewport_width: Viewport width in tiles.
            viewport_height: Viewport height in tiles.
            floor: Floor level.
            padding: Extra regions to include around viewport.

        Returns:
            List of visible MapRegion instances.
        """
        # Calculate region range
        min_rx = max(0, (viewport_x // self._chunk_size) - padding)
        min_ry = max(0, (viewport_y // self._chunk_size) - padding)
        max_rx = min(self._grid_width, ((viewport_x + viewport_width) // self._chunk_size) + padding + 1)
        max_ry = min(self._grid_height, ((viewport_y + viewport_height) // self._chunk_size) + padding + 1)

        regions: list[MapRegion] = []
        for ry in range(min_ry, max_ry):
            for rx in range(min_rx, max_rx):
                coord = (rx, ry, floor)
                regions.append(self.get_region(coord))

        return regions

    def get_regions_in_bounds(
        self,
        bounds: RegionBounds,
    ) -> list[MapRegion]:
        """Get all regions intersecting bounds.

        Args:
            bounds: Area bounds.

        Returns:
            List of intersecting MapRegion instances.
        """
        min_rx = bounds.min_x // self._chunk_size
        min_ry = bounds.min_y // self._chunk_size
        max_rx = bounds.max_x // self._chunk_size
        max_ry = bounds.max_y // self._chunk_size

        regions: list[MapRegion] = []
        for ry in range(min_ry, max_ry + 1):
            for rx in range(min_rx, max_rx + 1):
                coord = (rx, ry, bounds.z)
                regions.append(self.get_region(coord))

        return regions

    def get_regions_on_floor(self, floor: int) -> list[MapRegion]:
        """Get all regions on a specific floor.

        Args:
            floor: Floor level.

        Returns:
            List of MapRegion instances.
        """
        return [region for coord, region in self._regions.items() if coord[2] == floor]

    def get_all_regions(self) -> list[MapRegion]:
        """Get all loaded regions."""
        return list(self._regions.values())

    def iter_regions(self) -> Iterator[MapRegion]:
        """Iterate over all loaded regions."""
        yield from self._regions.values()

    def unload_region(self, coord: RegionCoord) -> bool:
        """Unload a region from memory.

        Args:
            coord: Region coordinates.

        Returns:
            True if unloaded, False if not found.
        """
        if coord not in self._regions:
            return False

        # Don't unload dirty regions
        region = self._regions[coord]
        if region.is_dirty:
            logger.warning("Cannot unload dirty region: %s", coord)
            return False

        del self._regions[coord]
        self._dirty_regions.discard(coord)
        return True

    def get_global_stats(self) -> RegionStats:
        """Get combined statistics for all loaded regions.

        Returns:
            Merged RegionStats.
        """
        combined = RegionStats()
        for region in self._regions.values():
            combined.merge(region.get_stats())
        return combined

    def preload_floor(self, floor: int) -> int:
        """Preload all regions for a floor.

        Args:
            floor: Floor level.

        Returns:
            Number of regions loaded.
        """
        count = 0
        for ry in range(self._grid_height):
            for rx in range(self._grid_width):
                coord = (rx, ry, floor)
                if coord not in self._regions:
                    self.get_region(coord)
                    count += 1

        logger.debug("Preloaded %d regions for floor %d", count, floor)
        return count

    def clear(self) -> None:
        """Clear all regions."""
        self._regions.clear()
        self._dirty_regions.clear()


def create_region_manager(
    game_map: GameMap,
    chunk_size: int = 64,
) -> RegionManager:
    """Factory function to create a RegionManager.

    Args:
        game_map: Map to manage.
        chunk_size: Region size in tiles.

    Returns:
        Configured RegionManager.
    """
    return RegionManager(game_map, chunk_size)
