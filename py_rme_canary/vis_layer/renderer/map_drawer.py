"""Map drawer: coordinates rendering based on DrawingOptions.

This module provides the MapDrawer class that mirrors the C++ MapDrawer from
source/map_drawer.cpp. It coordinates what gets drawn based on DrawingOptions.

Architecture Notes:
-------------------
- MapDrawer holds reference to DrawingOptions (logic_layer, Qt-free)
- MapDrawer provides methods matching C++ API: Draw(), DrawMap(), DrawGrid(), etc.
- Actual pixel output is delegated to a backend (QPainter, OpenGL, etc.)
- The canvas widget creates a MapDrawer and calls draw() on paint events
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional, Protocol

from py_rme_canary.logic_layer.drawing_options import DrawingOptions

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap


class RenderBackend(Protocol):
    """Protocol for render backends (QPainter, OpenGL, etc.)."""

    def clear(self, r: int, g: int, b: int, a: int = 255) -> None:
        """Clear the viewport with a color."""
        ...

    def draw_tile_color(self, x: int, y: int, size: int, r: int, g: int, b: int, a: int = 255) -> None:
        """Fill a tile rectangle with a solid color."""
        ...

    def draw_tile_sprite(self, x: int, y: int, size: int, sprite_id: int) -> None:
        """Draw a sprite at a tile position."""
        ...

    def draw_grid_line(self, x0: int, y0: int, x1: int, y1: int, r: int, g: int, b: int, a: int = 255) -> None:
        """Draw a grid line."""
        ...

    def draw_grid_rect(self, x: int, y: int, w: int, h: int, r: int, g: int, b: int, a: int = 255) -> None:
        """Draw a grid rectangle outline."""
        ...

    def draw_selection_rect(self, x: int, y: int, w: int, h: int, r: int, g: int, b: int, a: int = 255) -> None:
        """Draw a selection highlight rectangle."""
        ...

    def draw_indicator_icon(self, x: int, y: int, indicator_type: str, size: int) -> None:
        """Draw an indicator icon (hook, pickupable, etc.)."""
        ...

    def draw_text(self, x: int, y: int, text: str, r: int, g: int, b: int, a: int = 255) -> None:
        """Draw text at a position."""
        ...

    def draw_shade_overlay(self, x: int, y: int, w: int, h: int, alpha: int) -> None:
        """Draw shade overlay for current floor."""
        ...


@dataclass(slots=True)
class Viewport:
    """Viewport state for rendering."""
    origin_x: int = 0
    origin_y: int = 0
    z: int = 7
    tile_px: int = 32
    width_px: int = 800
    height_px: int = 600

    @property
    def tiles_wide(self) -> int:
        """Number of tiles visible horizontally."""
        return max(1, self.width_px // self.tile_px) + 1

    @property
    def tiles_high(self) -> int:
        """Number of tiles visible vertically."""
        return max(1, self.height_px // self.tile_px) + 1


@dataclass(slots=True)
class MapDrawer:
    """Coordinates map rendering based on DrawingOptions.

    This class mirrors the C++ MapDrawer from source/map_drawer.h/cpp.
    It decides what to draw based on the current DrawingOptions state
    and delegates actual drawing to a RenderBackend.

    The class is Qt-free; the RenderBackend implementation handles
    platform-specific rendering (QPainter, OpenGL, etc.).
    """

    options: DrawingOptions
    game_map: Optional["GameMap"] = None
    viewport: Viewport = field(default_factory=Viewport)

    # Internal state (mirrors C++ MapDrawer members)
    _zoom: float = 1.0
    _floor: int = 7
    _mouse_map_x: int = 0
    _mouse_map_y: int = 0
    _dragging: bool = False
    _dragging_draw: bool = False

    # Computed bounds (set by setup_vars)
    _start_x: int = 0
    _start_y: int = 0
    _start_z: int = 0
    _end_x: int = 0
    _end_y: int = 0
    _end_z: int = 0
    _view_scroll_x: int = 0
    _view_scroll_y: int = 0

    def setup_vars(self) -> None:
        """Set up rendering variables from viewport state.

        Mirrors C++ MapDrawer::SetupVars().
        """
        self._zoom = 32.0 / self.viewport.tile_px if self.viewport.tile_px > 0 else 1.0
        self._floor = self.viewport.z

        # View bounds
        self._view_scroll_x = self.viewport.origin_x * 32  # Tile units to pixels
        self._view_scroll_y = self.viewport.origin_y * 32

        self._start_x = self.viewport.origin_x
        self._start_y = self.viewport.origin_y
        self._end_x = self._start_x + self.viewport.tiles_wide
        self._end_y = self._start_y + self.viewport.tiles_high

        # Floor range based on show_all_floors
        if self.options.show_all_floors:
            if self._floor < 8:
                self._start_z = 7  # Ground layer
            else:
                self._start_z = min(15, self._floor + 2)
        else:
            self._start_z = self._floor

        self._end_z = self._floor

    def should_draw_grid(self) -> bool:
        """Check if grid should be drawn.

        Mirrors C++ logic: show_grid && zoom <= 10.
        """
        return bool(self.options.show_grid) and self._zoom <= 10.0

    def should_draw_items(self) -> bool:
        """Check if items should be drawn (not zoomed out too far)."""
        if not self.options.show_items:
            return False
        if self.options.hide_items_when_zoomed and self._zoom > 10.0:
            return False
        return True

    def should_draw_creatures(self) -> bool:
        """Check if creatures (monsters/NPCs) should be drawn."""
        return self.options.show_monsters or self.options.show_npcs

    def should_draw_spawns(self) -> bool:
        """Check if spawn indicators should be drawn."""
        return self.options.show_spawns_monster or self.options.show_spawns_npc

    def should_draw_indicators(self) -> bool:
        """Check if tile indicators (hooks, pickupables, etc.) should be drawn."""
        return self.options.is_tile_indicators()

    def should_draw_shade(self) -> bool:
        """Check if shade overlay should be drawn."""
        return self.options.show_shade and self._start_z != self._end_z

    def should_draw_tooltips(self) -> bool:
        """Check if tooltips should be drawn."""
        return self.options.is_tooltips()

    def should_draw_lights(self) -> bool:
        """Check if light effects should be drawn."""
        return self.options.show_lights

    def should_draw_ingame_box(self) -> bool:
        """Check if client viewport box should be drawn."""
        return self.options.show_ingame_box

    def is_minimap_mode(self) -> bool:
        """Check if we're in minimap/colors-only mode."""
        return self.options.is_only_colors()

    def get_tile_bounds(self) -> tuple[int, int, int, int]:
        """Return (start_x, start_y, end_x, end_y) tile bounds for iteration."""
        return self._start_x, self._start_y, self._end_x, self._end_y

    def get_floor_range(self) -> tuple[int, int]:
        """Return (start_z, end_z) floor range for iteration."""
        return self._start_z, self._end_z

    def draw(self, backend: RenderBackend) -> None:
        """Main draw method - renders the complete frame.

        Mirrors C++ MapDrawer::Draw().

        Parameters
        ----------
        backend : RenderBackend
            The rendering backend to use for output.
        """
        self.setup_vars()

        # Background
        self._draw_background(backend)

        # Map tiles
        self._draw_map(backend)

        # Lights (if enabled)
        if self.should_draw_lights():
            self._draw_lights(backend)

        # Shade overlay (for floor differentiation)
        if self.should_draw_shade():
            self._draw_shade(backend)

        # Grid overlay
        if self.should_draw_grid():
            self._draw_grid(backend)

        # Client viewport box
        if self.should_draw_ingame_box():
            self._draw_ingame_box(backend)

        # Tooltips
        if self.should_draw_tooltips():
            self._draw_tooltips(backend)

    def _draw_background(self, backend: RenderBackend) -> None:
        """Draw the background color.

        Mirrors C++ MapDrawer::DrawBackground().
        """
        backend.clear(0, 0, 0)  # Black background

    def _draw_map(self, backend: RenderBackend) -> None:
        """Draw all visible map tiles.

        Mirrors C++ MapDrawer::DrawMap().
        """
        if self.game_map is None:
            return

        tile_size = self.viewport.tile_px
        for z in range(self._start_z, self._end_z - 1, -1):
            for y in range(self._start_y, self._end_y):
                py = (y - self._start_y) * tile_size
                for x in range(self._start_x, self._end_x):
                    px = (x - self._start_x) * tile_size
                    self._draw_tile(backend, x, y, z, px, py, tile_size)

    def _draw_tile(
        self,
        backend: RenderBackend,
        map_x: int,
        map_y: int,
        map_z: int,
        screen_x: int,
        screen_y: int,
        size: int,
    ) -> None:
        """Draw a single tile at the given position."""
        if self.game_map is None:
            # Empty tile placeholder
            backend.draw_tile_color(screen_x, screen_y, size, 43, 43, 43)
            return

        tile = self.game_map.get_tile(map_x, map_y, map_z)
        if tile is None:
            # Empty tile
            backend.draw_tile_color(screen_x, screen_y, size, 43, 43, 43)
            return

        # Only show modified check
        if self.options.show_only_modified and not getattr(tile, "modified", False):
            backend.draw_tile_color(screen_x, screen_y, size, 43, 43, 43)
            return

        # Minimap mode - just show colors
        if self.is_minimap_mode():
            # Get top item color
            color = self._get_tile_color(tile)
            backend.draw_tile_color(screen_x, screen_y, size, *color)
            return

        # Normal rendering - ground then items
        if tile.ground is not None and self.options.show_items:
            backend.draw_tile_sprite(screen_x, screen_y, size, tile.ground.id)

        if self.should_draw_items() and tile.items:
            for item in tile.items:
                backend.draw_tile_sprite(screen_x, screen_y, size, item.id)

    def _get_tile_color(self, tile) -> tuple[int, int, int, int]:
        """Get the display color for a tile (for minimap mode)."""
        # Hash-based color to match qcolor_from_id (Qt-free).
        if tile.items:
            top_id = tile.items[-1].id
        elif tile.ground is not None:
            top_id = tile.ground.id
        else:
            return (43, 43, 43, 255)

        v = int(top_id) & 0xFFFFFFFF
        r = (v * 2654435761) & 0xFF
        g = (v * 2246822519) & 0xFF
        b = (v * 3266489917) & 0xFF

        def clamp(c: int) -> int:
            return 48 + (int(c) % 160)

        r = clamp(int(r))
        g = clamp(int(g))
        b = clamp(int(b))
        return (r, g, b, 255)

    def _draw_grid(self, backend: RenderBackend) -> None:
        """Draw the tile grid.

        Mirrors C++ MapDrawer::DrawGrid().
        """
        tile_size = self.viewport.tile_px
        grid_color = (58, 58, 58, 255)  # Dark gray

        for y in range(self._start_y, self._end_y + 1):
            py = (y - self._start_y) * tile_size
            for x in range(self._start_x, self._end_x + 1):
                px = (x - self._start_x) * tile_size
                backend.draw_grid_rect(px, py, tile_size, tile_size, *grid_color)

    def _draw_shade(self, backend: RenderBackend) -> None:
        """Draw shade overlay for current floor.

        Mirrors C++ MapDrawer::DrawShade().
        """
        width = self.viewport.width_px
        height = self.viewport.height_px
        backend.draw_shade_overlay(0, 0, width, height, 128)

    def _draw_lights(self, backend: RenderBackend) -> None:
        """Draw light effects.

        Mirrors C++ MapDrawer::DrawLight().
        """
        # Light drawing is complex - placeholder for now
        pass

    def _draw_ingame_box(self, backend: RenderBackend) -> None:
        """Draw the client viewport indicator box.

        Mirrors C++ MapDrawer::DrawIngameBox().
        """
        # Standard Tibia client viewport is 15x11 tiles
        client_tiles_x = 15
        client_tiles_y = 11
        tile_size = self.viewport.tile_px

        # Center on viewport
        center_x = self.viewport.width_px // 2
        center_y = self.viewport.height_px // 2

        box_w = client_tiles_x * tile_size
        box_h = client_tiles_y * tile_size
        box_x = center_x - box_w // 2
        box_y = center_y - box_h // 2

        backend.draw_selection_rect(box_x, box_y, box_w, box_h, 255, 255, 0, 200)

    def _draw_tooltips(self, backend: RenderBackend) -> None:
        """Draw tooltips for items under cursor.

        Mirrors C++ MapDrawer::DrawTooltips().
        """
        # Tooltip drawing requires cursor position - placeholder
        pass


# Factory function for default drawer
def create_map_drawer(game_map: Optional["GameMap"] = None) -> MapDrawer:
    """Create a MapDrawer with default DrawingOptions."""
    options = DrawingOptions()
    return MapDrawer(options=options, game_map=game_map)
