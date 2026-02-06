"""Lighting System for In-Game Preview.

This module implements per-tile lighting with ambient light support
for the preview window, matching the reference in project_tasks.json FUTURE-003.

Architecture:
    - LightSource: Point light with position, radius, intensity, and color.
    - LightingSystem: Manages multiple lights and generates a lightmap texture.
    - The lightmap is sampled in the LIGHTING_FRAGMENT shader to apply
      per-pixel lighting to the rendered scene.

Reference:
    - GLSL: shaders/__init__.py (LIGHTING_VERTEX, LIGHTING_FRAGMENT)
    - Redux: No direct equivalent (custom implementation)
"""

from __future__ import annotations

import logging
import math
from dataclasses import dataclass
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class LightSource:
    """A point light source.

    Attributes:
        x: World X position.
        y: World Y position.
        z: Floor level (affects intensity).
        radius: Light radius in tiles.
        intensity: Light intensity (0.0-1.0).
        color: RGB color tuple (0-255 each).
        falloff: Falloff exponent (1.0 = linear, 2.0 = quadratic).
    """

    x: int
    y: int
    z: int = 7
    radius: float = 5.0
    intensity: float = 1.0
    color: tuple[int, int, int] = (255, 200, 150)  # Warm light default
    falloff: float = 1.5


@dataclass
class AmbientLight:
    """Global ambient lighting settings.

    Attributes:
        color: RGB ambient color (0-255 each).
        intensity: Ambient intensity multiplier (0.0-1.0).
        underground_factor: Darkness multiplier for underground floors (0-6).
        outdoor_time: Time of day (0-24) for outdoor lighting cycle.
    """

    color: tuple[int, int, int] = (100, 100, 120)  # Slight blue tint
    intensity: float = 0.3
    underground_factor: float = 0.7
    outdoor_time: float = 12.0  # Noon by default

    def get_effective_color(self, floor: int) -> tuple[float, float, float]:
        """Get effective ambient color for a floor.

        Underground floors (0-6) get progressively darker.
        Surface floors (7+) use outdoor lighting based on time.

        Args:
            floor: Z coordinate (0-15).

        Returns:
            Normalized RGB tuple (0.0-1.0).
        """
        r, g, b = self.color
        base_r = (r / 255.0) * self.intensity
        base_g = (g / 255.0) * self.intensity
        base_b = (b / 255.0) * self.intensity

        if floor < 7:
            # Underground - apply darkness factor
            depth = 7 - floor
            darkness = self.underground_factor**depth
            return (base_r * darkness, base_g * darkness, base_b * darkness)
        else:
            # Surface - apply time-of-day cycle
            time_factor = self._get_time_factor()
            return (base_r * time_factor, base_g * time_factor, base_b * time_factor)

    def _get_time_factor(self) -> float:
        """Calculate lighting factor based on time of day.

        Returns a value between 0.3 (night) and 1.0 (noon).
        """
        # Simple sinusoidal day/night cycle
        # Noon (12:00) = max, Midnight (0:00/24:00) = min
        normalized_time = (self.outdoor_time % 24) / 24.0
        # Shift so noon = peak
        angle = (normalized_time - 0.5) * 2 * math.pi
        factor = (math.cos(angle) + 1) / 2  # 0-1 range
        return 0.3 + factor * 0.7  # 0.3-1.0 range


@dataclass
class TileLighting:
    """Lighting data for a single tile.

    Attributes:
        intensity: Combined light intensity (0.0-1.0).
        color: Combined light color (normalized RGB).
    """

    intensity: float = 0.0
    color: tuple[float, float, float] = (1.0, 1.0, 1.0)


