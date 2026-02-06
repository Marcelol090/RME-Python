"""NanoVG-like OpenGL adapter for vector graphics overlay.

This module provides a simplified NanoVG-compatible API for rendering
vector graphics overlays (selection boxes, highlights, guides) on top
of the OpenGL map canvas.

Based on the NanoVG library concepts but implemented as a pure Python
adapter for PyQt6/OpenGL integration.

Reference: https://github.com/memononen/nanovg
"""

from __future__ import annotations

import ctypes
import logging
import math
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from collections.abc import Sequence

logger = logging.getLogger(__name__)


@dataclass
class NanoVGPaint:
    """Paint definition for fills and strokes.

    Supports solid colors and linear gradients.
    """

    # Solid color (RGBA, 0-255)
    color: tuple[int, int, int, int] = (255, 255, 255, 255)

    # Gradient support
    is_gradient: bool = False
    gradient_start: tuple[float, float] = (0.0, 0.0)
    gradient_end: tuple[float, float] = (0.0, 0.0)
    gradient_color_start: tuple[int, int, int, int] = (255, 255, 255, 255)
    gradient_color_end: tuple[int, int, int, int] = (0, 0, 0, 255)

    @classmethod
    def rgba(cls, r: int, g: int, b: int, a: int = 255) -> NanoVGPaint:
        """Create a solid color paint."""
        return cls(color=(r, g, b, a))

    @classmethod
    def linear_gradient(
        cls,
        sx: float,
        sy: float,
        ex: float,
        ey: float,
        color_start: tuple[int, int, int, int],
        color_end: tuple[int, int, int, int],
    ) -> NanoVGPaint:
        """Create a linear gradient paint."""
        return cls(
            is_gradient=True,
            gradient_start=(sx, sy),
            gradient_end=(ex, ey),
            gradient_color_start=color_start,
            gradient_color_end=color_end,
        )


@dataclass
class _PathCommand:
    """Internal path command representation."""

    cmd: str  # 'M', 'L', 'C', 'Q', 'Z'
    args: tuple[float, ...] = field(default_factory=tuple)


