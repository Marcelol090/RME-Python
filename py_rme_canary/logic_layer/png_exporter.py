"""PNG Export Module for RME.

Provides tiled PNG export for large maps with memory-efficient chunked rendering.

Layer: logic_layer (no PyQt6 imports)
"""

from __future__ import annotations

import logging
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

log = logging.getLogger(__name__)

if TYPE_CHECKING:
    from PIL import Image as PILImage


@dataclass
class ExportConfig:
    """Configuration for PNG export."""

    z_level: int = 7
    tile_pixel_size: int = 32
    chunk_size: int = 256  # tiles per chunk
    format: str = "single"  # "single" or "tiled"
    image_format: str = "PNG"  # "PNG" or "BMP"
    background_color: tuple[int, int, int, int] = (0, 0, 0, 255)


class TileRenderCallback(Protocol):
    """Protocol for rendering a tile to pixels."""

    def __call__(self, x: int, y: int, z: int, tile_size: int) -> bytes | None:
        """Render tile at (x,y,z) to RGBA bytes of size tile_size x tile_size.

        Returns None if tile is empty.
        """
        ...


class ProgressCallback(Protocol):
    """Protocol for progress updates."""

    def __call__(self, current: int, total: int, message: str) -> bool:
        """Report progress. Return False to cancel export."""
        ...


