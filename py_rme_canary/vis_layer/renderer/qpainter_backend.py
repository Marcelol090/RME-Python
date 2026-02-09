"""QPainter backend for MapDrawer rendering."""

from __future__ import annotations

from collections.abc import Callable

from PyQt6.QtCore import QRect
from PyQt6.QtGui import QColor, QPainter, QPen, QPixmap


def _color_from_id(sprite_id: int) -> QColor:
    v = int(sprite_id) & 0xFFFFFFFF
    r = (v * 2654435761) & 0xFF
    g = (v * 2246822519) & 0xFF
    b = (v * 3266489917) & 0xFF

    def clamp(c: int) -> int:
        return 48 + (int(c) % 160)

    return QColor(clamp(r), clamp(g), clamp(b))


class QPainterRenderBackend:
    """RenderBackend implementation that draws using QPainter."""

    def __init__(
        self,
        painter: QPainter,
        *,
        target_rect: QRect,
        sprite_lookup: Callable[[int, int], QPixmap | None],
        indicator_lookup: Callable[[str, int], QPixmap | None] | None = None,
    ) -> None:
        self._painter = painter
        self._target_rect = target_rect
        self._sprite_lookup = sprite_lookup
        self._indicator_lookup = indicator_lookup
        self._sprite_frame_cache: dict[tuple[int, int], QPixmap | None] = {}
        self._indicator_frame_cache: dict[tuple[str, int], QPixmap | None] = {}

    def clear(self, r: int, g: int, b: int, a: int = 255) -> None:
        self._painter.fillRect(self._target_rect, QColor(int(r), int(g), int(b), int(a)))

    def draw_tile_color(self, x: int, y: int, size: int, r: int, g: int, b: int, a: int = 255) -> None:
        rect = QRect(int(x), int(y), int(size), int(size))
        self._painter.fillRect(rect, QColor(int(r), int(g), int(b), int(a)))

    def draw_tile_sprite(self, x: int, y: int, size: int, sprite_id: int) -> None:
        key = (int(sprite_id), int(size))
        if key not in self._sprite_frame_cache:
            self._sprite_frame_cache[key] = self._sprite_lookup(int(sprite_id), int(size))
        pm = self._sprite_frame_cache.get(key)
        if pm is None or pm.isNull():
            rect = QRect(int(x), int(y), int(size), int(size))
            self._painter.fillRect(rect, _color_from_id(int(sprite_id)))
            return
        self._painter.drawPixmap(int(x), int(y), pm)

    def draw_grid_line(self, x0: int, y0: int, x1: int, y1: int, r: int, g: int, b: int, a: int = 255) -> None:
        pen = QPen(QColor(int(r), int(g), int(b), int(a)))
        self._painter.setPen(pen)
        self._painter.drawLine(int(x0), int(y0), int(x1), int(y1))

    def draw_grid_rect(self, x: int, y: int, w: int, h: int, r: int, g: int, b: int, a: int = 255) -> None:
        pen = QPen(QColor(int(r), int(g), int(b), int(a)))
        self._painter.setPen(pen)
        self._painter.drawRect(int(x), int(y), int(w), int(h))

    def draw_selection_rect(self, x: int, y: int, w: int, h: int, r: int, g: int, b: int, a: int = 255) -> None:
        pen = QPen(QColor(int(r), int(g), int(b), int(a)))
        pen.setWidth(2)
        self._painter.setPen(pen)
        self._painter.drawRect(int(x), int(y), int(w), int(h))

    def draw_indicator_icon(self, x: int, y: int, indicator_type: str, size: int) -> None:
        if self._indicator_lookup is None:
            return
        key = (str(indicator_type), int(size))
        if key not in self._indicator_frame_cache:
            self._indicator_frame_cache[key] = self._indicator_lookup(str(indicator_type), int(size))
        pm = self._indicator_frame_cache.get(key)
        if pm is None or pm.isNull():
            return
        self._painter.drawPixmap(int(x), int(y), pm)

    def draw_text(self, x: int, y: int, text: str, r: int, g: int, b: int, a: int = 255) -> None:
        self._painter.setPen(QPen(QColor(int(r), int(g), int(b), int(a))))
        self._painter.drawText(int(x), int(y), str(text))

    def draw_shade_overlay(self, x: int, y: int, w: int, h: int, alpha: int) -> None:
        rect = QRect(int(x), int(y), int(w), int(h))
        self._painter.fillRect(rect, QColor(0, 0, 0, int(alpha)))
