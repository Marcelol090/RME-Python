from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from py_rme_canary.core.assets.appearances_dat import resolve_appearances_path
from py_rme_canary.core.assets.sprite_appearances import SpriteAppearancesError, resolve_assets_dir


class AssetProfileError(ValueError):
    """Raised when client assets cannot be resolved cleanly."""


@dataclass(frozen=True, slots=True)
class AssetProfile:
    kind: str  # "modern" or "legacy"
    root: Path
    assets_dir: Path | None = None
    appearances_path: Path | None = None
    dat_path: Path | None = None
    spr_path: Path | None = None

    def describe(self) -> str:
        if self.kind == "modern":
            ad = str(self.assets_dir) if self.assets_dir is not None else "?"
            ap = str(self.appearances_path) if self.appearances_path is not None else "missing"
            return f"modern assets_dir={ad} appearances={ap}"
        dp = str(self.dat_path) if self.dat_path is not None else "?"
        sp = str(self.spr_path) if self.spr_path is not None else "?"
        return f"legacy dat={dp} spr={sp}"


def detect_asset_profile(path: str | Path) -> AssetProfile:
    p = Path(path).expanduser()

    modern_assets_dir = _resolve_modern_assets_dir(p)
    legacy_paths = _resolve_legacy_paths(p)

    if modern_assets_dir is not None and legacy_paths is not None:
        raise AssetProfileError(
            "Both modern (assets/catalog-content.json) and legacy (.dat/.spr) assets were detected. "
            "Choose a specific folder (assets/ for modern or the .dat/.spr pair for legacy)."
        )

    if modern_assets_dir is not None:
        appearances_path = resolve_appearances_path(modern_assets_dir)
        return AssetProfile(
            kind="modern",
            root=modern_assets_dir,
            assets_dir=modern_assets_dir,
            appearances_path=appearances_path,
        )

    if legacy_paths is not None:
        dat_path, spr_path = legacy_paths
        return AssetProfile(
            kind="legacy",
            root=dat_path.parent,
            dat_path=dat_path,
            spr_path=spr_path,
        )

    raise AssetProfileError(
        "No supported assets found. Provide a Tibia client folder with assets/catalog-content.json "
        "or a legacy client folder containing .dat/.spr files."
    )


def _resolve_modern_assets_dir(path: Path) -> Path | None:
    try:
        resolved = resolve_assets_dir(path)
    except SpriteAppearancesError:
        return None
    return Path(resolved)


def _resolve_legacy_paths(path: Path) -> tuple[Path, Path] | None:
    p = path
    if p.is_file():
        suffix = p.suffix.lower()
        if suffix == ".spr":
            spr = p
            dat = p.with_suffix(".dat")
            if dat.exists():
                return dat, spr
            return None
        if suffix == ".dat":
            dat = p
            spr = p.with_suffix(".spr")
            if spr.exists():
                return dat, spr
            return None
        return None

    candidates = [
        ("Tibia.dat", "Tibia.spr"),
        ("items.dat", "items.spr"),
        ("client.dat", "client.spr"),
    ]
    for dat_name, spr_name in candidates:
        dat = p / dat_name
        spr = p / spr_name
        if dat.exists() and spr.exists():
            return dat, spr
    return None
