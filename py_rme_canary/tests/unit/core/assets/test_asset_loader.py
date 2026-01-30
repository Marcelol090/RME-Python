from __future__ import annotations

import json
import struct
from pathlib import Path

from py_rme_canary.core.assets.asset_profile import detect_asset_profile
from py_rme_canary.core.assets.legacy_dat_spr import LegacySpriteArchive
from py_rme_canary.core.assets.loader import load_assets_from_profile
from py_rme_canary.core.assets.sprite_appearances import SpriteAppearances


def _write_legacy_dat_spr(tmp_path: Path) -> tuple[Path, Path]:
    dat_path = tmp_path / "Tibia.dat"
    spr_path = tmp_path / "Tibia.spr"
    dat_path.write_bytes(struct.pack("<IHHHH", 0, 1, 0, 0, 0))

    sprite_count = 1
    header = struct.pack("<II", 0, sprite_count)
    offset_base = 8 + sprite_count * 4
    offsets = b"".join(struct.pack("<I", offset_base) for _ in range(sprite_count))
    spr_path.write_bytes(header + offsets)
    return dat_path, spr_path


def test_load_assets_modern_profile(tmp_path: Path) -> None:
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    doc = [
        {
            "type": "sprite",
            "firstspriteid": 1,
            "lastspriteid": 1,
            "spritetype": 0,
            "file": "dummy.dat",
        }
    ]
    (assets_dir / "catalog-content.json").write_text(json.dumps(doc), encoding="utf-8")

    profile = detect_asset_profile(tmp_path)
    loaded = load_assets_from_profile(profile)

    assert loaded.profile.kind == "modern"
    assert isinstance(loaded.sprite_assets, SpriteAppearances)
    assert loaded.sheet_count == 1
    assert loaded.sprite_count is None
    assert loaded.appearance_assets is None
    assert loaded.appearance_error is None


def test_load_assets_legacy_profile(tmp_path: Path) -> None:
    dat_path, spr_path = _write_legacy_dat_spr(tmp_path)

    profile = detect_asset_profile(tmp_path)
    loaded = load_assets_from_profile(profile)

    assert loaded.profile.kind == "legacy"
    assert isinstance(loaded.sprite_assets, LegacySpriteArchive)
    assert loaded.sprite_count == 1
    assert loaded.sheet_count is None
