"""XML parsing helpers (modularized).

Keep this package `__init__` lightweight.

Several modules import `py_rme_canary.core.io.xml.base` (a submodule). Importing a
submodule first imports this package, so importing heavy wrappers here can cause
circular imports.
"""

from __future__ import annotations

from typing import Any

from .base import as_bool, as_int

__all__ = ["as_bool", "as_int"]


def __getattr__(name: str) -> Any:
    # Lazy import facade exports to avoid circular imports.
    if name in {"build_houses_xml", "parse_houses_xml", "load_houses", "save_houses"}:
        from .houses import build_houses_xml, load_houses, parse_houses_xml, save_houses

        return {
            "build_houses_xml": build_houses_xml,
            "parse_houses_xml": parse_houses_xml,
            "load_houses": load_houses,
            "save_houses": save_houses,
        }[name]

    if name in {
        "parse_monster_spawns_xml",
        "parse_npc_spawns_xml",
        "load_monster_spawns",
        "load_npc_spawns",
        "save_monster_spawns",
        "save_npc_spawns",
    }:
        from .spawns import (
            load_monster_spawns,
            load_npc_spawns,
            parse_monster_spawns_xml,
            parse_npc_spawns_xml,
            save_monster_spawns,
            save_npc_spawns,
        )

        return {
            "parse_monster_spawns_xml": parse_monster_spawns_xml,
            "parse_npc_spawns_xml": parse_npc_spawns_xml,
            "load_monster_spawns": load_monster_spawns,
            "load_npc_spawns": load_npc_spawns,
            "save_monster_spawns": save_monster_spawns,
            "save_npc_spawns": save_npc_spawns,
        }[name]

    if name in {"build_zones_xml", "parse_zones_xml", "load_zones", "save_zones"}:
        from .zones import build_zones_xml, load_zones, parse_zones_xml, save_zones

        return {
            "build_zones_xml": build_zones_xml,
            "parse_zones_xml": parse_zones_xml,
            "load_zones": load_zones,
            "save_zones": save_zones,
        }[name]

    raise AttributeError(name)
