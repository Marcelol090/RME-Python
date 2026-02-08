from __future__ import annotations

import json
import lzma
import struct
from pathlib import Path

from py_rme_canary.core.assets.sprite_appearances import BYTES_IN_SPRITE_SHEET, SpriteAppearances


def _build_cip_lzma_sheet_payload() -> bytes:
    pixel_offset = 122
    bmp_like = bytearray(pixel_offset + BYTES_IN_SPRITE_SHEET)
    bmp_like[0:2] = b"BM"
    struct.pack_into("<I", bmp_like, 2, len(bmp_like))
    struct.pack_into("<I", bmp_like, 10, pixel_offset)

    for index in range(pixel_offset, len(bmp_like)):
        bmp_like[index] = index % 251

    filters = [
        {
            "id": lzma.FILTER_LZMA1,
            "dict_size": 1 << 23,
            "lc": 3,
            "lp": 0,
            "pb": 2,
        }
    ]
    compressed = lzma.compress(bytes(bmp_like), format=lzma.FORMAT_RAW, filters=filters)

    marker = bytes([0x70, 0x0A, 0xFA, 0x80, 0x24])
    varint_size = b"\x01"
    props = bytes([0x5D])  # lc=3, lp=0, pb=2
    dict_size = struct.pack("<I", 1 << 23)
    compressed_size = struct.pack("<Q", len(compressed))

    return (b"\x00" * 24) + marker + varint_size + props + dict_size + compressed_size + compressed


def test_load_sheet_supports_full_cip_marker_skip(tmp_path: Path) -> None:
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir(parents=True)

    sheet_path = assets_dir / "sheet.bmp.lzma"
    sheet_path.write_bytes(_build_cip_lzma_sheet_payload())

    catalog = [
        {
            "type": "sprite",
            "firstspriteid": 1,
            "lastspriteid": 1,
            "spritetype": 0,
            "file": sheet_path.name,
        }
    ]
    (assets_dir / "catalog-content.json").write_text(json.dumps(catalog), encoding="utf-8")

    appearances = SpriteAppearances(assets_dir=assets_dir)
    appearances.load_catalog_content(load_data=True)
    width, height, bgra = appearances.get_sprite_rgba(1)

    assert width == 32
    assert height == 32
    assert len(bgra) == 32 * 32 * 4
