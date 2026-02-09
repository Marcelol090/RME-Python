from __future__ import annotations

from pathlib import Path

from py_rme_canary.core.assets.asset_profile import detect_asset_profile


def test_detect_modern_assets_from_client_root(tmp_path: Path) -> None:
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    (assets_dir / "catalog-content.json").write_text("[]", encoding="utf-8")

    profile = detect_asset_profile(tmp_path)

    assert profile.kind == "modern"
    assert profile.assets_dir == assets_dir


def test_detect_legacy_assets_from_folder(tmp_path: Path) -> None:
    (tmp_path / "Tibia.dat").write_bytes(b"1234")
    (tmp_path / "Tibia.spr").write_bytes(b"5678")

    profile = detect_asset_profile(tmp_path)

    assert profile.kind == "legacy"
    assert profile.dat_path == tmp_path / "Tibia.dat"
    assert profile.spr_path == tmp_path / "Tibia.spr"


def test_detect_assets_conflict_defaults_to_modern(tmp_path: Path) -> None:
    assets_dir = tmp_path / "assets"
    assets_dir.mkdir()
    (assets_dir / "catalog-content.json").write_text("[]", encoding="utf-8")
    (tmp_path / "Tibia.dat").write_bytes(b"1234")
    (tmp_path / "Tibia.spr").write_bytes(b"5678")

    profile = detect_asset_profile(tmp_path)

    assert profile.kind == "modern"
    assert profile.assets_dir == assets_dir
    assert profile.is_ambiguous is True
    assert profile.legacy_dat_path == tmp_path / "Tibia.dat"
    assert profile.legacy_spr_path == tmp_path / "Tibia.spr"


def test_detect_modern_assets_from_nested_single_child(tmp_path: Path) -> None:
    root = tmp_path / "wrapper"
    client = root / "client_1511"
    assets_dir = client / "assets"
    assets_dir.mkdir(parents=True)
    (assets_dir / "catalog-content.json").write_text("[]", encoding="utf-8")

    profile = detect_asset_profile(root)

    assert profile.kind == "modern"
    assert profile.assets_dir == assets_dir


def test_detect_legacy_assets_from_nested_single_child(tmp_path: Path) -> None:
    root = tmp_path / "wrapper"
    client = root / "client_1098"
    client.mkdir(parents=True)
    (client / "Tibia.dat").write_bytes(b"1234")
    (client / "Tibia.spr").write_bytes(b"5678")

    profile = detect_asset_profile(root)

    assert profile.kind == "legacy"
    assert profile.dat_path == client / "Tibia.dat"
    assert profile.spr_path == client / "Tibia.spr"
