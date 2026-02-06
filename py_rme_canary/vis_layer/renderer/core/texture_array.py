"""OpenGL Texture Array (GL_TEXTURE_2D_ARRAY) for sprite atlas.

This module implements the TextureArray class matching the C++ Redux implementation
from `remeres-map-editor-redux/source/rendering/core/texture_array.cpp`.

Architecture:
    All game sprites are stored in layers of this array, eliminating
    texture switching during rendering. Each layer is a fixed-size 2D texture
    (e.g., 32x32 for sprites). Sprites get a layer_index which becomes
    the Z coordinate in shader sampling.

Usage:
    gl = get_opengl_context()
    array = TextureArray(gl)
    array.initialize(32, 32, max_layers=4096)

    # Upload sprite to layer
    layer = array.allocate_layer()
    array.upload_layer(layer, rgba_bytes)

    # Bind for rendering
    array.bind(unit=0)

Reference:
    - C++ Header: texture_array.h
    - C++ Source: texture_array.cpp
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class TextureArray:
    """OpenGL Texture Array (GL_TEXTURE_2D_ARRAY) for sprite atlas.

    This class manages a 3D texture where each layer stores a sprite.
    Using a texture array eliminates texture switching during rendering,
    significantly improving performance for large tilemaps.

    Attributes:
        texture_id: OpenGL texture ID.
        width: Width of each layer in pixels.
        height: Height of each layer in pixels.
        max_layers: Maximum number of layers allocated.
        allocated_layers: Number of layers currently in use.
    """

    # Default configuration matching Redux
    DEFAULT_WIDTH = 32
    DEFAULT_HEIGHT = 32
    DEFAULT_MAX_LAYERS = 4096

    def __init__(self, gl: Any) -> None:
        """Initialize TextureArray.

        Args:
            gl: OpenGL context (from PyOpenGL or moderngl).
        """
        self._gl = gl
        self._texture_id: int = 0
        self._width: int = 0
        self._height: int = 0
        self._max_layers: int = 0
        self._allocated_layers: int = 0
        self._initialized: bool = False

    @property
    def texture_id(self) -> int:
        """Get the OpenGL texture ID."""
        return self._texture_id

    @property
    def width(self) -> int:
        """Get width of each layer."""
        return self._width

    @property
    def height(self) -> int:
        """Get height of each layer."""
        return self._height

    @property
    def max_layers(self) -> int:
        """Get maximum number of layers."""
        return self._max_layers

    @property
    def allocated_layers(self) -> int:
        """Get number of allocated layers."""
        return self._allocated_layers

    @property
    def is_initialized(self) -> bool:
        """Check if texture array is initialized."""
        return self._initialized

    def initialize(
        self,
        width: int = DEFAULT_WIDTH,
        height: int = DEFAULT_HEIGHT,
        max_layers: int = DEFAULT_MAX_LAYERS,
    ) -> bool:
        """Initialize the texture array.

        Creates an immutable texture storage with the specified dimensions.
        Uses GL_RGBA8 format with nearest-neighbor filtering (no mipmaps).

        Args:
            width: Width of each layer (e.g., 32).
            height: Height of each layer (e.g., 32).
            max_layers: Maximum number of layers to allocate.

        Returns:
            True if successful, False otherwise.

        Raises:
            RuntimeError: If OpenGL operations fail.
        """
        if self._initialized:
            logger.warning("TextureArray: Already initialized")
            return True

        gl = self._gl

        self._width = int(width)
        self._height = int(height)
        self._max_layers = int(max_layers)

        try:
            # Create texture array using DSA if available, fallback otherwise
            if hasattr(gl, "glCreateTextures"):
                # OpenGL 4.5 DSA path
                tex_id = gl.glGenTextures(1)
                self._texture_id = int(tex_id) if not isinstance(tex_id, int) else tex_id

                gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, self._texture_id)
            else:
                # Legacy path
                self._texture_id = int(gl.glGenTextures(1))
                gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, self._texture_id)

            if self._texture_id == 0:
                logger.error("TextureArray: Failed to create texture")
                return False

            # Allocate immutable storage for all layers
            # Using RGBA8 format, no mipmaps (level 1)
            gl.glTexStorage3D(
                gl.GL_TEXTURE_2D_ARRAY,
                1,  # levels (no mipmaps)
                gl.GL_RGBA8,
                self._width,
                self._height,
                self._max_layers,
            )

            # Set texture parameters - nearest filtering for pixel art
            gl.glTexParameteri(gl.GL_TEXTURE_2D_ARRAY, gl.GL_TEXTURE_MIN_FILTER, gl.GL_NEAREST)
            gl.glTexParameteri(gl.GL_TEXTURE_2D_ARRAY, gl.GL_TEXTURE_MAG_FILTER, gl.GL_NEAREST)
            gl.glTexParameteri(gl.GL_TEXTURE_2D_ARRAY, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
            gl.glTexParameteri(gl.GL_TEXTURE_2D_ARRAY, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)

            # Unbind
            gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, 0)

            self._allocated_layers = 0
            self._initialized = True

            logger.info("TextureArray: Initialized %dx%d with %d layers", self._width, self._height, self._max_layers)

            return True

        except Exception as e:
            logger.error("TextureArray: Failed to initialize - %s", e)
            self.cleanup()
            return False

    def upload_layer(self, layer: int, rgba_data: bytes | bytearray) -> bool:
        """Upload RGBA pixel data to a specific layer.

        Args:
            layer: Layer index (0 to max_layers-1).
            rgba_data: RGBA pixel data (width * height * 4 bytes).

        Returns:
            True if successful, False otherwise.
        """
        if not self._initialized:
            logger.error("TextureArray: Not initialized")
            return False

        if layer < 0 or layer >= self._max_layers:
            logger.error("TextureArray: Layer %d out of range (max: %d)", layer, self._max_layers)
            return False

        if rgba_data is None:
            logger.error("TextureArray: Null data for layer %d", layer)
            return False

        expected_size = self._width * self._height * 4
        if len(rgba_data) != expected_size:
            logger.error(
                "TextureArray: Data size mismatch for layer %d (got %d, expected %d)",
                layer,
                len(rgba_data),
                expected_size,
            )
            return False

        gl = self._gl

        try:
            gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, self._texture_id)

            # Upload to specific layer (z offset = layer, depth = 1 layer)
            gl.glTexSubImage3D(
                gl.GL_TEXTURE_2D_ARRAY,
                0,  # level
                0,
                0,
                layer,  # x, y, z offset
                self._width,
                self._height,
                1,  # width, height, depth
                gl.GL_RGBA,
                gl.GL_UNSIGNED_BYTE,
                rgba_data,
            )

            gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, 0)
            return True

        except Exception as e:
            logger.error("TextureArray: Failed to upload layer %d - %s", layer, e)
            return False

    def allocate_layer(self) -> int:
        """Allocate the next available layer.

        Returns:
            Layer index, or -1 if full.
        """
        if not self._initialized:
            return -1

        if self._allocated_layers >= self._max_layers:
            logger.error("TextureArray: No more layers available (allocated: %d)", self._allocated_layers)
            return -1

        layer = self._allocated_layers
        self._allocated_layers += 1
        return layer

    def bind(self, unit: int = 0) -> None:
        """Bind the texture array to a texture unit.

        Args:
            unit: Texture unit (0, 1, 2, ...).
        """
        if not self._initialized:
            return

        gl = self._gl

        try:
            if hasattr(gl, "glBindTextureUnit"):
                # OpenGL 4.5 DSA path
                gl.glBindTextureUnit(unit, self._texture_id)
            else:
                # Legacy path
                gl.glActiveTexture(gl.GL_TEXTURE0 + unit)
                gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, self._texture_id)
        except Exception as e:
            logger.error("TextureArray: Failed to bind - %s", e)

    def unbind(self, unit: int = 0) -> None:
        """Unbind the texture array from a texture unit.

        Args:
            unit: Texture unit (0, 1, 2, ...).
        """
        if not self._initialized:
            return

        gl = self._gl

        try:
            gl.glActiveTexture(gl.GL_TEXTURE0 + unit)
            gl.glBindTexture(gl.GL_TEXTURE_2D_ARRAY, 0)
        except Exception:
            pass

    def cleanup(self) -> None:
        """Release GPU resources."""
        if self._texture_id:
            try:
                self._gl.glDeleteTextures([self._texture_id])
            except Exception:
                pass
            self._texture_id = 0

        self._initialized = False
        self._allocated_layers = 0
        logger.debug("TextureArray: Cleaned up")

    def __del__(self) -> None:
        """Destructor - cleanup on garbage collection."""
        self.cleanup()

    def __repr__(self) -> str:
        return (
            f"TextureArray(id={self._texture_id}, "
            f"{self._width}x{self._height}, "
            f"layers={self._allocated_layers}/{self._max_layers})"
        )
