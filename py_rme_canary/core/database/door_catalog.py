"""Door catalog helper (MVP).

Legacy RME has multiple door brushes (normal/locked/magic/quest/window/hatch).
The Python port does not (yet) have full wallbrush-driven door placement.

This module provides a best-effort, Qt-free way to choose a representative
"default" closed door id per door kind using `data/items/items.xml`.

It intentionally stays conservative:
- Only considers items with <attribute key="type" value="door"/>
- Requires that a door has a known open/closed pair (via `door_pairs`)
- Uses name-based heuristics to bucket doors into kinds

This is meant for MVP DoorBrush behavior (place a reasonable door on a wall).
"""

from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from .door_pairs import load_door_pairs
from .items_xml import ItemsXML

DOOR_KINDS: tuple[str, ...] = ("normal", "locked", "magic", "quest", "window", "hatch")


def _door_kind_for_name(name: str) -> str:
    n = (name or "").strip().lower()
    if "window" in n:
        return "window"
    if "hatch" in n:
        return "hatch"
    if "quest" in n:
        return "quest"
    if "magic" in n:
        return "magic"
    if "locked" in n:
        return "locked"
    return "normal"


def _is_closed_door(*, name: str, attrs: dict[str, str]) -> bool:
    n = (name or "").strip().lower()
    block_projectile = (attrs.get("blockProjectile") or attrs.get("blockprojectile") or "").strip().lower()
    return (block_projectile in ("1", "true", "yes", "y", "on")) or ("closed" in n)


@lru_cache(maxsize=8)
def load_default_closed_doors(items_xml_path: str | Path) -> dict[str, int]:
    """Return a mapping door_kind -> closed_door_server_id.

    If a kind cannot be resolved, it will be absent from the mapping.
    """

    p = Path(items_xml_path)
    items = ItemsXML.load(p, strict_mapping=False)
    pairs = load_door_pairs(p)

    # Pick the lowest-id closed door per kind as a stable default.
    best: dict[str, int] = {}

    for sid, it in items.items_by_server_id.items():
        if it.kind != "door":
            continue
        if int(sid) not in pairs:
            continue

        kind = _door_kind_for_name(it.name)
        if kind not in DOOR_KINDS:
            continue

        if not _is_closed_door(name=it.name, attrs=it.attributes):
            continue

        prev = best.get(kind)
        if prev is None or int(sid) < int(prev):
            best[kind] = int(sid)

    return best
