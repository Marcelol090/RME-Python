"""Minimap generation and export functionality.

Renders GameMap to minimap-style PNG/BMP images, one per floor.
"""
from __future__ import annotations

from typing import TYPE_CHECKING
from pathlib import Path

try:
    from PIL import Image
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap


# Default minimap colors for common ground types
DEFAULT_COLORS = {
    4526: (34, 139, 34),  # Grass - Green
    1295: (128, 128, 128),  # Stone Wall - Gray
    406: (205, 133, 63),   # Desert - Sandy
    # Add more as needed
}


class MinimapColorTable:
    """Lookup table for item ID -> minimap RGB color."""

    def __init__(self) -> None:
        """Initialize with default colors."""
        self._colors = DEFAULT_COLORS.copy()

    def get_color(self, item_id: int) -> tuple[int, int, int]:
        """Get RGB color for item ID."""
        return self._colors.get(item_id, (0, 0, 0))  # Black default

    def set_color(self, item_id: int, rgb: tuple[int, int, int]) -> None:
        """Set custom color for item ID."""
        self._colors[item_id] = rgb


class MinimapRenderer:
    """Renders GameMap to minimap image."""

    def __init__(self) -> None:
        """Initialize renderer with color table."""
        if not PIL_AVAILABLE:
            raise ImportError("Pillow (PIL) required for minimap export. Install with: pip install Pillow")

        self._color_table = MinimapColorTable()

    def render(self, game_map: GameMap, floor: int, bounds: tuple[int, int, int, int] | None = None) -> Image.Image:
        """Render single floor to PIL Image.

        Args:
            game_map: GameMap instance to render
            floor: Z-level to render (7 = ground floor)
            bounds: Optional (min_x, min_y, max_x, max_y) to render specific region

        Returns:
            PIL Image with minimap visualization
        """
        if bounds is not None:
            min_x, min_y, max_x, max_y = bounds
            if max_x <= min_x or max_y <= min_y:
                raise ValueError(f"Invalid bounds: {bounds}")
            width = max_x - min_x
            height = max_y - min_y
        else:
            xs = [x for x, y, z in game_map.tiles.keys() if z == floor]
            ys = [y for x, y, z in game_map.tiles.keys() if z == floor]

            if xs and ys:
                min_x, max_x = min(xs), max(xs)
                min_y, max_y = min(ys), max(ys)
                width = max_x - min_x + 1
                height = max_y - min_y + 1
            else:
                header = getattr(game_map, "header", None)
                if header is not None:
                    width = max(1, int(getattr(header, "width", 256) or 256))
                    height = max(1, int(getattr(header, "height", 256) or 256))
                else:
                    width, height = 256, 256
                min_x, min_y = 0, 0

        # Create RGB image
        img = Image.new("RGB", (width, height), color=(0, 0, 0))
        pixels = img.load()

        # Render each tile
        for x in range(width):
            for y in range(height):
                tile = game_map.get_tile(min_x + x, min_y + y, floor)
                if tile is None:
                    continue
                ground = getattr(tile, "ground", None)
                if ground is None:
                    continue
                color = self._color_table.get_color(int(getattr(ground, "id", 0)))
                pixels[x, y] = color

        return img

    def export_image(
        self,
        game_map: GameMap,
        floor: int,
        output_path: Path,
        image_format: str = "PNG",
        bounds: tuple[int, int, int, int] | None = None,
    ) -> None:
        """Export minimap floor to PNG/BMP file.

        Args:
            game_map: GameMap to export
            floor: Z-level to export
            output_path: Path for output image file
            image_format: Output format (PNG or BMP)
            bounds: Optional region bounds (min_x, min_y, max_x, max_y)
        """
        normalized = image_format.strip().upper()
        if normalized not in {"PNG", "BMP"}:
            raise ValueError(f"Unsupported image format: {image_format}")

        img = self.render(game_map, floor, bounds)
        img.save(output_path, normalized)

    def export_png(
        self,
        game_map: GameMap,
        floor: int,
        output_path: Path,
        bounds: tuple[int, int, int, int] | None = None,
    ) -> None:
        """Export minimap floor to PNG file."""
        self.export_image(game_map, floor, output_path, "PNG", bounds)

    def export_bmp(
        self,
        game_map: GameMap,
        floor: int,
        output_path: Path,
        bounds: tuple[int, int, int, int] | None = None,
    ) -> None:
        """Export minimap floor to BMP file."""
        self.export_image(game_map, floor, output_path, "BMP", bounds)
