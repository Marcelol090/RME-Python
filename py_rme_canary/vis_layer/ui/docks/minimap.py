from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from PyQt6.QtCore import QPoint, QRectF, Qt
from PyQt6.QtGui import QColor, QFont, QMouseEvent, QPainter, QPaintEvent, QPen
from PyQt6.QtWidgets import QWidget

from py_rme_canary.vis_layer.ui.helpers import qcolor_from_id
from py_rme_canary.vis_layer.ui.theme import get_theme_manager

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


@dataclass(slots=True)
class MinimapClick:
    x: int
    y: int
    z: int


def _parse_color(color_str: str) -> QColor:
    """Parse an rgba() or hex color string to QColor."""
    s = color_str.strip()
    if s.startswith("rgba("):
        parts = s[5:-1].split(",")
        return QColor(int(parts[0]), int(parts[1]), int(parts[2]), int(float(parts[3]) * 255))
    return QColor(s)


class MinimapWidget(QWidget):
    def __init__(self, parent: QWidget | None = None, *, editor: QtMapEditor) -> None:
        super().__init__(parent)
        self._editor = editor
        self._hover_pos: QPoint | None = None
        self.setMinimumSize(180, 180)
        self.setMouseTracking(True)

    def _get_map(self) -> GameMap | None:
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

    def mouseMoveEvent(self, event: QMouseEvent) -> None:
        self._hover_pos = event.position().toPoint()
        self.update()

    def leaveEvent(self, event: object) -> None:
        self._hover_pos = None
        self.update()

    def paintEvent(self, _event: QPaintEvent) -> None:
        tm = get_theme_manager()
        c = tm.tokens["color"]

        p = QPainter(self)
        p.setRenderHint(QPainter.RenderHint.Antialiasing, False)
        p.setRenderHint(QPainter.RenderHint.SmoothPixmapTransform, False)

        # Themed background
        bg_color = _parse_color(c["surface"]["secondary"])
        p.fillRect(self.rect(), bg_color)

        game_map = self._get_map()
        if game_map is None:
            # No map — draw placeholder text
            p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
            p.setPen(QColor(_parse_color(c["text"]["disabled"])))
            p.setFont(QFont("Segoe UI", 10))
            p.drawText(self.rect(), Qt.AlignmentFlag.AlignCenter, "No map loaded")
            return

        z = self._get_viewport_z()
        map_w, map_h = self._map_size()
        ww = max(1, int(self.width()))
        hh = max(1, int(self.height()))

        # Draw tiles
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

        # Viewport rectangle — themed brand color with alpha fill
        viewport = getattr(self._editor, "viewport", None)
        canvas = getattr(self._editor, "canvas", None)
        if viewport is not None and canvas is not None:
            tile_px = max(1, int(getattr(viewport, "tile_px", 16)))
            cols = max(1, int(canvas.width()) // tile_px)
            rows = max(1, int(canvas.height()) // tile_px)
            ox = int(getattr(viewport, "origin_x", 0))
            oy = int(getattr(viewport, "origin_y", 0))

            rx = int(ox * ww / map_w)
            ry = int(oy * hh / map_h)
            rw = int(cols * ww / map_w)
            rh = int(rows * hh / map_h)

            brand = QColor(c["brand"]["primary"])
            fill = QColor(brand)
            fill.setAlpha(30)
            p.fillRect(rx, ry, max(1, rw), max(1, rh), fill)
            p.setPen(QPen(brand, 1.5))
            p.drawRect(rx, ry, max(1, rw), max(1, rh))

        # Coordinate overlay (bottom-left)
        if self._hover_pos is not None:
            click = self._tile_at_point(self._hover_pos)
            if click is not None:
                coord_text = f"x:{click.x} y:{click.y} z:{click.z}"

                p.setRenderHint(QPainter.RenderHint.Antialiasing, True)
                font = QFont("Segoe UI", 9, QFont.Weight.Bold)
                p.setFont(font)
                fm = p.fontMetrics()
                tw = fm.horizontalAdvance(coord_text) + 12
                th = fm.height() + 6

                label_rect = QRectF(4, hh - th - 4, tw, th)
                label_bg = _parse_color(c["surface"]["elevated"])
                label_bg.setAlpha(200)
                p.setPen(Qt.PenStyle.NoPen)
                p.setBrush(label_bg)
                p.drawRoundedRect(label_rect, 4, 4)

                p.setPen(QColor(c["text"]["primary"]))
                p.drawText(label_rect, Qt.AlignmentFlag.AlignCenter, coord_text)