class LightingSystem:
    """Manages lighting for the preview window.

    This system collects light sources, computes per-tile lighting,
    and generates a texture that can be sampled in the fragment shader.

    Usage:
        lighting = LightingSystem(gl)
        lighting.set_viewport(800, 600)
        lighting.set_ambient(AmbientLight(intensity=0.3))

        # Add lights
        lighting.add_light(LightSource(x=100, y=100, radius=5, intensity=0.8))

        # Each frame:
        lighting.update(camera_x, camera_y, current_floor, tile_size)
        lighting.bind_lightmap(texture_unit=1)
    """

    # Lightmap is lower resolution than screen for performance
    LIGHTMAP_SCALE = 4  # 1 pixel per 4 screen pixels
    MAX_LIGHTS = 64

    def __init__(self, gl: Any) -> None:
        """Initialize the lighting system.

        Args:
            gl: OpenGL context.
        """
        self._gl = gl
        self._lights: list[LightSource] = []
        self._ambient = AmbientLight()
        self._enabled = True

        # Lightmap texture
        self._lightmap_texture: int = 0
        self._lightmap_width = 1
        self._lightmap_height = 1
        self._lightmap_data: bytearray | None = None

        # Viewport info
        self._viewport_width = 800
        self._viewport_height = 600

        self._initialized = False

    @property
    def enabled(self) -> bool:
        return self._enabled

    @enabled.setter
    def enabled(self, value: bool) -> None:
        self._enabled = bool(value)

    @property
    def ambient(self) -> AmbientLight:
        return self._ambient

    def set_ambient(self, ambient: AmbientLight) -> None:
        """Set ambient lighting configuration."""
        self._ambient = ambient

    def set_viewport(self, width: int, height: int) -> None:
        """Set the viewport size.

        Args:
            width: Viewport width in pixels.
            height: Viewport height in pixels.
        """
        self._viewport_width = max(1, int(width))
        self._viewport_height = max(1, int(height))

        # Recalculate lightmap size
        new_w = max(1, self._viewport_width // self.LIGHTMAP_SCALE)
        new_h = max(1, self._viewport_height // self.LIGHTMAP_SCALE)

        if new_w != self._lightmap_width or new_h != self._lightmap_height:
            self._lightmap_width = new_w
            self._lightmap_height = new_h
            self._recreate_lightmap_texture()

    def _recreate_lightmap_texture(self) -> None:
        """Create or resize the lightmap texture."""
        gl = self._gl

        # Delete old texture
        if self._lightmap_texture:
            try:
                gl.glDeleteTextures([self._lightmap_texture])
            except Exception:
                pass

        # Create new texture
        self._lightmap_texture = int(gl.glGenTextures(1))
        gl.glBindTexture(gl.GL_TEXTURE_2D, self._lightmap_texture)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MIN_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_MAG_FILTER, gl.GL_LINEAR)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_S, gl.GL_CLAMP_TO_EDGE)
        gl.glTexParameteri(gl.GL_TEXTURE_2D, gl.GL_TEXTURE_WRAP_T, gl.GL_CLAMP_TO_EDGE)

        # Allocate RGBA8 storage
        self._lightmap_data = bytearray(self._lightmap_width * self._lightmap_height * 4)
        gl.glTexImage2D(
            gl.GL_TEXTURE_2D,
            0,
            gl.GL_RGBA8,
            self._lightmap_width,
            self._lightmap_height,
            0,
            gl.GL_RGBA,
            gl.GL_UNSIGNED_BYTE,
            bytes(self._lightmap_data),
        )
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

        self._initialized = True
        logger.debug("LightingSystem: Lightmap %dx%d created", self._lightmap_width, self._lightmap_height)

    def add_light(self, light: LightSource) -> None:
        """Add a light source.

        Args:
            light: LightSource to add.
        """
        if len(self._lights) >= self.MAX_LIGHTS:
            logger.warning("LightingSystem: Max lights (%d) reached", self.MAX_LIGHTS)
            return
        self._lights.append(light)

    def remove_light(self, light: LightSource) -> None:
        """Remove a light source."""
        try:
            self._lights.remove(light)
        except ValueError:
            pass

    def clear_lights(self) -> None:
        """Remove all light sources."""
        self._lights.clear()

    def update(
        self,
        camera_x: float,
        camera_y: float,
        current_floor: int,
        tile_size: float,
    ) -> None:
        """Update the lightmap for the current frame.

        Args:
            camera_x: Camera X position in world units.
            camera_y: Camera Y position in world units.
            current_floor: Current floor being viewed.
            tile_size: Size of one tile in pixels.
        """
        if not self._enabled or not self._initialized:
            return

        if self._lightmap_data is None:
            return

        # Clear lightmap with ambient
        ambient_color = self._ambient.get_effective_color(current_floor)
        ambient_r = int(ambient_color[0] * 255)
        ambient_g = int(ambient_color[1] * 255)
        ambient_b = int(ambient_color[2] * 255)

        for i in range(0, len(self._lightmap_data), 4):
            self._lightmap_data[i] = ambient_r
            self._lightmap_data[i + 1] = ambient_g
            self._lightmap_data[i + 2] = ambient_b
            self._lightmap_data[i + 3] = 255

        # Apply each light source
        for light in self._lights:
            # Skip lights on different floors (with some bleed for adjacent floors)
            floor_diff = abs(light.z - current_floor)
            if floor_diff > 1:
                continue

            floor_factor = 1.0 if floor_diff == 0 else 0.3

            self._apply_light(light, camera_x, camera_y, tile_size, floor_factor)

        # Upload lightmap to GPU
        gl = self._gl
        gl.glBindTexture(gl.GL_TEXTURE_2D, self._lightmap_texture)
        gl.glTexSubImage2D(
            gl.GL_TEXTURE_2D,
            0,
            0,
            0,
            self._lightmap_width,
            self._lightmap_height,
            gl.GL_RGBA,
            gl.GL_UNSIGNED_BYTE,
            bytes(self._lightmap_data),
        )
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

    def _apply_light(
        self,
        light: LightSource,
        camera_x: float,
        camera_y: float,
        tile_size: float,
        floor_factor: float,
    ) -> None:
        """Apply a single light to the lightmap."""
        if self._lightmap_data is None:
            return

        # Convert light world position to screen position
        screen_x = (light.x - camera_x) * tile_size
        screen_y = (light.y - camera_y) * tile_size

        # Convert to lightmap coordinates
        lm_x = screen_x / self.LIGHTMAP_SCALE
        lm_y = screen_y / self.LIGHTMAP_SCALE

        # Light radius in lightmap pixels
        lm_radius = (light.radius * tile_size) / self.LIGHTMAP_SCALE

        # Iterate pixels in bounding box
        min_x = max(0, int(lm_x - lm_radius))
        max_x = min(self._lightmap_width - 1, int(lm_x + lm_radius))
        min_y = max(0, int(lm_y - lm_radius))
        max_y = min(self._lightmap_height - 1, int(lm_y + lm_radius))

        # Normalize light color
        lr = light.color[0] / 255.0
        lg = light.color[1] / 255.0
        lb = light.color[2] / 255.0

        for py in range(min_y, max_y + 1):
            for px in range(min_x, max_x + 1):
                # Distance from light center
                dx = px - lm_x
                dy = py - lm_y
                dist = math.sqrt(dx * dx + dy * dy)

                if dist > lm_radius:
                    continue

                # Falloff
                t = dist / lm_radius  # 0 at center, 1 at edge
                attenuation = max(0.0, 1.0 - (t**light.falloff))
                intensity = light.intensity * attenuation * floor_factor

                # Blend with existing light (additive)
                idx = (py * self._lightmap_width + px) * 4

                existing_r = self._lightmap_data[idx] / 255.0
                existing_g = self._lightmap_data[idx + 1] / 255.0
                existing_b = self._lightmap_data[idx + 2] / 255.0

                new_r = min(1.0, existing_r + lr * intensity)
                new_g = min(1.0, existing_g + lg * intensity)
                new_b = min(1.0, existing_b + lb * intensity)

                self._lightmap_data[idx] = int(new_r * 255)
                self._lightmap_data[idx + 1] = int(new_g * 255)
                self._lightmap_data[idx + 2] = int(new_b * 255)

    def bind_lightmap(self, unit: int = 1) -> None:
        """Bind the lightmap texture to a texture unit.

        Args:
            unit: Texture unit (default 1, since scene is usually on 0).
        """
        if not self._initialized:
            return

        gl = self._gl
        gl.glActiveTexture(gl.GL_TEXTURE0 + unit)
        gl.glBindTexture(gl.GL_TEXTURE_2D, self._lightmap_texture)

    def unbind_lightmap(self, unit: int = 1) -> None:
        """Unbind the lightmap texture."""
        gl = self._gl
        gl.glActiveTexture(gl.GL_TEXTURE0 + unit)
        gl.glBindTexture(gl.GL_TEXTURE_2D, 0)

    def get_ambient_uniform(self, floor: int) -> tuple[float, float, float]:
        """Get ambient light color for shader uniform.

        Args:
            floor: Current floor level.

        Returns:
            Normalized RGB tuple for u_ambient_light uniform.
        """
        return self._ambient.get_effective_color(floor)

    def cleanup(self) -> None:
        """Release GPU resources."""
        if self._lightmap_texture:
            try:
                self._gl.glDeleteTextures([self._lightmap_texture])
            except Exception:
                pass
            self._lightmap_texture = 0

        self._initialized = False
        self._lightmap_data = None
        logger.debug("LightingSystem: Cleaned up")

    def __del__(self) -> None:
        self.cleanup()
