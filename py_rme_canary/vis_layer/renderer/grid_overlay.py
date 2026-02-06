"""Optional Grid Overlay for Preview Window.

This module implements a toggleable grid overlay that can be displayed
over the preview window, matching the reference in project_tasks.json FUTURE-002.

Architecture:
    - GridStyle: Configuration for grid appearance.
    - GridOverlay: Renders a grid using GL_LINES or a shader.
    - The grid is rendered after the scene but before UI elements.

Reference:
    - GLSL: shaders/__init__.py (GRID_VERTEX, GRID_FRAGMENT)
"""

from __future__ import annotations

import ctypes
import logging
import struct
from dataclasses import dataclass
from enum import Enum
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class GridMode(Enum):
    """Grid rendering modes."""

    LINES = "lines"  # Traditional GL_LINES
    SHADER = "shader"  # Per-pixel shader (more expensive, prettier)
    DASHED = "dashed"  # Dashed lines (pattern)


@dataclass
class GridStyle:
    """Visual configuration for the grid.

    Attributes:
        color: RGBA color tuple (0-255 each).
        line_width: Width of grid lines in pixels.
        opacity: Overall opacity (0.0-1.0).
        mode: Rendering mode (lines, shader, dashed).
        dash_length: For dashed mode, pixels per dash.
        gap_length: For dashed mode, pixels per gap.
        major_interval: Every N lines is a major line (thicker/brighter).
        major_color: Color for major grid lines.
        show_major: Whether to show major lines.
    """

    color: tuple[int, int, int, int] = (100, 100, 100, 128)
    line_width: float = 1.0
    opacity: float = 0.5
    mode: GridMode = GridMode.LINES
    dash_length: float = 4.0
    gap_length: float = 2.0
    major_interval: int = 8  # Major line every 8 tiles
    major_color: tuple[int, int, int, int] = (150, 150, 150, 180)
    show_major: bool = True


@dataclass
class GridBounds:
    """Visible area for grid rendering.

    Attributes:
        min_x: Minimum X in tile coordinates.
        max_x: Maximum X in tile coordinates.
        min_y: Minimum Y in tile coordinates.
        max_y: Maximum Y in tile coordinates.
    """

    min_x: int = 0
    max_x: int = 100
    min_y: int = 0
    max_y: int = 100


