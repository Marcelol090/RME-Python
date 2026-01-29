"""
Renderer package: Modern rendering backends for py_rme_canary.

This package provides:
- RenderModel: Qt-free data structures for draw commands
- OpenGLCanvas: Hardware-accelerated rendering widget
- MapDrawer: Coordinates rendering based on DrawingOptions
"""
from .render_model import (
    Color,
    DrawCommand,
    DrawCommandType,
    LayerType,
    Rect,
    RenderFrame,
    THEME_COLORS,
)

# Heavy Qt imports are optional to keep MapDrawer usable in headless/unit tests.
try:
    from .opengl_canvas import (
        OpenGLCanvasWidget,
        is_opengl_available,
    )
except Exception:  # pragma: no cover - fallback for headless envs without PyQt6/OpenGL
    class OpenGLCanvasWidget:  # type: ignore[no-redef]
        def __init__(self, *args, **kwargs) -> None:
            raise ImportError("PyQt6/OpenGL not available")

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
