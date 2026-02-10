"""Compatibility facade for legacy imports.

Historically, tests and UI imported OTBM I/O from `py_rme_canary.core.io.otbm_loader`.
The implementation is modularized under `py_rme_canary.core.io.otbm`.

This module preserves the public API while delegating to the modular loader.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from py_rme_canary.core.config.configuration_manager import ConfigurationManager
from py_rme_canary.core.config.project import (
    MapMetadata,
    find_project_for_otbm,
    load_project_json,
    resolve_map_file,
)
from py_rme_canary.core.data.gamemap import GameMap
from py_rme_canary.core.database.id_mapper import IdMapper
from py_rme_canary.core.database.items_otb import ItemsOTB, ItemsOTBError
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
        self._memory_guard = memory_guard or default_memory_guard()
        self._unknown_item_policy = unknown_item_policy
        self._allow_unsupported_versions = allow_unsupported_versions

        self._inner = _ModularOTBMLoader(
            items_db=items_db,
            id_mapper=id_mapper,
            unknown_item_policy=self._unknown_item_policy,
            allow_unsupported_versions=self._allow_unsupported_versions,
            memory_guard=self._memory_guard,
        )

        self.last_id_mapper: IdMapper | None = None
        self.last_items_db: ItemsXML | None = None
        self.last_config: ConfigurationManager | None = None
        self.last_otbm_path: Path | None = None

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

    def load_with_detection(self, path: str, *, workspace_root: str | Path | None = None) -> GameMap:
        """Load a map with project/definition resolution.

        Priority:
        - Project wrapper JSON (sidecar or explicit)
        - Fallback sniff (repo defaults)
        """
        p = Path(path)
        project_path = p if p.suffix.lower() == ".json" else find_project_for_otbm(p)

        cfg: ConfigurationManager
        map_path: Path

        if project_path is not None:
            project = load_project_json(project_path, allow_missing_map_file=True)
            cfg = ConfigurationManager.from_project(project, project_path=project_path)
            map_path = resolve_map_file(project, project_path=project_path, fallback_otbm=p)
        else:
            md = MapMetadata(engine="unknown", client_version=0, otbm_version=0, source="sniff")
            root = Path(workspace_root) if workspace_root is not None else Path.cwd()
            cfg = ConfigurationManager.from_sniff(md, workspace_root=root)
            map_path = p

        items_db, id_mapper, warnings = _load_items_definitions(cfg)

        self.last_items_db = items_db
        self.last_id_mapper = id_mapper
        self.last_config = cfg
        self.last_otbm_path = map_path

        self._inner = _ModularOTBMLoader(
            items_db=items_db,
            id_mapper=id_mapper,
            unknown_item_policy=self._unknown_item_policy,
            allow_unsupported_versions=self._allow_unsupported_versions,
            memory_guard=self._memory_guard,
        )

        gm = self.load(str(map_path))
        try:
            md_engine = str(cfg.metadata.engine or "unknown")
            md_cv = int(cfg.metadata.client_version or 0)
            if md_engine == "unknown" and md_cv > 0:
                md_engine = ConfigurationManager.infer_engine_from_client_version(md_cv)
            md = MapMetadata(
                engine=md_engine,
                client_version=md_cv,
                otbm_version=int(getattr(gm.header, "otbm_version", 0)),
                source=str(cfg.metadata.source or "unknown"),
            )
            gm.load_report = gm.load_report or {}
            gm.load_report["metadata"] = {
                "engine": md.engine,
                "client_version": int(md.client_version),
                "otbm_version": int(md.otbm_version),
                "source": md.source,
            }
        except Exception:
            pass
        if warnings:
            self._inner.warnings.extend(warnings)
            if hasattr(gm, "load_report") and isinstance(gm.load_report, dict):
                gm.load_report.setdefault("warnings", [])
                gm.load_report["warnings"].extend(warnings)
        return gm


def _load_items_definitions(
    cfg: ConfigurationManager,
) -> tuple[ItemsXML | None, IdMapper | None, list[LoadWarning]]:
    warnings: list[LoadWarning] = []

    items_db: ItemsXML | None = None
    if cfg.definitions.items_xml is not None:
        try:
            items_db = ItemsXML.load(cfg.definitions.items_xml, strict_mapping=False)
        except Exception as e:
            warnings.append(LoadWarning(code="items_xml_error", message=str(e)))

    id_mapper: IdMapper | None = None
    if cfg.definitions.items_otb is not None:
        try:
            items_otb = ItemsOTB.load(cfg.definitions.items_otb)
            id_mapper = IdMapper.from_items_otb(items_otb)
        except ItemsOTBError as e:
            warnings.append(LoadWarning(code="items_otb_error", message=str(e)))
        except Exception as e:
            warnings.append(LoadWarning(code="items_otb_error", message=str(e)))

    if id_mapper is None and items_db is not None:
        id_mapper = IdMapper.from_items_xml(items_db)

    return items_db, id_mapper, warnings
