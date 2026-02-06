"""Mirror drawing helpers (legacy RME-compatible).

This module implements the *position mirroring* behavior from the legacy RME
editor, used to duplicate draw positions across a mirror axis.

Legacy references:
- `source/gui.h` / `source/gui.cpp`: mirror state + axis selection.
- `source/map_display.cpp`: `getMirroredPosition` + `unionWithMirrored`.
- `source/ground_brush.cpp`: flip logic for borders.

Key behavior (matches legacy):
- Mirror axis is either X or Y.
- Mirrored coordinate is computed as:
  - X axis: x' = 2*axis_value - x
  - Y axis: y' = 2*axis_value - y
- If mirrored position equals the original, it is ignored.
- When producing a draw list, positions are de-duplicated (stable order).

This is pure logic: no UI and no map mutations.
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from enum import IntEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

TibiaPosition = tuple[int, int, int]


class BorderDirection(IntEnum):
    """Border directions for wall/ground auto-bordering.

    Matches the legacy RME border direction flags.
    """

    NORTH = 0
    EAST = 1
    SOUTH = 2
    WEST = 3
    NORTH_EAST = 4
    SOUTH_EAST = 5
    SOUTH_WEST = 6
    NORTH_WEST = 7
    CENTER = 8


# Flip mappings for horizontal (X-axis) and vertical (Y-axis) mirroring
# Based on source/ground_brush.cpp flip logic
FLIP_HORIZONTAL: dict[BorderDirection, BorderDirection] = {
    BorderDirection.NORTH: BorderDirection.NORTH,
    BorderDirection.EAST: BorderDirection.WEST,
    BorderDirection.SOUTH: BorderDirection.SOUTH,
    BorderDirection.WEST: BorderDirection.EAST,
    BorderDirection.NORTH_EAST: BorderDirection.NORTH_WEST,
    BorderDirection.SOUTH_EAST: BorderDirection.SOUTH_WEST,
    BorderDirection.SOUTH_WEST: BorderDirection.SOUTH_EAST,
    BorderDirection.NORTH_WEST: BorderDirection.NORTH_EAST,
    BorderDirection.CENTER: BorderDirection.CENTER,
}

FLIP_VERTICAL: dict[BorderDirection, BorderDirection] = {
    BorderDirection.NORTH: BorderDirection.SOUTH,
    BorderDirection.EAST: BorderDirection.EAST,
    BorderDirection.SOUTH: BorderDirection.NORTH,
    BorderDirection.WEST: BorderDirection.WEST,
    BorderDirection.NORTH_EAST: BorderDirection.SOUTH_EAST,
    BorderDirection.SOUTH_EAST: BorderDirection.NORTH_EAST,
    BorderDirection.SOUTH_WEST: BorderDirection.NORTH_WEST,
    BorderDirection.NORTH_WEST: BorderDirection.SOUTH_WEST,
    BorderDirection.CENTER: BorderDirection.CENTER,
}


@dataclass(slots=True)
class MirrorConfig:
    """Configuration for mirroring operations.

    Attributes:
        axis: The mirror axis ("x" or "y").
        axis_value: The coordinate value of the mirror axis.
        width: Optional map width for bounds checking.
        height: Optional map height for bounds checking.
        flip_borders: Whether to flip border directions.
    """

    axis: str = "x"
    axis_value: int = 0
    width: int | None = None
    height: int | None = None
    flip_borders: bool = True


def flip_border_direction(
    direction: BorderDirection,
    axis: str,
) -> BorderDirection:
    """Flip a border direction across an axis.

    Args:
        direction: The original border direction.
        axis: "x" for horizontal flip, "y" for vertical flip.

    Returns:
        The flipped border direction.

    Example:
        >>> flip_border_direction(BorderDirection.EAST, "x")
        BorderDirection.WEST
        >>> flip_border_direction(BorderDirection.NORTH, "y")
        BorderDirection.SOUTH
    """
    axis_norm = (axis or "").strip().lower()

    if axis_norm == "x":
        return FLIP_HORIZONTAL.get(direction, direction)
    elif axis_norm == "y":
        return FLIP_VERTICAL.get(direction, direction)
    else:
        return direction


def flip_border_index(
    border_index: int,
    axis: str,
) -> int:
    """Flip a border index (0-8) across an axis.

    Convenience function that converts int to BorderDirection and back.

    Args:
        border_index: Border index (0-8).
        axis: "x" or "y".

    Returns:
        Flipped border index.
    """
    if not (0 <= border_index <= 8):
        return border_index

    direction = BorderDirection(border_index)
    flipped = flip_border_direction(direction, axis)
    return int(flipped)


def mirrored_position(
    x: int,
    y: int,
    *,
    axis: str,
    axis_value: int,
    width: int | None = None,
    height: int | None = None,
) -> tuple[int, int] | None:
    """Return the mirrored (x, y) for the given axis, or None if invalid.

    Args:
        x: Source x.
        y: Source y.
        axis: "x" or "y" (case-insensitive).
        axis_value: The mirror axis coordinate (integer).
        width: Optional map width to validate bounds.
        height: Optional map height to validate bounds.

    Returns:
        A tuple (mx, my) if a valid mirrored coordinate exists and differs from
        the input; otherwise None.
    """

    axis_norm = (axis or "").strip().lower()
    if axis_norm not in ("x", "y"):
        raise ValueError("axis must be 'x' or 'y'")

    x = int(x)
    y = int(y)
    axis_value = int(axis_value)

    if axis_norm == "x":
        mx, my = int(2 * axis_value - x), y
    else:
        mx, my = x, int(2 * axis_value - y)

    if mx == x and my == y:
        return None

    if width is not None and not (0 <= mx < int(width)):
        return None
    if height is not None and not (0 <= my < int(height)):
        return None

    return (mx, my)


def union_with_mirrored(
    positions: Iterable[TibiaPosition],
    *,
    axis: str,
    axis_value: int,
    width: int | None = None,
    height: int | None = None,
) -> list[TibiaPosition]:
    """Return a stable, de-duplicated list with mirrored positions included.

    This mirrors the legacy `unionWithMirrored` behavior: for each valid input
    position, the original position is included first, then its mirrored
    position (if valid and different).
    """

    seen: set[TibiaPosition] = set()
    out: list[TibiaPosition] = []

    for x, y, z in positions:
        x = int(x)
        y = int(y)
        z = int(z)

        # Tibia floors are typically 0..15 (legacy Position::isValid gate).
        if not (0 <= z < 16):
            continue
        if width is not None and not (0 <= x < int(width)):
            continue
        if height is not None and not (0 <= y < int(height)):
            continue

        p: TibiaPosition = (x, y, z)
        if p not in seen:
            seen.add(p)
            out.append(p)

        mp = mirrored_position(x, y, axis=axis, axis_value=axis_value, width=width, height=height)
        if mp is None:
            continue
        mx, my = mp
        mp3: TibiaPosition = (int(mx), int(my), z)
        if mp3 not in seen:
            seen.add(mp3)
            out.append(mp3)

    return out


@dataclass(slots=True, frozen=True)
class MirroredTileData:
    """Data for a mirrored tile.

    Attributes:
        x: Mirrored X position.
        y: Mirrored Y position.
        z: Floor level.
        flipped_border: Border direction after flipping (if applicable).
        original_x: Original X position.
        original_y: Original Y position.
    """

    x: int
    y: int
    z: int
    flipped_border: BorderDirection | None
    original_x: int
    original_y: int


def mirror_tile_with_borders(
    x: int,
    y: int,
    z: int,
    border_direction: BorderDirection | None,
    config: MirrorConfig,
) -> MirroredTileData | None:
    """Mirror a tile position and flip its border direction.

    This function combines position mirroring with border flipping,
    matching the behavior of legacy RME's ground brush mirror logic.

    Args:
        x: Source X position.
        y: Source Y position.
        z: Floor level.
        border_direction: Optional border direction to flip.
        config: Mirror configuration.

    Returns:
        MirroredTileData if mirroring is valid, None otherwise.

    Example:
        >>> config = MirrorConfig(axis="x", axis_value=100)
        >>> result = mirror_tile_with_borders(90, 50, 7, BorderDirection.EAST, config)
        >>> result.x
        110
        >>> result.flipped_border
        BorderDirection.WEST
    """
    mp = mirrored_position(
        x,
        y,
        axis=config.axis,
        axis_value=config.axis_value,
        width=config.width,
        height=config.height,
    )

    if mp is None:
        return None

    mx, my = mp

    flipped_border: BorderDirection | None = None
    if border_direction is not None and config.flip_borders:
        flipped_border = flip_border_direction(border_direction, config.axis)
    elif border_direction is not None:
        flipped_border = border_direction

    return MirroredTileData(
        x=mx,
        y=my,
        z=z,
        flipped_border=flipped_border,
        original_x=x,
        original_y=y,
    )


def mirror_selection(
    tiles: Iterable[TibiaPosition],
    config: MirrorConfig,
) -> list[MirroredTileData]:
    """Mirror a selection of tiles.

    This is the main entry point for mirroring multiple tiles at once.

    Args:
        tiles: Iterable of (x, y, z) positions.
        config: Mirror configuration.

    Returns:
        List of MirroredTileData for valid mirrored positions.
    """
    results: list[MirroredTileData] = []
    seen: set[TibiaPosition] = set()

    for x, y, z in tiles:
        x = int(x)
        y = int(y)
        z = int(z)

        # Skip invalid floors
        if not (0 <= z < 16):
            continue

        # Get mirrored position
        result = mirror_tile_with_borders(x, y, z, None, config)
        if result is None:
            continue

        pos = (result.x, result.y, result.z)
        if pos in seen:
            continue

        seen.add(pos)
        results.append(result)

    return results


def calculate_mirror_axis(
    selection_bounds: tuple[int, int, int, int],
    axis: str,
) -> int:
    """Calculate the mirror axis value from selection bounds.

    The mirror axis is placed at the center of the selection.

    Args:
        selection_bounds: (min_x, min_y, max_x, max_y) of the selection.
        axis: "x" or "y".

    Returns:
        The axis coordinate value (center of selection along the axis).
    """
    min_x, min_y, max_x, max_y = selection_bounds
    axis_norm = (axis or "").strip().lower()

    if axis_norm == "x":
        return (min_x + max_x) // 2
    elif axis_norm == "y":
        return (min_y + max_y) // 2
    else:
        raise ValueError("axis must be 'x' or 'y'")
