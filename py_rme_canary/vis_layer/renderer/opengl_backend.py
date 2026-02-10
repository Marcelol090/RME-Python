from __future__ import annotations

import contextlib
import ctypes
import logging
from collections import OrderedDict
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from .core import ModernSpriteBatcher, TextureArray
from .map_drawer import RenderBackend

logger = logging.getLogger(__name__)

SpriteLookup = Callable[[int], tuple[int, int, int, bytes] | None]


def _placeholder_color(sprite_id: int) -> tuple[int, int, int, int]:
    v = int(sprite_id) & 0xFFFFFFFF
    r = (v * 2654435761) & 0xFF
    g = (v * 2246822519) & 0xFF
    b = (v * 3266489917) & 0xFF

    def clamp(c: int) -> int:
        return 80 + (int(c) % 140)

    return (clamp(r), clamp(g), clamp(b), 255)


def _placeholder_border_color(sprite_id: int) -> tuple[int, int, int, int]:
    """Darker border color for placeholders to make items stand out."""
    r, g, b, _ = _placeholder_color(sprite_id)
    return (max(0, r - 60), max(0, g - 60), max(0, b - 60), 255)


@dataclass(slots=True)
class _SpriteRun:
    texture_id: int
    vertices: list[float]


def _bgra_to_rgba(bgra: bytes | bytearray) -> bytes:
    mv = memoryview(bgra)
    out = bytearray(len(mv))
    out[0::4] = mv[2::4]  # R
    out[1::4] = mv[1::4]  # G
    out[2::4] = mv[0::4]  # B
    out[3::4] = mv[3::4]  # A
    return bytes(out)


class _TextureArrayAtlas:
    """LRU-managed texture array atlas for sprites."""

    def __init__(
        self,
        gl: Any,
        *,
        layer_width: int = 32,
        layer_height: int = 32,
        max_layers: int = 4096,
    ) -> None:
        self._gl = gl
        self._layer_width = int(layer_width)
        self._layer_height = int(layer_height)
        self._max_layers = int(max_layers)

        self._array = TextureArray(gl)
        self._initialized = False
        self._white_layer: int | None = None
        self._sprite_to_layer: OrderedDict[int, int] = OrderedDict()

    @property
    def is_initialized(self) -> bool:
        return self._initialized and self._array.is_initialized

    @property
    def texture_array(self) -> TextureArray:
        return self._array

    @property
    def white_layer(self) -> int:
        return int(self._white_layer or 0)

    def initialize(self) -> bool:
        if self.is_initialized:
            return True

        if self._max_layers < 2:
            logger.debug("TextureArrayAtlas disabled: max_layers < 2")
            return False

        if not self._array.initialize(self._layer_width, self._layer_height, self._max_layers):
            return False

        white_layer = self._array.allocate_layer()
        if white_layer != 0:
            logger.debug("Unexpected white layer index=%s, expected 0", white_layer)
            return False

        white = bytes([255, 255, 255, 255]) * (self._layer_width * self._layer_height)
        if not self._array.upload_layer(white_layer, white):
            return False

        self._white_layer = 0
        self._initialized = True
        return True

    def get_or_upload_layer(self, sprite_id: int, w: int, h: int, bgra: bytes) -> int | None:
        if not self.is_initialized:
            return None

        sid = int(sprite_id)
        layer = self._sprite_to_layer.get(sid)
        if layer is not None:
            with contextlib.suppress(Exception):
                self._sprite_to_layer.move_to_end(sid)
            return int(layer)

        if int(w) != self._layer_width or int(h) != self._layer_height:
            logger.debug(
                "TextureArrayAtlas: sprite %s has %sx%s (expected %sx%s)",
                sid,
                w,
                h,
                self._layer_width,
                self._layer_height,
            )
            return None

        expected = self._layer_width * self._layer_height * 4
        if len(bgra) != expected:
            logger.debug("TextureArrayAtlas: sprite %s bytes=%s (expected %s)", sid, len(bgra), expected)
            return None

        layer = self._array.allocate_layer()
        if layer == -1:
            if not self._sprite_to_layer:
                return None
            old_sid, old_layer = self._sprite_to_layer.popitem(last=False)
            logger.debug("TextureArrayAtlas: evict sprite_id=%s layer=%s", old_sid, old_layer)
            layer = int(old_layer)

        rgba = _bgra_to_rgba(bgra)
        if not self._array.upload_layer(int(layer), rgba):
            return None

        self._sprite_to_layer[sid] = int(layer)
        with contextlib.suppress(Exception):
            self._sprite_to_layer.move_to_end(sid)
        return int(layer)

    def cleanup(self) -> None:
        self._sprite_to_layer.clear()
        with contextlib.suppress(Exception):
            self._array.cleanup()
        self._white_layer = None
        self._initialized = False


