"""Render Optimization Utilities.

Performance optimization for map rendering:
- Viewport culling
- Dirty rectangle tracking
- Batch rendering
- Level of detail (LOD)
"""

from __future__ import annotations

import logging
from collections.abc import Iterator
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class BoundingBox:
    """Axis-aligned bounding box."""

    x1: int
    y1: int
    x2: int
    y2: int

    @property
    def width(self) -> int:
        """Box width."""
        return self.x2 - self.x1

    @property
    def height(self) -> int:
        """Box height."""
        return self.y2 - self.y1

    def contains(self, x: int, y: int) -> bool:
        """Check if point is inside box."""
        return self.x1 <= x <= self.x2 and self.y1 <= y <= self.y2

    def intersects(self, other: BoundingBox) -> bool:
        """Check if boxes intersect."""
        return not (self.x2 < other.x1 or self.x1 > other.x2 or self.y2 < other.y1 or self.y1 > other.y2)

    def expand(self, margin: int) -> BoundingBox:
        """Return expanded box."""
        return BoundingBox(self.x1 - margin, self.y1 - margin, self.x2 + margin, self.y2 + margin)

    def union(self, other: BoundingBox) -> BoundingBox:
        """Return union of two boxes."""
        return BoundingBox(
            min(self.x1, other.x1), min(self.y1, other.y1), max(self.x2, other.x2), max(self.y2, other.y2)
        )


