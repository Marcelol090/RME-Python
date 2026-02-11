from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace

from py_rme_canary.logic_layer import minimap_png_exporter as png_mod
from py_rme_canary.logic_layer.minimap_png_exporter import MinimapExportConfig, MinimapPNGExporter


def test_export_floor_single_uses_render_minimap_buffer(tmp_path: Path, monkeypatch) -> None:
    exporter = MinimapPNGExporter()
    game_map = SimpleNamespace(
        tiles={
            (100, 200, 7): SimpleNamespace(minimap_color=8),
            (101, 200, 7): SimpleNamespace(minimap_color=21),
        }
    )

    captured: dict[str, object] = {}

    def _fake_render(
        tile_colors: list[tuple[int, int, int, int]],
        tiles_x: int,
        tiles_y: int,
        tile_size: int,
        bg_r: int,
        bg_g: int,
        bg_b: int,
    ) -> bytearray:
        captured["tile_colors"] = tile_colors
        captured["tiles_x"] = tiles_x
        captured["tiles_y"] = tiles_y
        captured["tile_size"] = tile_size
        captured["bg"] = (bg_r, bg_g, bg_b)
        # 2x1 pixels, RGB
        return bytearray([255, 0, 0, 0, 0, 255])

    written: list[tuple[Path, int, int, int]] = []

    def _fake_write(path: Path, image_data: bytearray, width: int, height: int) -> None:
        written.append((path, len(image_data), width, height))

    monkeypatch.setattr(png_mod, "render_minimap_buffer", _fake_render)
    monkeypatch.setattr(exporter, "_write_png", _fake_write)

    cfg = MinimapExportConfig(output_dir=tmp_path, tile_size=1, max_image_size=0)
    files = exporter._export_floor_single(
        game_map=game_map,
        floor=7,
        map_name="testmap",
        config=cfg,
        bounds=(100, 200, 101, 200),
        progress_base=0.0,
        progress_scale=1.0,
    )

    assert files and files[0].name.startswith("testmap_floor07")
    assert captured["tiles_x"] == 2
    assert captured["tiles_y"] == 1
    assert captured["tile_size"] == 1
    assert captured["bg"] == cfg.background_color
    colors = captured["tile_colors"]
    assert isinstance(colors, list)
    assert colors == [(255, 0, 0, 255), (0, 0, 204, 255)]
    assert written and written[0][1:] == (6, 2, 1)


def test_write_png_uses_assembled_idat_payload(tmp_path: Path, monkeypatch) -> None:
    exporter = MinimapPNGExporter()
    out_file = tmp_path / "mini.png"
    calls: list[tuple[bytes, int, int]] = []

    def _fake_assemble(image_data: bytearray | bytes, width: int, height: int) -> bytes:
        calls.append((bytes(image_data), int(width), int(height)))
        return b"RUST-IDAT"

    monkeypatch.setattr(png_mod, "assemble_png_idat", _fake_assemble)
    exporter._write_png(out_file, bytearray([1, 2, 3]), 1, 1)

    assert out_file.exists()
    raw = out_file.read_bytes()
    assert raw.startswith(b"\x89PNG\r\n\x1a\n")
    assert b"IDATRUST-IDAT" in raw
    assert calls == [(b"\x01\x02\x03", 1, 1)]