class NanoVGContext:
    """NanoVG-like context for OpenGL vector rendering.

    Provides a simplified API for drawing vector shapes on OpenGL canvas:
    - Rectangles, rounded rectangles
    - Circles, ellipses
    - Lines, polylines
    - Bezier curves
    - Text (placeholder)

    Usage:
        ctx = NanoVGContext(gl)
        ctx.begin_frame(width, height, pixel_ratio)

        ctx.begin_path()
        ctx.rect(10, 10, 100, 50)
        ctx.fill_color(255, 100, 100, 200)
        ctx.fill()

        ctx.end_frame()
    """

    def __init__(self, gl: Any) -> None:
        """Initialize NanoVG context.

        Args:
            gl: OpenGL context (OpenGL.GL module or similar)
        """
        self._gl = gl
        self._width = 0.0
        self._height = 0.0
        self._pixel_ratio = 1.0

        # Current path
        self._path: list[_PathCommand] = []
        self._path_x = 0.0
        self._path_y = 0.0

        # Current style state
        self._fill_paint = NanoVGPaint.rgba(255, 255, 255, 255)
        self._stroke_paint = NanoVGPaint.rgba(0, 0, 0, 255)
        self._stroke_width = 1.0
        self._line_cap = "butt"  # butt, round, square
        self._line_join = "miter"  # miter, round, bevel

        # State stack for save/restore
        self._state_stack: list[dict[str, Any]] = []

        # Shader program (lazily initialized)
        self._program: int | None = None
        self._vao: int | None = None
        self._vbo: int | None = None

        logger.debug("NanoVGContext initialized")

    def begin_frame(self, width: float, height: float, pixel_ratio: float = 1.0) -> None:
        """Begin a new frame for rendering.

        Call this at the start of each frame before drawing.
        """
        self._width = width
        self._height = height
        self._pixel_ratio = pixel_ratio

        # Initialize GL resources if needed
        if self._program is None:
            self._init_gl_resources()

    def end_frame(self) -> None:
        """End the current frame.

        Call this after all drawing is complete.
        """
        pass  # Placeholder for frame finalization

    def _init_gl_resources(self) -> None:
        """Initialize OpenGL shader program and buffers."""
        gl = self._gl

        # Vertex shader
        vs_source = """
        #version 330 core
        layout(location = 0) in vec2 a_position;
        layout(location = 1) in vec4 a_color;

        uniform vec2 u_viewport;

        out vec4 v_color;

        void main() {
            vec2 pos = (a_position / u_viewport) * 2.0 - 1.0;
            pos.y = -pos.y;
            gl_Position = vec4(pos, 0.0, 1.0);
            v_color = a_color;
        }
        """

        # Fragment shader
        fs_source = """
        #version 330 core
        in vec4 v_color;
        out vec4 frag_color;

        void main() {
            frag_color = v_color;
        }
        """

        try:
            # Compile shaders
            vs = gl.glCreateShader(gl.GL_VERTEX_SHADER)
            gl.glShaderSource(vs, vs_source)
            gl.glCompileShader(vs)

            fs = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
            gl.glShaderSource(fs, fs_source)
            gl.glCompileShader(fs)

            # Link program
            self._program = gl.glCreateProgram()
            gl.glAttachShader(self._program, vs)
            gl.glAttachShader(self._program, fs)
            gl.glLinkProgram(self._program)

            gl.glDeleteShader(vs)
            gl.glDeleteShader(fs)

            # Create VAO/VBO
            self._vao = gl.glGenVertexArrays(1)
            self._vbo = gl.glGenBuffers(1)

            gl.glBindVertexArray(self._vao)
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._vbo)

            # Position attribute (vec2)
            gl.glEnableVertexAttribArray(0)
            gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 24, ctypes.c_void_p(0))

            # Color attribute (vec4)
            gl.glEnableVertexAttribArray(1)
            gl.glVertexAttribPointer(1, 4, gl.GL_FLOAT, gl.GL_FALSE, 24, ctypes.c_void_p(8))

            gl.glBindVertexArray(0)

            logger.debug("NanoVG GL resources initialized")

        except Exception as e:
            logger.error("Failed to initialize NanoVG GL resources: %s", e)
            self._program = None

    # === State Management ===

    def save(self) -> None:
        """Save current state to stack."""
        self._state_stack.append(
            {
                "fill_paint": self._fill_paint,
                "stroke_paint": self._stroke_paint,
                "stroke_width": self._stroke_width,
                "line_cap": self._line_cap,
                "line_join": self._line_join,
            }
        )

    def restore(self) -> None:
        """Restore state from stack."""
        if self._state_stack:
            state = self._state_stack.pop()
            self._fill_paint = state["fill_paint"]
            self._stroke_paint = state["stroke_paint"]
            self._stroke_width = state["stroke_width"]
            self._line_cap = state["line_cap"]
            self._line_join = state["line_join"]

    # === Style Setters ===

    def fill_color(self, r: int, g: int, b: int, a: int = 255) -> None:
        """Set fill color."""
        self._fill_paint = NanoVGPaint.rgba(r, g, b, a)

    def fill_paint(self, paint: NanoVGPaint) -> None:
        """Set fill paint."""
        self._fill_paint = paint

    def stroke_color(self, r: int, g: int, b: int, a: int = 255) -> None:
        """Set stroke color."""
        self._stroke_paint = NanoVGPaint.rgba(r, g, b, a)

    def stroke_paint(self, paint: NanoVGPaint) -> None:
        """Set stroke paint."""
        self._stroke_paint = paint

    def stroke_width(self, width: float) -> None:
        """Set stroke width."""
        self._stroke_width = max(0.0, width)

    def line_cap(self, cap: str) -> None:
        """Set line cap style: 'butt', 'round', or 'square'."""
        if cap in ("butt", "round", "square"):
            self._line_cap = cap

    def line_join(self, join: str) -> None:
        """Set line join style: 'miter', 'round', or 'bevel'."""
        if join in ("miter", "round", "bevel"):
            self._line_join = join

    # === Path Operations ===

    def begin_path(self) -> None:
        """Clear current path and begin new one."""
        self._path.clear()
        self._path_x = 0.0
        self._path_y = 0.0

    def move_to(self, x: float, y: float) -> None:
        """Move to position without drawing."""
        self._path.append(_PathCommand("M", (x, y)))
        self._path_x = x
        self._path_y = y

    def line_to(self, x: float, y: float) -> None:
        """Draw line to position."""
        self._path.append(_PathCommand("L", (x, y)))
        self._path_x = x
        self._path_y = y

    def bezier_to(self, c1x: float, c1y: float, c2x: float, c2y: float, x: float, y: float) -> None:
        """Draw cubic bezier curve."""
        self._path.append(_PathCommand("C", (c1x, c1y, c2x, c2y, x, y)))
        self._path_x = x
        self._path_y = y

    def quad_to(self, cx: float, cy: float, x: float, y: float) -> None:
        """Draw quadratic bezier curve."""
        self._path.append(_PathCommand("Q", (cx, cy, x, y)))
        self._path_x = x
        self._path_y = y

    def close_path(self) -> None:
        """Close current path."""
        self._path.append(_PathCommand("Z"))

    # === Shape Helpers ===

    def rect(self, x: float, y: float, w: float, h: float) -> None:
        """Add rectangle to path."""
        self.move_to(x, y)
        self.line_to(x + w, y)
        self.line_to(x + w, y + h)
        self.line_to(x, y + h)
        self.close_path()

    def rounded_rect(self, x: float, y: float, w: float, h: float, r: float) -> None:
        """Add rounded rectangle to path."""
        r = min(r, min(w, h) / 2)

        self.move_to(x + r, y)
        self.line_to(x + w - r, y)
        self.quad_to(x + w, y, x + w, y + r)
        self.line_to(x + w, y + h - r)
        self.quad_to(x + w, y + h, x + w - r, y + h)
        self.line_to(x + r, y + h)
        self.quad_to(x, y + h, x, y + h - r)
        self.line_to(x, y + r)
        self.quad_to(x, y, x + r, y)
        self.close_path()

    def circle(self, cx: float, cy: float, r: float) -> None:
        """Add circle to path."""
        self.ellipse(cx, cy, r, r)

    def ellipse(self, cx: float, cy: float, rx: float, ry: float) -> None:
        """Add ellipse to path using bezier approximation."""
        # Magic number for bezier circle approximation
        kappa = 0.5522847493
        ox = rx * kappa
        oy = ry * kappa

        self.move_to(cx - rx, cy)
        self.bezier_to(cx - rx, cy - oy, cx - ox, cy - ry, cx, cy - ry)
        self.bezier_to(cx + ox, cy - ry, cx + rx, cy - oy, cx + rx, cy)
        self.bezier_to(cx + rx, cy + oy, cx + ox, cy + ry, cx, cy + ry)
        self.bezier_to(cx - ox, cy + ry, cx - rx, cy + oy, cx - rx, cy)
        self.close_path()

    # === Drawing ===

    def fill(self) -> None:
        """Fill current path."""
        if not self._path or self._program is None:
            return

        vertices = self._triangulate_path()
        if not vertices:
            return

        self._draw_triangles(vertices, self._fill_paint)

    def stroke(self) -> None:
        """Stroke current path."""
        if not self._path or self._program is None:
            return

        vertices = self._stroke_path()
        if not vertices:
            return

        self._draw_triangles(vertices, self._stroke_paint)

    def _triangulate_path(self) -> list[float]:
        """Convert path to triangle vertices for fill.

        Returns list of floats: [x1, y1, r, g, b, a, x2, y2, ...]
        """
        # Simple fan triangulation (works for convex shapes)
        points = self._path_to_points()
        if len(points) < 3:
            return []

        c = self._fill_paint.color
        r, g, b, a = c[0] / 255, c[1] / 255, c[2] / 255, c[3] / 255

        vertices: list[float] = []
        p0 = points[0]

        for i in range(1, len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]

            # Triangle: p0, p1, p2
            vertices.extend([p0[0], p0[1], r, g, b, a])
            vertices.extend([p1[0], p1[1], r, g, b, a])
            vertices.extend([p2[0], p2[1], r, g, b, a])

        return vertices

    def _stroke_path(self) -> list[float]:
        """Convert path to triangle strip for stroke.

        Returns list of floats: [x1, y1, r, g, b, a, x2, y2, ...]
        """
        points = self._path_to_points()
        if len(points) < 2:
            return []

        c = self._stroke_paint.color
        r, g, b, a = c[0] / 255, c[1] / 255, c[2] / 255, c[3] / 255
        hw = self._stroke_width / 2

        vertices: list[float] = []

        for i in range(len(points) - 1):
            p1 = points[i]
            p2 = points[i + 1]

            # Calculate perpendicular
            dx = p2[0] - p1[0]
            dy = p2[1] - p1[1]
            length = math.sqrt(dx * dx + dy * dy)
            if length < 0.0001:
                continue

            nx = -dy / length * hw
            ny = dx / length * hw

            # Quad as two triangles
            vertices.extend([p1[0] + nx, p1[1] + ny, r, g, b, a])
            vertices.extend([p1[0] - nx, p1[1] - ny, r, g, b, a])
            vertices.extend([p2[0] + nx, p2[1] + ny, r, g, b, a])

            vertices.extend([p1[0] - nx, p1[1] - ny, r, g, b, a])
            vertices.extend([p2[0] - nx, p2[1] - ny, r, g, b, a])
            vertices.extend([p2[0] + nx, p2[1] + ny, r, g, b, a])

        return vertices

    def _path_to_points(self) -> list[tuple[float, float]]:
        """Convert path commands to point list."""
        points: list[tuple[float, float]] = []
        x, y = 0.0, 0.0

        for cmd in self._path:
            if cmd.cmd == "M" or cmd.cmd == "L":
                x, y = cmd.args[0], cmd.args[1]
                points.append((x, y))
            elif cmd.cmd == "C":
                # Cubic bezier - flatten to line segments
                x1, y1, x2, y2, x3, y3 = cmd.args
                for t in [0.25, 0.5, 0.75, 1.0]:
                    bx = ((1 - t) ** 3) * x + 3 * ((1 - t) ** 2) * t * x1 + 3 * (1 - t) * (t**2) * x2 + (t**3) * x3
                    by = ((1 - t) ** 3) * y + 3 * ((1 - t) ** 2) * t * y1 + 3 * (1 - t) * (t**2) * y2 + (t**3) * y3
                    points.append((bx, by))
                x, y = x3, y3
            elif cmd.cmd == "Q":
                # Quadratic bezier - flatten to line segments
                cx, cy, ex, ey = cmd.args
                for t in [0.25, 0.5, 0.75, 1.0]:
                    bx = ((1 - t) ** 2) * x + 2 * (1 - t) * t * cx + (t**2) * ex
                    by = ((1 - t) ** 2) * y + 2 * (1 - t) * t * cy + (t**2) * ey
                    points.append((bx, by))
                x, y = ex, ey
            elif cmd.cmd == "Z":
                if points and len(points) > 1:
                    points.append(points[0])

        return points

    def _draw_triangles(self, vertices: Sequence[float], paint: NanoVGPaint) -> None:
        """Draw triangles with given vertices and paint."""
        if not vertices or self._program is None:
            return

        gl = self._gl

        try:
            # Setup state
            gl.glUseProgram(self._program)
            gl.glBindVertexArray(self._vao)

            # Enable blending
            gl.glEnable(gl.GL_BLEND)
            gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)

            # Set viewport uniform
            u_viewport = gl.glGetUniformLocation(self._program, "u_viewport")
            gl.glUniform2f(u_viewport, self._width, self._height)

            # Upload vertex data
            data = (ctypes.c_float * len(vertices))(*vertices)
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._vbo)
            gl.glBufferData(gl.GL_ARRAY_BUFFER, ctypes.sizeof(data), data, gl.GL_DYNAMIC_DRAW)

            # Draw
            vertex_count = len(vertices) // 6  # 6 floats per vertex (x, y, r, g, b, a)
            gl.glDrawArrays(gl.GL_TRIANGLES, 0, vertex_count)

            # Cleanup
            gl.glBindVertexArray(0)
            gl.glUseProgram(0)

        except Exception as e:
            logger.error("NanoVG draw error: %s", e)

    # === Text (Placeholder) ===

    def text(self, x: float, y: float, text: str) -> None:
        """Draw text at position (placeholder).

        Note: Full text rendering requires font loading and glyph rendering.
        This is a placeholder for future implementation.
        """
        # TODO: Implement proper text rendering
        pass

    def cleanup(self) -> None:
        """Release OpenGL resources."""
        if self._gl is None:
            return

        gl = self._gl

        try:
            if self._vbo is not None:
                gl.glDeleteBuffers(1, [self._vbo])
            if self._vao is not None:
                gl.glDeleteVertexArrays(1, [self._vao])
            if self._program is not None:
                gl.glDeleteProgram(self._program)
        except Exception:
            pass

        self._program = None
        self._vao = None
        self._vbo = None

        logger.debug("NanoVG resources cleaned up")
