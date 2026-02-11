"""Antigravity Icon System — Custom QPainter-drawn icons.

All icons are generated programmatically:
  - No emoji, no external SVG files
  - Gradient fills and subtle glow effects
  - Consistent sizing and weight across the set
"""

from __future__ import annotations

import math
from functools import lru_cache

from PyQt6.QtCore import QPointF, QRectF, Qt
from PyQt6.QtGui import (
    QBrush,
    QColor,
    QIcon,
    QLinearGradient,
    QPainter,
    QPainterPath,
    QPen,
    QPixmap,
    QRadialGradient,
)

# ---------------------------------------------------------------------------
#  Canvas helpers
# ---------------------------------------------------------------------------

def _canvas(size: int) -> tuple[QPixmap, QPainter]:
    px = QPixmap(size, size)
    px.fill(QColor(0, 0, 0, 0))
    p = QPainter(px)
    p.setRenderHint(QPainter.RenderHint.Antialiasing)
    return px, p


def _done(px: QPixmap, p: QPainter) -> QIcon:
    p.end()
    return QIcon(px)


def _grad(y0: float, y1: float, c0: QColor, c1: QColor) -> QLinearGradient:
    g = QLinearGradient(0, y0, 0, y1)
    g.setColorAt(0.0, c0)
    g.setColorAt(1.0, c1)
    return g


# ---------------------------------------------------------------------------
#  Palette tab icons — Antigravity style with gradients
# ---------------------------------------------------------------------------

def icon_terrain(size: int = 20) -> QIcon:
    """3×3 grid — terrain / ground tiles."""
    px, p = _canvas(size)
    s = float(size)
    gap = s * 0.08
    cell = (s - gap * 4) / 3

    c0 = QColor(76, 175, 80)
    c1 = QColor(46, 135, 50)
    for row in range(3):
        for col in range(3):
            x = gap + col * (cell + gap)
            y = gap + row * (cell + gap)
            g = _grad(y, y + cell, c0, c1)
            p.setPen(Qt.PenStyle.NoPen)
            p.setBrush(QBrush(g))
            p.drawRoundedRect(QRectF(x, y, cell, cell), 1.5, 1.5)
    return _done(px, p)


def icon_doodad(size: int = 20) -> QIcon:
    """Leaf — decorative objects."""
    px, p = _canvas(size)
    s = float(size)
    path = QPainterPath()
    path.moveTo(s * 0.5, s * 0.9)
    path.cubicTo(s * 0.08, s * 0.55, s * 0.12, s * 0.1, s * 0.5, s * 0.08)
    path.cubicTo(s * 0.88, s * 0.1, s * 0.92, s * 0.55, s * 0.5, s * 0.9)

    g = _grad(0, s, QColor(129, 199, 132), QColor(46, 125, 50))
    p.setPen(QPen(QColor(33, 100, 40, 200), 1.2))
    p.setBrush(QBrush(g))
    p.drawPath(path)

    # Vein
    p.setPen(QPen(QColor(200, 230, 201, 140), 0.8))
    p.drawLine(QPointF(s * 0.5, s * 0.2), QPointF(s * 0.5, s * 0.78))
    p.drawLine(QPointF(s * 0.5, s * 0.45), QPointF(s * 0.32, s * 0.3))
    p.drawLine(QPointF(s * 0.5, s * 0.55), QPointF(s * 0.68, s * 0.42))
    return _done(px, p)


def icon_item(size: int = 20) -> QIcon:
    """Box — items / objects."""
    px, p = _canvas(size)
    s = float(size)
    m = s * 0.14

    g = _grad(0, s, QColor(255, 183, 77), QColor(230, 110, 0))
    p.setPen(QPen(QColor(200, 90, 0, 200), 1.2))
    p.setBrush(QBrush(g))
    body = QRectF(m, m + s * 0.12, s - 2 * m, s - 2 * m - s * 0.12)
    p.drawRoundedRect(body, 3.0, 3.0)

    # Lid highlight
    p.setPen(QPen(QColor(255, 240, 220, 160), 1.0))
    y_lid = body.y() + body.height() * 0.28
    p.drawLine(QPointF(m + 3, y_lid), QPointF(s - m - 3, y_lid))

    # Handle
    p.setPen(QPen(QColor(255, 240, 220, 120), 1.2))
    p.drawLine(QPointF(s * 0.4, body.y()), QPointF(s * 0.6, body.y()))
    return _done(px, p)


