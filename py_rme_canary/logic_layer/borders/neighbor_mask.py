"""Neighbor bitmask computation for auto-border.

The neighbor bit order mirrors the legacy C++ implementation
(`source/ground_brush.cpp`, `GroundBrush::doBorders`):

Bit index -> offset
- 0: (-1, -1)  (NW)
- 1: ( 0, -1)  (N)
- 2: (+1, -1)  (NE)
- 3: (-1,  0)  (W)
- 4: (+1,  0)  (E)
- 5: (-1, +1)  (SW)
- 6: ( 0, +1)  (S)
- 7: (+1, +1)  (SE)
"""

from __future__ import annotations

from collections.abc import Sequence

from py_rme_canary.core.data.gamemap import GameMap

# Neighbor offsets in bit order
NEIGHBOR_OFFSETS: tuple[tuple[int, int], ...] = (
    (-1, -1),  # NW - bit 0
    (0, -1),  # N  - bit 1
    (1, -1),  # NE - bit 2
    (-1, 0),  # W  - bit 3
    (1, 0),  # E  - bit 4
    (-1, 1),  # SW - bit 5
    (0, 1),  # S  - bit 6
    (1, 1),  # SE - bit 7
)


def compute_neighbor_mask_for_ground(
    game_map: GameMap,
    *,
    x: int,
    y: int,
    z: int,
    same_ground_ids: Sequence[int],
) -> int:
    """Compute an 8-bit neighbor mask based on ground identity.

    A bit is set when the corresponding neighbor tile exists and its ground id
    is in `same_ground_ids`.

    Args:
        game_map: The map to query.
        x, y, z: Center tile position.
        same_ground_ids: Ground IDs considered "same terrain".

    Returns:
        8-bit mask where each bit indicates neighbor presence.
    """
    ids = {int(i) for i in same_ground_ids}
    mask = 0
    for bit, (dx, dy) in enumerate(NEIGHBOR_OFFSETS):
        t = game_map.get_tile(int(x + dx), int(y + dy), int(z))
        if t is None or t.ground is None:
            continue
        if int(t.ground.id) in ids:
            mask |= 1 << bit
    return mask


def compute_neighbor_mask_for_target_ground(
    game_map: GameMap,
    *,
    x: int,
    y: int,
    z: int,
    target_ground_ids: tuple[int, ...],
) -> int:
    """Compute neighbor mask where bits indicate presence of target ground ids.

    Args:
        game_map: The map to query.
        x, y, z: Center tile position.
        target_ground_ids: Ground IDs to detect.

    Returns:
        8-bit mask where each bit indicates target presence.
    """
    mask = 0
    for bit, (dx, dy) in enumerate(NEIGHBOR_OFFSETS):
        t = game_map.get_tile(int(x + dx), int(y + dy), int(z))
        gid = None if t is None or t.ground is None else int(t.ground.id)
        if gid is not None and int(gid) in target_ground_ids:
            mask |= 1 << int(bit)
    return int(mask)


def bit_is_set(mask: int, bit_index: int) -> bool:
    """Check if a specific bit is set in the mask."""
    return (int(mask) & (1 << int(bit_index))) != 0
