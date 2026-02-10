"""Asset loading and management."""

from __future__ import annotations

from py_rme_canary.core.assets.appearances_dat import (
    AppearanceFlags,
    AppearanceFlagLight,
    AppearanceFlagMarket,
    AppearanceIndex,
    AppearancesDatError,
    load_appearances_dat,
    resolve_appearances_path,
)
from py_rme_canary.core.assets.creatures_loader import (
    CreatureDatabase,
    CreatureDefinition,
    load_all_creatures,
    load_creatures_xml,
)

__all__ = [
    "AppearanceFlags",
    "AppearanceFlagLight",
    "AppearanceFlagMarket",
    "AppearanceIndex",
    "AppearancesDatError",
    "CreatureDatabase",
    "CreatureDefinition",
    "load_all_creatures",
    "load_appearances_dat",
    "load_creatures_xml",
    "resolve_appearances_path",
]
