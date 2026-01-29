from __future__ import annotations

import json
from pathlib import Path

import pytest

from py_rme_canary.core.assets.sprite_appearances import SpriteAppearances


def _require_pillow():
    try:
        from PIL import Image  # type: ignore[import-untyped]  # optional dependency
    except Exception:
        pytest.skip("Pillow not installed")
    return Image


def test_load_png_sprite_sheet(tmp_path: Path) -> None:
    image_lib = _require_pillow()

    sheet_path = tmp_path / "sheet.png"
    img = image_lib.new("RGBA", (384, 384), (0, 0, 0, 0))
    img.putpixel((0, 0), (255, 0, 0, 255))
    img.save(sheet_path)

    catalog = [
        {
            "type": "sprite",
            "firstspriteid": 1,
            "lastspriteid": 1,
            "spritetype": 0,
            "file": "sheet.png",
        }
    ]
    (tmp_path / "catalog-content.json").write_text(json.dumps(catalog), encoding="utf-8")

    sa = SpriteAppearances(assets_dir=str(tmp_path))
    sa.load_catalog_content(load_data=True)

    w, h, bgra = sa.get_sprite_rgba(1)
    assert (w, h) == (32, 32)
    assert bgra[:4] == bytes([0, 0, 255, 255])
