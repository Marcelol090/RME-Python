"""Map-wide processor operations — C++ MapProcessor parity.

Mirrors the C++ ``MapProcessor`` used by ``Editor``:
  - ``Editor::borderizeMap``  → :func:`borderize_map`
  - ``Editor::randomizeMap``  → :func:`randomize_map`
  - ``Editor::clearInvalidHouseTiles`` → :func:`clear_invalid_house_tiles`
  - ``Editor::clearModifiedTileState`` → :func:`clear_modified_tile_state`

All operations accept an optional *progress_callback* ``(int) -> None``
receiving percentages 0-100 so the UI can drive a progress bar.
"""

from __future__ import annotations

import logging
import random
from collections.abc import Callable
from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap

logger = logging.getLogger(__name__)

ProgressCallback = Callable[[int], None]
TileKey = tuple[int, int, int]


# ---------------------------------------------------------------------------
# Result dataclasses
# ---------------------------------------------------------------------------


@dataclass(slots=True)
class BorderizeResult:
    """Outcome of a borderize-map operation."""

    tiles_processed: int
    tiles_changed: int


@dataclass(slots=True)
class RandomizeResult:
    """Outcome of a randomize-map operation."""

    tiles_processed: int
    tiles_randomized: int


@dataclass(slots=True)
class ClearHouseTilesResult:
    """Outcome of clearing invalid house tiles."""

    tiles_checked: int
    tiles_cleared: int


@dataclass(slots=True)
class ClearModifiedResult:
    """Outcome of clearing the modified-tile flag."""

    tiles_cleared: int


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _emit(cb: ProgressCallback | None, pct: int) -> None:
    if cb is not None:
        try:
            cb(max(0, min(100, pct)))
        except Exception:
            pass


def _all_tile_keys(game_map: GameMap) -> list[TileKey]:
    """Return all tile keys present in the map."""
    try:
        # Prefer a .tiles dict or .all_tiles() method if available
        if hasattr(game_map, "tiles") and isinstance(game_map.tiles, dict):
            return list(game_map.tiles.keys())
        if hasattr(game_map, "all_tiles"):
            return [
                (int(t.x), int(t.y), int(t.z)) for t in game_map.all_tiles()
            ]
        # Fallback: iterate over the internal storage
        return list(game_map._tiles.keys()) if hasattr(game_map, "_tiles") else []
    except Exception:
        logger.warning("Could not collect tile keys from GameMap", exc_info=True)
        return []


# ---------------------------------------------------------------------------
# borderize_map  (C++ Editor::borderizeMap / MapProcessor::borderizeMap)
# ---------------------------------------------------------------------------