class _SpriteTextureCache:
    def __init__(self, gl: Any, *, max_entries: int = 10_000) -> None:
        self._gl = gl
        self._max_entries = int(max_entries)
        self._entries: OrderedDict[int, int] = OrderedDict()

    def clear(self) -> None:
        if not self._entries:
            return
        try:
            ids = list(self._entries.values())
            self._gl.glDeleteTextures(ids)
        except Exception as e:
            logger.debug("Failed to clear OpenGL textures: %s", e)
        self._entries.clear()

    def get_or_create(self, sprite_id: int, create_fn: Callable[[], int | None]) -> int | None:
        sid = int(sprite_id)
        tex = self._entries.get(sid)
        if tex is not None:
            with contextlib.suppress(Exception):
                self._entries.move_to_end(sid)
            return tex

        tex = create_fn()
        if tex is None:
            return None

        self._entries[sid] = int(tex)
        with contextlib.suppress(Exception):
            self._entries.move_to_end(sid)

        if self._max_entries > 0 and len(self._entries) > self._max_entries:
            try:
                old_sid, old_tex = self._entries.popitem(last=False)
                self._gl.glDeleteTextures([int(old_tex)])
                logger.debug("Evicted OpenGL texture for sprite_id=%s", old_sid)
            except Exception as e:
                logger.debug("Failed to delete evicted texture: %s", e)

        return int(tex)


