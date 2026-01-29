"""Border alignment selection based on neighbor masks.

Provides functions to select the appropriate border piece alignment
based on the computed neighbor bitmask.
"""

from __future__ import annotations

from ..brush_definitions import BrushDefinition
from .neighbor_mask import bit_is_set


def select_border_alignment(mask: int, *, borders: dict[str, int]) -> str | None:
    """Select a human-readable alignment key given a neighbor mask.

    This is a simplified selector compatible with the proposed `brushes.json`
    format.

    Semantics: bits represent presence of the same terrain in that neighbor.
    Therefore, a border on a side is typically chosen when that side is absent.

    Priority order is from most specific to least specific.

    Args:
        mask: 8-bit neighbor presence mask.
        borders: Dict mapping alignment keys to server IDs.

    Returns:
        Alignment key or None if no match.
    """
    # Short aliases for neighbor presence.
    nw = bit_is_set(mask, 0)
    n = bit_is_set(mask, 1)
    ne = bit_is_set(mask, 2)
    w = bit_is_set(mask, 3)
    e = bit_is_set(mask, 4)
    sw = bit_is_set(mask, 5)
    s = bit_is_set(mask, 6)
    se = bit_is_set(mask, 7)

    def has(key: str) -> bool:
        return key in borders

    def has_any(*keys: str) -> bool:
        return any(k in borders for k in keys)

    # Concave (inner) corners: sides exist but diagonal is missing.
    if (has("INNER_CORNER_NE") or has("INNER_NE")) and n and e and (not ne):
        return "INNER_CORNER_NE" if has("INNER_CORNER_NE") else "INNER_NE"
    if (has("INNER_CORNER_NW") or has("INNER_NW")) and n and w and (not nw):
        return "INNER_CORNER_NW" if has("INNER_CORNER_NW") else "INNER_NW"
    if (has("INNER_CORNER_SE") or has("INNER_SE")) and s and e and (not se):
        return "INNER_CORNER_SE" if has("INNER_CORNER_SE") else "INNER_SE"
    if (has("INNER_CORNER_SW") or has("INNER_SW")) and s and w and (not sw):
        return "INNER_CORNER_SW" if has("INNER_CORNER_SW") else "INNER_SW"

    # Outer corners: two sides missing.
    if has_any("OUTER_CORNER_NE", "NORTH_EAST", "CORNER_NE") and (not n) and (not e):
        if has("OUTER_CORNER_NE"):
            return "OUTER_CORNER_NE"
        if has("NORTH_EAST"):
            return "NORTH_EAST"
        return "CORNER_NE"
    if has_any("OUTER_CORNER_NW", "NORTH_WEST", "CORNER_NW") and (not n) and (not w):
        if has("OUTER_CORNER_NW"):
            return "OUTER_CORNER_NW"
        if has("NORTH_WEST"):
            return "NORTH_WEST"
        return "CORNER_NW"
    if has_any("OUTER_CORNER_SE", "SOUTH_EAST", "CORNER_SE") and (not s) and (not e):
        if has("OUTER_CORNER_SE"):
            return "OUTER_CORNER_SE"
        if has("SOUTH_EAST"):
            return "SOUTH_EAST"
        return "CORNER_SE"
    if has_any("OUTER_CORNER_SW", "SOUTH_WEST", "CORNER_SW") and (not s) and (not w):
        if has("OUTER_CORNER_SW"):
            return "OUTER_CORNER_SW"
        if has("SOUTH_WEST"):
            return "SOUTH_WEST"
        return "CORNER_SW"

    # Cardinal edges.
    if has("NORTH") and (not n):
        return "NORTH"
    if has("EAST") and (not e):
        return "EAST"
    if has("SOUTH") and (not s):
        return "SOUTH"
    if has("WEST") and (not w):
        return "WEST"

    return None


