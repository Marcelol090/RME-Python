from __future__ import annotations

import functools
from collections.abc import Iterable
from pathlib import Path

from py_rme_canary.core.io.xml.safe import safe_etree as ET


def _default_monsters_path() -> Path:
    return Path("data") / "creatures" / "monsters.xml"


def _default_npcs_path() -> Path:
    return Path("data") / "creatures" / "npcs.xml"


def default_monsters_path() -> Path:
    return _default_monsters_path()


def default_npcs_path() -> Path:
    return _default_npcs_path()


def _parse_creature_names(xml_text: str, *, root_tag: str, child_tag: str) -> tuple[str, ...]:
    try:
        root = ET.fromstring(xml_text)
    except Exception:
        return ()

    if str(root.tag or "").strip().lower() != str(root_tag).strip().lower():
        return ()

    out: list[str] = []
    for child in list(root):
        if str(child.tag or "").strip().lower() != str(child_tag).strip().lower():
            continue
        nm = str(child.attrib.get("name", "") or "").strip()
        if not nm:
            continue
        out.append(nm)

    # Keep stable ordering (and unique) to support deterministic virtual-id mapping.
    seen: set[str] = set()
    uniq: list[str] = []
    for nm in out:
        key = nm.lower()
        if key in seen:
            continue
        seen.add(key)
        uniq.append(nm)
    return tuple(sorted(uniq, key=lambda s: s.lower()))


@functools.lru_cache(maxsize=4)
def load_monster_names(path: str | Path | None = None) -> tuple[str, ...]:
    p = _default_monsters_path() if path is None else Path(path)
    try:
        xml_text = p.read_text(encoding="utf-8")
    except Exception:
        return ()
    return _parse_creature_names(xml_text, root_tag="monsters", child_tag="monster")


@functools.lru_cache(maxsize=4)
def load_npc_names(path: str | Path | None = None) -> tuple[str, ...]:
    p = _default_npcs_path() if path is None else Path(path)
    try:
        xml_text = p.read_text(encoding="utf-8")
    except Exception:
        return ()
    return _parse_creature_names(xml_text, root_tag="npcs", child_tag="npc")


def iter_monster_names(path: str | Path | None = None) -> Iterable[str]:
    return load_monster_names(path)


def iter_npc_names(path: str | Path | None = None) -> Iterable[str]:
    return load_npc_names(path)


def clear_creature_name_cache() -> None:
    load_monster_names.cache_clear()
    load_npc_names.cache_clear()