class OpenGLResources:
    """OpenGL shader/buffer resources shared across frames."""

    def __init__(self, gl: Any) -> None:
        self.gl = gl
        self.program = self._create_program()
        self.u_viewport = gl.glGetUniformLocation(self.program, "u_viewport")
        self.u_use_texture = gl.glGetUniformLocation(self.program, "u_use_texture")
        self.u_texture = gl.glGetUniformLocation(self.program, "u_texture")

        self.vao = gl.glGenVertexArrays(1)
        self.vbo = gl.glGenBuffers(1)
        self._configure_vertex_layout()

        self.white_texture = self._create_white_texture()
        self.texture_cache = _SpriteTextureCache(gl)

        # Optional: modern sprite batching via GL_TEXTURE_2D_ARRAY.
        self.texture_array_atlas: _TextureArrayAtlas | None = None
        self.sprite_batcher: ModernSpriteBatcher | None = None
        self._init_texture_array_pipeline()

    def _init_texture_array_pipeline(self) -> None:
        gl = self.gl
        try:
            atlas = _TextureArrayAtlas(gl)
            if not atlas.initialize():
                return

            batcher = ModernSpriteBatcher(gl)
            if not batcher.initialize(atlas.texture_array):
                atlas.cleanup()
                return

            self.texture_array_atlas = atlas
            self.sprite_batcher = batcher
            logger.info(
                "OpenGLResources: TextureArray pipeline enabled (layer=%sx%s, max_layers=%s)",
                atlas.texture_array.width,
                atlas.texture_array.height,
                atlas.texture_array.max_layers,
            )
        except Exception as exc:
            logger.debug("OpenGLResources: TextureArray pipeline unavailable: %s", exc)
            self.texture_array_atlas = None
            self.sprite_batcher = None

    def _compile_shader(self, source: str, shader_type: int) -> int:
        gl = self.gl
        shader = gl.glCreateShader(shader_type)
        gl.glShaderSource(shader, source)
        gl.glCompileShader(shader)
        status = gl.glGetShaderiv(shader, gl.GL_COMPILE_STATUS)
        if not status:
            info = gl.glGetShaderInfoLog(shader)
            msg = info.decode("utf-8", errors="ignore") if isinstance(info, (bytes, bytearray)) else str(info)
            raise RuntimeError(f"OpenGL shader compile failed: {msg}")
        return int(shader)

    def _create_program(self) -> int:
        gl = self.gl
        vertex_src = """
#version 330 core
layout(location = 0) in vec2 a_pos;
layout(location = 1) in vec2 a_uv;
layout(location = 2) in vec4 a_color;
uniform vec2 u_viewport;
out vec2 v_uv;
out vec4 v_color;
void main() {
    vec2 ndc = vec2(
        (a_pos.x / u_viewport.x) * 2.0 - 1.0,
        1.0 - (a_pos.y / u_viewport.y) * 2.0
    );
    gl_Position = vec4(ndc, 0.0, 1.0);
    v_uv = a_uv;
    v_color = a_color;
}
"""
        fragment_src = """
#version 330 core
in vec2 v_uv;
in vec4 v_color;
uniform sampler2D u_texture;
uniform int u_use_texture;
out vec4 fragColor;
void main() {
    vec4 base = v_color;
    if (u_use_texture == 1) {
        vec4 tex = texture(u_texture, v_uv);
        base *= tex;
    }
    fragColor = base;
}
"""
        vs = self._compile_shader(vertex_src, gl.GL_VERTEX_SHADER)
        fs = self._compile_shader(fragment_src, gl.GL_FRAGMENT_SHADER)
        program = gl.glCreateProgram()
        gl.glAttachShader(program, vs)
        gl.glAttachShader(program, fs)
        gl.glLinkProgram(program)
        status = gl.glGetProgramiv(program, gl.GL_LINK_STATUS)
        if not status:
            info = gl.glGetProgramInfoLog(program)
            msg = info.decode("utf-8", errors="ignore") if isinstance(info, (bytes, bytearray)) else str(info)
            raise RuntimeError(f"OpenGL program link failed: {msg}")
        gl.glDeleteShader(vs)
        gl.glDeleteShader(fs)
        return int(program)

    def _configure_vertex_layout(self) -> None:
        gl = self.gl
        gl.glBindVertexArray(self.vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, self.vbo)
        stride = 8 * 4  # 8 floats
        gl.glEnableVertexAttribArray(0)
        gl.glVertexAttribPointer(0, 2, gl.GL_FLOAT, gl.GL_FALSE, stride, ctypes.c_void_p(0))
        gl.glEnableVertexAttribArray(1)
        gl.glVertexAttribPointer(1, 2, gl.GL_FLOAT, gl.GL_FALSE, stride, ctypes.c_void_p(8))
        gl.glEnableVertexAttribArray(2)
        gl.glVertexAttribPointer(2, 4, gl.GL_FLOAT, gl.GL_FALSE, stride, ctypes.c_void_p(16))
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glBindVertexArray(0)

    def _create_white_texture(self) -> int:
        gl = self.gl
        tex = gl.glGenTextures(1)
        gl.glBindTexture(gl.GL_TEXTURE_2D, tex)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)
        white = bytes([255, 255, 255, 255])
        gl.glTexImage2D(
            gl.GL_TEXTURE_2D,
            0,
            gl.GL_RGBA,
            1,
            1,
            0,
            gl.GL_RGBA,
            gl.GL_UNSIGNED_BYTE,
            white,
        )
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        return int(tex)


