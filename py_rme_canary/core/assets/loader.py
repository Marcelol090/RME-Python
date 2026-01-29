from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Protocol

from py_rme_canary.core.assets.appearances_dat import (
    AppearanceIndex,
    AppearancesDatError,
    load_appearances_dat,
)
from py_rme_canary.core.assets.asset_profile import AssetProfile, detect_asset_profile
from py_rme_canary.core.assets.legacy_dat_spr import LegacySpriteArchive
from py_rme_canary.core.assets.sprite_appearances import (
    SpriteAppearances,
    SpriteAppearancesError,
    resolve_assets_dir,
)
from py_rme_canary.core.memory_guard import MemoryGuard, default_memory_guard


class SpriteProvider(Protocol):
    def get_sprite_rgba(self, sprite_id: int) -> tuple[int, int, bytes]:
        """Return sprite pixel data (w, h, BGRA) by sprite id."""


@dataclass(slots=True)
class LoadedAssets:
    profile: AssetProfile
    sprite_assets: SpriteProvider
    appearance_assets: AppearanceIndex | None = None
    appearance_error: str | None = None
    sheet_count: int | None = None
    sprite_count: int | None = None


def load_assets_from_path(
    path: str | Path,
    *,
    memory_guard: MemoryGuard | None = None,
) -> LoadedAssets:
    """Detect the asset profile and load the matching sprite/appearance data."""

    profile = detect_asset_profile(path)
    return load_assets_from_profile(profile, memory_guard=memory_guard)


def load_assets_from_profile(
    profile: AssetProfile,
    *,
    memory_guard: MemoryGuard | None = None,
) -> LoadedAssets:
    """Load sprites and appearance metadata for the provided asset profile."""

    guard = memory_guard or default_memory_guard()
    if profile.kind == "modern":
        assets_dir = resolve_assets_dir(profile.assets_dir or profile.root)
        sprites = SpriteAppearances(assets_dir=assets_dir, memory_guard=guard)
        sprites.load_catalog_content(load_data=False)
        appearance_assets: AppearanceIndex | None = None
        appearance_error: str | None = None
        if profile.appearances_path is not None:
            try:
                appearance_assets = load_appearances_dat(profile.appearances_path)
            except AppearancesDatError as exc:
                appearance_error = str(exc)
        return LoadedAssets(
            profile=profile,
            sprite_assets=sprites,
            appearance_assets=appearance_assets,
            appearance_error=appearance_error,
            sheet_count=len(sprites.sheets),
        )

    if profile.kind == "legacy":
        legacy = LegacySpriteArchive(
            dat_path=profile.dat_path or profile.root,
            spr_path=profile.spr_path or profile.root,
            memory_guard=guard,
        )
        return LoadedAssets(
            profile=profile,
            sprite_assets=legacy,
            sheet_count=None,
            sprite_count=legacy.sprite_count,
        )

    raise SpriteAppearancesError(f"Unsupported asset profile kind: {profile.kind}")
