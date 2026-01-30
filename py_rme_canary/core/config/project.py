from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class MapMetadata:
    """Detected or declared metadata for an OTBM map."""

    engine: str = "unknown"
    otbm_version: int = 0
    client_version: int = 0
    source: str = "unknown"  # project|sniff|unknown


@dataclass(frozen=True, slots=True)
class ProjectDefinitions:
    items_otb: str | None = None
    items_xml: str | None = None


@dataclass(frozen=True, slots=True)
class MapProject:
    project_name: str
    engine: str
    client_version: int
    map_file: str
    definitions: ProjectDefinitions


class ProjectError(ValueError):
    pass


def _as_int(value: Any, *, field: str) -> int:
    try:
        return int(value)
    except Exception as e:
        raise ProjectError(f"Invalid {field}: expected int") from e


def load_project_json(project_path: str | Path, *, allow_missing_map_file: bool = False) -> MapProject:
    """Load the explicit project wrapper JSON.

    Supports two forms:
    1) Full project file with `map_file`.
    2) Sidecar JSON next to an `.otbm` where `map_file` is omitted.
    """

    p = Path(project_path)
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
    except FileNotFoundError as e:
        raise ProjectError(f"Project file not found: {p}") from e
    except json.JSONDecodeError as e:
        raise ProjectError(f"Invalid JSON in project file: {p}") from e

    if not isinstance(data, dict):
        raise ProjectError("Project JSON must be an object")

    # Support both:
    # - Flat schema: {engine, client_version, map_file, definitions}
    # - Nested schema: {metadata: {engine, client_version, ...}, map_file, definitions}
    # The nested form exists to mirror legacy tooling patterns where map metadata
    # is treated separately from project bookkeeping.
    meta = data.get("metadata")
    if meta is not None and not isinstance(meta, dict):
        raise ProjectError("Project JSON field 'metadata' must be an object")

    project_name = str(data.get("project_name") or "")

    engine_raw = meta.get("engine") if isinstance(meta, dict) and meta.get("engine") is not None else data.get("engine")
    engine = str(engine_raw or "unknown").strip().lower()

    client_version_raw = (
        meta.get("client_version")
        if isinstance(meta, dict) and meta.get("client_version") is not None
        else data.get("client_version")
    )
    client_version = _as_int(client_version_raw or 0, field="client_version")

    map_file = data.get("map_file")
    if map_file is None and isinstance(meta, dict):
        map_file = meta.get("map_file")
    if map_file is None:
        if allow_missing_map_file:
            map_file = ""
        else:
            raise ProjectError("Project JSON missing required field: map_file")
    map_file = str(map_file)

    defs = data.get("definitions") or {}
    if not isinstance(defs, dict):
        raise ProjectError("Project JSON field 'definitions' must be an object")

    definitions = ProjectDefinitions(
        items_otb=(str(defs.get("items_otb")) if defs.get("items_otb") else None),
        items_xml=(str(defs.get("items_xml")) if defs.get("items_xml") else None),
    )

    return MapProject(
        project_name=project_name,
        engine=engine,
        client_version=int(client_version),
        map_file=map_file,
        definitions=definitions,
    )


def find_project_for_otbm(otbm_path: str | Path) -> Path | None:
    """Find a wrapper JSON for a selected `.otbm`.

    Priority:
    - `<map>.json` (sidecar)
    - `map_project.json` in the same directory
    """

    p = Path(otbm_path)
    if p.suffix.lower() == ".json":
        return p

    sidecar = p.with_suffix(".json")
    if sidecar.exists():
        return sidecar

    proj = p.parent / "map_project.json"
    if proj.exists():
        return proj

    return None


def resolve_map_file(project: MapProject, *, project_path: str | Path, fallback_otbm: str | Path) -> Path:
    """Resolve the actual OTBM path from the project wrapper."""

    base = Path(project_path).parent
    if project.map_file:
        return (base / project.map_file).resolve()
    return Path(fallback_otbm).resolve()


def normalize_engine(engine: str) -> str:
    e = (engine or "").strip().lower()
    if e in ("canary", "otservbr", "opentibia-canary"):
        return "canary"
    if e in ("tfs", "forgottenserver", "theforgottenserver", "otx"):
        return "tfs"
    if not e:
        return "unknown"
    return e
