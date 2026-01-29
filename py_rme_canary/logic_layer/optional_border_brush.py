"""Optional border brush implementation for py_rme_canary.

Forces auto-bordering on brushes that support it.
Reference: source/optional_border_brush.cpp (legacy C++)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from py_rme_canary.core.data.tile import Tile

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap
    from py_rme_canary.core.data.item import Position
    from py_rme_canary.logic_layer.brush_definitions import BrushManager


@dataclass(frozen=True, slots=True)
class OptionalBorderBrush:
    """Forces auto-bordering on supported brushes.

    OptionalBorderBrush triggers the auto-border system for brushes
    that have optional border support (e.g., carpet, doodad).

    Attributes:
        target_brush_name: Name of the brush to apply borders to

    Example:
        >>> brush = OptionalBorderBrush(target_brush_name="carpet_blue")
        >>> changes = brush.draw(game_map, pos, brush_manager=manager)
    """

    target_brush_name: str

    def get_name(self) -> str:
        """Get brush name."""
        return f"Optional Border: {self.target_brush_name}"

    def _resolve_target_brush_id(self) -> int | None:
        """Resolve target brush id from the configured name."""
        try:
            return int(self.target_brush_name)
        except (TypeError, ValueError):
            return None

    def can_draw(self, game_map: GameMap, pos: Position, *, brush_manager: BrushManager | None = None) -> bool:
        """Check if optional border can be applied.

        Requirements:
        1. Tile exists
        2. Tile has ground
        3. Target brush exists in manager

        Args:
            game_map: Target game map
            pos: Position to check
            brush_manager: Brush manager providing brush definitions

        Returns:
            True if optional border can be applied, False otherwise
        """
        tile = game_map.get_tile(pos.x, pos.y, pos.z)
        if tile is None or tile.ground is None:
            return False

        if brush_manager is None:
            return True  # Assume can draw if no manager provided

        # Check if target brush exists
        target_id = self._resolve_target_brush_id()
        if target_id is None:
            return False
        return brush_manager.get_brush(target_id) is not None

    def draw(
        self, game_map: GameMap, pos: Position, *, brush_manager: BrushManager | None = None
    ) -> list[tuple[Position, Tile]]:
        """Apply optional borders at position.

        This triggers the auto-border system for the target brush.

        Args:
            game_map: Target game map
            pos: Position to apply borders
            brush_manager: Brush manager providing brush definitions

        Returns:
            List of (position, new_tile) tuples for history system
        """
        tile = game_map.get_tile(pos.x, pos.y, pos.z)
        if tile is None or brush_manager is None:
            return []

        if not self.can_draw(game_map, pos, brush_manager=brush_manager):
            return []

        # Get target brush
        target_id = self._resolve_target_brush_id()
        if target_id is None:
            return []
        brush_def = brush_manager.get_brush(target_id)
        if brush_def is None:
            return []

        # Apply autoborder if brush supports it
        # NOTE: This is a simplified version. Full implementation would:
        # 1. Get brush's border spec
        # 2. Apply borders to neighbors
        # 3. Return all modified tiles

        # For now, just return empty (will be completed when border system is enhanced)
        return []

    def undraw(
        self,
        game_map: GameMap,
        pos: Position,
    ) -> list[tuple[Position, Tile]]:
        """Remove optional borders (no-op).

        Undraw is not supported for optional borders as they modify
        multiple tiles. Use EraserBrush instead.

        Args:
            game_map: Target game map
            pos: Position to remove borders from

        Returns:
            Empty list (no changes)
        """
        return []
