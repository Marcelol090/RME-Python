"""Mirror drawing helpers (legacy RME-compatible).

This module implements the *position mirroring* behavior from the legacy RME
editor, used to duplicate draw positions across a mirror axis.

Legacy references:
- `source/gui.h` / `source/gui.cpp`: mirror state + axis selection.
- `source/map_display.cpp`: `getMirroredPosition` + `unionWithMirrored`.

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

TibiaPosition = tuple[int, int, int]


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
