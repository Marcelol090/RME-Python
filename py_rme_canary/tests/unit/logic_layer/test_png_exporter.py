from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from py_rme_canary.logic_layer.png_exporter import ExportConfig, PNGExporter


def _make_render_tile(tile_size: int) -> Callable[[int, int, int, int], bytes | None]:
    pixel = bytes([255, 0, 0, 128])
    tile_data = pixel * (tile_size * tile_size)

    def render_tile(x: int, y: int, z: int, size: int) -> bytes | None:
        if x == 0 and y == 0 and z == 7 and size == tile_size:
            return tile_data
        return None

    return render_tile


def test_png_exporter_single_bmp(tmp_path: Path) -> None:
    pil = pytest.importorskip("PIL")

    exporter = PNGExporter()
    exporter.set_map_bounds(0, 0, 1, 1)

    config = ExportConfig(
        z_level=7,
        tile_pixel_size=2,
        format="single",
        image_format="BMP",
    )

    output_path = tmp_path / "export_test.bmp"

    success = exporter.export(
        path=str(output_path),
        config=config,
        render_tile=_make_render_tile(tile_size=2),
    )

    assert success is True
    assert output_path.exists()
    assert output_path.stat().st_size > 0

    with pil.Image.open(output_path) as image:
        assert image.format == "BMP"
        assert image.mode == "RGB"
