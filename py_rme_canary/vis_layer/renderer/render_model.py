"""
RenderModel: Qt-free, thread-safe structure for draw commands.
This module defines the data structures that represent what to draw,
without depending on any specific rendering backend (QPainter, OpenGL, etc.)
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Optional


class DrawCommandType(Enum):
    """Types of drawing operations."""
    FILL_RECT = auto()
    DRAW_RECT = auto()
    DRAW_SPRITE = auto()
    DRAW_TEXT = auto()
    DRAW_LINE = auto()


class LayerType(Enum):
    """Rendering layer order (bottom to top)."""
    GROUND = 0
    BORDERS = 1
    ITEMS = 2
    CREATURES = 3
    SELECTION = 10
    GRID = 20
    OVERLAY = 30


@dataclass(frozen=True, slots=True)
class Color:
    """RGBA color representation."""
    r: int
    g: int
    b: int
    a: int = 255

    @classmethod
    def from_hex(cls, hex_str: str) -> "Color":
        """Create color from hex string like '#RRGGBB' or '#RRGGBBAA'."""
        hex_str = hex_str.lstrip("#")
        if len(hex_str) not in (6, 8):
            raise ValueError(f"Invalid hex color: {hex_str}")
        
        try:
            if len(hex_str) == 6:
                return cls(
                    r=int(hex_str[0:2], 16),
                    g=int(hex_str[2:4], 16),
                    b=int(hex_str[4:6], 16),
                )
            else:  # len == 8
                return cls(
                    r=int(hex_str[0:2], 16),
                    g=int(hex_str[2:4], 16),
                    b=int(hex_str[4:6], 16),
                    a=int(hex_str[6:8], 16),
                )
        except ValueError:
            raise ValueError(f"Invalid hex color: {hex_str}")


@dataclass(frozen=True, slots=True)
class Rect:
    """Rectangle with position and size."""
    x: int
    y: int
    width: int
    height: int


@dataclass(frozen=True, slots=True)
class DrawCommand:
    """A single drawing operation."""
    command_type: DrawCommandType
    layer: LayerType
    rect: Rect
    color: Optional[Color] = None
    sprite_id: Optional[int] = None
    text: Optional[str] = None
    line_width: int = 1
    dashed: bool = False


@dataclass(slots=True)
class RenderFrame:
    """
    A complete frame to be rendered.
    Contains all draw commands for a single frame, organized by layer.
    Thread-safe: can be built in a worker thread and consumed by UI thread.
    """
    commands: list[DrawCommand] = field(default_factory=list)
    viewport_origin_x: int = 0
    viewport_origin_y: int = 0
    viewport_z: int = 7
    tile_size: int = 32

    def add_command(self, command: DrawCommand) -> None:
        """Add a draw command to the frame."""
        self.commands.append(command)

    def get_commands_by_layer(self) -> dict[LayerType, list[DrawCommand]]:
        """Return commands grouped by layer, sorted by layer order."""
        by_layer: dict[LayerType, list[DrawCommand]] = {}
        for cmd in self.commands:
            if cmd.layer not in by_layer:
                by_layer[cmd.layer] = []
            by_layer[cmd.layer].append(cmd)
        return dict(sorted(by_layer.items(), key=lambda x: x[0].value))

    def clear(self) -> None:
        """Clear all commands."""
        self.commands.clear()


# Convenience colors matching dark theme
THEME_COLORS = {
    "background": Color(30, 30, 30),
    "empty_tile": Color(43, 43, 43),
    "grid": Color(58, 58, 58),
    "selection": Color(230, 230, 230),
    "selection_box": Color(200, 200, 200),
    "highlight": Color(42, 130, 218),
}
