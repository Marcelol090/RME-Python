"""Minimap Exporter Module for RME.

Handles exporting the map to .otmm minimap format.
Format:
    Header: 4 bytes "OTMM"
    Version: 2 bytes (unused?)
    Width: 2 bytes
    Height: 2 bytes
    Pixel Data: Width * Height bytes (color indices)

Layer: logic_layer (no PyQt6 imports)
"""

from __future__ import annotations

import logging
import struct
from typing import Any

log = logging.getLogger(__name__)


class MinimapExporter:
    """Exporter for OTMM minimap format."""

    def __init__(self, *, appearance_index: Any = None) -> None:
        self._appearance_index = appearance_index
        self._color_cache: dict[int, int] = {}

    def export(self, game_map: Any, output_path: str, z_level: int = 7) -> None:
        """Export a specific Z-level to .otmm file.

        Args:
            game_map: GameMap instance
            output_path: Destination file path
            z_level: Z-level to export (OTMM is typically 2D or multi-file)
        """
        log.info("Exporting minimap level %d to %s", z_level, output_path)

        bounds = self._get_bounds(game_map, z_level)
        if not bounds:
            raise ValueError(f"No tiles found at z={z_level}")

        min_x, min_y, max_x, max_y = bounds
        width = max_x - min_x + 1
        height = max_y - min_y + 1

        log.debug("Map bounds: %s, Size: %dx%d", bounds, width, height)

        # Prepare pixel data
        # OTMM typically uses distinct color bytes.
        # For simplicity, we'll map common ground IDs to rough colors
        # or use the map's get_color capability if available.
        pixels = bytearray(width * height)

        tiles = getattr(game_map, "tiles", {})

        # Optimization: pre-calculate offset
        # pixel_index = (y - min_y) * width + (x - min_x)

        count = 0
        for key, tile in tiles.items():
            tx, ty, tz = key if isinstance(key, tuple) else (tile.x, tile.y, tile.z)

            if tz != z_level:
                continue

            # Check bounds (just in case)
            if not (min_x <= tx <= max_x and min_y <= ty <= max_y):
                continue

            idx = (ty - min_y) * width + (tx - min_x)

            # Simple color mapping logic
            # This should ideally call a proper ColorMapper
            color = self._get_tile_minimap_color(tile)
            pixels[idx] = color
            count += 1

        log.info("Processed %d tiles", count)

        # Write file
        with open(output_path, "wb") as f:
            # Header
            f.write(b"OTMM")
            f.write(struct.pack("<H", 0))  # Version or reserved
            f.write(struct.pack("<H", width))
            f.write(struct.pack("<H", height))

            # Data
            f.write(pixels)

        log.info("Export complete")

    def _get_bounds(self, game_map: Any, z: int) -> tuple[int, int, int, int] | None:
        """Calculate bounding box for the given z-level."""
        tiles = getattr(game_map, "tiles", {})

        min_x, min_y = float("inf"), float("inf")
        max_x, max_y = float("-inf"), float("-inf")
        found = False

        for key in tiles:
            x, y, current_z = key if isinstance(key, tuple) else (0, 0, 0)
            if current_z == z:
                min_x = min(min_x, x)
                max_x = max(max_x, x)
                min_y = min(min_y, y)
                max_y = max(max_y, y)
                found = True

        if not found:
            return None

        return int(min_x), int(min_y), int(max_x), int(max_y)

    def _get_tile_minimap_color(self, tile: Any) -> int:
        """Determine minimap color index for a tile.

        Uses the automap color from ``appearances.dat`` when available,
        falling back to a basic heuristic for legacy assets.

        Returns a byte value (0-255).
        """
        ground = getattr(tile, "ground", None)
        if not ground:
            return 0  # Empty/Black

        # Try to resolve via appearances.dat minimap_color
        client_id = getattr(ground, "client_id", None)
        if client_id is None:
            client_id = getattr(ground, "server_id", 0) or getattr(ground, "id", 0)
        client_id = int(client_id or 0)

        cached = self._color_cache.get(client_id)
        if cached is not None:
            return cached

        color = self._resolve_automap_color(client_id)
        if color is None:
            # Fallback to ID-based heuristic
            color = self._fallback_color(ground)
        self._color_cache[client_id] = color
        return color

    def _resolve_automap_color(self, client_id: int) -> int | None:
        """Look up minimap color from appearances.dat."""
        if self._appearance_index is None:
            return None
        obj_info = getattr(self._appearance_index, "object_info", None)
        if obj_info is None:
            return None
        info = obj_info.get(client_id)
        if info is None:
            return None
        if getattr(info, "has_minimap_color", False):
            return max(0, min(255, int(info.minimap_color)))
        return None

    @staticmethod
    def _fallback_color(ground: Any) -> int:
        """Simple ID-based color heuristic for legacy assets."""
        sid = getattr(ground, "server_id", 0) or getattr(ground, "id", 0)
        sid = int(sid)
        if sid in (4526, 4527, 4528):  # Grass
            return 24  # Greenish
        if sid in (351, 352, 353, 354, 355):  # Stone/Cave
            return 128  # Grey
        if sid in (4632, 4633, 4634, 4635):  # Sand
            return 210  # Yellow/Sand
        if sid in (4664, 4665, 4666):  # Water
            return 20  # Blue
        return 200  # Default generic tile


def get_minimap_exporter(*, appearance_index: Any = None) -> MinimapExporter:
    return MinimapExporter(appearance_index=appearance_index)