class GridOverlay:
    """Renders a toggleable grid overlay.

    Usage:
        grid = GridOverlay(gl)
        grid.set_style(GridStyle(color=(80, 80, 80, 100)))
        grid.visible = True

        # Each frame:
        grid.render(
            camera_x=cam_x, camera_y=cam_y,
            viewport_width=800, viewport_height=600,
            tile_size=32.0
        )
    """

    def __init__(self, gl: Any) -> None:
        """Initialize the grid overlay.

        Args:
            gl: OpenGL context.
        """
        self._gl = gl
        self._style = GridStyle()
        self._visible = False

        # OpenGL resources
        self._vao: int = 0
        self._vbo: int = 0
        self._shader: int = 0

        # Cached line data
        self._line_vertices: list[float] = []
        self._line_count = 0
        self._max_lines = 4096  # Max number of lines in buffer

        # Cached bounds for invalidation
        self._cached_bounds = GridBounds()
        self._cached_tile_size = 0.0
        self._needs_rebuild = True

        self._initialized = False

    @property
    def visible(self) -> bool:
        return self._visible

    @visible.setter
    def visible(self, value: bool) -> None:
        self._visible = bool(value)

    @property
    def style(self) -> GridStyle:
        return self._style

    def set_style(self, style: GridStyle) -> None:
        """Set grid style."""
        self._style = style
        self._needs_rebuild = True

    def toggle(self) -> bool:
        """Toggle grid visibility.

        Returns:
            New visibility state.
        """
        self._visible = not self._visible
        return self._visible

    def initialize(self) -> bool:
        """Initialize OpenGL resources.

        Returns:
            True if successful.
        """
        if self._initialized:
            return True

        gl = self._gl

        try:
            # Create VAO
            self._vao = int(gl.glGenVertexArrays(1))
            gl.glBindVertexArray(self._vao)

            # Create VBO with initial size
            self._vbo = int(gl.glGenBuffers(1))
            gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._vbo)

            # 2D position per vertex, preallocate
            buffer_size = self._max_lines * 2 * 2 * 4  # lines * 2 verts * 2 floats * 4 bytes
            gl.glBufferData(gl.GL_ARRAY_BUFFER, buffer_size, None, gl.GL_DYNAMIC_DRAW)

            # Position attribute (location 0)
            gl.glEnableVertexAttribArray(0)
            gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, 8, ctypes.c_void_p(0))

            gl.glBindVertexArray(0)

            # Compile shaders
            self._shader = self._compile_shader()

            self._initialized = True
            logger.debug("GridOverlay: Initialized")
            return True

        except Exception as e:
            logger.error("GridOverlay: Initialization failed: %s", e)
            return False

    def _compile_shader(self) -> int:
        """Compile the grid shader program.

        Returns:
            Shader program ID.
        """
        gl = self._gl

        # Simple line shader
        vert_src = """
        #version 330 core
        layout(location = 0) in vec2 a_position;
        uniform mat4 u_projection;
        void main() {
            gl_Position = u_projection * vec4(a_position, 0.0, 1.0);
        }
        """

        frag_src = """
        #version 330 core
        uniform vec4 u_color;
        out vec4 FragColor;
        void main() {
            FragColor = u_color;
        }
        """

        # Compile vertex shader
        vert = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vert, vert_src)
        gl.glCompileShader(vert)

        status = gl.glGetShaderiv(vert, gl.GL_COMPILE_STATUS)
        if not status:
            log = gl.glGetShaderInfoLog(vert)
            logger.error("Grid vertex shader error: %s", log)
            raise RuntimeError(f"Grid vertex shader: {log}")

        # Compile fragment shader
        frag = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(frag, frag_src)
        gl.glCompileShader(frag)

        status = gl.glGetShaderiv(frag, gl.GL_COMPILE_STATUS)
        if not status:
            log = gl.glGetShaderInfoLog(frag)
            logger.error("Grid fragment shader error: %s", log)
            raise RuntimeError(f"Grid fragment shader: {log}")

        # Link program
        prog = gl.glCreateProgram()
        gl.glAttachShader(prog, vert)
        gl.glAttachShader(prog, frag)
        gl.glLinkProgram(prog)

        status = gl.glGetProgramiv(prog, gl.GL_LINK_STATUS)
        if not status:
            log = gl.glGetProgramInfoLog(prog)
            logger.error("Grid shader link error: %s", log)
            raise RuntimeError(f"Grid shader link: {log}")

        # Cleanup
        gl.glDeleteShader(vert)
        gl.glDeleteShader(frag)

        return int(prog)

    def render(
        self,
        camera_x: float,
        camera_y: float,
        viewport_width: int,
        viewport_height: int,
        tile_size: float,
        projection_matrix: list[float] | None = None,
    ) -> None:
        """Render the grid overlay.

        Args:
            camera_x: Camera X in world units.
            camera_y: Camera Y in world units.
            viewport_width: Viewport width in pixels.
            viewport_height: Viewport height in pixels.
            tile_size: Size of one tile in pixels.
            projection_matrix: Optional 4x4 projection matrix (column-major).
                If None, an orthographic matrix is generated.
        """
        if not self._visible:
            return

        if not self._initialized and not self.initialize():
            return

        gl = self._gl

        # Calculate visible bounds in tile coordinates
        tiles_x = int(viewport_width / tile_size) + 2
        tiles_y = int(viewport_height / tile_size) + 2

        bounds = GridBounds(
            min_x=int(camera_x) - 1,
            max_x=int(camera_x) + tiles_x,
            min_y=int(camera_y) - 1,
            max_y=int(camera_y) + tiles_y,
        )

        # Rebuild if bounds changed significantly
        if (
            self._needs_rebuild
            or abs(tile_size - self._cached_tile_size) > 0.01
            or bounds.min_x != self._cached_bounds.min_x
            or bounds.max_x != self._cached_bounds.max_x
            or bounds.min_y != self._cached_bounds.min_y
            or bounds.max_y != self._cached_bounds.max_y
        ):
            self._rebuild_lines(bounds, camera_x, camera_y, tile_size)
            self._cached_bounds = bounds
            self._cached_tile_size = tile_size
            self._needs_rebuild = False

        if self._line_count == 0:
            return

        # Generate projection matrix if not provided
        if projection_matrix is None:
            projection_matrix = self._ortho_matrix(0, viewport_width, viewport_height, 0, -1, 1)

        # Setup state
        gl.glEnable(gl.GL_BLEND)
        gl.glBlendFunc(gl.GL_SRC_ALPHA, gl.GL_ONE_MINUS_SRC_ALPHA)
        gl.glLineWidth(self._style.line_width)

        gl.glUseProgram(self._shader)
        gl.glBindVertexArray(self._vao)

        # Set uniforms
        proj_loc = gl.glGetUniformLocation(self._shader, "u_projection")
        color_loc = gl.glGetUniformLocation(self._shader, "u_color")

        gl.glUniformMatrix4fv(proj_loc, 1, gl.GL_FALSE, projection_matrix)

        # Draw minor lines
        c = self._style.color
        opacity = self._style.opacity
        gl.glUniform4f(color_loc, c[0] / 255.0, c[1] / 255.0, c[2] / 255.0, (c[3] / 255.0) * opacity)
        gl.glDrawArrays(gl.GL_LINES, 0, self._line_count * 2)

        # Draw major lines if enabled (overdraw for now, could optimize)
        if self._style.show_major and self._major_line_count > 0:
            mc = self._style.major_color
            gl.glUniform4f(color_loc, mc[0] / 255.0, mc[1] / 255.0, mc[2] / 255.0, (mc[3] / 255.0) * opacity)
            gl.glLineWidth(self._style.line_width * 2.0)
            gl.glDrawArrays(gl.GL_LINES, self._major_offset * 2, self._major_line_count * 2)

        gl.glBindVertexArray(0)
        gl.glUseProgram(0)
        gl.glLineWidth(1.0)

    def _rebuild_lines(
        self,
        bounds: GridBounds,
        camera_x: float,
        camera_y: float,
        tile_size: float,
    ) -> None:
        """Rebuild the line vertex buffer.

        Args:
            bounds: Visible tile bounds.
            camera_x: Camera X position.
            camera_y: Camera Y position.
            tile_size: Size of one tile in pixels.
        """
        gl = self._gl

        vertices: list[float] = []
        major_vertices: list[float] = []

        # Offset from camera to pixel coordinates
        offset_x = -camera_x * tile_size
        offset_y = -camera_y * tile_size

        # Vertical lines (x = constant)
        for x in range(bounds.min_x, bounds.max_x + 1):
            px = x * tile_size + offset_x
            py0 = bounds.min_y * tile_size + offset_y
            py1 = bounds.max_y * tile_size + offset_y

            if self._style.show_major and x % self._style.major_interval == 0:
                major_vertices.extend([px, py0, px, py1])
            else:
                vertices.extend([px, py0, px, py1])

        # Horizontal lines (y = constant)
        for y in range(bounds.min_y, bounds.max_y + 1):
            py = y * tile_size + offset_y
            px0 = bounds.min_x * tile_size + offset_x
            px1 = bounds.max_x * tile_size + offset_x

            if self._style.show_major and y % self._style.major_interval == 0:
                major_vertices.extend([px0, py, px1, py])
            else:
                vertices.extend([px0, py, px1, py])

        # Combine: minor lines first, then major lines
        self._minor_line_count = len(vertices) // 4
        self._major_offset = self._minor_line_count
        self._major_line_count = len(major_vertices) // 4

        all_vertices = vertices + major_vertices
        self._line_count = len(all_vertices) // 4

        if self._line_count == 0:
            return

        # Upload to GPU
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._vbo)

        data = struct.pack(f"{len(all_vertices)}f", *all_vertices)
        gl.glBufferSubData(gl.GL_ARRAY_BUFFER, 0, len(data), data)

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)

    def _ortho_matrix(
        self,
        left: float,
        right: float,
        bottom: float,
        top: float,
        near: float,
        far: float,
    ) -> list[float]:
        """Generate an orthographic projection matrix (column-major).

        Args:
            left, right: X bounds.
            bottom, top: Y bounds.
            near, far: Z bounds.

        Returns:
            16-element list for OpenGL (column-major).
        """
        dx = right - left
        dy = top - bottom
        dz = far - near

        return [
            2.0 / dx,
            0.0,
            0.0,
            0.0,
            0.0,
            2.0 / dy,
            0.0,
            0.0,
            0.0,
            0.0,
            -2.0 / dz,
            0.0,
            -(right + left) / dx,
            -(top + bottom) / dy,
            -(far + near) / dz,
            1.0,
        ]

    def cleanup(self) -> None:
        """Release GPU resources."""
        if not self._initialized:
            return

        gl = self._gl

        try:
            if self._vao:
                gl.glDeleteVertexArrays([self._vao])
            if self._vbo:
                gl.glDeleteBuffers([self._vbo])
            if self._shader:
                gl.glDeleteProgram(self._shader)
        except Exception as e:
            logger.warning("GridOverlay cleanup error: %s", e)

        self._vao = 0
        self._vbo = 0
        self._shader = 0
        self._initialized = False
        logger.debug("GridOverlay: Cleaned up")

    def __del__(self) -> None:
        # Note: cleanup() should be called explicitly with valid GL context
        pass
