"""Asset loading and management."""

from __future__ import annotations

from py_rme_canary.core.assets.creatures_loader import (
    CreatureDatabase,
    CreatureDefinition,
    load_all_creatures,
    load_creatures_xml,
)

__all__ = [
    "CreatureDatabase",
    "CreatureDefinition",
    "load_all_creatures",
    "load_creatures_xml",
]
