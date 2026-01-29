from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QMouseEvent, QPaintEvent, QPainter
from PyQt6.QtWidgets import QWidget

from py_rme_canary.vis_layer.ui.helpers import qcolor_from_id

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


@dataclass(slots=True)
class MinimapClick:
    x: int
    y: int
    z: int


class MinimapWidget(QWidget):
    def __init__(self, parent: QWidget | None = None, *, editor: "QtMapEditor") -> None:
        super().__init__(parent)
        self._editor = editor
        self.setMinimumSize(180, 180)
        self.setMouseTracking(True)

    def _get_map(self) -> "GameMap" | None:
        return getattr(self._editor, "map", None)

    def _get_viewport_z(self) -> int:
        viewport = getattr(self._editor, "viewport", None)
        if viewport is None:
            return 7
        return int(getattr(viewport, "z", 7))

    def _map_size(self) -> tuple[int, int]:
        game_map = self._get_map()
        if game_map is None:
            return 1, 1

        header = getattr(game_map, "header", None)
        if header is None:
            return 1, 1

        w = int(getattr(header, "width", 1) or 1)
        h = int(getattr(header, "height", 1) or 1)
        return max(1, w), max(1, h)

    def _tile_at_point(self, p: QPoint) -> MinimapClick | None:
        w, h = self._map_size()
        ww = max(1, int(self.width()))
        hh = max(1, int(self.height()))

        x = int(p.x() * w / ww)
        y = int(p.y() * h / hh)
        x = max(0, min(w - 1, x))
        y = max(0, min(h - 1, y))

        z = self._get_viewport_z()

        return MinimapClick(x=x, y=y, z=z)

    def mousePressEvent(self, event: QMouseEvent) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        click = self._tile_at_point(event.position().toPoint())
        if click is None:
            return
        center_view_on = getattr(self._editor, "center_view_on", None)
        if callable(center_view_on):
            center_view_on(click.x, click.y, click.z, push_history=True)

    def paintEvent(self, _event: QPaintEvent) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)

        # Background
        p.fillRect(self.rect(), self.palette().window())

        game_map = self._get_map()
        if game_map is None:
            return
        z = self._get_viewport_z()

        map_w, map_h = self._map_size()
        ww = max(1, int(self.width()))
        hh = max(1, int(self.height()))

        # Downsample by mapping each screen pixel to a map tile.
        # This is intentionally simple and safe; performance is ok for typical sizes.
        for py in range(hh):
            y = int(py * map_h / hh)
            for px in range(ww):
                x = int(px * map_w / ww)
                t = game_map.get_tile(int(x), int(y), int(z))
                sid = None
                if t is not None:
                    ground = getattr(t, "ground", None)
                    if ground is not None:
                        sid = int(getattr(ground, "id", 0))
                    else:
                        items = getattr(t, "items", None) or []
                        if items:
                            sid = int(getattr(items[-1], "id", 0))

                if sid is None:
                    continue

                p.setPen(qcolor_from_id(int(sid)))
                p.drawPoint(px, py)

        # Viewport rectangle
        viewport = getattr(self._editor, "viewport", None)
        canvas = getattr(self._editor, "canvas", None)
        if viewport is None or canvas is None:
            return

        tile_px = max(1, int(getattr(viewport, "tile_px", 16)))
        cols = max(1, int(canvas.width()) // tile_px)
        rows = max(1, int(canvas.height()) // tile_px)
        ox = int(getattr(viewport, "origin_x", 0))
        oy = int(getattr(viewport, "origin_y", 0))

        rx = int(ox * ww / map_w)
        ry = int(oy * hh / map_h)
        rw = int(cols * ww / map_w)
        rh = int(rows * hh / map_h)

        p.setPen(self.palette().highlight().color())
        p.drawRect(rx, ry, max(1, rw), max(1, rh))