def borderize_map(
    game_map: GameMap,
    *,
    selection_only: bool = False,
    selection_tiles: set[TileKey] | None = None,
    progress_callback: ProgressCallback | None = None,
) -> BorderizeResult:
    """Apply auto-border logic to every ground tile on the map.

    C++ parity: ``MapProcessor::borderizeMap(editor, showdialog)``

    For each tile with a ground item that has an associated ``GroundBrush``,
    re-computes border neighbours and updates border items accordingly.

    Parameters
    ----------
    game_map
        The map to process.
    selection_only
        If *True* and *selection_tiles* is provided, only process those tiles.
    selection_tiles
        Explicit set of TileKey to process (used when selection_only=True).
    progress_callback
        Optional ``(int) -> None`` called with 0-100 progress.
    """
    try:
        from py_rme_canary.logic_layer.auto_border import apply_auto_border_to_tile
    except ImportError:
        logger.warning("auto_border module not available; borderize_map is a no-op")
        return BorderizeResult(tiles_processed=0, tiles_changed=0)

    if selection_only and selection_tiles is not None:
        keys = list(selection_tiles)
    else:
        keys = _all_tile_keys(game_map)

    total = len(keys)
    processed = 0
    changed = 0
    check_interval = max(1, total // 100)

    for i, key in enumerate(keys):
        tile = game_map.get_tile(*key)
        if tile is not None and tile.ground is not None:
            try:
                did_change = apply_auto_border_to_tile(game_map, tile)
                if did_change:
                    changed += 1
            except Exception:
                logger.debug("Auto-border failed for tile %s", key, exc_info=True)
            processed += 1

        if i % check_interval == 0:
            _emit(progress_callback, int(i / total * 100) if total else 100)

    _emit(progress_callback, 100)
    logger.info("borderize_map: %d tiles processed, %d changed", processed, changed)
    return BorderizeResult(tiles_processed=processed, tiles_changed=changed)


# ---------------------------------------------------------------------------
# randomize_map  (C++ Editor::randomizeMap / MapProcessor::randomizeMap)
# ---------------------------------------------------------------------------


def randomize_map(
    game_map: GameMap,
    *,
    selection_only: bool = False,
    selection_tiles: set[TileKey] | None = None,
    seed: int | None = None,
    progress_callback: ProgressCallback | None = None,
) -> RandomizeResult:
    """Re-randomize ground variation indices for all terrain tiles.

    C++ parity: ``MapProcessor::randomizeMap(editor, showdialog)``

    Ground brushes have multiple sprite alternatives; this function picks a
    new random alternative for each ground tile, mirroring the C++ behaviour
    of replacing ``item->getSubtype()`` with a new random variant.

    Parameters
    ----------
    seed
        RNG seed for reproducible results (useful for scripting / tests).
    """
    rng = random.Random(seed)

    if selection_only and selection_tiles is not None:
        keys = list(selection_tiles)
    else:
        keys = _all_tile_keys(game_map)

    total = len(keys)
    randomized = 0
    check_interval = max(1, total // 100)

    for i, key in enumerate(keys):
        tile = game_map.get_tile(*key)
        if tile is not None and tile.ground is not None:
            item = tile.ground
            # C++ equivalent: item->setSubtype(rng.next() % num_alternatives)
            # We use the item's count field as subtype proxy when it has
            # a brush with alternatives.
            brush = getattr(item, "ground_brush", None) or getattr(item, "_brush", None)
            num_alternatives = 1
            if brush is not None and hasattr(brush, "num_alternatives"):
                num_alternatives = max(1, int(brush.num_alternatives))
            elif hasattr(item, "subtype_count"):
                num_alternatives = max(1, int(item.subtype_count))

            if num_alternatives > 1:
                new_subtype = rng.randrange(num_alternatives)
                old_subtype = getattr(item, "subtype", None) or getattr(item, "count", 0)
                if new_subtype != old_subtype:
                    try:
                        if hasattr(item, "subtype"):
                            item.subtype = new_subtype
                        else:
                            item.count = new_subtype
                        tile.modified = True
                        randomized += 1
                    except Exception:
                        logger.debug("Could not randomize tile %s", key, exc_info=True)

        if i % check_interval == 0:
            _emit(progress_callback, int(i / total * 100) if total else 100)

    _emit(progress_callback, 100)
    logger.info("randomize_map: %d tiles randomized out of %d", randomized, total)
    return RandomizeResult(tiles_processed=total, tiles_randomized=randomized)


# ---------------------------------------------------------------------------
# clear_invalid_house_tiles  (C++ Editor::clearInvalidHouseTiles)
# ---------------------------------------------------------------------------


def clear_invalid_house_tiles(
    game_map: GameMap,
    *,
    progress_callback: ProgressCallback | None = None,
) -> ClearHouseTilesResult:
    """Remove house_id from tiles that belong to non-existent houses.

    C++ parity: ``MapProcessor::clearInvalidHouseTiles(editor, showdialog)``

    A tile is "invalid" when its ``house_id`` references a house that no
    longer exists in the map's house registry.
    """
    # Build set of valid house IDs
    valid_ids: set[int] = set()
    try:
        if hasattr(game_map, "houses"):
            houses_obj = game_map.houses
            if isinstance(houses_obj, dict) or hasattr(houses_obj, "keys"):
                valid_ids = set(houses_obj.keys())
            elif hasattr(houses_obj, "__iter__"):
                for h in houses_obj:
                    hid = getattr(h, "id", None) or getattr(h, "house_id", None)
                    if hid is not None:
                        valid_ids.add(int(hid))
    except Exception:
        logger.warning("Could not enumerate houses", exc_info=True)

    keys = _all_tile_keys(game_map)
    total = len(keys)
    checked = 0
    cleared = 0
    check_interval = max(1, total // 100)

    for i, key in enumerate(keys):
        tile = game_map.get_tile(*key)
        if tile is not None:
            checked += 1
            hid = getattr(tile, "house_id", None) or 0
            if hid and int(hid) not in valid_ids:
                try:
                    tile.house_id = 0
                    tile.modified = True
                    cleared += 1
                    logger.debug("Cleared invalid house_id=%d from tile %s", hid, key)
                except Exception:
                    logger.debug("Could not clear house_id for tile %s", key, exc_info=True)

        if i % check_interval == 0:
            _emit(progress_callback, int(i / total * 100) if total else 100)

    _emit(progress_callback, 100)
    logger.info("clear_invalid_house_tiles: %d checked, %d cleared", checked, cleared)
    return ClearHouseTilesResult(tiles_checked=checked, tiles_cleared=cleared)


# ---------------------------------------------------------------------------
# clear_modified_tile_state  (C++ Editor::clearModifiedTileState)
# ---------------------------------------------------------------------------


def clear_modified_tile_state(
    game_map: GameMap,
    *,
    progress_callback: ProgressCallback | None = None,
) -> ClearModifiedResult:
    """Clear the ``modified`` flag on every tile in the map.

    C++ parity: ``MapProcessor::clearModifiedTileState(editor, showdialog)``

    This is called after a successful save to reset unsaved-changes tracking.
    """
    keys = _all_tile_keys(game_map)
    total = len(keys)
    cleared = 0
    check_interval = max(1, total // 100)

    for i, key in enumerate(keys):
        tile = game_map.get_tile(*key)
        if tile is not None and getattr(tile, "modified", False):
            try:
                tile.modified = False
                cleared += 1
            except Exception:
                pass

        if i % check_interval == 0:
            _emit(progress_callback, int(i / total * 100) if total else 100)

    _emit(progress_callback, 100)
    logger.info("clear_modified_tile_state: %d tiles cleared", cleared)
    return ClearModifiedResult(tiles_cleared=cleared)


# ---------------------------------------------------------------------------
# Convenience aliases matching C++ naming
# ---------------------------------------------------------------------------

borderize_selection = borderize_map   # called with selection_only=True
randomize_selection = randomize_map   # called with selection_only=True
