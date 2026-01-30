"""Grid settings and configuration.

Manages grid display settings including:
- Grid visibility
- Grid color and transparency
- Grid line thickness
- Grid type (standard/dotted/dashed)
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class GridType(str, Enum):
    """Grid line rendering style."""

    SOLID = "solid"
    DOTTED = "dotted"
    DASHED = "dashed"
    NONE = "none"


@dataclass(frozen=True, slots=True)
class GridColor:
    """Grid color with RGBA components.

    Attributes:
        r: Red component (0-255)
        g: Green component (0-255)
        b: Blue component (0-255)
        a: Alpha/transparency (0-255, 0=transparent, 255=opaque)
    """

    r: int
    g: int
    b: int
    a: int

    def __post_init__(self) -> None:
        """Validate color components."""
        for component in (self.r, self.g, self.b, self.a):
            if not 0 <= component <= 255:
                msg = f"Color components must be 0-255, got {component}"
                raise ValueError(msg)

    def to_rgba_tuple(self) -> tuple[int, int, int, int]:
        """Convert to RGBA tuple."""
        return (self.r, self.g, self.b, self.a)

    def to_hex(self) -> str:
        """Convert to hex string (without alpha)."""
        return f"#{self.r:02x}{self.g:02x}{self.b:02x}"

    def with_alpha(self, alpha: int) -> GridColor:
        """Create new color with different alpha."""
        return GridColor(self.r, self.g, self.b, alpha)

    @classmethod
    def from_rgba(cls, r: int, g: int, b: int, a: int = 255) -> GridColor:
        """Create color from RGBA components."""
        return cls(r, g, b, a)

    @classmethod
    def from_hex(cls, hex_color: str, alpha: int = 255) -> GridColor:
        """Create color from hex string.

        Args:
            hex_color: Hex color string (e.g., "#FF0000" or "FF0000")
            alpha: Alpha component (0-255)

        Example:
            >>> GridColor.from_hex("#FF0000", 128)
            GridColor(r=255, g=0, b=0, a=128)
        """
        hex_color = hex_color.lstrip("#")
        if len(hex_color) != 6:  # noqa: PLR2004
            msg = "Hex color must be 6 characters (RRGGBB)"
            raise ValueError(msg)

        r = int(hex_color[0:2], 16)
        g = int(hex_color[2:4], 16)
        b = int(hex_color[4:6], 16)

        return cls(r, g, b, alpha)


@dataclass(frozen=True, slots=True)
class GridSettings:
    """Grid display configuration.

    Attributes:
        enabled: Whether grid is visible
        grid_type: Line rendering style
        color: Grid line color with transparency
        thickness: Line thickness in pixels (1-5)
        show_coordinates: Show tile coordinates on grid
    """

    enabled: bool = True
    grid_type: GridType = GridType.SOLID
    color: GridColor = GridColor(128, 128, 128, 100)  # Gray, semi-transparent
    thickness: int = 1
    show_coordinates: bool = False

    def __post_init__(self) -> None:
        """Validate settings."""
        if not 1 <= self.thickness <= 5:  # noqa: PLR2004
            msg = "Grid thickness must be 1-5 pixels"
            raise ValueError(msg)

    def with_enabled(self, enabled: bool) -> GridSettings:
        """Create new settings with different enabled state."""
        return GridSettings(
            enabled=enabled,
            grid_type=self.grid_type,
            color=self.color,
            thickness=self.thickness,
            show_coordinates=self.show_coordinates,
        )

    def with_color(self, color: GridColor) -> GridSettings:
        """Create new settings with different color."""
        return GridSettings(
            enabled=self.enabled,
            grid_type=self.grid_type,
            color=color,
            thickness=self.thickness,
            show_coordinates=self.show_coordinates,
        )

    def with_transparency(self, alpha: int) -> GridSettings:
        """Create new settings with different transparency."""
        new_color = self.color.with_alpha(alpha)
        return self.with_color(new_color)

    def with_type(self, grid_type: GridType) -> GridSettings:
        """Create new settings with different grid type."""
        return GridSettings(
            enabled=self.enabled,
            grid_type=grid_type,
            color=self.color,
            thickness=self.thickness,
            show_coordinates=self.show_coordinates,
        )

    def with_thickness(self, thickness: int) -> GridSettings:
        """Create new settings with different line thickness."""
        return GridSettings(
            enabled=self.enabled,
            grid_type=self.grid_type,
            color=self.color,
            thickness=thickness,
            show_coordinates=self.show_coordinates,
        )


# Predefined color schemes
GRID_COLORS = {
    "default": GridColor(128, 128, 128, 100),  # Gray
    "white": GridColor(255, 255, 255, 120),  # White
    "black": GridColor(0, 0, 0, 150),  # Black
    "blue": GridColor(64, 128, 255, 100),  # Blue
    "green": GridColor(64, 255, 128, 100),  # Green
    "red": GridColor(255, 64, 64, 100),  # Red
}
