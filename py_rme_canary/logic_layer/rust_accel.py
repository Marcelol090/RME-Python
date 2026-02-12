from __future__ import annotations

import sys
import zlib
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


# ---------------------------------------------------------------------------
# 1. Spawn entry names at cursor (existing)
# ---------------------------------------------------------------------------

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


# ---------------------------------------------------------------------------
# 2. FNV-1a 64-bit hash  (NEW)
# ---------------------------------------------------------------------------

# Python constants (same as sprite_hash.py)
_FNV_OFFSET_BASIS_64: int = 0xCBF29CE484222325
_FNV_PRIME_64: int = 0x100000001B3


def _python_fnv1a_64(data: bytes) -> int:
    """Pure Python FNV-1a 64-bit hash."""
    if not data:
        return _FNV_OFFSET_BASIS_64
    hash_value = _FNV_OFFSET_BASIS_64
    for byte in data:
        hash_value ^= byte
        hash_value = (hash_value * _FNV_PRIME_64) & 0xFFFFFFFFFFFFFFFF
    return hash_value


def fnv1a_64(data: bytes) -> int:
    """FNV-1a 64-bit hash — uses Rust backend when available (100-200× faster)."""
    backend = _import_backend()
    if backend is not None:
        fn: Callable[..., Any] | None = getattr(backend, "fnv1a_64_hash", None)
        if fn is not None:
            try:
                return int(fn(data))
            except Exception:
                pass
    return _python_fnv1a_64(data)


def sprite_hash(pixel_data: bytes, width: int, height: int) -> int:
    """FNV-1a hash of sprite with dimensions — uses Rust backend when available."""
    backend = _import_backend()
    if backend is not None:
        fn: Callable[..., Any] | None = getattr(backend, "sprite_hash", None)
        if fn is not None:
            try:
                return int(fn(pixel_data, width, height))
            except Exception:
                pass
    # Fallback: prepend dimensions + hash
    dimension_bytes = width.to_bytes(4, "little") + height.to_bytes(4, "little")
    return _python_fnv1a_64(dimension_bytes + pixel_data)


# ---------------------------------------------------------------------------
# 3. Minimap pixel buffer rendering  (NEW)
# ---------------------------------------------------------------------------

def _python_render_minimap_buffer(
    tile_colors: list[tuple[int, int, int, int]],
    tiles_x: int,
    tiles_y: int,
    tile_size: int,
    bg_r: int,
    bg_g: int,
    bg_b: int,
) -> bytearray:
    """Pure Python minimap pixel buffer renderer."""
    img_w = tiles_x * tile_size
    img_h = tiles_y * tile_size
    total = img_w * img_h * 3

    buf = bytearray(total)
    # Fill background
    for i in range(0, total, 3):
        buf[i] = bg_r
        buf[i + 1] = bg_g
        buf[i + 2] = bg_b

    ts = tile_size
    for idx, (r, g, b, a) in enumerate(tile_colors):
        if a == 0:
            continue
        tx = idx % tiles_x
        ty = idx // tiles_x
        px_base = tx * ts
        py_base = ty * ts

        for oy in range(ts):
            row_start = ((py_base + oy) * img_w + px_base) * 3
            if row_start + ts * 3 > total:
                break
            for ox in range(ts):
                off = row_start + ox * 3
                buf[off] = r
                buf[off + 1] = g
                buf[off + 2] = b

    return buf


def render_minimap_buffer(
    tile_colors: list[tuple[int, int, int, int]],
    tiles_x: int,
    tiles_y: int,
    tile_size: int,
    bg_r: int,
    bg_g: int,
    bg_b: int,
) -> bytearray | bytes:
    """Render minimap pixel buffer — uses Rust backend when available (50-100× faster)."""
    backend = _import_backend()
    if backend is not None:
        fn: Callable[..., Any] | None = getattr(backend, "render_minimap_buffer", None)
        if fn is not None:
            try:
                result = fn(tile_colors, tiles_x, tiles_y, tile_size, bg_r, bg_g, bg_b)
                if isinstance(result, (bytes, bytearray)):
                    return result
            except Exception:
                pass
    return _python_render_minimap_buffer(tile_colors, tiles_x, tiles_y, tile_size, bg_r, bg_g, bg_b)


# ---------------------------------------------------------------------------
# 4. PNG IDAT assembly  (NEW)
# ---------------------------------------------------------------------------

def _python_assemble_png_idat(
    image_data: bytearray | bytes,
    width: int,
    height: int,
) -> bytes:
    """Pure Python PNG IDAT assembly: add filter bytes + zlib compress."""
    row_bytes = width * 3
    raw = b""
    for y in range(height):
        raw += b"\x00"  # Filter byte = None
        row_start = y * row_bytes
        raw += bytes(image_data[row_start: row_start + row_bytes])
    return zlib.compress(raw, level=6)


def assemble_png_idat(
    image_data: bytearray | bytes,
    width: int,
    height: int,
) -> bytes:
    """Assemble PNG IDAT data — uses Rust backend when available (10-30× faster)."""
    backend = _import_backend()
    if backend is not None:
        fn: Callable[..., Any] | None = getattr(backend, "assemble_png_idat", None)
        if fn is not None:
            try:
                result = fn(bytes(image_data), width, height)
                if isinstance(result, (bytes, bytearray)):
                    return bytes(result)
            except Exception:
                pass
    return _python_assemble_png_idat(image_data, width, height)


# ---------------------------------------------------------------------------
# 5. Position Deduplication (NEW)
# ---------------------------------------------------------------------------

def _python_dedupe_positions(positions: list[tuple[int, int, int]]) -> list[tuple[int, int, int]]:
    """Pure Python position deduplication (order-preserving)."""
    seen: set[tuple[int, int, int]] = set()
    out: list[tuple[int, int, int]] = []
    for px, py, pz in positions:
        key = (int(px), int(py), int(pz))
        if key in seen:
            continue
        seen.add(key)
        out.append(key)
    return out


def dedupe_positions(positions: list[tuple[int, int, int]]) -> list[tuple[int, int, int]]:
    """Deduplicate positions — uses Rust backend when available."""
    backend = _import_backend()
    if backend is not None:
        fn: Callable[..., Any] | None = getattr(backend, "dedupe_positions", None)
        if fn is not None:
            try:
                result = fn(positions)
                if isinstance(result, list):
                    return result
            except Exception:
                pass
    return _python_dedupe_positions(positions)
