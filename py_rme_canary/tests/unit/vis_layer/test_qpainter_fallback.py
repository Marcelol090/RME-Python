from __future__ import annotations

import pytest

try:  # pragma: no cover - skip when PyQt6 is not available (e.g. headless CI)
    from PyQt6.QtCore import QRect
    from PyQt6.QtGui import QColor, QImage, QPainter
except Exception:  # pragma: no cover
    pytest.skip("PyQt6 is required for QPainter fallback test", allow_module_level=True)

from py_rme_canary.vis_layer.renderer.qpainter_backend import QPainterRenderBackend, _color_from_id


def test_qpainter_fallback_draws_placeholder_color() -> None:
    img = QImage(16, 16, QImage.Format.Format_ARGB32)
    img.fill(QColor(0, 0, 0))

    painter = QPainter(img)
    backend = QPainterRenderBackend(
        painter,
        target_rect=QRect(0, 0, 16, 16),
        sprite_lookup=lambda _sid, _size: None,
    )
    backend.draw_tile_sprite(0, 0, 16, 12345)
    painter.end()

    expected = _color_from_id(12345)
    got = QColor(img.pixelColor(8, 8))
    assert (got.red(), got.green(), got.blue()) == (expected.red(), expected.green(), expected.blue())


def test_qpainter_backend_caches_sprite_lookup_per_frame() -> None:
    img = QImage(16, 16, QImage.Format.Format_ARGB32)
    img.fill(QColor(0, 0, 0))

    calls = {"count": 0}

    def sprite_lookup(_sid: int, _size: int):
        calls["count"] += 1
        return None

    painter = QPainter(img)
    backend = QPainterRenderBackend(
        painter,
        target_rect=QRect(0, 0, 16, 16),
        sprite_lookup=sprite_lookup,
    )
    backend.draw_tile_sprite(0, 0, 16, 200)
    backend.draw_tile_sprite(0, 0, 16, 200)
    painter.end()

    assert calls["count"] == 1