class _OpenGLBatcher:
    def __init__(self) -> None:
        self.color_vertices: list[float] = []
        self.line_vertices: list[float] = []
        self.sprite_runs: list[_SpriteRun] = []
        self._current_texture: int | None = None

    def add_color_rect(self, x: int, y: int, w: int, h: int, color: tuple[int, int, int, int]) -> None:
        r, g, b, a = color
        self._append_quad(self.color_vertices, x, y, w, h, (r, g, b, a), uv=(0.0, 0.0, 0.0, 0.0))

    def add_line(self, x0: int, y0: int, x1: int, y1: int, color: tuple[int, int, int, int]) -> None:
        r, g, b, a = color
        self._append_vertex(self.line_vertices, x0, y0, 0.0, 0.0, r, g, b, a)
        self._append_vertex(self.line_vertices, x1, y1, 0.0, 0.0, r, g, b, a)

    def add_sprite(self, texture_id: int, x: int, y: int, w: int, h: int) -> None:
        tex = int(texture_id)
        if not self.sprite_runs or self._current_texture != tex:
            self.sprite_runs.append(_SpriteRun(texture_id=tex, vertices=[]))
            self._current_texture = tex
        run = self.sprite_runs[-1]
        self._append_sprite_quad(run.vertices, x, y, w, h)

    def _append_vertex(
        self,
        out: list[float],
        x: float,
        y: float,
        u: float,
        v: float,
        r: int,
        g: int,
        b: int,
        a: int,
    ) -> None:
        out.extend(
            [
                float(x),
                float(y),
                float(u),
                float(v),
                float(r) / 255.0,
                float(g) / 255.0,
                float(b) / 255.0,
                float(a) / 255.0,
            ]
        )

    def _append_quad(
        self,
        out: list[float],
        x: int,
        y: int,
        w: int,
        h: int,
        color: tuple[int, int, int, int],
        *,
        uv: tuple[float, float, float, float],
    ) -> None:
        r, g, b, a = color
        u0, v0, u1, v1 = uv
        x0 = float(x)
        y0 = float(y)
        x1 = float(x + w)
        y1 = float(y + h)
        self._append_vertex(out, x0, y0, u0, v0, r, g, b, a)
        self._append_vertex(out, x1, y0, u1, v0, r, g, b, a)
        self._append_vertex(out, x1, y1, u1, v1, r, g, b, a)
        self._append_vertex(out, x0, y0, u0, v0, r, g, b, a)
        self._append_vertex(out, x1, y1, u1, v1, r, g, b, a)
        self._append_vertex(out, x0, y1, u0, v1, r, g, b, a)

    def _append_sprite_quad(self, out: list[float], x: int, y: int, w: int, h: int) -> None:
        # Flip V to account for top-left origin in sprite data.
        self._append_quad(out, x, y, w, h, (255, 255, 255, 255), uv=(0.0, 1.0, 1.0, 0.0))


