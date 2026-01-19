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
from .opengl_canvas import (
    OpenGLCanvasWidget,
    is_opengl_available,
)
from .map_drawer import (
    MapDrawer,
    RenderBackend,
    Viewport,
    create_map_drawer,
)
from .qpainter_backend import QPainterRenderBackend

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
