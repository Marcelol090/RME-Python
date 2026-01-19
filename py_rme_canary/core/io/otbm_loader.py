"""Compatibility facade for legacy imports.

Historically, tests and UI imported OTBM I/O from `py_rme_canary.core.io.otbm_loader`.
The implementation is modularized under `py_rme_canary.core.io.otbm`.

This module preserves the public API while delegating to the modular loader.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from py_rme_canary.core.data.gamemap import GameMap
from py_rme_canary.core.database.id_mapper import IdMapper
from py_rme_canary.core.database.items_xml import ItemsXML
from py_rme_canary.core.exceptions.io import HousesXmlError, SpawnXmlError, ZonesXmlError
from py_rme_canary.core.io.houses_xml import load_houses
from py_rme_canary.core.io.otbm.loader import (
    LoadWarning,
    load_game_map,
    load_game_map_with_items_db,
)
from py_rme_canary.core.io.otbm.loader import (
    OTBMLoader as _ModularOTBMLoader,
)
from py_rme_canary.core.io.spawn_xml import load_monster_spawns, load_npc_spawns
from py_rme_canary.core.io.zones_xml import load_zones
from py_rme_canary.core.memory_guard import MemoryGuard, default_memory_guard

__all__ = [
    "LoadWarning",
    "OTBMLoader",
    "load_game_map",
    "load_game_map_with_items_db",
]


def _load_external_files_into_gamemap(game_map: GameMap, *, otbm_path: Path) -> list[LoadWarning]:
    base_dir = otbm_path.parent
    h = game_map.header
    warnings: list[LoadWarning] = []

    def resolve(p: str) -> Path:
        pp = Path(p)
        return pp if pp.is_absolute() else (base_dir / pp)

    def load_one(kind: str, rel: str, loader: Callable[[Path], None]) -> None:
        if not rel:
            return
        p = resolve(rel)
        try:
            if not p.exists():
                warnings.append(LoadWarning(code="external_file_missing", message=f"Missing {kind} file: {p}"))
                return
            loader(p)
        except (SpawnXmlError, HousesXmlError, ZonesXmlError) as e:
            warnings.append(LoadWarning(code="external_parse_error", message=f"Failed to parse {kind} file {p}: {e}"))
        except Exception as e:
            warnings.append(LoadWarning(code="external_file_error", message=f"Failed to load {kind} file {p}: {e}"))

    def load_monsters(p: Path) -> None:
        game_map.monster_spawns = list(load_monster_spawns(p))

    def load_npcs(p: Path) -> None:
        game_map.npc_spawns = list(load_npc_spawns(p))

    def load_h(p: Path) -> None:
        game_map.houses = load_houses(p)

    def load_z(p: Path) -> None:
        game_map.zones = load_zones(p)

    load_one("monster spawns", h.spawnmonsterfile, load_monsters)
    load_one("npc spawns", h.spawnnpcfile, load_npcs)
    load_one("houses", h.housefile, load_h)
    load_one("zones", h.zonefile, load_z)
    return warnings


class OTBMLoader:
    """Legacy-compatible wrapper around the modular loader.

    Adds legacy behavior: auto-load external XML files referenced by the OTBM header.
    """

    def __init__(
        self,
        *,
        items_db: ItemsXML | None = None,
        id_mapper: IdMapper | None = None,
        unknown_item_policy: str = "placeholder",
        allow_unsupported_versions: bool = False,
        memory_guard: MemoryGuard | None = None,
    ) -> None:
        self._inner = _ModularOTBMLoader(
            items_db=items_db,
            id_mapper=id_mapper,
            unknown_item_policy=unknown_item_policy,
            allow_unsupported_versions=allow_unsupported_versions,
            memory_guard=memory_guard or default_memory_guard(),
        )

    @property
    def warnings(self) -> list[LoadWarning]:
        return self._inner.warnings

    def load(self, path: str) -> GameMap:
        gm = self._inner.load(path)

        ext = _load_external_files_into_gamemap(gm, otbm_path=Path(path))
        if ext:
            self._inner.warnings.extend(ext)
            if hasattr(gm, "load_report") and isinstance(gm.load_report, dict):
                gm.load_report["warnings"] = list(self._inner.warnings)

        return gm
