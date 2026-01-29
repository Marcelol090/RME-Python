"""Sprite system utilities (legacy .dat/.spr metadata helpers)."""

from .legacy_dat import (
    LegacyDatError,
    LegacyItemSpriteInfo,
    LegacyItemSprites,
    load_legacy_item_sprites,
)

__all__ = [
    "LegacyDatError",
    "LegacyItemSpriteInfo",
    "LegacyItemSprites",
    "load_legacy_item_sprites",
]