class ViewportCuller:
    """Performs viewport culling to skip off-screen tiles.

    Usage:
        culler = ViewportCuller()
        culler.set_viewport(100, 100, 800, 600)

        for tile in tiles:
            if culler.is_visible(tile.x, tile.y):
                render_tile(tile)
    """

    def __init__(self) -> None:
        self._viewport = BoundingBox(0, 0, 800, 600)
        self._tile_size = 32
        self._margin = 1  # Extra tiles around viewport

        # Cached tile bounds
        self._tile_x1 = 0
        self._tile_y1 = 0
        self._tile_x2 = 25
        self._tile_y2 = 19

    def set_viewport(self, x: int, y: int, width: int, height: int, tile_size: int = 32) -> None:
        """Set the viewport dimensions.

        Args:
            x, y: Viewport position (in pixels)
            width, height: Viewport size (in pixels)
            tile_size: Size of tiles in pixels
        """
        self._viewport = BoundingBox(x, y, x + width, y + height)
        self._tile_size = tile_size
        self._update_tile_bounds()

    def _update_tile_bounds(self) -> None:
        """Update cached tile bounds."""
        ts = self._tile_size
        m = self._margin

        self._tile_x1 = (self._viewport.x1 // ts) - m
        self._tile_y1 = (self._viewport.y1 // ts) - m
        self._tile_x2 = (self._viewport.x2 // ts) + m
        self._tile_y2 = (self._viewport.y2 // ts) + m

    def is_visible(self, tile_x: int, tile_y: int) -> bool:
        """Check if a tile is visible.

        Args:
            tile_x, tile_y: Tile position (in tile coordinates)

        Returns:
            True if tile is in viewport
        """
        return self._tile_x1 <= tile_x <= self._tile_x2 and self._tile_y1 <= tile_y <= self._tile_y2

    def get_visible_tiles(
        self, start_x: int = 0, start_y: int = 0, end_x: int = 65535, end_y: int = 65535
    ) -> Iterator[tuple[int, int]]:
        """Get iterator of visible tile positions.

        Args:
            start_x, start_y: Map start bounds
            end_x, end_y: Map end bounds

        Yields:
            (x, y) tuples of visible tiles
        """
        x1 = max(self._tile_x1, start_x)
        y1 = max(self._tile_y1, start_y)
        x2 = min(self._tile_x2, end_x)
        y2 = min(self._tile_y2, end_y)

        for y in range(y1, y2 + 1):
            for x in range(x1, x2 + 1):
                yield (x, y)

    @property
    def visible_tile_count(self) -> int:
        """Approximate number of visible tiles."""
        return (self._tile_x2 - self._tile_x1 + 1) * (self._tile_y2 - self._tile_y1 + 1)


class DirtyRectTracker:
    """Tracks dirty rectangles for partial redraws.

    Instead of redrawing the entire viewport, only redraw
    regions that have changed.

    Usage:
        tracker = DirtyRectTracker()

        # Mark changed area
        tracker.mark_dirty(100, 100, 50, 50)

        # Get regions to redraw
        for rect in tracker.get_dirty_rects():
            redraw_region(rect)

        tracker.clear()
    """

    def __init__(self, merge_threshold: int = 32) -> None:
        self._dirty_rects: list[BoundingBox] = []
        self._merge_threshold = merge_threshold
        self._full_redraw = False

    def mark_dirty(self, x: int, y: int, width: int, height: int) -> None:
        """Mark a rectangle as dirty.

        Args:
            x, y: Top-left position
            width, height: Rectangle size
        """
        rect = BoundingBox(x, y, x + width, y + height)
        self._dirty_rects.append(rect)
        self._merge_nearby()

    def mark_dirty_tile(self, tile_x: int, tile_y: int, tile_size: int = 32) -> None:
        """Mark a single tile as dirty.

        Args:
            tile_x, tile_y: Tile position
            tile_size: Size of tile in pixels
        """
        self.mark_dirty(tile_x * tile_size, tile_y * tile_size, tile_size, tile_size)

    def mark_full_redraw(self) -> None:
        """Mark entire viewport for redraw."""
        self._full_redraw = True
        self._dirty_rects.clear()

    def _merge_nearby(self) -> None:
        """Merge overlapping or nearby rectangles."""
        if len(self._dirty_rects) < 2:
            return

        merged = True
        while merged:
            merged = False
            new_rects = []
            skip = set()

            for i, r1 in enumerate(self._dirty_rects):
                if i in skip:
                    continue

                for j, r2 in enumerate(self._dirty_rects[i + 1 :], i + 1):
                    if j in skip:
                        continue

                    # Check if close enough to merge
                    expanded = r1.expand(self._merge_threshold)
                    if expanded.intersects(r2):
                        r1 = r1.union(r2)
                        skip.add(j)
                        merged = True

                new_rects.append(r1)

            self._dirty_rects = new_rects

    def get_dirty_rects(self) -> list[BoundingBox]:
        """Get list of dirty rectangles."""
        return self._dirty_rects.copy()

    def is_full_redraw(self) -> bool:
        """Check if full redraw is needed."""
        return self._full_redraw

    def clear(self) -> None:
        """Clear all dirty rectangles."""
        self._dirty_rects.clear()
        self._full_redraw = False

    @property
    def dirty_count(self) -> int:
        """Number of dirty rectangles."""
        return len(self._dirty_rects)


@dataclass
class LevelOfDetail:
    """Level of detail settings."""

    threshold: float  # Zoom threshold
    show_items: bool
    show_creatures: bool
    show_grid: bool
    show_names: bool


class LODManager:
    """Manages level of detail based on zoom level.

    At lower zoom levels (zoomed out), skip rendering
    details to improve performance.

    Usage:
        lod = LODManager()
        settings = lod.get_lod(0.25)  # 25% zoom

        if settings.show_items:
            render_items()
    """

    DEFAULT_LEVELS = [
        LevelOfDetail(2.0, True, True, True, True),  # 200%+ - show everything
        LevelOfDetail(1.0, True, True, True, True),  # 100-200% - show everything
        LevelOfDetail(0.5, True, True, False, True),  # 50-100% - hide grid
        LevelOfDetail(0.25, True, False, False, False),  # 25-50% - hide creatures, names
        LevelOfDetail(0.1, False, False, False, False),  # <25% - hide items
    ]

    def __init__(self, levels: list[LevelOfDetail] | None = None) -> None:
        self._levels = levels or self.DEFAULT_LEVELS
        # Sort by threshold descending
        self._levels.sort(key=lambda x: x.threshold, reverse=True)

    def get_lod(self, zoom: float) -> LevelOfDetail:
        """Get LOD settings for zoom level.

        Args:
            zoom: Current zoom (1.0 = 100%)

        Returns:
            LevelOfDetail settings
        """
        for level in self._levels:
            if zoom >= level.threshold:
                return level

        # Return minimum LOD
        return self._levels[-1] if self._levels else LevelOfDetail(0, True, True, True, True)

    def should_render_items(self, zoom: float) -> bool:
        """Check if items should be rendered at zoom level."""
        return self.get_lod(zoom).show_items

    def should_render_creatures(self, zoom: float) -> bool:
        """Check if creatures should be rendered."""
        return self.get_lod(zoom).show_creatures

    def should_render_grid(self, zoom: float) -> bool:
        """Check if grid should be rendered."""
        return self.get_lod(zoom).show_grid


class BatchRenderer:
    """Batches render calls for efficiency.

    Groups similar render operations together
    to minimize state changes and draw calls.
    """

    def __init__(self) -> None:
        self._ground_batch: list[tuple[int, int, int]] = []  # (x, y, sprite_id)
        self._item_batch: list[tuple[int, int, int]] = []
        self._creature_batch: list[tuple[int, int, int]] = []

    def add_ground(self, x: int, y: int, sprite_id: int) -> None:
        """Add ground to batch."""
        self._ground_batch.append((x, y, sprite_id))

    def add_item(self, x: int, y: int, sprite_id: int) -> None:
        """Add item to batch."""
        self._item_batch.append((x, y, sprite_id))

    def add_creature(self, x: int, y: int, sprite_id: int) -> None:
        """Add creature to batch."""
        self._creature_batch.append((x, y, sprite_id))

    def flush(self) -> tuple[list, list, list]:
        """Flush and return all batches.

        Returns:
            Tuple of (ground, items, creatures) batches
        """
        result = (self._ground_batch.copy(), self._item_batch.copy(), self._creature_batch.copy())
        self.clear()
        return result

    def clear(self) -> None:
        """Clear all batches."""
        self._ground_batch.clear()
        self._item_batch.clear()
        self._creature_batch.clear()

    @property
    def total_count(self) -> int:
        """Total items in all batches."""
        return len(self._ground_batch) + len(self._item_batch) + len(self._creature_batch)


class RenderOptimizer:
    """Combines all optimization techniques.

    Provides a unified interface for all render optimizations.

    Usage:
        optimizer = RenderOptimizer()
        optimizer.set_viewport(0, 0, 800, 600)
        optimizer.set_zoom(0.5)

        for tile in tiles:
            if optimizer.should_render(tile.x, tile.y):
                optimizer.batch.add_ground(tile.x, tile.y, tile.ground_id)

                if optimizer.should_render_items():
                    for item in tile.items:
                        optimizer.batch.add_item(tile.x, tile.y, item.id)
    """

    def __init__(self) -> None:
        self.culler = ViewportCuller()
        self.dirty_tracker = DirtyRectTracker()
        self.lod_manager = LODManager()
        self.batch = BatchRenderer()

        self._zoom = 1.0
        self._tile_size = 32

    def set_viewport(self, x: int, y: int, width: int, height: int, tile_size: int = 32) -> None:
        """Set viewport for culling."""
        self._tile_size = tile_size
        self.culler.set_viewport(x, y, width, height, tile_size)

    def set_zoom(self, zoom: float) -> None:
        """Set current zoom level."""
        self._zoom = zoom

    def should_render(self, tile_x: int, tile_y: int) -> bool:
        """Check if tile should be rendered."""
        return self.culler.is_visible(tile_x, tile_y)

    def should_render_items(self) -> bool:
        """Check if items should be rendered at current LOD."""
        return self.lod_manager.should_render_items(self._zoom)

    def should_render_creatures(self) -> bool:
        """Check if creatures should be rendered."""
        return self.lod_manager.should_render_creatures(self._zoom)

    def should_render_grid(self) -> bool:
        """Check if grid should be rendered."""
        return self.lod_manager.should_render_grid(self._zoom)

    def mark_dirty(self, tile_x: int, tile_y: int) -> None:
        """Mark tile as needing redraw."""
        self.dirty_tracker.mark_dirty_tile(tile_x, tile_y, self._tile_size)

    def get_visible_tiles(self) -> Iterator[tuple[int, int]]:
        """Get iterator of visible tiles."""
        return self.culler.get_visible_tiles()

    def begin_frame(self) -> None:
        """Prepare for new frame."""
        self.batch.clear()

    def end_frame(self) -> tuple[list, list, list]:
        """End frame and get render batches."""
        return self.batch.flush()
