from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from PyQt6.QtCore import QPoint, Qt
from PyQt6.QtGui import QPainter
from PyQt6.QtWidgets import QWidget

from py_rme_canary.vis_layer.ui.helpers import qcolor_from_id

if TYPE_CHECKING:
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

    def _map_size(self) -> tuple[int, int]:
        try:
            w = int(self._editor.map.header.width)
            h = int(self._editor.map.header.height)
            return max(1, w), max(1, h)
        except Exception:
            return 1, 1

    def _tile_at_point(self, p: QPoint) -> MinimapClick | None:
        w, h = self._map_size()
        ww = max(1, int(self.width()))
        hh = max(1, int(self.height()))

        x = int(p.x() * w / ww)
        y = int(p.y() * h / hh)
        x = max(0, min(w - 1, x))
        y = max(0, min(h - 1, y))

        try:
            z = int(self._editor.viewport.z)
        except Exception:
            z = 7

        return MinimapClick(x=x, y=y, z=z)

    def mousePressEvent(self, event) -> None:
        if event.button() != Qt.MouseButton.LeftButton:
            return
        click = self._tile_at_point(event.position().toPoint())
        if click is None:
            return
        try:
            self._editor.center_view_on(click.x, click.y, click.z, push_history=True)
        except Exception:
            pass

    def paintEvent(self, _event) -> None:
        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)

        # Background
        p.fillRect(self.rect(), self.palette().window())

        try:
            game_map = self._editor.map
            z = int(self._editor.viewport.z)
        except Exception:
            return

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
                try:
                    if t is not None:
                        if getattr(t, "ground", None) is not None:
                            sid = int(t.ground.id)
                        else:
                            items = getattr(t, "items", None) or []
                            if items:
                                sid = int(items[-1].id)
                except Exception:
                    sid = None

                if sid is None:
                    continue

                p.setPen(qcolor_from_id(int(sid)))
                p.drawPoint(px, py)

        # Viewport rectangle
        try:
            tile_px = max(1, int(self._editor.viewport.tile_px))
            cols = max(1, int(self._editor.canvas.width()) // tile_px)
            rows = max(1, int(self._editor.canvas.height()) // tile_px)
            ox = int(self._editor.viewport.origin_x)
            oy = int(self._editor.viewport.origin_y)

            rx = int(ox * ww / map_w)
            ry = int(oy * hh / map_h)
            rw = int(cols * ww / map_w)
            rh = int(rows * hh / map_h)

            p.setPen(self.palette().highlight().color())
            p.drawRect(rx, ry, max(1, rw), max(1, rh))
        except Exception:
            pass
