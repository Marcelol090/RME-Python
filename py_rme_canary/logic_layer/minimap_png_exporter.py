"""Enhanced Minimap PNG Exporter.

This module provides advanced minimap export to PNG format with support for:
- Tiled export for huge maps (split into grid of images)
- Multi-floor export (all floors or selection)
- Progress callback for UI integration
- Configurable resolution and colors

Reference:
    - GAP_ANALYSIS.md: P2 - Minimap Export
    - Legacy: minimap_window.cpp export functions

Layer: logic_layer (no PyQt6 imports)
"""

from __future__ import annotations

import logging
import struct
import zlib
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap

logger = logging.getLogger(__name__)

# Tibia minimap color palette (256 colors)
# Index -> RGB tuple
MINIMAP_PALETTE: list[tuple[int, int, int]] = [
    (0, 0, 0),  # 0: Black (void)
    (0, 102, 0),  # 1: Dark green
    (0, 204, 0),  # 2: Bright green (grass)
    (51, 102, 0),  # 3: Olive
    (128, 128, 0),  # 4: Dark yellow
    (255, 255, 0),  # 5: Yellow
    (255, 128, 0),  # 6: Orange
    (179, 51, 0),  # 7: Dark orange
    (255, 0, 0),  # 8: Red
    (179, 0, 0),  # 9: Dark red
    (128, 0, 0),  # 10: Maroon
    (102, 51, 0),  # 11: Brown
    (153, 102, 51),  # 12: Light brown (dirt)
    (204, 153, 102),  # 13: Tan/sand
    (255, 204, 153),  # 14: Light sand
    (255, 255, 255),  # 15: White
    (204, 204, 204),  # 16: Light grey
    (153, 153, 153),  # 17: Grey
    (102, 102, 102),  # 18: Dark grey
    (51, 51, 51),  # 19: Darker grey
    (0, 0, 102),  # 20: Deep blue (water)
    (0, 0, 204),  # 21: Blue
    (51, 102, 204),  # 22: Light blue
    (102, 153, 255),  # 23: Sky blue
    (0, 153, 0),  # 24: Green (grass alt)
    (204, 255, 204),  # 25: Light green
    (255, 102, 204),  # 26: Pink
    (153, 0, 153),  # 27: Purple
    (102, 0, 204),  # 28: Violet
    (64, 64, 64),  # 29: Coal
    (200, 200, 200),  # 30: Silver
]

# Fill remaining palette slots with grayscale
for i in range(len(MINIMAP_PALETTE), 256):
    v = int((i / 255) * 200)
    MINIMAP_PALETTE.append((v, v, v))


@dataclass
class MinimapExportConfig:
    """Configuration for minimap PNG export.

    Attributes:
        floors: List of floor levels to export (None = all used floors).
        tile_size: Pixels per tile (1 for actual minimap, higher for detail).
        max_image_size: Max dimension before tiling (0 = no limit).
        output_dir: Directory for output files.
        filename_pattern: Pattern for filenames ({name}, {floor}, {x}, {y}).
        show_grid: Draw grid lines at major intervals.
        grid_interval: Tiles between grid lines.
        grid_color: Grid line color (RGB tuple).
        background_color: Color for unmapped areas.
        include_creatures: Render creature spawn markers.
        include_waypoints: Render waypoint markers.
    """

    floors: list[int] | None = None
    tile_size: int = 1
    max_image_size: int = 8192
    output_dir: Path = field(default_factory=lambda: Path.cwd())
    filename_pattern: str = "{name}_floor{floor:02d}_{x}_{y}.png"
    show_grid: bool = False
    grid_interval: int = 100
    grid_color: tuple[int, int, int] = (100, 100, 100)
    background_color: tuple[int, int, int] = (0, 0, 0)
    include_creatures: bool = False
    include_waypoints: bool = False


@dataclass
class ExportResult:
    """Result of a minimap export operation.

    Attributes:
        success: Whether export completed successfully.
        files_created: List of created file paths.
        total_tiles: Number of tiles processed.
        elapsed_seconds: Time taken.
        error: Error message if failed.
    """

    success: bool = True
    files_created: list[Path] = field(default_factory=list)
    total_tiles: int = 0
    elapsed_seconds: float = 0.0
    error: str = ""


