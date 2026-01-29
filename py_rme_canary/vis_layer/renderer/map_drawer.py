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

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Optional, Protocol

from py_rme_canary.logic_layer.drawing_options import DrawingOptions
from py_rme_canary.logic_layer.settings.light_settings import LightMode

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap
    from py_rme_canary.core.data.tile import Tile


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
    _hover_tile: tuple[int, int, int] | None = None
    _hover_stack: list[int] = field(default_factory=list)
    _highlight_tile: tuple[int, int, int] | None = None
    _highlight_until: float = 0.0
    _live_cursors: list[dict[str, object]] = field(default_factory=list)
    _light_cache: list[tuple[int, int, int]] = field(default_factory=list)

    def set_hover_tile(self, x: int, y: int, z: int, stack: list[int]) -> None:
        """Set hover tile and visible stack for tooltip rendering."""
        self._hover_tile = (int(x), int(y), int(z))
        self._hover_stack = list(stack)

    def set_highlight_tile(self, x: int, y: int, z: int, *, duration_ms: int = 1200) -> None:
        """Highlight a tile for a short duration."""
        self._highlight_tile = (int(x), int(y), int(z))
        self._highlight_until = time.monotonic() + (max(100, int(duration_ms)) / 1000.0)

    def set_live_cursors(self, cursors: list[dict[str, object]]) -> None:
        """Set live cursor overlay list."""
        self._live_cursors = list(cursors)

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

        # Go-to highlight
        self._draw_highlight(backend)

        # Live cursors overlay
        self._draw_live_cursors(backend)

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

        self._light_cache.clear()
        collect_lights = False
        if self.should_draw_lights():
            settings = self.options.light_settings
            if settings.enabled and settings.mode == LightMode.FULL:
                collect_lights = True

        tile_size = self.viewport.tile_px
        for z in range(self._start_z, self._end_z - 1, -1):
            for y in range(self._start_y, self._end_y):
                py = (y - self._start_y) * tile_size
                for x in range(self._start_x, self._end_x):
                    px = (x - self._start_x) * tile_size

                    tile = self.game_map.get_tile(x, y, z)
                    self._draw_tile(backend, x, y, z, px, py, tile_size, tile=tile)

                    if collect_lights and tile is not None:
                        strength = self._tile_light_strength(tile)
                        if strength > 0:
                            self._light_cache.append((x, y, strength))

    def _draw_tile(
        self,
        backend: RenderBackend,
        map_x: int,
        map_y: int,
        map_z: int,
        screen_x: int,
        screen_y: int,
        size: int,
        tile: Optional["Tile"] = None,
    ) -> None:
        """Draw a single tile at the given position."""
        if self.game_map is None:
            # Empty tile placeholder
            backend.draw_tile_color(screen_x, screen_y, size, 43, 43, 43)
            return

        if tile is None:
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

        # Spawn/creature indicators (legacy parity: render markers when toggled).
        if (self.options.show_spawns_monster or self.options.show_monsters) and tile.spawn_monster is not None:
            self._draw_spawn_indicator(backend, screen_x, screen_y, size, kind="spawn_monster")
        if (self.options.show_spawns_npc or self.options.show_npcs) and tile.spawn_npc is not None:
            self._draw_spawn_indicator(backend, screen_x, screen_y, size, kind="spawn_npc")

        # Creature name overlays (monsters/NPCs).
        if not self.is_minimap_mode():
            self._draw_creature_names(backend, tile, screen_x, screen_y, size)

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

    def _draw_highlight(self, backend: RenderBackend) -> None:
        """Draw a temporary highlight box for a tile."""
        if self._highlight_tile is None:
            return
        if time.monotonic() > float(self._highlight_until):
            self._highlight_tile = None
            return

        hx, hy, hz = self._highlight_tile
        if int(hz) != int(self._floor):
            return

        tile_size = self.viewport.tile_px
        px = (int(hx) - int(self._start_x)) * int(tile_size)
        py = (int(hy) - int(self._start_y)) * int(tile_size)
        backend.draw_selection_rect(px, py, tile_size, tile_size, 255, 215, 0, 220)

    def _draw_live_cursors(self, backend: RenderBackend) -> None:
        if not self._live_cursors:
            return
        tile_size = self.viewport.tile_px
        for cursor in self._live_cursors:
            try:
                x = int(cursor.get("x", 0))
                y = int(cursor.get("y", 0))
                z = int(cursor.get("z", 0))
            except Exception:
                continue
            if int(z) != int(self._floor):
                continue
            if not (self._start_x <= x <= self._end_x and self._start_y <= y <= self._end_y):
                continue
            px = (int(x) - int(self._start_x)) * int(tile_size)
            py = (int(y) - int(self._start_y)) * int(tile_size)
            color = cursor.get("color", (255, 255, 255))
            try:
                r, g, b = color
            except Exception:
                r, g, b = (255, 255, 255)
            backend.draw_selection_rect(px, py, tile_size, tile_size, int(r), int(g), int(b), 200)
            name = str(cursor.get("name", ""))
            if name:
                backend.draw_text(px + 2, py + 10, name, int(r), int(g), int(b), 220)

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
        if self.game_map is None or not self.options.show_lights:
            return

        settings = self.options.light_settings
        if not settings.enabled or settings.mode == LightMode.OFF:
            return

        ambient_color = settings.ambient_color.to_rgb_tuple()
        ambient_level = settings.ambient_level
        ambient_alpha = max(0, min(200, int((255 - ambient_level) * 0.75)))
        overlay_size = max(self.viewport.width_px, self.viewport.height_px)
        if ambient_alpha > 0:
            backend.draw_tile_color(
                0,
                0,
                overlay_size,
                ambient_color[0],
                ambient_color[1],
                ambient_color[2],
                ambient_alpha,
            )

        if settings.mode != LightMode.FULL:
            return

        tile_size = max(1, self.viewport.tile_px)
        glow_radius = tile_size * 2
        glow_color = self._mix_color(ambient_color, (255, 255, 255), 0.55)

        for x, y, strength in self._light_cache:
            glow_alpha = min(220, max(60, int(strength * 0.6)))
            px = int((x - self._start_x) * tile_size - glow_radius // 2)
            py = int((y - self._start_y) * tile_size - glow_radius // 2)
            backend.draw_tile_color(
                px,
                py,
                glow_radius,
                glow_color[0],
                glow_color[1],
                glow_color[2],
                glow_alpha,
            )

            if self.options.show_light_strength:
                text_x = int((x - self._start_x) * tile_size + 2)
                text_y = int((y - self._start_y) * tile_size + tile_size - 4)
                backend.draw_text(
                    text_x,
                    text_y,
                    str(strength),
                    glow_color[0],
                    glow_color[1],
                    glow_color[2],
                    200,
                )

    def _tile_light_strength(self, tile: "Tile" | None) -> int:
        """Estimate a normalized light strength for a given tile."""

        if tile is None:
            return 0

        strength = 0
        if tile.ground is not None:
            strength += 20

        strength += min(5, len(tile.items)) * 12

        if tile.spawn_monster is not None or tile.spawn_npc is not None:
            strength += 35

        strength += len(tile.monsters) * 8

        if tile.npc is not None:
            strength += 25

        for item in tile.items:
            for attr in item.attribute_map:
                key = attr.key.lower()
                if "light" in key or "brilho" in key or "luminosity" in key:
                    strength += 40

        return min(255, strength)

    @staticmethod
    def _mix_color(
        base: tuple[int, int, int],
        accent: tuple[int, int, int],
        ratio: float,
    ) -> tuple[int, int, int]:
        """Blend two colors, useful for glows."""

        ratio = max(0.0, min(1.0, ratio))
        return tuple(
            int(max(0, min(255, base[i] * (1.0 - ratio) + accent[i] * ratio)))
            for i in range(3)
        )

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
        if self._hover_tile is None or not self.should_draw_tooltips():
            return
        hx, hy, hz = self._hover_tile
        if not (self._start_z <= hz <= self._end_z) and not (self._end_z <= hz <= self._start_z):
            return

        if not (self._start_x <= hx <= self._end_x and self._start_y <= hy <= self._end_y):
            return

        tile_size = self.viewport.tile_px
        px = (hx - self._start_x) * tile_size
        py = (hy - self._start_y) * tile_size

        backend.draw_selection_rect(px, py, tile_size, tile_size, 255, 255, 255, 160)

        if not self._hover_stack:
            text = f"{hx},{hy},{hz} (empty)"
        else:
            top = self._hover_stack[-1]
            text = f"{hx},{hy},{hz} top:{top} stack:{len(self._hover_stack)}"
        backend.draw_text(px + 2, py + tile_size - 4, text, 230, 230, 230, 220)

    def _draw_spawn_indicator(self, backend: RenderBackend, x: int, y: int, size: int, *, kind: str) -> None:
        """Draw a spawn/creature marker; falls back to a colored rect when icons are missing."""
        indicator_key = str(kind)
        icon_size = int(max(10, min(32, size)))
        # Try indicator icon first.
        backend.draw_indicator_icon(x, y, indicator_key, icon_size)
        # Fallback overlay rectangle for visibility.
        if indicator_key == "spawn_monster":
            backend.draw_selection_rect(x, y, size, size, 200, 60, 60, 180)
        else:
            backend.draw_selection_rect(x, y, size, size, 60, 120, 220, 180)

    @staticmethod
    def _format_creature_names(names: list[str]) -> str:
        cleaned = [str(n).strip() for n in names if str(n).strip()]
        if not cleaned:
            return ""
        if len(cleaned) == 1:
            return cleaned[0]
        if len(cleaned) == 2:
            return f"{cleaned[0]}, {cleaned[1]}"
        return f"{cleaned[0]} +{len(cleaned) - 1}"

    def _draw_creature_names(
        self,
        backend: RenderBackend,
        tile,
        screen_x: int,
        screen_y: int,
        size: int,
    ) -> None:
        """Draw monster/NPC names on top of the tile."""
        if int(size) < 16:
            return

        labels: list[tuple[str, str]] = []

        if self.options.show_monsters and getattr(tile, "monsters", None):
            names = [getattr(m, "name", "") for m in tile.monsters]
            label = self._format_creature_names(names)
            if label:
                labels.append(("monster", label))

        npc = getattr(tile, "npc", None)
        if self.options.show_npcs and npc is not None:
            npc_name = str(getattr(npc, "name", "") or "").strip()
            if npc_name:
                labels.append(("npc", npc_name))

        if not labels:
            return

        line_height = max(10, min(14, int(size) // 2))
        base_y = int(screen_y) + line_height
        base_x = int(screen_x) + 2

        for idx, (kind, text) in enumerate(labels):
            if kind == "monster":
                r, g, b, a = 220, 80, 80, 230
            else:
                r, g, b, a = 100, 180, 255, 230
            backend.draw_text(base_x, base_y + (idx * line_height), text, r, g, b, a)


# Factory function for default drawer
def create_map_drawer(game_map: Optional["GameMap"] = None) -> MapDrawer:
    """Create a MapDrawer with default DrawingOptions."""
    options = DrawingOptions()
    return MapDrawer(options=options, game_map=game_map)