def select_border_id_from_definition(mask: int, brush: BrushDefinition) -> int | None:
    """Select border ID from a BrushDefinition based on mask.

    Args:
        mask: 8-bit neighbor presence mask.
        brush: Brush definition with borders dict.

    Returns:
        Server ID for the border piece or None.
    """
    alignment = select_border_alignment(mask, borders=brush.borders)
    if alignment is None:
        return None
    v = brush.borders.get(alignment)
    if v is None:
        return None
    return int(v)


def select_border_alignment_when_present(mask: int, *, borders: dict[str, int]) -> str | None:
    """Select alignment when bits indicate *presence* of a specific neighbor type.

    Used for `ground` transition borders (`align="inner" to="..."`), where the
    border is chosen based on which neighboring tiles match the transition target.

    Args:
        mask: 8-bit mask indicating presence of target neighbors.
        borders: Dict mapping alignment keys to server IDs.

    Returns:
        Alignment key or None if no match.
    """
    # Short aliases for neighbor presence.
    nw = bit_is_set(mask, 0)
    n = bit_is_set(mask, 1)
    ne = bit_is_set(mask, 2)
    w = bit_is_set(mask, 3)
    e = bit_is_set(mask, 4)
    sw = bit_is_set(mask, 5)
    s = bit_is_set(mask, 6)
    se = bit_is_set(mask, 7)

    def has(key: str) -> bool:
        return key in borders

    # Prefer corners when two sides match.
    if (n and e) and (has("OUTER_CORNER_NE") or has("NORTH_EAST") or has("CORNER_NE")):
        if has("OUTER_CORNER_NE"):
            return "OUTER_CORNER_NE"
        if has("NORTH_EAST"):
            return "NORTH_EAST"
        return "CORNER_NE"
    if (n and w) and (has("OUTER_CORNER_NW") or has("NORTH_WEST") or has("CORNER_NW")):
        if has("OUTER_CORNER_NW"):
            return "OUTER_CORNER_NW"
        if has("NORTH_WEST"):
            return "NORTH_WEST"
        return "CORNER_NW"
    if (s and e) and (has("OUTER_CORNER_SE") or has("SOUTH_EAST") or has("CORNER_SE")):
        if has("OUTER_CORNER_SE"):
            return "OUTER_CORNER_SE"
        if has("SOUTH_EAST"):
            return "SOUTH_EAST"
        return "CORNER_SE"
    if (s and w) and (has("OUTER_CORNER_SW") or has("SOUTH_WEST") or has("CORNER_SW")):
        if has("OUTER_CORNER_SW"):
            return "OUTER_CORNER_SW"
        if has("SOUTH_WEST"):
            return "SOUTH_WEST"
        return "CORNER_SW"

    # Then single edges.
    if n and has("NORTH"):
        return "NORTH"
    if e and has("EAST"):
        return "EAST"
    if s and has("SOUTH"):
        return "SOUTH"
    if w and has("WEST"):
        return "WEST"

    # Diagonal-only: pick any supported corner.
    if ne or nw or se or sw:
        for key in (
            "NORTH_EAST",
            "NORTH_WEST",
            "SOUTH_EAST",
            "SOUTH_WEST",
            "CORNER_NE",
            "CORNER_NW",
            "CORNER_SE",
            "CORNER_SW",
        ):
            if has(key):
                return key

    return None


def transition_alignment_weight(alignment: str) -> int:
    """Heuristic weight for transition alignment preference.

    When multiple transitions apply, prefer corner pieces over straight edges.

    Args:
        alignment: Alignment key string.

    Returns:
        Numeric weight (higher = more preferred).
    """
    alignment = str(alignment)
    if alignment.startswith("OUTER_CORNER_"):
        return 3
    if alignment in {"NORTH_EAST", "NORTH_WEST", "SOUTH_EAST", "SOUTH_WEST"}:
        return 3
    if alignment.startswith("CORNER_"):
        return 3
    if alignment in {"NORTH", "EAST", "SOUTH", "WEST"}:
        return 2
    return 1
