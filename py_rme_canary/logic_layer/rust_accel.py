from __future__ import annotations

import sys
from collections.abc import Callable
from typing import Any

_BACKEND_MODULE_CANDIDATES = (
    "py_rme_canary_rust",
    "rme_rust_accel",
)
_BACKEND_CACHE: Any | None = None
_BACKEND_CACHE_READY = False


def _import_backend() -> Any | None:
    global _BACKEND_CACHE
    global _BACKEND_CACHE_READY
    if _BACKEND_CACHE_READY and _BACKEND_CACHE is not None:
        return _BACKEND_CACHE
    if _BACKEND_CACHE_READY:
        for mod_name in _BACKEND_MODULE_CANDIDATES:
            module = sys.modules.get(mod_name)
            if module is not None and hasattr(module, "spawn_entry_names_at_cursor"):
                _BACKEND_CACHE = module
                return module
        return None

    for mod_name in _BACKEND_MODULE_CANDIDATES:
        try:
            module = __import__(mod_name, fromlist=["*"])
        except Exception:
            continue
        if hasattr(module, "spawn_entry_names_at_cursor"):
            _BACKEND_CACHE = module
            _BACKEND_CACHE_READY = True
            return module
    _BACKEND_CACHE_READY = True
    return None


def _python_spawn_entry_names_at_cursor(
    spawn_areas: list[object],
    *,
    entries_attr: str,
    x: int,
    y: int,
    z: int,
) -> list[str]:
    names: list[str] = []
    for area in spawn_areas:
        center = getattr(area, "center", None)
        if center is None:
            continue
        if int(getattr(center, "z", -1)) != int(z):
            continue
        dx = int(int(x) - int(getattr(center, "x", 0)))
        dy = int(int(y) - int(getattr(center, "y", 0)))
        if max(abs(dx), abs(dy)) > int(getattr(area, "radius", 0)):
            continue

        entries = getattr(area, entries_attr, ()) or ()
        for entry in entries:
            if int(getattr(entry, "dx", 0)) == dx and int(getattr(entry, "dy", 0)) == dy:
                names.append(str(getattr(entry, "name", "")))
        if names:
            break
    return names


def _build_spawn_area_payload(spawn_areas: list[object], *, entries_attr: str) -> list[dict[str, object]]:
    payload: list[dict[str, object]] = []
    for area in spawn_areas:
        center = getattr(area, "center", None)
        if center is None:
            continue
        entries_payload: list[tuple[str, int, int]] = []
        for entry in getattr(area, entries_attr, ()) or ():
            entries_payload.append(
                (
                    str(getattr(entry, "name", "")),
                    int(getattr(entry, "dx", 0)),
                    int(getattr(entry, "dy", 0)),
                )
            )

        payload.append(
            {
                "x": int(getattr(center, "x", 0)),
                "y": int(getattr(center, "y", 0)),
                "z": int(getattr(center, "z", -1)),
                "radius": int(getattr(area, "radius", 0)),
                "entries": entries_payload,
            }
        )
    return payload


def spawn_entry_names_at_cursor(
    spawn_areas: list[object],
    *,
    entries_attr: str,
    x: int,
    y: int,
    z: int,
) -> list[str]:
    backend = _import_backend()
    if backend is None:
        return _python_spawn_entry_names_at_cursor(spawn_areas, entries_attr=entries_attr, x=int(x), y=int(y), z=int(z))

    backend_fn: Callable[..., Any] | None = getattr(backend, "spawn_entry_names_at_cursor", None)
    if backend_fn is None:
        return _python_spawn_entry_names_at_cursor(spawn_areas, entries_attr=entries_attr, x=int(x), y=int(y), z=int(z))

    try:
        payload = _build_spawn_area_payload(spawn_areas, entries_attr=entries_attr)
        result = backend_fn(payload, int(x), int(y), int(z))
        if isinstance(result, list):
            return [str(value) for value in result]
    except Exception:
        pass

    return _python_spawn_entry_names_at_cursor(spawn_areas, entries_attr=entries_attr, x=int(x), y=int(y), z=int(z))
