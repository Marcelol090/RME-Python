"""Mouse gesture handling for editor session.

Handles mouse down/move/up events for painting operations.
"""

from __future__ import annotations

from dataclasses import dataclass

from py_rme_canary.core.data.gamemap import GameMap

from ..brush_definitions import BrushManager
from ..transactional_brush import HistoryManager, PaintAction, TransactionalBrushStroke
from .selection import TileKey


@dataclass(slots=True)
class GestureHandler:
    """Handles mouse painting gestures for the editor."""

    game_map: GameMap
    brush_manager: BrushManager
    history: HistoryManager
    auto_border_enabled: bool = True

    _stroke: TransactionalBrushStroke | None = None
    _active: bool = False
    _active_brush_id: int = 0
    _brush_variation: int = 0

    _doodad_use_custom_thickness: bool = False
    _doodad_custom_thickness_low: int = 1
    _doodad_custom_thickness_ceil: int = 100

    def __post_init__(self) -> None:
        self._stroke = TransactionalBrushStroke(
            game_map=self.game_map,
            brush_manager=self.brush_manager,
            history=self.history,
            auto_border_enabled=bool(self.auto_border_enabled),
        )

    @property
    def is_active(self) -> bool:
        """Check if a gesture is currently in progress."""
        return self._active

    @property
    def active_brush_id(self) -> int:
        """Get the currently active brush ID."""
        return self._active_brush_id

    def set_auto_border_enabled(self, enabled: bool) -> None:
        """Enable/disable auto-border pass on stroke finalize."""
        self.auto_border_enabled = bool(enabled)
        if self._stroke is not None:
            self._stroke.auto_border_enabled = bool(enabled)

    def set_selected_brush(self, server_id: int) -> None:
        """Set the currently selected brush ID."""
        self._active_brush_id = int(server_id)

    def set_brush_variation(self, variation: int) -> None:
        """Set the active brush variation index.

        This is currently used as a deterministic selector for brushes that
        define `randomize_ids` (primarily ground brushes).
        """
        self._brush_variation = int(variation)
        if self._stroke is not None:
            self._stroke.brush_variation = int(variation)

    def set_doodad_custom_thickness(self, *, enabled: bool, low: int = 1, ceil: int = 100) -> None:
        self._doodad_use_custom_thickness = bool(enabled)
        self._doodad_custom_thickness_low = int(low)
        self._doodad_custom_thickness_ceil = int(ceil)
        if self._stroke is not None:
            self._stroke.doodad_use_custom_thickness = bool(enabled)
            self._stroke.doodad_custom_thickness_low = int(low)
            self._stroke.doodad_custom_thickness_ceil = int(ceil)

    def mouse_down(
        self,
        *,
        x: int,
        y: int,
        z: int,
        selected_server_id: int | None = None,
        alt: bool = False,
    ) -> None:
        """Begin a paint stroke at the given position.

        Args:
            x, y, z: Starting position.
            selected_server_id: Brush ID to use (uses active brush if None).
            alt: Whether Alt key is held for replace mode.
        """
        if selected_server_id is not None:
            self._active_brush_id = int(selected_server_id)
        if self._active_brush_id <= 0:
            raise ValueError("No selected_server_id for stroke")

        self._active = True

        # Legacy Replace tool (Alt):
        # - Only meaningful for ground brushes.
        brush_def = self.brush_manager.get_brush(int(self._active_brush_id))
        is_ground = brush_def is not None and str(brush_def.brush_type).lower() == "ground"
        replace_enabled = bool(is_ground)
        replace_source_ground_id: int | None = None

        if is_ground and bool(alt):
            t = self.game_map.get_tile(int(x), int(y), int(z))
            if t is not None and t.ground is not None:
                replace_source_ground_id = int(t.ground.id)

        assert self._stroke is not None
        self._stroke.brush_variation = int(self._brush_variation)
        self._stroke.doodad_use_custom_thickness = bool(self._doodad_use_custom_thickness)
        self._stroke.doodad_custom_thickness_low = int(self._doodad_custom_thickness_low)
        self._stroke.doodad_custom_thickness_ceil = int(self._doodad_custom_thickness_ceil)
        self._stroke.begin(
            x=int(x),
            y=int(y),
            z=int(z),
            selected_server_id=int(self._active_brush_id),
            replace_enabled=replace_enabled,
            replace_source_ground_id=replace_source_ground_id,
            alt=bool(alt),
        )

    def mouse_move(self, *, x: int, y: int, z: int, alt: bool = False) -> None:
        """Continue a paint stroke at the given position."""
        if not self._active:
            return
        assert self._stroke is not None
        self._stroke.brush_variation = int(self._brush_variation)
        self._stroke.doodad_use_custom_thickness = bool(self._doodad_use_custom_thickness)
        self._stroke.doodad_custom_thickness_low = int(self._doodad_custom_thickness_low)
        self._stroke.doodad_custom_thickness_ceil = int(self._doodad_custom_thickness_ceil)
        self._stroke.paint(
            x=int(x),
            y=int(y),
            z=int(z),
            selected_server_id=int(self._active_brush_id),
            alt=bool(alt),
        )

    def mark_autoborder_position(self, *, x: int, y: int, z: int) -> None:
        """Include an extra tile in the finalize auto-border pass.

        Used by UI layers to emulate legacy `tilestoborder` set:
        a perimeter around the brush footprint that should be re-evaluated.
        """
        if not self._active:
            return
        assert self._stroke is not None
        self._stroke.mark_autoborder_position(x=int(x), y=int(y), z=int(z))

    def mouse_up(self) -> PaintAction | None:
        """End the current paint stroke and return the resulting action."""
        if not self._active:
            return None
        self._active = False
        assert self._stroke is not None
        return self._stroke.end()

    def cancel(self) -> None:
        """Cancel the current paint stroke without committing."""
        self._active = False
        if self._stroke is not None:
            self._stroke.cancel()

    def fill_ground(self, *, x: int, y: int, z: int) -> PaintAction | None:
        """Flood-fill ground within a bounded area (legacy BLOCK_SIZE=64).

        This mirrors the legacy behavior triggered by Ctrl+D for ground brushes.
        """
        if self._active:
            raise RuntimeError("Cannot fill while a stroke is active")

        brush_id = int(self._active_brush_id)
        brush_def = self.brush_manager.get_brush(brush_id)
        if brush_def is None or brush_def.brush_type != "ground":
            raise ValueError("Fill is only supported for ground brushes")

        x, y, z = int(x), int(y), int(z)
        positions = self._flood_fill_positions_64x64(x=x, y=y, z=z)
        if not positions:
            return None

        # Use a dedicated stroke object
        stroke = TransactionalBrushStroke(
            game_map=self.game_map,
            brush_manager=self.brush_manager,
            history=self.history,
            auto_border_enabled=bool(self.auto_border_enabled),
        )
        stroke.brush_variation = int(self._brush_variation)
        first_x, first_y, first_z = positions[0]
        stroke.begin(x=first_x, y=first_y, z=first_z, selected_server_id=brush_id)
        for px, py, pz in positions[1:]:
            stroke.paint(x=px, y=py, z=pz, selected_server_id=brush_id)

        return stroke.end()

    def _flood_fill_positions_64x64(self, *, x: int, y: int, z: int) -> list[TileKey]:
        """Calculate flood fill positions in a 64x64 block."""
        block_size = 64
        half = block_size // 2

        center_x, center_y, z = int(x), int(y), int(z)

        def ground_id_at(px: int, py: int) -> int | None:
            t = self.game_map.get_tile(int(px), int(py), int(z))
            if t is None or t.ground is None:
                return None
            return int(t.ground.id)

        old_ground_id = ground_id_at(center_x, center_y)

        x_min = max(0, center_x - half)
        y_min = max(0, center_y - half)
        x_max = min(int(self.game_map.header.width) - 1, center_x + half - 1)
        y_max = min(int(self.game_map.header.height) - 1, center_y + half - 1)
        if x_min > x_max or y_min > y_max:
            return []

        # If clicked tile already matches the brush ground, bail early
        if old_ground_id == int(self._active_brush_id):
            return []

        def in_bounds(px: int, py: int) -> bool:
            return x_min <= px <= x_max and y_min <= py <= y_max

        def matches_old(px: int, py: int) -> bool:
            return ground_id_at(px, py) == old_ground_id

        if not in_bounds(center_x, center_y):
            return []
        if not matches_old(center_x, center_y):
            return []

        out: list[TileKey] = []
        visited: set[tuple[int, int]] = set()
        stack: list[tuple[int, int]] = [(center_x, center_y)]
        visited.add((center_x, center_y))

        while stack:
            px, py = stack.pop()
            if not matches_old(px, py):
                continue
            out.append((int(px), int(py), int(z)))
            for nx, ny in ((px - 1, py), (px + 1, py), (px, py - 1), (px, py + 1)):
                if not in_bounds(nx, ny):
                    continue
                key = (int(nx), int(ny))
                if key in visited:
                    continue
                visited.add(key)
                stack.append((int(nx), int(ny)))

        return out
