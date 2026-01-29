"""Light rendering settings and configuration.

Manages global light and ambient light settings for map rendering:
- Global ambient light level
- Light rendering mode
- Light color tint
- Dynamic light effects
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class LightMode(str, Enum):
    """Light rendering mode."""

    FULL = "full"  # Full light effects with shadows
    SIMPLE = "simple"  # Simple light without shadows
    AMBIENT_ONLY = "ambient_only"  # Only ambient light, no item lights
    OFF = "off"  # No light rendering


@dataclass(frozen=True, slots=True)
class LightColor:
    """Light color with RGB components.

    Attributes:
        r: Red component (0-255)
        g: Green component (0-255)
        b: Blue component (0-255)
    """

    r: int
    g: int
    b: int

    def __post_init__(self) -> None:
        """Validate color components."""
        for component in (self.r, self.g, self.b):
            if not 0 <= component <= 255:
                msg = f"Color components must be 0-255, got {component}"
                raise ValueError(msg)

    def to_rgb_tuple(self) -> tuple[int, int, int]:
        """Convert to RGB tuple."""
        return (self.r, self.g, self.b)

    def to_hex(self) -> str:
        """Convert to hex string."""
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    @classmethod
    def from_rgb(cls, r: int, g: int, b: int) -> LightColor:
        """Create color from RGB components."""
        return cls(r, g, b)

    @classmethod
    def from_hex(cls, hex_color: str) -> LightColor:
        """Create color from hex string.

        Args:
            hex_color: Hex color string (e.g., "#FFFFFF" or "FFFFFF")

        Example:
            >>> LightColor.from_hex("#FFCC99")
            LightColor(r=255, g=204, b=153)
        """
        hex_color = hex_color.lstrip("#")
        if len(hex_color) != 6:  # noqa: PLR2004
            msg = "Hex color must be 6 characters (RRGGBB)"
            raise ValueError(msg)

        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        return cls(r, g, b)


@dataclass(frozen=True, slots=True)
class LightSettings:
    """Global light rendering configuration.

    Attributes:
        enabled: Whether light rendering is enabled
        mode: Light rendering mode (full/simple/ambient_only/off)
        ambient_level: Global ambient light level (0-255, 0=dark, 255=bright)
        ambient_color: Ambient light color tint
        show_light_sources: Highlight items that emit light
        dynamic_updates: Update lights in real-time during editing
    """

    enabled: bool = True
    mode: LightMode = LightMode.SIMPLE
    ambient_level: int = 255  # Full brightness by default
    ambient_color: LightColor = LightColor(255, 255, 255)  # White
    show_light_sources: bool = False
    dynamic_updates: bool = True

    def __post_init__(self) -> None:
        """Validate settings."""
        if not 0 <= self.ambient_level <= 255:
            msg = "Ambient level must be 0-255"
            raise ValueError(msg)

    def with_enabled(self, enabled: bool) -> LightSettings:
        """Create new settings with different enabled state."""
        return LightSettings(
            enabled=enabled,
            mode=self.mode,
            ambient_level=self.ambient_level,
            ambient_color=self.ambient_color,
            show_light_sources=self.show_light_sources,
            dynamic_updates=self.dynamic_updates,
        )

    def with_mode(self, mode: LightMode) -> LightSettings:
        """Create new settings with different light mode."""
        return LightSettings(
            enabled=self.enabled,
            mode=mode,
            ambient_level=self.ambient_level,
            ambient_color=self.ambient_color,
            show_light_sources=self.show_light_sources,
            dynamic_updates=self.dynamic_updates,
        )

    def with_ambient_level(self, level: int) -> LightSettings:
        """Create new settings with different ambient light level."""
        return LightSettings(
            enabled=self.enabled,
            mode=self.mode,
            ambient_level=level,
            ambient_color=self.ambient_color,
            show_light_sources=self.show_light_sources,
            dynamic_updates=self.dynamic_updates,
        )

    def with_ambient_color(self, color: LightColor) -> LightSettings:
        """Create new settings with different ambient color."""
        return LightSettings(
            enabled=self.enabled,
            mode=self.mode,
            ambient_level=self.ambient_level,
            ambient_color=color,
            show_light_sources=self.show_light_sources,
            dynamic_updates=self.dynamic_updates,
        )

    def with_show_light_sources(self, show: bool) -> LightSettings:
        """Create new settings with different light source visibility."""
        return LightSettings(
            enabled=self.enabled,
            mode=self.mode,
            ambient_level=self.ambient_level,
            ambient_color=self.ambient_color,
            show_light_sources=show,
            dynamic_updates=self.dynamic_updates,
        )

    def is_dark_mode(self) -> bool:
        """Check if current settings create dark environment."""
        return self.enabled and self.ambient_level < 128

    def get_brightness_percentage(self) -> float:
        """Get ambient brightness as percentage (0.0-1.0)."""
        return self.ambient_level / 255.0


# Predefined light presets
LIGHT_PRESETS = {
    "daylight": LightSettings(
        enabled=True,
        mode=LightMode.SIMPLE,
        ambient_level=255,
        ambient_color=LightColor(255, 255, 255),
    ),
    "twilight": LightSettings(
        enabled=True,
        mode=LightMode.FULL,
        ambient_level=180,
        ambient_color=LightColor(255, 200, 150),  # Warm orange tint
    ),
    "night": LightSettings(
        enabled=True,
        mode=LightMode.FULL,
        ambient_level=80,
        ambient_color=LightColor(150, 150, 200),  # Cool blue tint
    ),
    "cave": LightSettings(
        enabled=True,
        mode=LightMode.FULL,
        ambient_level=30,
        ambient_color=LightColor(180, 180, 200),  # Dim blue-gray
        show_light_sources=True,
    ),
    "editor_default": LightSettings(
        enabled=False,  # No light effects in editor by default
        mode=LightMode.OFF,
        ambient_level=255,
    ),
}
