from __future__ import annotations

"""Shared XML parsing helpers.

These helpers were previously duplicated across `houses_xml.py`, `spawn_xml.py`,
and `zones_xml.py`.
"""


def as_int(value: str | None, default: int = 0) -> int:
    try:
        return int((value or "").strip())
    except Exception:
        return int(default)


def as_bool(value: str | None, default: bool = False) -> bool:
    v = (value or "").strip().lower()
    if v in ("1", "true", "yes", "y", "on"):
        return True
    if v in ("0", "false", "no", "n", "off"):
        return False
    return bool(default)