class MinimapPNGExporter:
    """Advanced minimap exporter with tiling support.

    This exporter creates PNG images of the map with proper Tibia
    minimap colors. For very large maps, it can split the output
    into a grid of tiles.

    Usage:
        exporter = MinimapPNGExporter()
        config = MinimapExportConfig(
            floors=[7],
            output_dir=Path("output"),
            max_image_size=4096,
        )
        result = exporter.export(game_map, "mymap", config)

        if result.success:
            print(f"Created {len(result.files_created)} files")
    """

    def __init__(self) -> None:
        self._progress_callback: Callable[[float, str], None] | None = None
        self._cancelled = False

    def set_progress_callback(self, callback: Callable[[float, str], None]) -> None:
        """Set callback for progress updates.

        Args:
            callback: Function(progress: 0.0-1.0, message: str)
        """
        self._progress_callback = callback

    def cancel(self) -> None:
        """Request cancellation of current export."""
        self._cancelled = True

    def export(
        self,
        game_map: GameMap,
        map_name: str,
        config: MinimapExportConfig | None = None,
    ) -> ExportResult:
        """Export the map to PNG file(s).

        Args:
            game_map: GameMap instance to export.
            map_name: Base name for output files.
            config: Export configuration.

        Returns:
            ExportResult with file list and statistics.
        """
        import time

        self._cancelled = False
        config = config or MinimapExportConfig()
        result = ExportResult()
        start_time = time.perf_counter()

        try:
            # Determine floors to export
            floors = config.floors
            if floors is None:
                floors = self._get_used_floors(game_map)

            if not floors:
                result.error = "No floors to export"
                result.success = False
                return result

            self._report_progress(0.0, f"Exporting {len(floors)} floor(s)...")

            # Export each floor
            for floor_idx, floor in enumerate(floors):
                if self._cancelled:
                    result.error = "Cancelled"
                    result.success = False
                    break

                progress_base = floor_idx / len(floors)
                progress_scale = 1.0 / len(floors)

                self._report_progress(progress_base, f"Processing floor {floor}...")

                floor_files = self._export_floor(
                    game_map,
                    floor,
                    map_name,
                    config,
                    progress_base,
                    progress_scale,
                )

                result.files_created.extend(floor_files)

            # Count tiles
            result.total_tiles = sum(
                1 for key in getattr(game_map, "tiles", {}) if isinstance(key, tuple) and key[2] in floors
            )

            result.elapsed_seconds = time.perf_counter() - start_time
            self._report_progress(1.0, f"Exported {len(result.files_created)} file(s)")

        except Exception as e:
            logger.exception("Minimap export failed")
            result.success = False
            result.error = str(e)

        return result

    def _export_floor(
        self,
        game_map: GameMap,
        floor: int,
        map_name: str,
        config: MinimapExportConfig,
        progress_base: float,
        progress_scale: float,
    ) -> list[Path]:
        """Export a single floor.

        Returns list of created file paths.
        """
        # Get bounds for this floor
        bounds = self._get_floor_bounds(game_map, floor)
        if bounds is None:
            return []

        min_x, min_y, max_x, max_y = bounds
        width = (max_x - min_x + 1) * config.tile_size
        height = (max_y - min_y + 1) * config.tile_size

        logger.debug("Floor %d bounds: (%d,%d)-(%d,%d), image: %dx%d", floor, min_x, min_y, max_x, max_y, width, height)

        # Determine if tiling is needed
        if config.max_image_size > 0 and (width > config.max_image_size or height > config.max_image_size):
            return self._export_floor_tiled(game_map, floor, map_name, config, bounds, progress_base, progress_scale)
        else:
            return self._export_floor_single(game_map, floor, map_name, config, bounds, progress_base, progress_scale)

    def _export_floor_single(
        self,
        game_map: GameMap,
        floor: int,
        map_name: str,
        config: MinimapExportConfig,
        bounds: tuple[int, int, int, int],
        progress_base: float,
        progress_scale: float,
    ) -> list[Path]:
        """Export floor to a single PNG file."""
        min_x, min_y, max_x, max_y = bounds
        width = (max_x - min_x + 1) * config.tile_size
        height = (max_y - min_y + 1) * config.tile_size

        # Create image data (RGB)
        image_data = bytearray(width * height * 3)

        # Fill background
        bg = config.background_color
        for i in range(0, len(image_data), 3):
            image_data[i] = bg[0]
            image_data[i + 1] = bg[1]
            image_data[i + 2] = bg[2]

        # Render tiles
        tiles = getattr(game_map, "tiles", {})
        total = max_x - min_x + 1

        for tx in range(min_x, max_x + 1):
            if self._cancelled:
                break

            progress = progress_base + progress_scale * ((tx - min_x) / total) * 0.8
            self._report_progress(progress, f"Floor {floor}: rendering...")

            for ty in range(min_y, max_y + 1):
                key = (tx, ty, floor)
                tile = tiles.get(key)

                if tile is None:
                    continue

                color = self._get_tile_color(tile, config)

                # Calculate pixel position
                px = (tx - min_x) * config.tile_size
                py = (ty - min_y) * config.tile_size

                # Fill tile pixels
                for ox in range(config.tile_size):
                    for oy in range(config.tile_size):
                        idx = ((py + oy) * width + (px + ox)) * 3
                        if idx + 2 < len(image_data):
                            image_data[idx] = color[0]
                            image_data[idx + 1] = color[1]
                            image_data[idx + 2] = color[2]

        # Draw grid if enabled
        if config.show_grid:
            self._draw_grid(image_data, width, height, config, bounds)

        # Write PNG
        filename = config.filename_pattern.format(
            name=map_name,
            floor=floor,
            x=0,
            y=0,
        )
        output_path = config.output_dir / filename
        output_path.parent.mkdir(parents=True, exist_ok=True)

        self._report_progress(progress_base + progress_scale * 0.9, f"Writing {filename}...")

        self._write_png(output_path, image_data, width, height)

        return [output_path]

    def _export_floor_tiled(
        self,
        game_map: GameMap,
        floor: int,
        map_name: str,
        config: MinimapExportConfig,
        bounds: tuple[int, int, int, int],
        progress_base: float,
        progress_scale: float,
    ) -> list[Path]:
        """Export floor to multiple tiled PNG files."""
        min_x, min_y, max_x, max_y = bounds

        tiles_per_image = config.max_image_size // config.tile_size

        # Calculate tile grid
        grid_cols = ((max_x - min_x) // tiles_per_image) + 1
        grid_rows = ((max_y - min_y) // tiles_per_image) + 1

        logger.info("Tiled export: %dx%d grid for floor %d", grid_cols, grid_rows, floor)

        files: list[Path] = []
        total_tiles = grid_cols * grid_rows

        for grid_y in range(grid_rows):
            for grid_x in range(grid_cols):
                if self._cancelled:
                    break

                tile_idx = grid_y * grid_cols + grid_x
                progress = progress_base + progress_scale * (tile_idx / total_tiles)
                self._report_progress(progress, f"Floor {floor}: tile {grid_x},{grid_y}...")

                # Calculate bounds for this tile
                tile_min_x = min_x + grid_x * tiles_per_image
                tile_min_y = min_y + grid_y * tiles_per_image
                tile_max_x = min(tile_min_x + tiles_per_image - 1, max_x)
                tile_max_y = min(tile_min_y + tiles_per_image - 1, max_y)

                tile_bounds = (tile_min_x, tile_min_y, tile_max_x, tile_max_y)

                # Override filename pattern for this tile
                sub_config = MinimapExportConfig(
                    floors=[floor],
                    tile_size=config.tile_size,
                    max_image_size=0,  # No further tiling
                    output_dir=config.output_dir,
                    filename_pattern=config.filename_pattern.replace("{x}_{y}", f"{{x}}_{grid_x}_{{y}}_{grid_y}"),
                    show_grid=config.show_grid,
                    grid_interval=config.grid_interval,
                    grid_color=config.grid_color,
                    background_color=config.background_color,
                    include_creatures=config.include_creatures,
                    include_waypoints=config.include_waypoints,
                )

                tile_files = self._export_floor_single(
                    game_map, floor, map_name, sub_config, tile_bounds, progress, 0.0
                )
                files.extend(tile_files)

        return files

    def _get_tile_color(
        self,
        tile: Any,
        config: MinimapExportConfig,
    ) -> tuple[int, int, int]:
        """Get RGB color for a tile."""
        # Check for minimap color property
        if hasattr(tile, "minimap_color"):
            color_idx = int(tile.minimap_color)
            if 0 <= color_idx < len(MINIMAP_PALETTE):
                return MINIMAP_PALETTE[color_idx]

        # Get ground item
        ground = getattr(tile, "ground", None)
        if ground is None:
            return config.background_color

        # Check if ground has minimap color
        if hasattr(ground, "minimap_color"):
            color_idx = int(ground.minimap_color)
            if 0 <= color_idx < len(MINIMAP_PALETTE):
                return MINIMAP_PALETTE[color_idx]

        # Fallback to ID-based mapping
        item_id: int = int(getattr(ground, "item_id", 0) or getattr(ground, "id", 0))
        return self._id_to_color(item_id)

    def _id_to_color(self, item_id: int) -> tuple[int, int, int]:
        """Map item ID to approximate minimap color."""
        # Simple heuristic mapping (should use items.otb data ideally)
        if item_id == 0:
            return (0, 0, 0)

        # Grass-like
        if item_id in range(4526, 4542):
            return MINIMAP_PALETTE[24]  # Green

        # Stone/cave
        if item_id in range(351, 400) or item_id in range(4400, 4450):
            return MINIMAP_PALETTE[17]  # Grey

        # Sand
        if item_id in range(4632, 4700):
            return MINIMAP_PALETTE[13]  # Tan

        # Water
        if item_id in range(4608, 4632):
            return MINIMAP_PALETTE[20]  # Blue

        # Lava
        if item_id in range(5765, 5780):
            return MINIMAP_PALETTE[8]  # Red

        # Snow
        if item_id in range(4880, 4930):
            return MINIMAP_PALETTE[15]  # White

        # Default - use ID to generate color
        return MINIMAP_PALETTE[item_id % 30]

    def _draw_grid(
        self,
        image_data: bytearray,
        width: int,
        height: int,
        config: MinimapExportConfig,
        bounds: tuple[int, int, int, int],
    ) -> None:
        """Draw grid lines on image."""
        min_x, min_y, max_x, max_y = bounds
        color = config.grid_color
        interval = config.grid_interval * config.tile_size

        # Vertical lines
        for tx in range(min_x, max_x + 1, config.grid_interval):
            px = (tx - min_x) * config.tile_size
            if px >= width:
                continue
            for py in range(height):
                idx = (py * width + px) * 3
                if idx + 2 < len(image_data):
                    image_data[idx] = color[0]
                    image_data[idx + 1] = color[1]
                    image_data[idx + 2] = color[2]

        # Horizontal lines
        for ty in range(min_y, max_y + 1, config.grid_interval):
            py = (ty - min_y) * config.tile_size
            if py >= height:
                continue
            for px in range(width):
                idx = (py * width + px) * 3
                if idx + 2 < len(image_data):
                    image_data[idx] = color[0]
                    image_data[idx + 1] = color[1]
                    image_data[idx + 2] = color[2]

    def _write_png(
        self,
        path: Path,
        image_data: bytearray,
        width: int,
        height: int,
    ) -> None:
        """Write raw RGB data to PNG file.

        Uses minimal PNG implementation without PIL dependency.
        """

        def png_chunk(chunk_type: bytes, data: bytes) -> bytes:
            chunk = chunk_type + data
            crc = zlib.crc32(chunk) & 0xFFFFFFFF
            return struct.pack(">I", len(data)) + chunk + struct.pack(">I", crc)

        # PNG signature
        signature = b"\x89PNG\r\n\x1a\n"

        # IHDR chunk
        ihdr_data = struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0)
        ihdr = png_chunk(b"IHDR", ihdr_data)

        # IDAT chunk (image data)
        # Add filter byte (0 = none) to each row
        raw_data = b""
        for y in range(height):
            raw_data += b"\x00"  # Filter byte
            row_start = y * width * 3
            raw_data += bytes(image_data[row_start : row_start + width * 3])

        compressed = zlib.compress(raw_data, level=6)
        idat = png_chunk(b"IDAT", compressed)

        # IEND chunk
        iend = png_chunk(b"IEND", b"")

        # Write file
        with open(path, "wb") as f:
            f.write(signature + ihdr + idat + iend)

        logger.debug("Wrote PNG: %s (%dx%d)", path, width, height)

    def _get_used_floors(self, game_map: GameMap) -> list[int]:
        """Get list of floors that have tiles."""
        floors: set[int] = set()

        for key in getattr(game_map, "tiles", {}):
            if isinstance(key, tuple) and len(key) >= 3:
                floors.add(key[2])

        return sorted(floors)

    def _get_floor_bounds(
        self,
        game_map: GameMap,
        floor: int,
    ) -> tuple[int, int, int, int] | None:
        """Get bounding box for a floor."""
        min_x = float("inf")
        min_y = float("inf")
        max_x = float("-inf")
        max_y = float("-inf")
        found = False

        for key in getattr(game_map, "tiles", {}):
            if isinstance(key, tuple) and len(key) >= 3 and key[2] == floor:
                x, y = key[0], key[1]
                min_x = min(min_x, x)
                min_y = min(min_y, y)
                max_x = max(max_x, x)
                max_y = max(max_y, y)
                found = True

        if not found:
            return None

        return int(min_x), int(min_y), int(max_x), int(max_y)

    def _report_progress(self, progress: float, message: str) -> None:
        """Report progress via callback."""
        if self._progress_callback:
            try:
                self._progress_callback(progress, message)
            except Exception:
                pass


def get_minimap_png_exporter() -> MinimapPNGExporter:
    """Get a new minimap PNG exporter instance."""
    return MinimapPNGExporter()
