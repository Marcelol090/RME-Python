"""Modern Sprite Batcher using Texture Arrays.

This module implements a high-performance sprite batcher matching the Redux
architecture using GL_TEXTURE_2D_ARRAY for efficient batching.

Architecture:
    Instead of switching textures for each sprite, all sprites are stored
    in a TextureArray. Each sprite gets a layer index which is passed to
    the shader as an attribute. This eliminates texture binding overhead.

Reference:
    - C++ Redux: source/rendering/sprite_batch.cpp
    - Shader: source/rendering/shaders/sprite_batch.vert/frag
"""

from __future__ import annotations

import ctypes
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

from .texture_array import TextureArray

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class SpriteInstance:
    """A single sprite instance to be batched.

    Attributes:
        x: Screen X position.
        y: Screen Y position.
        width: Sprite width in pixels.
        height: Sprite height in pixels.
        layer: TextureArray layer index.
        tint: RGBA tint color (0-255 each).
    """

    x: float
    y: float
    width: float
    height: float
    layer: int
    tint: tuple[int, int, int, int] = (255, 255, 255, 255)


@dataclass
class BatcherStats:
    """Statistics for the current frame."""

    sprites_drawn: int = 0
    draw_calls: int = 0
    vertices_uploaded: int = 0


class ModernSpriteBatcher:
    """High-performance sprite batcher using TextureArray.

    This batcher collects sprite instances and renders them in a single
    draw call by using a texture array. All sprites share the same
    texture binding, eliminating state changes.

    Usage:
        batcher = ModernSpriteBatcher(gl)
        batcher.initialize(texture_array)

        # Each frame:
        batcher.begin()
        batcher.add_sprite(x, y, w, h, layer, tint)
        batcher.add_sprite(...)
        batcher.end(viewport_width, viewport_height)
    """

    # Vertex layout: pos(2) + uv(2) + color(4) + layer(1) = 9 floats
    FLOATS_PER_VERTEX = 9
    VERTICES_PER_QUAD = 6  # 2 triangles
    FLOATS_PER_QUAD = FLOATS_PER_VERTEX * VERTICES_PER_QUAD

    # Maximum sprites per batch (prevents huge buffer allocations)
    MAX_SPRITES_PER_BATCH = 10000

    def __init__(self, gl: Any) -> None:
        """Initialize the batcher.

        Args:
            gl: OpenGL context.
        """
        self._gl = gl
        self._texture_array: TextureArray | None = None
        self._program: int = 0
        self._vao: int = 0
        self._vbo: int = 0

        # Uniform locations
        self._u_viewport: int = -1
        self._u_texture_array: int = -1
        self._u_use_texture: int = -1

        # Batch data
        self._sprites: list[SpriteInstance] = []
        self._vertices: list[float] = []
        self._initialized: bool = False

        # Stats
        self._stats = BatcherStats()

    @property
    def stats(self) -> BatcherStats:
        """Get rendering statistics for the last frame."""
        return self._stats

    def initialize(self, texture_array: TextureArray) -> bool:
        """Initialize the batcher with a texture array.

        Args:
            texture_array: TextureArray containing sprite data.

        Returns:
            True if successful.
        """
        if self._initialized:
            return True

        self._texture_array = texture_array

        try:
            self._create_shader_program()
            self._create_buffers()
            self._initialized = True
            logger.info("ModernSpriteBatcher: Initialized")
            return True
        except Exception as e:
            logger.error("ModernSpriteBatcher: Failed to initialize - %s", e)
            return False

    def _create_shader_program(self) -> None:
        """Create and link the shader program."""
        from ..shaders import SPRITE_BATCH_FRAGMENT, SPRITE_BATCH_VERTEX

        gl = self._gl

        # Compile vertex shader
        vs = gl.glCreateShader(gl.GL_VERTEX_SHADER)
        gl.glShaderSource(vs, SPRITE_BATCH_VERTEX)
        gl.glCompileShader(vs)
        if not gl.glGetShaderiv(vs, gl.GL_COMPILE_STATUS):
            info = gl.glGetShaderInfoLog(vs)
            raise RuntimeError(f"Vertex shader compile failed: {info}")

        # Compile fragment shader
        fs = gl.glCreateShader(gl.GL_FRAGMENT_SHADER)
        gl.glShaderSource(fs, SPRITE_BATCH_FRAGMENT)
        gl.glCompileShader(fs)
        if not gl.glGetShaderiv(fs, gl.GL_COMPILE_STATUS):
            info = gl.glGetShaderInfoLog(fs)
            raise RuntimeError(f"Fragment shader compile failed: {info}")

        # Link program
        self._program = gl.glCreateProgram()
        gl.glAttachShader(self._program, vs)
        gl.glAttachShader(self._program, fs)
        gl.glLinkProgram(self._program)
        if not gl.glGetProgramiv(self._program, gl.GL_LINK_STATUS):
            info = gl.glGetProgramInfoLog(self._program)
            raise RuntimeError(f"Shader link failed: {info}")

        gl.glDeleteShader(vs)
        gl.glDeleteShader(fs)

        # Get uniform locations
        self._u_viewport = gl.glGetUniformLocation(self._program, "u_viewport")
        self._u_texture_array = gl.glGetUniformLocation(self._program, "u_texture_array")
        self._u_use_texture = gl.glGetUniformLocation(self._program, "u_use_texture")

    def _create_buffers(self) -> None:
        """Create VAO and VBO."""
        gl = self._gl

        self._vao = gl.glGenVertexArrays(1)
        self._vbo = gl.glGenBuffers(1)

        gl.glBindVertexArray(self._vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._vbo)

        stride = self.FLOATS_PER_VERTEX * 4  # 9 floats * 4 bytes

        # Position (location 0)
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, stride, ctypes.c_void_p(0))

        # UV (location 1)
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, stride, ctypes.c_void_p(8))

        # Color (location 2)
        gl.glEnableVertexAttribArray(2)
        gl.glVertexAttribPointer(2, 4, gl.GL_FLOAT, gl.GL_FALSE, stride, ctypes.c_void_p(16))

        # Layer (location 3)
        gl.glEnableVertexAttribArray(3)
        gl.glVertexAttribPointer(3, 1, gl.GL_FLOAT, gl.GL_FALSE, stride, ctypes.c_void_p(32))

        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glBindVertexArray(0)

    def begin(self) -> None:
        """Begin a new frame/batch."""
        self._sprites.clear()
        self._vertices.clear()
        self._stats = BatcherStats()

    def add_sprite(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        layer: int,
        tint: tuple[int, int, int, int] = (255, 255, 255, 255),
    ) -> None:
        """Add a sprite to the batch.

        Args:
            x: Screen X position.
            y: Screen Y position.
            width: Sprite width.
            height: Sprite height.
            layer: TextureArray layer index.
            tint: RGBA tint color.
        """
        if len(self._sprites) >= self.MAX_SPRITES_PER_BATCH:
            logger.warning("ModernSpriteBatcher: Max sprites reached, sprite dropped")
            return

        self._sprites.append(
            SpriteInstance(
                x=float(x),
                y=float(y),
                width=float(width),
                height=float(height),
                layer=int(layer),
                tint=tint,
            )
        )

    def _build_vertices(self) -> None:
        """Convert sprites to vertex data."""
        self._vertices.clear()

        for sprite in self._sprites:
            x0 = sprite.x
            y0 = sprite.y
            x1 = sprite.x + sprite.width
            y1 = sprite.y + sprite.height

            # Normalize color
            r = float(sprite.tint[0]) / 255.0
            g = float(sprite.tint[1]) / 255.0
            b = float(sprite.tint[2]) / 255.0
            a = float(sprite.tint[3]) / 255.0
            layer = float(sprite.layer)

            # UV coordinates (flip V for top-left origin)
            u0, v0 = 0.0, 1.0
            u1, v1 = 1.0, 0.0

            # Two triangles (6 vertices per quad)
            # Triangle 1: top-left, top-right, bottom-right
            self._vertices.extend(
                [
                    x0,
                    y0,
                    u0,
                    v0,
                    r,
                    g,
                    b,
                    a,
                    layer,
                    x1,
                    y0,
                    u1,
                    v0,
                    r,
                    g,
                    b,
                    a,
                    layer,
                    x1,
                    y1,
                    u1,
                    v1,
                    r,
                    g,
                    b,
                    a,
                    layer,
                ]
            )
            # Triangle 2: top-left, bottom-right, bottom-left
            self._vertices.extend(
                [
                    x0,
                    y0,
                    u0,
                    v0,
                    r,
                    g,
                    b,
                    a,
                    layer,
                    x1,
                    y1,
                    u1,
                    v1,
                    r,
                    g,
                    b,
                    a,
                    layer,
                    x0,
                    y1,
                    u0,
                    v1,
                    r,
                    g,
                    b,
                    a,
                    layer,
                ]
            )

    def end(self, viewport_width: int, viewport_height: int) -> None:
        """End the batch and render all sprites.

        Args:
            viewport_width: Viewport width in pixels.
            viewport_height: Viewport height in pixels.
        """
        if not self._initialized or not self._sprites:
            return

        self._build_vertices()

        if not self._vertices:
            return

        gl = self._gl

        # Use shader program
        gl.glUseProgram(self._program)
        gl.glUniform2f(self._u_viewport, float(viewport_width), float(viewport_height))
        gl.glUniform1i(self._u_use_texture, 1)

        # Bind texture array
        if self._texture_array:
            self._texture_array.bind(0)
            gl.glUniform1i(self._u_texture_array, 0)

        # Upload vertex data
        gl.glBindVertexArray(self._vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self._vbo)

        data = (ctypes.c_float * len(self._vertices))(*self._vertices)
        gl.glBufferData(gl.GL_ARRAY_BUFFER, ctypes.sizeof(data), data, gl.GL_DYNAMIC_DRAW)

        # Draw
        vertex_count = len(self._sprites) * self.VERTICES_PER_QUAD
        gl.glDrawArrays(gl.GL_TRIANGLES, 0, vertex_count)

        # Update stats
        self._stats.sprites_drawn = len(self._sprites)
        self._stats.draw_calls = 1
        self._stats.vertices_uploaded = len(self._vertices)

        # Cleanup
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glBindVertexArray(0)
        gl.glUseProgram(0)

        if self._texture_array:
            self._texture_array.unbind(0)

    def cleanup(self) -> None:
        """Release GPU resources."""
        gl = self._gl

        if self._vbo:
            gl.glDeleteBuffers(1, [self._vbo])
            self._vbo = 0

        if self._vao:
            gl.glDeleteVertexArrays(1, [self._vao])
            self._vao = 0

        if self._program:
            gl.glDeleteProgram(self._program)
            self._program = 0

        self._initialized = False
        logger.debug("ModernSpriteBatcher: Cleaned up")

    def __del__(self) -> None:
        self.cleanup()