def icon_recent(size: int = 20) -> QIcon:
    """Clock — recent items."""
    px, p = _canvas(size)
    s = float(size)
    cx, cy = s / 2, s / 2
    r = s * 0.36

    # Glow
    glow = QRadialGradient(cx, cy, r * 1.5)
    glow.setColorAt(0, QColor(139, 92, 246, 15))
    glow.setColorAt(1, QColor(0, 0, 0, 0))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(glow))
    p.drawEllipse(QRectF(0, 0, s, s))

    p.setPen(QPen(QColor(160, 175, 185), 1.4))
    p.setBrush(QColor(30, 38, 48, 100))
    p.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))

    # Hands
    p.setPen(QPen(QColor(200, 210, 220), 1.5))
    p.drawLine(QPointF(cx, cy), QPointF(cx, cy - r * 0.6))
    p.setPen(QPen(QColor(167, 139, 250), 1.5))
    p.drawLine(QPointF(cx, cy), QPointF(cx + r * 0.45, cy + r * 0.1))
    return _done(px, p)


def icon_house(size: int = 20) -> QIcon:
    """House — building zones."""
    px, p = _canvas(size)
    s = float(size)

    # Roof
    roof = QPainterPath()
    roof.moveTo(s * 0.5, s * 0.08)
    roof.lineTo(s * 0.08, s * 0.48)
    roof.lineTo(s * 0.92, s * 0.48)
    roof.closeSubpath()
    g = _grad(0, s * 0.5, QColor(239, 68, 68), QColor(185, 28, 28))
    p.setPen(QPen(QColor(160, 20, 20, 180), 1.0))
    p.setBrush(QBrush(g))
    p.drawPath(roof)

    # Wall
    wall_g = _grad(s * 0.48, s * 0.92, QColor(200, 185, 175), QColor(165, 145, 130))
    p.setPen(QPen(QColor(130, 105, 90, 160), 1.0))
    p.setBrush(QBrush(wall_g))
    p.drawRect(QRectF(s * 0.18, s * 0.48, s * 0.64, s * 0.44))

    # Door
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(65, 40, 30))
    p.drawRoundedRect(QRectF(s * 0.38, s * 0.58, s * 0.24, s * 0.34), 2.5, 2.5)

    # Window
    p.setBrush(QColor(240, 220, 120, 180))
    p.drawRoundedRect(QRectF(s * 0.68, s * 0.56, s * 0.1, s * 0.1), 1.5, 1.5)
    return _done(px, p)


def icon_creature(size: int = 20) -> QIcon:
    """Paw print — creatures / monsters."""
    px, p = _canvas(size)
    s = float(size)

    g = _grad(0, s, QColor(206, 147, 216), QColor(156, 70, 180))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(g))

    # Main pad
    p.drawEllipse(QRectF(s * 0.23, s * 0.46, s * 0.54, s * 0.44))

    # Toes with individual gradients
    toes = [(0.2, 0.27), (0.4, 0.14), (0.6, 0.14), (0.8, 0.27)]
    tr = s * 0.1
    for tx, ty in toes:
        p.drawEllipse(QRectF(s * tx - tr, s * ty - tr, tr * 2, tr * 2))
    return _done(px, p)


def icon_npc(size: int = 20) -> QIcon:
    """Person — NPCs."""
    px, p = _canvas(size)
    s = float(size)

    g = _grad(0, s, QColor(120, 200, 255), QColor(60, 140, 220))
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QBrush(g))

    # Head
    hr = s * 0.14
    p.drawEllipse(QRectF(s * 0.5 - hr, s * 0.1, hr * 2, hr * 2))

    # Body
    body = QPainterPath()
    body.moveTo(s * 0.28, s * 0.42)
    body.lineTo(s * 0.72, s * 0.42)
    body.lineTo(s * 0.76, s * 0.88)
    body.lineTo(s * 0.24, s * 0.88)
    body.closeSubpath()
    p.drawPath(body)

    # Shoulder glow
    p.setBrush(QColor(180, 230, 255, 40))
    p.drawEllipse(QRectF(s * 0.3, s * 0.38, s * 0.4, s * 0.12))
    return _done(px, p)


