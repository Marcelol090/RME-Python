from __future__ import annotations

from dataclasses import dataclass

from PyQt6.QtGui import QColor

from py_rme_canary.logic_layer.geometry import (
    get_brush_border_offsets,
    get_brush_offsets,
    iter_brush_border_offsets,
    iter_brush_offsets,
)

__all__ = (
    "ItemProps",
    "Viewport",
    "get_brush_border_offsets",
    "get_brush_offsets",
    "iter_brush_border_offsets",
    "iter_brush_offsets",
    "qcolor_from_id",
)


def qcolor_from_id(server_id: int) -> QColor:
    v = int(server_id) & 0xFFFFFFFF
    r = (v * 2654435761) & 0xFF
    g = (v * 2246822519) & 0xFF
    b = (v * 3266489917) & 0xFF

    def clamp(c: int) -> int:
        c = int(c)
        return 48 + (c % 160)

    return QColor(clamp(r), clamp(g), clamp(b))


@dataclass(slots=True)
class Viewport:
    origin_x: int = 0
    origin_y: int = 0
    z: int = 7
    tile_px: int = 16


@dataclass(slots=True)
class ItemProps:
    pickupable: bool = False
    moveable: bool = True
    avoidable: bool = False
    hook: bool = False
