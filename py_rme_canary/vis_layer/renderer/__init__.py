"""
Renderer package: Modern rendering backends for py_rme_canary.

This package provides:
- RenderModel: Qt-free data structures for draw commands
- OpenGLCanvas: Hardware-accelerated rendering widget
- MapDrawer: Coordinates rendering based on DrawingOptions
"""

import contextlib

from .render_model import (
    THEME_COLORS,
    Color,
    DrawCommand,
    DrawCommandType,
    LayerType,
    Rect,
    RenderFrame,
)

# Heavy Qt imports are optional to keep MapDrawer usable in headless/unit tests.
try:
    from .opengl_canvas import (
        OpenGLCanvasWidget,
        is_opengl_available,
    )
except Exception:  # pragma: no cover - fallback for headless envs without PyQt6/OpenGL
    try:
        from PyQt6.QtCore import QSize
        from PyQt6.QtGui import QColor, QPainter
        from PyQt6.QtWidgets import QWidget
    except Exception:  # pragma: no cover

        class OpenGLCanvasWidget:  # type: ignore[no-redef]
            def __init__(self, *args, **kwargs) -> None:
                raise ImportError("PyQt6/OpenGL not available")

        def is_opengl_available() -> bool:
            return False
    else:
        from .qpainter_backend import QPainterRenderBackend

        class OpenGLCanvasWidget(QWidget):  # type: ignore[no-redef]
            """Fallback QPainter canvas when OpenGL canvas cannot be imported."""

            def __init__(self, parent: QWidget | None, editor) -> None:  # type: ignore[no-redef]
                super().__init__(parent)
                self._editor = editor
                self.setMouseTracking(True)

            def sizeHint(self) -> QSize:
                return QSize(800, 600)

            def request_render(self) -> None:
                self.update()

            def paintEvent(self, event) -> None:  # type: ignore[override]
                painter = QPainter(self)
                painter.fillRect(self.rect(), QColor(30, 30, 30))

                drawer = getattr(self._editor, "map_drawer", None)
                if drawer is not None and hasattr(self._editor, "drawing_options_coordinator"):
                    self._editor.drawing_options_coordinator.sync_from_editor()
                    drawer.game_map = self._editor.map
                    drawer.viewport.origin_x = int(self._editor.viewport.origin_x)
                    drawer.viewport.origin_y = int(self._editor.viewport.origin_y)
                    drawer.viewport.z = int(self._editor.viewport.z)
                    drawer.viewport.tile_px = int(self._editor.viewport.tile_px)
                    drawer.viewport.width_px = int(self.width())
                    drawer.viewport.height_px = int(self.height())
                    with contextlib.suppress(Exception):
                        drawer.set_live_cursors(self._editor.session.get_live_cursor_overlays())

                    backend = QPainterRenderBackend(
                        painter,
                        target_rect=self.rect(),
                        sprite_lookup=lambda sid, size: self._editor._sprite_pixmap_for_server_id(
                            int(sid), tile_px=int(size)
                        ),
                        indicator_lookup=self._editor.indicators.icon,
                    )
                    drawer.draw(backend)

                painter.end()

        def is_opengl_available() -> bool:
            return False


try:
    from .qpainter_backend import QPainterRenderBackend
except Exception:  # pragma: no cover - fallback for headless envs without PyQt6

    class QPainterRenderBackend:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs) -> None:
            raise ImportError("PyQt6 is required for QPainterRenderBackend")


from .map_drawer import (
    MapDrawer,
    RenderBackend,
    Viewport,
    create_map_drawer,
)

__all__ = [
    # Model
    "Color",
    "DrawCommand",
    "DrawCommandType",
    "LayerType",
    "Rect",
    "RenderFrame",
    "THEME_COLORS",
    # OpenGL Canvas
    "OpenGLCanvasWidget",
    "is_opengl_available",
    # MapDrawer
    "MapDrawer",
    "RenderBackend",
    "Viewport",
    "create_map_drawer",
    "QPainterRenderBackend",
]