def icon_zone(size: int = 20) -> QIcon:
    """Map region — zones."""
    px, p = _canvas(size)
    s = float(size)
    m = s * 0.12

    p.setPen(QPen(QColor(77, 182, 172), 1.4))
    p.setBrush(QColor(77, 182, 172, 30))
    p.drawRoundedRect(QRectF(m, m, s - 2 * m, s - 2 * m), 4.0, 4.0)

    # Cross-hairs
    p.setPen(QPen(QColor(77, 182, 172, 100), 0.8))
    p.drawLine(QPointF(s * 0.5, m + 3), QPointF(s * 0.5, s - m - 3))
    p.drawLine(QPointF(m + 3, s * 0.5), QPointF(s - m - 3, s * 0.5))

    # Corner marks
    p.setPen(QPen(QColor(77, 182, 172, 160), 1.2))
    d = s * 0.06
    for cx, cy in [(m, m), (s - m, m), (m, s - m), (s - m, s - m)]:
        p.drawLine(QPointF(cx - d, cy), QPointF(cx + d, cy))
        p.drawLine(QPointF(cx, cy - d), QPointF(cx, cy + d))
    return _done(px, p)


def icon_waypoint(size: int = 20) -> QIcon:
    """Map pin — waypoints."""
    px, p = _canvas(size)
    s = float(size)
    cx = s * 0.5

    pin = QPainterPath()
    pin.moveTo(cx, s * 0.9)
    pin.cubicTo(cx - s * 0.05, s * 0.55, cx - s * 0.32, s * 0.42, cx - s * 0.32, s * 0.28)
    pin.arcTo(QRectF(cx - s * 0.32, s * 0.06, s * 0.64, s * 0.44), 180, -180)
    pin.cubicTo(cx + s * 0.32, s * 0.42, cx + s * 0.05, s * 0.55, cx, s * 0.9)

    g = _grad(0, s, QColor(248, 100, 95), QColor(190, 30, 30))
    p.setPen(QPen(QColor(160, 20, 20, 180), 1.0))
    p.setBrush(QBrush(g))
    p.drawPath(pin)

    # Center dot
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(255, 255, 255, 210))
    dr = s * 0.07
    p.drawEllipse(QRectF(cx - dr, s * 0.24, dr * 2, dr * 2))
    return _done(px, p)


def icon_raw(size: int = 20) -> QIcon:
    """Gear — raw IDs."""
    px, p = _canvas(size)
    s = float(size)
    cx, cy = s / 2, s / 2
    outer_r = s * 0.4
    inner_r = s * 0.24
    teeth = 8

    path = QPainterPath()
    for i in range(teeth):
        a1 = (i / teeth) * 2 * math.pi - math.pi / 2
        a2 = ((i + 0.35) / teeth) * 2 * math.pi - math.pi / 2
        a3 = ((i + 0.5) / teeth) * 2 * math.pi - math.pi / 2
        a4 = ((i + 0.85) / teeth) * 2 * math.pi - math.pi / 2

        if i == 0:
            path.moveTo(cx + outer_r * math.cos(a1), cy + outer_r * math.sin(a1))
        else:
            path.lineTo(cx + outer_r * math.cos(a1), cy + outer_r * math.sin(a1))
        path.lineTo(cx + outer_r * math.cos(a2), cy + outer_r * math.sin(a2))
        path.lineTo(cx + inner_r * math.cos(a3), cy + inner_r * math.sin(a3))
        path.lineTo(cx + inner_r * math.cos(a4), cy + inner_r * math.sin(a4))
    path.closeSubpath()

    g = _grad(0, s, QColor(170, 170, 175), QColor(100, 100, 108))
    p.setPen(QPen(QColor(110, 110, 120, 180), 1.0))
    p.setBrush(QBrush(g))
    p.drawPath(path)

    # Center hole
    p.setPen(Qt.PenStyle.NoPen)
    p.setCompositionMode(QPainter.CompositionMode.CompositionMode_Clear)
    hole = s * 0.1
    p.drawEllipse(QRectF(cx - hole, cy - hole, hole * 2, hole * 2))
    return _done(px, p)


# ---------------------------------------------------------------------------
#  Utility icons
# ---------------------------------------------------------------------------

