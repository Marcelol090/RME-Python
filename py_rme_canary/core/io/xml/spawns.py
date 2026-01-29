"""Spawns XML I/O (new module path).

Kept as a thin wrapper over `core/io/spawn_xml.py` for compatibility.
"""

from __future__ import annotations

from py_rme_canary.core.io.spawn_xml import (
    load_monster_spawns,
    load_npc_spawns,
    parse_monster_spawns_xml,
    parse_npc_spawns_xml,
    save_monster_spawns,
    save_npc_spawns,
)

__all__ = [
    "load_monster_spawns",
    "load_npc_spawns",
    "parse_monster_spawns_xml",
    "parse_npc_spawns_xml",
    "save_monster_spawns",
    "save_npc_spawns",
]
