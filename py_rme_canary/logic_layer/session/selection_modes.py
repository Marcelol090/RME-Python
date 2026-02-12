"""Selection depth modes for multi-floor selection.

Reference: source/selection.cpp (legacy C++)
Implements COMPENSATE, CURRENT, LOWER, VISIBLE modes.
"""

from __future__ import annotations

from enum import StrEnum


class SelectionDepthMode(StrEnum):
    """Determines which Z layers are included in selection.

    Reference: Legacy C++ Config::COMPENSATED_SELECT and related settings.

    Modes:
    - COMPENSATE: Auto-compensate for perspective (default legacy behavior)
                  Selects floors in a way that feels intuitive for 3D view
                  Below ground level (z=7), shifts selection up/right
    - CURRENT: Select only the current Z floor
    - LOWER: Select currentZ + all lower floors (higher Z values)
    - VISIBLE: Select all visible floors based on view settings
    """

    COMPENSATE = "compensate"
    CURRENT = "current"
    LOWER = "lower"
    VISIBLE = "visible"

    @classmethod
    def from_value(cls, value: SelectionDepthMode | str) -> SelectionDepthMode:
        """Normalize arbitrary value into a SelectionDepthMode enum."""
        if isinstance(value, cls):
            return value
        normalized = str(value or "").strip().lower()
        for mode in cls:
            if str(mode.value) == normalized:
                return mode
        return cls.COMPENSATE


def get_floors_for_selection(
    *,
    start_z: int,
    end_z: int,
    mode: SelectionDepthMode,
    visible_floors: list[int] | None = None,
) -> list[int]:
    """Get list of Z floors to include in selection based on mode.

    Args:
        start_z: Starting Z coordinate (top floor)
        end_z: Ending Z coordinate (bottom floor)
        mode: Selection depth mode
        visible_floors: List of currently visible floors (for VISIBLE mode)

    Returns:
        List of Z levels to include in selection

    Example:
        >>> get_floors_for_selection(start_z=7, end_z=7, mode=SelectionDepthMode.CURRENT)
        [7]
        >>> get_floors_for_selection(start_z=7, end_z=10, mode=SelectionDepthMode.LOWER)
        [7, 8, 9, 10]
    """
    if mode == SelectionDepthMode.CURRENT:
        # Only select the starting floor
        return [start_z]
    if mode == SelectionDepthMode.LOWER:
        # Select starting floor + all floors below (higher Z)
        return list(range(start_z, end_z + 1))
    if mode == SelectionDepthMode.VISIBLE:
        # Select only visible floors within range
        if visible_floors is None:
            visible_floors = [start_z]
        return [z for z in visible_floors if start_z <= z <= end_z]

    # Default legacy behavior - select range with compensation.
    # This is the same as LOWER for the basic implementation.
    # Advanced compensation (shifting X/Y per floor) happens in selection logic.
    return list(range(start_z, end_z + 1))


def apply_compensation_offset(*, x: int, y: int, z: int, base_z: int) -> tuple[int, int]:
    """Apply perspective compensation offset for floor Z.

    Legacy behavior (from selection.cpp line 432-436):
    When selecting with compensation mode below ground (z > 7),
    shift X and Y by (z - base_z) to account for 3D perspective.

    Args:
        x: Original X coordinate
        y: Original Y coordinate
        z: Current Z floor being selected
        base_z: Base Z floor (where selection started)

    Returns:
        Tuple of (compensated_x, compensated_y)

    Example:
        >>> apply_compensation_offset(x=100, y=100, z=9, base_z=7)
        (102, 102)  # Shifted by 2 in both directions
    """
    ground_level = 7

    # Only apply compensation below ground level
    if z <= ground_level or base_z < ground_level:
        return (x, y)

    # Calculate offset based on how many floors below ground
    offset = z - base_z

    return (x + offset, y + offset)
