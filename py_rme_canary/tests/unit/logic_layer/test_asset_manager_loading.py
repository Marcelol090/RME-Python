from __future__ import annotations

import json
import struct
from pathlib import Path

from py_rme_canary.logic_layer.asset_manager import AssetManager


def _write_legacy_dat_spr(tmp_path: Path) -> None:
    dat_path = tmp_path / "Tibia.dat"
    spr_path = tmp_path / "Tibia.spr"
    dat_path.write_bytes(struct.pack("<IHHHH", 0, 1, 0, 0, 0))

    sprite_count = 1
    header = struct.pack("<II", 0, sprite_count)
    offset_base = 8 + sprite_count * 4
    offsets = b"".join(struct.pack("<I", offset_base) for _ in range(sprite_count))
    spr_path.write_bytes(header + offsets)


def _write_modern_assets(tmp_path: Path) -> Path:
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir(parents=True)
    catalog = [
        {
            "type": "sprite",
            "firstspriteid": 1,
            "lastspriteid": 1,
            "spritetype": 0,
            "file": "sheet_00.dat",
        }
    ]
    (assets_dir / "catalog-content.json").write_text(json.dumps(catalog), encoding="utf-8")
    return assets_dir


def test_asset_manager_loads_legacy_assets(tmp_path: Path) -> None:
    _write_legacy_dat_spr(tmp_path)
    manager = AssetManager.instance()

    assert manager.load_assets(tmp_path) is True
    assert manager.is_loaded is True
    assert Path(str(manager.assets_path)).resolve() == tmp_path.resolve()


def test_asset_manager_loads_nested_modern_assets(tmp_path: Path) -> None:
    wrapper = tmp_path / "wrapper"
    client = wrapper / "15.11 localhost"
    assets_dir = _write_modern_assets(client)
    manager = AssetManager.instance()

    assert manager.load_assets(wrapper) is True
    assert manager.is_loaded is True
    assert Path(str(manager.assets_path)).resolve() == assets_dir.resolve()