def icon_search(size: int = 20) -> QIcon:
    """Magnifying glass — search."""
    px, p = _canvas(size)
    s = float(size)

    r = s * 0.26
    cx, cy = s * 0.4, s * 0.38
    p.setPen(QPen(QColor(161, 161, 170, 180), 1.8))
    p.setBrush(Qt.BrushStyle.NoBrush)
    p.drawEllipse(QRectF(cx - r, cy - r, r * 2, r * 2))

    # Handle
    p.setPen(QPen(QColor(161, 161, 170, 140), 2.0))
    p.drawLine(QPointF(cx + r * 0.7, cy + r * 0.7), QPointF(s * 0.84, s * 0.84))
    return _done(px, p)


def icon_brush_size(size: int = 16) -> QIcon:
    """Diamond — brush size header."""
    px, p = _canvas(size)
    s = float(size)

    path = QPainterPath()
    path.moveTo(s * 0.5, s * 0.08)
    path.lineTo(s * 0.88, s * 0.5)
    path.lineTo(s * 0.5, s * 0.92)
    path.lineTo(s * 0.12, s * 0.5)
    path.closeSubpath()

    g = _grad(0, s, QColor(167, 139, 250), QColor(124, 58, 237))
    p.setPen(QPen(QColor(100, 40, 200, 180), 1.0))
    p.setBrush(QBrush(g))
    p.drawPath(path)

    # Inner highlight
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(255, 255, 255, 30))
    h = QPainterPath()
    h.moveTo(s * 0.5, s * 0.2)
    h.lineTo(s * 0.72, s * 0.5)
    h.lineTo(s * 0.5, s * 0.5)
    h.lineTo(s * 0.28, s * 0.5)
    h.closeSubpath()
    p.drawPath(h)
    return _done(px, p)


# ---------------------------------------------------------------------------
#  Tool icons (for ToolSelector fallback)
# ---------------------------------------------------------------------------

def icon_pointer(size: int = 22) -> QIcon:
    """Arrow cursor — select/move tool."""
    px, p = _canvas(size)
    s = float(size)

    arrow = QPainterPath()
    arrow.moveTo(s * 0.25, s * 0.12)
    arrow.lineTo(s * 0.25, s * 0.82)
    arrow.lineTo(s * 0.45, s * 0.65)
    arrow.lineTo(s * 0.7, s * 0.88)
    arrow.lineTo(s * 0.78, s * 0.78)
    arrow.lineTo(s * 0.55, s * 0.55)
    arrow.lineTo(s * 0.75, s * 0.48)
    arrow.closeSubpath()

    p.setPen(QPen(QColor(220, 220, 230, 200), 1.0))
    p.setBrush(QColor(200, 200, 210, 180))
    p.drawPath(arrow)
    return _done(px, p)


def icon_pencil(size: int = 22) -> QIcon:
    """Pencil — draw tool."""
    px, p = _canvas(size)
    s = float(size)

    # Pencil body
    body = QPainterPath()
    body.moveTo(s * 0.7, s * 0.12)
    body.lineTo(s * 0.88, s * 0.3)
    body.lineTo(s * 0.3, s * 0.88)
    body.lineTo(s * 0.12, s * 0.7)
    body.closeSubpath()

    g = _grad(0, s, QColor(167, 139, 250), QColor(124, 58, 237))
    p.setPen(QPen(QColor(100, 40, 200, 180), 1.0))
    p.setBrush(QBrush(g))
    p.drawPath(body)

    # Tip
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(255, 220, 180))
    tip = QPainterPath()
    tip.moveTo(s * 0.12, s * 0.7)
    tip.lineTo(s * 0.3, s * 0.88)
    tip.lineTo(s * 0.1, s * 0.9)
    tip.closeSubpath()
    p.drawPath(tip)
    return _done(px, p)


def icon_eraser(size: int = 22) -> QIcon:
    """Eraser tool."""
    px, p = _canvas(size)
    s = float(size)

    body = QPainterPath()
    body.moveTo(s * 0.5, s * 0.15)
    body.lineTo(s * 0.85, s * 0.5)
    body.lineTo(s * 0.5, s * 0.85)
    body.lineTo(s * 0.15, s * 0.5)
    body.closeSubpath()

    g = _grad(0, s, QColor(255, 140, 140), QColor(220, 80, 80))
    p.setPen(QPen(QColor(180, 50, 50, 180), 1.0))
    p.setBrush(QBrush(g))
    p.drawPath(body)

    # Split line
    p.setPen(QPen(QColor(255, 255, 255, 60), 1.0))
    p.drawLine(QPointF(s * 0.35, s * 0.65), QPointF(s * 0.65, s * 0.35))
    return _done(px, p)


