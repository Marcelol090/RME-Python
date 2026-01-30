"""Selection management for editor session.

Handles tile selection state including:
- Single tile selection
- Box/rectangle selection
- Toggle selection
- Selection queries
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum

from py_rme_canary.core.data.gamemap import GameMap
from py_rme_canary.logic_layer.session.selection_modes import (
    SelectionDepthMode,
    apply_compensation_offset,
    get_floors_for_selection,
)

TileKey = tuple[int, int, int]


class SelectionApplyMode(str, Enum):
    """How a selection operation modifies the current selection."""

    REPLACE = "replace"
    ADD = "add"
    SUBTRACT = "subtract"
    TOGGLE = "toggle"


def tile_is_nonempty(tile: object) -> bool:
    """Check if a tile is non-empty (has ground or items).

    Legacy behavior: selection should only include existing/non-empty tiles.
    In our core model, a tile object may exist but be logically empty.
    """
    if tile is None:
        return False
    try:
        ground = getattr(tile, "ground", None)
        items = getattr(tile, "items", None)
        map_flags = int(getattr(tile, "map_flags", 0) or 0)
        zones = getattr(tile, "zones", frozenset()) or frozenset()
        has_items = not (ground is None and not items)
        has_meta = map_flags != 0 or bool(zones)
        return bool(has_items or has_meta)
    except Exception:
        return True


@dataclass(slots=True)
class SelectionManager:
    """Manages tile selection state for the editor."""

    game_map: GameMap

    # Selection state
    _selection_tiles: set[TileKey] = field(default_factory=set)
    _selection_box_active: bool = False
    _selection_box_start: TileKey | None = None
    _selection_box_end: TileKey | None = None

    # Selection depth mode (for multi-floor selection)
    selection_mode: SelectionDepthMode = SelectionDepthMode.COMPENSATE

    # === Basic Selection API ===

    def has_selection(self) -> bool:
        """Check if there are any selected tiles."""
        return bool(self._selection_tiles)

    def get_selection_tiles(self) -> set[TileKey]:
        """Return a copy of the current selection tiles."""
        return set(self._selection_tiles)

    def clear_selection(self) -> None:
        """Clear all selected tiles."""
        self._selection_tiles.clear()

    def toggle_select_tile(self, *, x: int, y: int, z: int) -> None:
        """Toggle selection state of a single tile."""
        key = (int(x), int(y), int(z))
        t = self.game_map.get_tile(*key)
        if not tile_is_nonempty(t):
            return
        if key in self._selection_tiles:
            self._selection_tiles.remove(key)
        else:
            self._selection_tiles.add(key)

    def set_single_selection(self, *, x: int, y: int, z: int) -> None:
        """Clear selection and select a single tile."""
        self._selection_tiles.clear()
        key = (int(x), int(y), int(z))
        t = self.game_map.get_tile(*key)
        if tile_is_nonempty(t):
            self._selection_tiles.add(key)

    def add_tile(self, key: TileKey) -> None:
        """Add a tile to the selection."""
        self._selection_tiles.add(key)

    def remove_tile(self, key: TileKey) -> None:
        """Remove a tile from the selection."""
        self._selection_tiles.discard(key)

    def set_selection(self, tiles: set[TileKey]) -> None:
        """Replace the entire selection."""
        self._selection_tiles = set(tiles)

    # === Box Selection API ===

    def begin_box_selection(self, *, x: int, y: int, z: int) -> None:
        """Begin a Shift-drag selection box.

        UI should clear the selection first when Shift is held without Ctrl,
        matching the legacy behavior.
        """
        key = (int(x), int(y), int(z))
        self._selection_box_active = True
        self._selection_box_start = key
        self._selection_box_end = key

    def update_box_selection(self, *, x: int, y: int, z: int) -> None:
        """Update the end point of the selection box."""
        if not self._selection_box_active:
            return
        if self._selection_box_start is None:
            return
        self._selection_box_end = (int(x), int(y), int(z))

    def finish_box_selection(
        self,
        *,
        toggle_if_single: bool = False,
        mode: SelectionApplyMode | str = SelectionApplyMode.ADD,
        visible_floors: list[int] | None = None,
    ) -> None:
        """Apply the current selection box.

        - Applies tiles in rectangle according to selection_mode depth
        - If `toggle_if_single` and the rectangle is 1 tile, toggles it.
        - Supports multi-floor selection via selection_mode

        Args:
            toggle_if_single: Toggle if selection is single tile
            mode: How to apply selection (ADD/SUBTRACT/TOGGLE/REPLACE)
            visible_floors: List of visible floors (for VISIBLE mode)
        """
        if not self._selection_box_active or self._selection_box_start is None or self._selection_box_end is None:
            self.cancel_box_selection()
            return

        sx, sy, sz = self._selection_box_start
        ex, ey, ez = self._selection_box_end
        base_z = int(sz)

        x0, x1 = (int(sx), int(ex)) if sx <= ex else (int(ex), int(sx))
        y0, y1 = (int(sy), int(ey)) if sy <= ey else (int(ey), int(sy))
        z_min = min(int(sz), int(ez))
        z_max = max(int(sz), int(ez))

        if toggle_if_single and x0 == x1 and y0 == y1:
            self.toggle_select_tile(x=x0, y=y0, z=base_z)
            self.cancel_box_selection()
            return

        # Get floors to select based on depth mode
        floors_to_select = get_floors_for_selection(
            start_z=z_min,
            end_z=z_max,
            mode=self.selection_mode,
            visible_floors=visible_floors,
        )

        box_tiles: set[TileKey] = set()
        for z in floors_to_select:
            # Apply compensation offset if using COMPENSATE mode
            if self.selection_mode == SelectionDepthMode.COMPENSATE:
                comp_x0, comp_y0 = apply_compensation_offset(x=x0, y=y0, z=z, base_z=base_z)
                comp_x1, comp_y1 = apply_compensation_offset(x=x1, y=y1, z=z, base_z=base_z)
            else:
                comp_x0, comp_y0 = x0, y0
                comp_x1, comp_y1 = x1, y1

            for xx in range(int(comp_x0), int(comp_x1) + 1):
                for yy in range(int(comp_y0), int(comp_y1) + 1):
                    t = self.game_map.get_tile(int(xx), int(yy), int(z))
                    if not tile_is_nonempty(t):
                        continue
                    box_tiles.add((int(xx), int(yy), int(z)))

        # `mode` is usually already a SelectionApplyMode (default arg). Avoid
        # converting it via `str(mode)` because Enum(str, Enum) renders like
        # 'SelectionApplyMode.ADD', which is not a valid value.
        if not isinstance(mode, SelectionApplyMode):
            mode = SelectionApplyMode(str(mode))
        if mode is SelectionApplyMode.REPLACE:
            self._selection_tiles = set(box_tiles)
        elif mode is SelectionApplyMode.SUBTRACT:
            self._selection_tiles.difference_update(box_tiles)
        elif mode is SelectionApplyMode.TOGGLE:
            self._selection_tiles.symmetric_difference_update(box_tiles)
        elif mode is SelectionApplyMode.ADD:
            self._selection_tiles.update(box_tiles)

        self.cancel_box_selection()

    def cancel_box_selection(self) -> None:
        """Cancel the current box selection."""
        self._selection_box_active = False
        self._selection_box_start = None
        self._selection_box_end = None

    def get_selection_box(self) -> tuple[TileKey, TileKey] | None:
        """Return selection box endpoints while active, else None."""
        if not self._selection_box_active or self._selection_box_start is None or self._selection_box_end is None:
            return None
        return (self._selection_box_start, self._selection_box_end)
