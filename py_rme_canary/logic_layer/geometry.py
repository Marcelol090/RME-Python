from __future__ import annotations

import math
from collections.abc import Iterator
from functools import lru_cache


def _normalize_brush_shape(size: int, shape: str) -> tuple[int, str]:
    size = max(0, int(size))
    shape = (shape or "square").strip().lower()
    if shape not in ("square", "circle"):
        shape = "square"
    return size, shape


@lru_cache(maxsize=128)
def _cached_brush_offsets(size: int, shape: str) -> tuple[tuple[int, int], ...]:
    out: list[tuple[int, int]] = []
    for dy in range(-size - 1, size + 2):
        for dx in range(-size - 1, size + 2):
            if shape == "circle":
                distance = math.sqrt(float(dx * dx + dy * dy))
                if distance < float(size) + 0.005:
                    out.append((dx, dy))
            elif -size <= dx <= size and -size <= dy <= size:
                out.append((dx, dy))
    return tuple(out)


def get_brush_offsets(size: int, shape: str) -> tuple[tuple[int, int], ...]:
    """Return cached draw offsets matching legacy MapCanvas::getTilesToDraw."""
    norm_size, norm_shape = _normalize_brush_shape(size, shape)
    return _cached_brush_offsets(norm_size, norm_shape)


@lru_cache(maxsize=128)
def _cached_brush_border_offsets(size: int, shape: str) -> tuple[tuple[int, int], ...]:
    out: list[tuple[int, int]] = []
    for dy in range(-size - 1, size + 2):
        for dx in range(-size - 1, size + 2):
            if shape == "circle":
                distance = math.sqrt(float(dx * dx + dy * dy))
                if abs(distance - float(size)) < 1.5:
                    out.append((dx, dy))
            elif (abs(int(dx)) - size) < 2 and (abs(int(dy)) - size) < 2:
                out.append((dx, dy))
    return tuple(out)


def get_brush_border_offsets(size: int, shape: str) -> tuple[tuple[int, int], ...]:
    """Return cached border offsets matching legacy MapCanvas::getTilesToDraw."""
    norm_size, norm_shape = _normalize_brush_shape(size, shape)
    return _cached_brush_border_offsets(norm_size, norm_shape)


def iter_brush_offsets(size: int, shape: str) -> Iterator[tuple[int, int]]:
    """Yield (dx, dy) offsets matching legacy MapCanvas::getTilesToDraw (draw)."""
    yield from get_brush_offsets(size, shape)


def iter_brush_border_offsets(size: int, shape: str) -> Iterator[tuple[int, int]]:
    """Yield (dx, dy) offsets matching legacy MapCanvas::getTilesToDraw (tilestoborder)."""
    yield from get_brush_border_offsets(size, shape)
