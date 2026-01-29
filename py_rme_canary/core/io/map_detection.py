from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from py_rme_canary.core.constants import MAGIC_OTBM, MAGIC_OTMM


@dataclass(frozen=True, slots=True)
class MapDetection:
    kind: str  # otbm|project_json|canary_json|otml_xml|unknown
    engine: str  # tfs|canary|unknown
    reason: str


class MapDetectionError(ValueError):
    pass


def detect_map_file(path: str | Path) -> MapDetection:
    """Detect map format and (best-effort) engine.

    Rules (legacy-first):
    - OTBM: check binary magic (first 4 bytes == 'OTBM')
    - JSON: parse; if looks like project wrapper -> project_json (engine from metadata/engine)
            elif metadata.engine == 'canary' -> canary_json
            else -> unknown
    - XML/OTML: parse root tag; if <map> -> otml_xml (engine=tfs)
    """

    p = Path(path)
    suffix = p.suffix.lower()

    # Fast-path by signature for binary.
    if suffix in (".otbm", ".otmm"):
        with p.open("rb") as f:
            magic = f.read(4)
        if magic == MAGIC_OTBM:
            return MapDetection(kind="otbm", engine="unknown", reason="OTBM magic")
        if magic == MAGIC_OTMM:
            return MapDetection(kind="otmm", engine="unknown", reason="OTMM magic")
        return MapDetection(kind="unknown", engine="unknown", reason=f"Unexpected magic {magic!r}")

    if suffix == ".json":
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
        except Exception as e:
            return MapDetection(kind="unknown", engine="unknown", reason=f"Invalid JSON: {e}")

        if not isinstance(data, dict):
            return MapDetection(kind="unknown", engine="unknown", reason="JSON is not an object")

        meta = data.get("metadata")
        meta_engine = _read_engine(meta)
        flat_engine = _normalize_engine(str(data.get("engine") or ""))
        engine = meta_engine or flat_engine or "unknown"

        if _looks_like_project_wrapper(data):
            return MapDetection(kind="project_json", engine=engine, reason="Project wrapper schema")

        if meta_engine == "canary":
            return MapDetection(kind="canary_json", engine="canary", reason="metadata.engine=canary")

        return MapDetection(kind="unknown", engine=engine or "unknown", reason="Unknown JSON schema")

    if suffix in (".otml", ".xml"):
        root = _read_xml_root_tag(p)
        if root == "map":
            # Classic OTML maps are typically TFS ecosystem.
            return MapDetection(kind="otml_xml", engine="tfs", reason="XML root <map>")
        if root:
            return MapDetection(kind="unknown", engine="unknown", reason=f"XML root <{root}>")
        return MapDetection(kind="unknown", engine="unknown", reason="Invalid XML")

    # Unknown extension: attempt OTBM magic (user may pass without extension)
    try:
        with p.open("rb") as f:
            magic = f.read(4)
        if magic == MAGIC_OTBM:
            return MapDetection(kind="otbm", engine="unknown", reason="OTBM magic (no ext)")
    except Exception:
        pass

    return MapDetection(kind="unknown", engine="unknown", reason="Unsupported extension")


def _looks_like_project_wrapper(data: dict[str, Any]) -> bool:
    if "definitions" in data:
        return True
    meta = data.get("metadata")
    if isinstance(meta, dict) and "engine" in meta and ("map_file" in data or "map_file" in meta):
        # Could still be a Canary map JSON, but wrapper is the only JSON we support for now.
        # Use map_file as a stronger signal.
        return True
    return "map_file" in data


def _read_engine(meta: Any) -> str | None:
    if not isinstance(meta, dict):
        return None
    v = meta.get("engine")
    if v is None:
        return None
    return _normalize_engine(str(v)) or None


def _normalize_engine(engine: str) -> str:
    e = (engine or "").strip().lower()
    if e in ("canary", "opentibia-canary", "otservbr", "opentibiabr"):
        return "canary"
    if e in ("tfs", "forgottenserver", "theforgottenserver"):
        return "tfs"
    return e


def _read_xml_root_tag(path: Path) -> str:
    # Minimal root-tag scan: avoids full XML parsing (fast and robust enough for detection).
    try:
        text = path.read_text(encoding="utf-8", errors="ignore")
    except Exception:
        return ""

    i = 0
    n = len(text)
    while i < n:
        lt = text.find("<", i)
        if lt == -1:
            return ""
        # Skip XML decl and comments
        if text.startswith("<?", lt):
            end = text.find("?>", lt + 2)
            i = (end + 2) if end != -1 else (lt + 2)
            continue
        if text.startswith("<!--", lt):
            end = text.find("-->", lt + 4)
            i = (end + 3) if end != -1 else (lt + 4)
            continue
        if lt + 1 < n and text[lt + 1] in ("/", "!", "?"):
            i = lt + 2
            continue

        # Read tag name
        j = lt + 1
        while j < n and text[j].isspace():
            j += 1
        k = j
        while k < n and (text[k].isalnum() or text[k] in ("_", ":", "-")):
            k += 1
        return text[j:k].strip().lower()

    return ""