def icon_fill(size: int = 22) -> QIcon:
    """Paint bucket — fill tool."""
    px, p = _canvas(size)
    s = float(size)

    # Bucket body
    bucket = QPainterPath()
    bucket.moveTo(s * 0.25, s * 0.35)
    bucket.lineTo(s * 0.65, s * 0.35)
    bucket.lineTo(s * 0.58, s * 0.78)
    bucket.lineTo(s * 0.22, s * 0.78)
    bucket.closeSubpath()

    g = _grad(s * 0.35, s * 0.78, QColor(100, 181, 246), QColor(50, 120, 200))
    p.setPen(QPen(QColor(40, 90, 170, 180), 1.0))
    p.setBrush(QBrush(g))
    p.drawPath(bucket)

    # Paint drip
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(139, 92, 246, 200))
    drip = QPainterPath()
    drip.moveTo(s * 0.65, s * 0.35)
    drip.cubicTo(s * 0.8, s * 0.3, s * 0.88, s * 0.45, s * 0.78, s * 0.55)
    drip.cubicTo(s * 0.7, s * 0.62, s * 0.62, s * 0.55, s * 0.65, s * 0.45)
    drip.closeSubpath()
    p.drawPath(drip)
    return _done(px, p)


def icon_select(size: int = 22) -> QIcon:
    """Dashed rectangle — selection tool."""
    px, p = _canvas(size)
    s = float(size)
    m = s * 0.18

    pen = QPen(QColor(167, 139, 250, 200), 1.5)
    pen.setDashPattern([3, 2])
    p.setPen(pen)
    p.setBrush(QColor(139, 92, 246, 15))
    p.drawRoundedRect(QRectF(m, m, s - 2 * m, s - 2 * m), 3.0, 3.0)
    return _done(px, p)


def icon_picker(size: int = 22) -> QIcon:
    """Eye dropper — color picker tool."""
    px, p = _canvas(size)
    s = float(size)

    # Dropper body
    body = QPainterPath()
    body.moveTo(s * 0.65, s * 0.15)
    body.lineTo(s * 0.85, s * 0.35)
    body.lineTo(s * 0.4, s * 0.8)
    body.lineTo(s * 0.2, s * 0.6)
    body.closeSubpath()

    p.setPen(QPen(QColor(180, 180, 190, 200), 1.0))
    p.setBrush(QColor(160, 160, 170, 150))
    p.drawPath(body)

    # Tip
    p.setPen(Qt.PenStyle.NoPen)
    p.setBrush(QColor(139, 92, 246, 220))
    tip = QPainterPath()
    tip.moveTo(s * 0.2, s * 0.6)
    tip.lineTo(s * 0.4, s * 0.8)
    tip.lineTo(s * 0.15, s * 0.88)
    tip.closeSubpath()
    p.drawPath(tip)
    return _done(px, p)


# ---------------------------------------------------------------------------
#  Convenience: palette tab icon dict
# ---------------------------------------------------------------------------

@lru_cache(maxsize=1)
def palette_tab_icons(size: int = 18) -> dict[str, QIcon]:
    """Return dict mapping palette key -> QIcon."""
    return {
        "terrain": icon_terrain(size),
        "doodad": icon_doodad(size),
        "item": icon_item(size),
        "recent": icon_recent(size),
        "house": icon_house(size),
        "creature": icon_creature(size),
        "npc": icon_npc(size),
        "zones": icon_zone(size),
        "waypoint": icon_waypoint(size),
        "raw": icon_raw(size),
    }


@lru_cache(maxsize=1)
def tool_icons(size: int = 22) -> dict[str, QIcon]:
    """Return dict mapping tool_id -> QIcon fallback."""
    return {
        "pointer": icon_pointer(size),
        "pencil": icon_pencil(size),
        "eraser": icon_eraser(size),
        "fill": icon_fill(size),
        "select": icon_select(size),
        "picker": icon_picker(size),
    }
