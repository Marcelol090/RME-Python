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
    legacy_dat_path: Path | None = None
    legacy_spr_path: Path | None = None
    is_ambiguous: bool = False

    def describe(self) -> str:
        if self.kind == "modern":
            ad = str(self.assets_dir) if self.assets_dir is not None else "?"
            ap = str(self.appearances_path) if self.appearances_path is not None else "missing"
            return f"modern assets_dir={ad} appearances={ap}"
        dp = str(self.dat_path) if self.dat_path is not None else "?"
        sp = str(self.spr_path) if self.spr_path is not None else "?"
        return f"legacy dat={dp} spr={sp}"


def detect_asset_profile(path: str | Path, *, prefer_kind: str | None = None) -> AssetProfile:
    p = Path(path).expanduser()

    modern_assets_dir = _resolve_modern_assets_dir(p)
    legacy_paths = _resolve_legacy_paths(p)
    if legacy_paths is None and modern_assets_dir is not None:
        # If user selected assets/ directly, allow legacy lookup from parent.
        with_parent = _resolve_legacy_paths(p.parent)
        if with_parent is not None:
            legacy_paths = with_parent

    if modern_assets_dir is not None and legacy_paths is not None:
        preferred = str(prefer_kind or "").strip().lower() or None
        if preferred == "legacy":
            dat_path, spr_path = legacy_paths
            return AssetProfile(
                kind="legacy",
                root=dat_path.parent,
                dat_path=dat_path,
                spr_path=spr_path,
                is_ambiguous=True,
            )

        appearances_path = resolve_appearances_path(modern_assets_dir)
        dat_path, spr_path = legacy_paths
        return AssetProfile(
            kind="modern",
            root=modern_assets_dir,
            assets_dir=modern_assets_dir,
            appearances_path=appearances_path,
            legacy_dat_path=dat_path,
            legacy_spr_path=spr_path,
            is_ambiguous=True,
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
        return _resolve_nested_modern_assets_dir(path)
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

    direct = _resolve_legacy_paths_in_directory(p)
    if direct is not None:
        return direct
    return _resolve_nested_legacy_paths(p)


def _resolve_nested_modern_assets_dir(path: Path) -> Path | None:
    if not path.is_dir():
        return None

    discovered: list[Path] = []
    for child in sorted(path.iterdir(), key=lambda entry: entry.name.lower()):
        if not child.is_dir():
            continue
        try:
            resolved = Path(resolve_assets_dir(child))
        except SpriteAppearancesError:
            continue
        discovered.append(resolved)

    unique: list[Path] = []
    seen: set[str] = set()
    for candidate in discovered:
        key = str(candidate.resolve())
        if key in seen:
            continue
        seen.add(key)
        unique.append(candidate)

    if len(unique) == 1:
        return unique[0]
    return None


def _resolve_nested_legacy_paths(path: Path) -> tuple[Path, Path] | None:
    if not path.is_dir():
        return None

    discovered: list[tuple[Path, Path]] = []
    for child in sorted(path.iterdir(), key=lambda entry: entry.name.lower()):
        if not child.is_dir():
            continue
        legacy = _resolve_legacy_paths_in_directory(child)
        if legacy is None:
            continue
        discovered.append(legacy)

    unique: list[tuple[Path, Path]] = []
    seen: set[tuple[str, str]] = set()
    for dat_path, spr_path in discovered:
        key = (str(dat_path.resolve()), str(spr_path.resolve()))
        if key in seen:
            continue
        seen.add(key)
        unique.append((dat_path, spr_path))

    if len(unique) == 1:
        return unique[0]
    return None


def _resolve_legacy_paths_in_directory(path: Path) -> tuple[Path, Path] | None:
    candidates = [
        ("Tibia.dat", "Tibia.spr"),
        ("items.dat", "items.spr"),
        ("client.dat", "client.spr"),
    ]
    for dat_name, spr_name in candidates:
        dat = path / dat_name
        spr = path / spr_name
        if dat.exists() and spr.exists():
            return dat, spr
    return None