class PNGExporter:
    """Exports map to PNG/BMP with support for tiled export of large maps.

    Usage:
        exporter = PNGExporter()
        exporter.set_map_bounds(0, 0, 2048, 2048)
        exporter.export(
            path="output.png",
            config=ExportConfig(z_level=7),
            render_tile=my_tile_renderer,
            on_progress=my_progress_callback,
        )
    """

    # Maximum image dimension to use single-file export (4096x4096)
    MAX_SINGLE_PIXELS = 4096

    def __init__(self) -> None:
        self._x_min: int = 0
        self._y_min: int = 0
        self._x_max: int = 2048
        self._y_max: int = 2048
        self._cancelled: bool = False

    def set_map_bounds(self, x_min: int, y_min: int, x_max: int, y_max: int) -> None:
        """Set the map bounds for export."""
        self._x_min = int(x_min)
        self._y_min = int(y_min)
        self._x_max = int(x_max)
        self._y_max = int(y_max)

    def cancel(self) -> None:
        """Cancel ongoing export."""
        self._cancelled = True

    def export(
        self,
        path: str,
        config: ExportConfig,
        render_tile: TileRenderCallback,
        on_progress: ProgressCallback | None = None,
    ) -> bool:
        """Export map to PNG.

        Automatically chooses tiled or single export based on map size.

        Args:
            path: Output path (for tiled, creates directory)
            config: Export configuration
            render_tile: Callback to render individual tiles
            on_progress: Optional progress callback

        Returns:
            True if export succeeded
        """
        self._cancelled = False

        width_tiles = self._x_max - self._x_min
        height_tiles = self._y_max - self._y_min
        width_px = width_tiles * config.tile_pixel_size
        height_px = height_tiles * config.tile_pixel_size

        # Determine export mode
        if config.format == "tiled" or max(width_px, height_px) > self.MAX_SINGLE_PIXELS:
            return self._export_tiled(path, config, render_tile, on_progress)
        else:
            return self._export_single(path, config, render_tile, on_progress)

    def _normalize_image_format(self, image_format: str) -> str | None:
        normalized = image_format.strip().upper()
        if normalized not in {"PNG", "BMP"}:
            log.error("Unsupported image format: %s", image_format)
            return None
        return normalized

    def _prepare_image_for_save(
        self,
        image: PILImage.Image,
        image_format: str,
        background_color: tuple[int, int, int, int],
    ) -> PILImage.Image:
        if image_format != "BMP":
            return image

        if image.mode == "RGBA":
            from PIL import Image

            background = Image.new("RGBA", image.size, background_color)
            background.alpha_composite(image)
            return background.convert("RGB")

        if image.mode != "RGB":
            return image.convert("RGB")

        return image

    def _export_single(
        self,
        path: str,
        config: ExportConfig,
        render_tile: TileRenderCallback,
        on_progress: ProgressCallback | None,
    ) -> bool:
        """Export map as a single image file."""
        try:
            from PIL import Image
        except ImportError:
            log.error("PIL/Pillow not installed, cannot export image")
            return False

        image_format = self._normalize_image_format(config.image_format)
        if image_format is None:
            return False

        width_tiles = self._x_max - self._x_min
        height_tiles = self._y_max - self._y_min
        width_px = width_tiles * config.tile_pixel_size
        height_px = height_tiles * config.tile_pixel_size

        log.info("Exporting single %s: %dx%dpx", image_format, width_px, height_px)

        # Create output image
        image = Image.new("RGBA", (width_px, height_px), config.background_color)

        total_tiles = width_tiles * height_tiles
        processed = 0

        for ty in range(height_tiles):
            for tx in range(width_tiles):
                if self._cancelled:
                    return False

                world_x = self._x_min + tx
                world_y = self._y_min + ty

                tile_data = render_tile(world_x, world_y, config.z_level, config.tile_pixel_size)
                if tile_data:
                    tile_img = Image.frombytes(
                        "RGBA",
                        (config.tile_pixel_size, config.tile_pixel_size),
                        tile_data,
                    )
                    px_x = tx * config.tile_pixel_size
                    px_y = ty * config.tile_pixel_size
                    image.paste(tile_img, (px_x, px_y))

                processed += 1
                if (
                    on_progress
                    and processed % 100 == 0
                    and not on_progress(
                        processed,
                        total_tiles,
                        f"Rendering tile {processed}/{total_tiles}",
                    )
                ):
                    self._cancelled = True
                    return False

        # Save
        prepared_image = self._prepare_image_for_save(image, image_format, config.background_color)
        prepared_image.save(str(path), image_format)
        log.info("Saved %s to %s", image_format, path)

        if on_progress:
            on_progress(total_tiles, total_tiles, "Export complete")

        return True

    def _export_tiled(
        self,
        path: str,
        config: ExportConfig,
        render_tile: TileRenderCallback,
        on_progress: ProgressCallback | None,
    ) -> bool:
        """Export map as multiple tiled image files."""
        try:
            from PIL import Image
        except ImportError:
            log.error("PIL/Pillow not installed, cannot export image")
            return False

        image_format = self._normalize_image_format(config.image_format)
        if image_format is None:
            return False

        # Create output directory
        output_dir = os.path.splitext(str(path))[0] + "_tiles"
        os.makedirs(output_dir, exist_ok=True)

        width_tiles = self._x_max - self._x_min
        height_tiles = self._y_max - self._y_min
        chunk_size = config.chunk_size

        chunks_x = (width_tiles + chunk_size - 1) // chunk_size
        chunks_y = (height_tiles + chunk_size - 1) // chunk_size
        total_chunks = chunks_x * chunks_y

        log.info("Exporting tiled %s: %dx%d chunks", image_format, chunks_x, chunks_y)

        processed_chunks = 0

        for cy in range(chunks_y):
            for cx in range(chunks_x):
                if self._cancelled:
                    return False

                # Calculate chunk bounds
                chunk_x_start = self._x_min + cx * chunk_size
                chunk_y_start = self._y_min + cy * chunk_size
                chunk_x_end = min(chunk_x_start + chunk_size, self._x_max)
                chunk_y_end = min(chunk_y_start + chunk_size, self._y_max)

                chunk_width = chunk_x_end - chunk_x_start
                chunk_height = chunk_y_end - chunk_y_start
                chunk_width_px = chunk_width * config.tile_pixel_size
                chunk_height_px = chunk_height * config.tile_pixel_size

                # Create chunk image
                chunk_img = Image.new("RGBA", (chunk_width_px, chunk_height_px), config.background_color)

                for ty in range(chunk_height):
                    for tx in range(chunk_width):
                        world_x = chunk_x_start + tx
                        world_y = chunk_y_start + ty

                        tile_data = render_tile(world_x, world_y, config.z_level, config.tile_pixel_size)
                        if tile_data:
                            tile_img = Image.frombytes(
                                "RGBA",
                                (config.tile_pixel_size, config.tile_pixel_size),
                                tile_data,
                            )
                            px_x = tx * config.tile_pixel_size
                            px_y = ty * config.tile_pixel_size
                            chunk_img.paste(tile_img, (px_x, px_y))

                # Save chunk
                file_ext = image_format.lower()
                chunk_path = os.path.join(output_dir, f"chunk_{cx}_{cy}_z{config.z_level}.{file_ext}")
                prepared_chunk = self._prepare_image_for_save(chunk_img, image_format, config.background_color)
                prepared_chunk.save(chunk_path, image_format)

                processed_chunks += 1
                if on_progress and not on_progress(
                    processed_chunks,
                    total_chunks,
                    f"Exported chunk {processed_chunks}/{total_chunks}",
                ):
                    self._cancelled = True
                    return False

        # Create metadata file
        meta_path = os.path.join(output_dir, "metadata.txt")
        with open(meta_path, "w", encoding="utf-8") as f:
            f.write(f"chunks_x={chunks_x}\n")
            f.write(f"chunks_y={chunks_y}\n")
            f.write(f"chunk_size={chunk_size}\n")
            f.write(f"tile_pixel_size={config.tile_pixel_size}\n")
            f.write(f"z_level={config.z_level}\n")
            f.write(f"map_bounds={self._x_min},{self._y_min},{self._x_max},{self._y_max}\n")

        log.info("Saved %d chunks to %s", total_chunks, output_dir)

        if on_progress:
            on_progress(total_chunks, total_chunks, "Tiled export complete")

        return True

    def estimate_memory_mb(self, config: ExportConfig) -> float:
        """Estimate memory usage in MB for single-file export."""
        width_tiles = self._x_max - self._x_min
        height_tiles = self._y_max - self._y_min
        width_px = width_tiles * config.tile_pixel_size
        height_px = height_tiles * config.tile_pixel_size
        # RGBA = 4 bytes per pixel
        return (width_px * height_px * 4) / (1024 * 1024)


def get_default_exporter() -> PNGExporter:
    """Get a new PNG exporter instance."""
    return PNGExporter()
