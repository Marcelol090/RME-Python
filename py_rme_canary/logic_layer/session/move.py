"""Selection movement operations for editor session.

Handles moving selected tiles with merge and auto-border support.
"""

from __future__ import annotations

from dataclasses import dataclass

from py_rme_canary.core.data.gamemap import GameMap
from py_rme_canary.core.data.tile import Tile

from ..brush_definitions import BrushDefinition, BrushManager
from ..transactional_brush import PaintAction
from .selection import TileKey, tile_is_nonempty


@dataclass(slots=True)
class MoveHandler:
    """Handles selection movement operations."""

    game_map: GameMap
    brush_manager: BrushManager
    merge_move_enabled: bool = False

    def move_selection(
        self,
        selection: set[TileKey],
        *,
        move_x: int,
        move_y: int,
        move_z: int = 0,
    ) -> tuple[PaintAction | None, set[TileKey], set[TileKey]]:
        """Move selected tiles and return the action plus affected and new selection.

        Legacy note: MapCanvas computes `move_x = last_click_x - mouse_x` and
        Editor::moveSelection applies `new_pos = old_pos - offset`.

        Args:
            selection: Set of tile keys to move.
            move_x, move_y, move_z: Movement offset (subtracted from positions).

        Returns:
            Tuple of (action, affected_keys, new_selection_keys).
        """
        if not selection:
            return None, set(), set()

        dx, dy, dz = int(move_x), int(move_y), int(move_z)
        if dx == 0 and dy == 0 and dz == 0:
            return None, set(), set()

        width = int(self.game_map.header.width)
        height = int(self.game_map.header.height)

        selected = sorted(selection)
        ops: list[tuple[TileKey, TileKey]] = []
        before: dict[TileKey, Tile | None] = {}

        for sx, sy, sz in selected:
            src = (int(sx), int(sy), int(sz))
            t = self.game_map.get_tile(*src)
            if not tile_is_nonempty(t):
                continue

            dst = (int(src[0] - dx), int(src[1] - dy), int(src[2] - dz))
            if not (0 <= int(dst[0]) < width and 0 <= int(dst[1]) < height):
                continue

            ops.append((src, dst))
            before[src] = t
            if dst not in before:
                before[dst] = self.game_map.get_tile(*dst)

        if not ops:
            return None, set(), set()

        # Apply onto a temp dict to avoid in-place conflicts.
        temp_tiles: dict[TileKey, Tile] = dict(self.game_map.tiles)

        # Remove sources first.
        for src, _dst in ops:
            temp_tiles.pop(src, None)

        # Place/merge at destinations.
        for src, dst in ops:
            src_tile = before.get(src)
            if src_tile is None:
                continue

            moved = Tile(
                x=int(dst[0]),
                y=int(dst[1]),
                z=int(dst[2]),
                ground=src_tile.ground,
                items=list(src_tile.items),
                house_id=src_tile.house_id,
                map_flags=int(src_tile.map_flags),
                zones=src_tile.zones,
                modified=True,
            )

            existing = temp_tiles.get(dst)
            if existing is None:
                temp_tiles[dst] = moved
                continue

            # Legacy: if src has no ground, OR if MERGE_MOVE is enabled,
            # merge into destination; otherwise replace destination.
            if moved.ground is None or self.merge_move_enabled:
                moved_house = int(moved.house_id or 0)
                existing_house = int(existing.house_id or 0)
                moved_flags = int(getattr(moved, "map_flags", 0) or 0)
                existing_flags = int(getattr(existing, "map_flags", 0) or 0)
                merged = Tile(
                    x=int(dst[0]),
                    y=int(dst[1]),
                    z=int(dst[2]),
                    ground=existing.ground if moved.ground is None else moved.ground,
                    items=list(existing.items) + list(moved.items),
                    house_id=existing_house if moved_house == 0 else moved_house,
                    map_flags=existing_flags | moved_flags,
                    zones=existing.zones,
                    modified=True,
                )
                temp_tiles[dst] = merged
            else:
                temp_tiles[dst] = moved

        # Build action
        action = PaintAction(brush_id=0)
        affected: set[TileKey] = set(before.keys())
        for key in affected:
            b = before.get(key)
            a = temp_tiles.get(key)
            if b == a:
                continue
            action.record_tile_change(key, b, a)

        if not action.has_changes():
            return None, set(), set()

        # Update selection to destination positions that now exist.
        new_sel: set[TileKey] = set()
        for _src, dst in ops:
            if dst in temp_tiles and tile_is_nonempty(temp_tiles[dst]):
                new_sel.add(dst)

        return action, affected, new_sel

    def calculate_expanded_area(self, affected: set[TileKey]) -> set[TileKey]:
        """Expand affected area by 3x3 for auto-border processing."""
        expanded: set[TileKey] = set()
        for x, y, z in affected:
            for dx in (-1, 0, 1):
                for dy in (-1, 0, 1):
                    expanded.add((int(x + dx), int(y + dy), int(z)))
        return expanded

    def collect_brush_ids(self, positions: set[TileKey]) -> set[int]:
        """Collect brush IDs present in the given positions."""
        brush_ids: set[int] = set()

        for x, y, z in positions:
            t = self.game_map.get_tile(int(x), int(y), int(z))
            if t is None:
                continue
            if t.ground is not None:
                b = self._get_brush_any(int(t.ground.id))
                if b is not None:
                    brush_ids.add(int(b.server_id))
            for it in getattr(t, "items", []) or []:
                b = self._get_brush_any(int(it.id))
                if b is not None:
                    brush_ids.add(int(b.server_id))

        return brush_ids

    def _get_brush_any(self, server_id: int) -> BrushDefinition | None:
        """Get brush by server ID with family lookup support."""
        if hasattr(self.brush_manager, "get_brush_any"):
            return self.brush_manager.get_brush_any(int(server_id))
        return self.brush_manager.get_brush(int(server_id))