class OpenGLRenderBackend(RenderBackend):
    def __init__(
        self,
        gl: Any,
        resources: OpenGLResources,
        *,
        viewport_width: int,
        viewport_height: int,
        sprite_lookup: SpriteLookup,
    ) -> None:
        self._gl = gl
        self._resources = resources
        self._viewport_width = int(max(1, viewport_width))
        self._viewport_height = int(max(1, viewport_height))
        self._sprite_lookup = sprite_lookup
        self._batcher = _OpenGLBatcher()
        self._sprite_batcher = resources.sprite_batcher
        self._texture_array_atlas = resources.texture_array_atlas
        self._use_texture_array = bool(
            self._sprite_batcher is not None
            and self._texture_array_atlas is not None
            and self._texture_array_atlas.is_initialized
        )
        if self._use_texture_array and self._sprite_batcher is not None:
            self._sprite_batcher.begin()
        self.text_calls: list[tuple[int, int, str, int, int, int, int]] = []

    def clear(self, r: int, g: int, b: int, a: int = 255) -> None:
        self._gl.glClearColor(float(r) / 255.0, float(g) / 255.0, float(b) / 255.0, float(a) / 255.0)
        self._gl.glClear(self._gl.GL_COLOR_BUFFER_BIT)

    def draw_tile_color(self, x: int, y: int, size: int, r: int, g: int, b: int, a: int = 255) -> None:
        self._batcher.add_color_rect(int(x), int(y), int(size), int(size), (int(r), int(g), int(b), int(a)))

    def draw_tile_sprite(self, x: int, y: int, size: int, sprite_id: int) -> None:
        if self._use_texture_array and self._sprite_batcher is not None and self._texture_array_atlas is not None:
            sprite = self._sprite_lookup(int(sprite_id))
            if sprite is None:
                tint = _placeholder_color(int(sprite_id))
                layer = self._texture_array_atlas.white_layer
            else:
                client_id, w, h, bgra = sprite
                layer = self._texture_array_atlas.get_or_upload_layer(int(client_id), int(w), int(h), bgra)
                if layer is None:
                    tint = _placeholder_color(int(sprite_id))
                    layer = self._texture_array_atlas.white_layer
                else:
                    tint = (255, 255, 255, 255)

            self._sprite_batcher.add_sprite(float(x), float(y), float(size), float(size), int(layer), tint=tint)
            return

        sprite = self._sprite_lookup(int(sprite_id))
        if sprite is None:
            fill = _placeholder_color(int(sprite_id))
            border = _placeholder_border_color(int(sprite_id))
            self._batcher.add_color_rect(int(x), int(y), int(size), int(size), fill)
            # Draw contrasting border so placeholder items stand out
            self._batcher.add_line(int(x), int(y), int(x + size), int(y), border)
            self._batcher.add_line(int(x + size), int(y), int(x + size), int(y + size), border)
            self._batcher.add_line(int(x + size), int(y + size), int(x), int(y + size), border)
            self._batcher.add_line(int(x), int(y + size), int(x), int(y), border)
            # Show sprite ID as text overlay for identification
            sid_abs = abs(int(sprite_id))
            if int(size) >= 12:
                self.text_calls.append((int(x) + 1, int(y) + int(size) - 2, str(sid_abs), 255, 255, 255, 200))
            return

        client_id, w, h, bgra = sprite

        def _create_texture() -> int | None:
            try:
                tex = self._gl.glGenTextures(1)
                self._gl.glBindTexture(self._gl.GL_TEXTURE_2D, tex)
                self._gl.glTexParameteri(self._gl.GL_TEXTURE_2D, self._gl.GL_TEXTURE_MIN_FILTER, self._gl.GL_NEAREST)
                self._gl.glTexParameteri(self._gl.GL_TEXTURE_2D, self._gl.GL_TEXTURE_MAG_FILTER, self._gl.GL_NEAREST)
                self._gl.glTexParameteri(self._gl.GL_TEXTURE_2D, self._gl.GL_TEXTURE_WRAP_S, self._gl.GL_CLAMP_TO_EDGE)
                self._gl.glTexParameteri(self._gl.GL_TEXTURE_2D, self._gl.GL_TEXTURE_WRAP_T, self._gl.GL_CLAMP_TO_EDGE)
                self._gl.glTexImage2D(
                    self._gl.GL_TEXTURE_2D,
                    0,
                    self._gl.GL_RGBA,
                    int(w),
                    int(h),
                    0,
                    self._gl.GL_BGRA,
                    self._gl.GL_UNSIGNED_BYTE,
                    bgra,
                )
                self._gl.glBindTexture(self._gl.GL_TEXTURE_2D, 0)
                return int(tex)
            except Exception as exc:
                logger.debug("Failed to create OpenGL texture for sprite_id=%s: %s", client_id, exc)
                return None

        tex_id = self._resources.texture_cache.get_or_create(int(client_id), _create_texture)
        if tex_id is None:
            return

        self._batcher.add_sprite(int(tex_id), int(x), int(y), int(size), int(size))

    def draw_grid_line(self, x0: int, y0: int, x1: int, y1: int, r: int, g: int, b: int, a: int = 255) -> None:
        self._batcher.add_line(int(x0), int(y0), int(x1), int(y1), (int(r), int(g), int(b), int(a)))

    def draw_grid_rect(self, x: int, y: int, w: int, h: int, r: int, g: int, b: int, a: int = 255) -> None:
        x0 = int(x)
        y0 = int(y)
        x1 = int(x + w)
        y1 = int(y + h)
        color = (int(r), int(g), int(b), int(a))
        self._batcher.add_line(x0, y0, x1, y0, color)
        self._batcher.add_line(x1, y0, x1, y1, color)
        self._batcher.add_line(x1, y1, x0, y1, color)
        self._batcher.add_line(x0, y1, x0, y0, color)

    def draw_selection_rect(self, x: int, y: int, w: int, h: int, r: int, g: int, b: int, a: int = 255) -> None:
        self.draw_grid_rect(x, y, w, h, r, g, b, a)

    def draw_indicator_icon(self, x: int, y: int, indicator_type: str, size: int) -> None:
        # Indicators are rendered via QPainter overlays for now.
        return

    def draw_text(self, x: int, y: int, text: str, r: int, g: int, b: int, a: int = 255) -> None:
        self.text_calls.append((int(x), int(y), str(text), int(r), int(g), int(b), int(a)))

    def draw_shade_overlay(self, x: int, y: int, w: int, h: int, alpha: int) -> None:
        self._batcher.add_color_rect(int(x), int(y), int(w), int(h), (0, 0, 0, int(alpha)))

    def flush(self) -> None:
        gl = self._gl
        resources = self._resources
        gl.glUseProgram(resources.program)
        gl.glUniform2f(resources.u_viewport, float(self._viewport_width), float(self._viewport_height))
        gl.glBindVertexArray(resources.vao)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, resources.vbo)

        if self._batcher.color_vertices:
            data = (ctypes.c_float * len(self._batcher.color_vertices))(*self._batcher.color_vertices)
            gl.glBufferData(gl.GL_ARRAY_BUFFER, ctypes.sizeof(data), data, gl.GL_DYNAMIC_DRAW)
            gl.glUniform1i(resources.u_use_texture, 0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, resources.white_texture)
            gl.glDrawArrays(gl.GL_TRIANGLES, 0, len(self._batcher.color_vertices) // 8)

        if self._batcher.line_vertices:
            data = (ctypes.c_float * len(self._batcher.line_vertices))(*self._batcher.line_vertices)
            gl.glBufferData(gl.GL_ARRAY_BUFFER, ctypes.sizeof(data), data, gl.GL_DYNAMIC_DRAW)
            gl.glUniform1i(resources.u_use_texture, 0)
            gl.glBindTexture(gl.GL_TEXTURE_2D, resources.white_texture)
            gl.glDrawArrays(gl.GL_LINES, 0, len(self._batcher.line_vertices) // 8)

        if self._batcher.sprite_runs:
            gl.glUniform1i(resources.u_use_texture, 1)
            for run in self._batcher.sprite_runs:
                if not run.vertices:
                    continue
                data = (ctypes.c_float * len(run.vertices))(*run.vertices)
                gl.glBufferData(gl.GL_ARRAY_BUFFER, ctypes.sizeof(data), data, gl.GL_DYNAMIC_DRAW)
                gl.glBindTexture(gl.GL_TEXTURE_2D, int(run.texture_id))
                gl.glDrawArrays(gl.GL_TRIANGLES, 0, len(run.vertices) // 8)

        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)
        gl.glBindBuffer(gl.GL_ARRAY_BUFFER, 0)
        gl.glBindVertexArray(0)
        gl.glUseProgram(0)

        if self._use_texture_array and self._sprite_batcher is not None:
            self._sprite_batcher.end(self._viewport_width, self._viewport_height)
