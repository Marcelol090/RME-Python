from __future__ import annotations

import math
from collections.abc import Iterator


def iter_brush_offsets(size: int, shape: str) -> Iterator[tuple[int, int]]:
    """Yield (dx, dy) offsets matching legacy MapCanvas::getTilesToDraw (draw)."""

    size = max(0, int(size))
    shape = (shape or "square").strip().lower()

    for dy in range(-size - 1, size + 2):
        for dx in range(-size - 1, size + 2):
            if shape == "circle":
                distance = math.sqrt(float(dx * dx + dy * dy))
                if distance < float(size) + 0.005:
                    yield (dx, dy)
            elif -size <= dx <= size and -size <= dy <= size:
                yield (dx, dy)


def iter_brush_border_offsets(size: int, shape: str) -> Iterator[tuple[int, int]]:
    """Yield (dx, dy) offsets matching legacy MapCanvas::getTilesToDraw (tilestoborder)."""

    size = max(0, int(size))
    shape = (shape or "square").strip().lower()

    for dy in range(-size - 1, size + 2):
        for dx in range(-size - 1, size + 2):
            if shape == "circle":
                distance = math.sqrt(float(dx * dx + dy * dy))
                if abs(distance - float(size)) < 1.5:
                    yield (dx, dy)
            elif (abs(int(dx)) - size) < 2 and (abs(int(dy)) - size) < 2:
                yield (dx, dy)
