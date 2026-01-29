"""Clipboard operations for editor session.

Handles copy, cut, and paste of tile selections.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from py_rme_canary.core.data.gamemap import GameMap
from py_rme_canary.core.data.tile import Tile

from .selection import TileKey, tile_is_nonempty


@dataclass(slots=True)
class ClipboardManager:
    """Manages copy/paste buffer for the editor."""

    game_map: GameMap

    # Clipboard state
    _buffer_tiles: dict[TileKey, Tile] = field(default_factory=dict)
    _buffer_pos: TileKey | None = None

    def can_paste(self) -> bool:
        """Check if there's content to paste."""
        return bool(self._buffer_tiles) and self._buffer_pos is not None

    def get_buffer_tiles(self) -> dict[TileKey, Tile]:
        """Get the current buffer tiles."""
        return dict(self._buffer_tiles)

    def get_buffer_origin(self) -> TileKey | None:
        """Get the origin position of the buffer."""
        return self._buffer_pos

    def clear(self) -> None:
        """Clear the clipboard buffer."""
        self._buffer_tiles.clear()
        self._buffer_pos = None

    def load_tiles(self, tiles: list[Tile], origin: TileKey | None = None) -> bool:
        """Load external tiles into the buffer.

        Args:
            tiles: List of tiles to load
            origin: Optional buffer origin; if None, min position is used

        Returns:
            True if any tiles were loaded.
        """
        if not tiles:
            return False

        buffer_tiles: dict[TileKey, Tile] = {}
        min_x = min(int(t.x) for t in tiles)
        min_y = min(int(t.y) for t in tiles)
        min_z = min(int(t.z) for t in tiles)
        for t in tiles:
            buffer_tiles[(int(t.x), int(t.y), int(t.z))] = t

        self._buffer_tiles = buffer_tiles
        if origin is None:
            self._buffer_pos = (int(min_x), int(min_y), int(min_z))
        else:
            self._buffer_pos = (int(origin[0]), int(origin[1]), int(origin[2]))
        return True

    def copy_tiles(self, selection: set[TileKey]) -> bool:
        """Copy selected tiles into the buffer.

        Args:
            selection: Set of tile keys to copy.

        Returns:
            True if any tiles were copied.
        """
        if not selection:
            return False

        tiles: dict[TileKey, Tile] = {}
        min_x: int | None = None
        min_y: int | None = None
        min_z: int | None = None

        for key in sorted(selection):
            t = self.game_map.get_tile(*key)
            if t is None or not tile_is_nonempty(t):
                continue
            tiles[key] = t
            min_x = int(t.x) if min_x is None else min(int(min_x), int(t.x))
            min_y = int(t.y) if min_y is None else min(int(min_y), int(t.y))
            min_z = int(t.z) if min_z is None else int(min_z)

        if not tiles or min_x is None or min_y is None or min_z is None:
            return False

        self._buffer_tiles = tiles
        self._buffer_pos = (int(min_x), int(min_y), int(min_z))
        return True

    def calculate_paste_tiles(
        self,
        target_x: int,
        target_y: int,
        target_z: int,
        *,
        merge_enabled: bool = False,
    ) -> dict[TileKey, tuple[Tile | None, Tile]] | None:
        """Calculate what tiles would result from pasting at target position.

        Args:
            target_x, target_y, target_z: Target paste position.
            merge_enabled: Whether to merge with existing tiles.

        Returns:
            Dict mapping destination key to (before_tile, after_tile) or None if can't paste.
        """
        if not self.can_paste():
            return None

        base = self._buffer_pos
        assert base is not None

        to_pos = (int(target_x), int(target_y), int(target_z))
        width = int(self.game_map.header.width)
        height = int(self.game_map.header.height)

        result: dict[TileKey, tuple[Tile | None, Tile]] = {}

        for (bx, by, bz), buffer_tile in sorted(self._buffer_tiles.items()):
            dst = (
                int(bx - base[0] + to_pos[0]),
                int(by - base[1] + to_pos[1]),
                int(bz - base[2] + to_pos[2]),
            )
            if not (0 <= int(dst[0]) < width and 0 <= int(dst[1]) < height):
                continue

            before = self.game_map.get_tile(*dst)
            moved = Tile(
                x=int(dst[0]),
                y=int(dst[1]),
                z=int(dst[2]),
                ground=buffer_tile.ground,
                items=list(buffer_tile.items),
                house_id=buffer_tile.house_id,
                map_flags=int(buffer_tile.map_flags),
                zones=buffer_tile.zones,
                modified=True,
                monsters=list(buffer_tile.monsters),
                npc=buffer_tile.npc,
                spawn_monster=buffer_tile.spawn_monster,
                spawn_npc=buffer_tile.spawn_npc,
            )

            after: Tile
            if merge_enabled or moved.ground is None:
                if before is None:
                    after = moved
                else:
                    moved_house = int(moved.house_id or 0)
                    before_house = int(before.house_id or 0)
                    moved_flags = int(getattr(moved, "map_flags", 0) or 0)
                    before_flags = int(getattr(before, "map_flags", 0) or 0)
                    merged_monsters = list(before.monsters)
                    if moved.monsters:
                        merged_monsters.extend(moved.monsters)
                    merged_npc = moved.npc if moved.npc is not None else before.npc
                    merged_spawn_monster = (
                        moved.spawn_monster if moved.spawn_monster is not None else before.spawn_monster
                    )
                    merged_spawn_npc = moved.spawn_npc if moved.spawn_npc is not None else before.spawn_npc
                    merged_zones = before.zones | moved.zones

                    after = Tile(
                        x=int(dst[0]),
                        y=int(dst[1]),
                        z=int(dst[2]),
                        ground=before.ground if moved.ground is None else moved.ground,
                        items=list(before.items) + list(moved.items),
                        house_id=before_house if moved_house == 0 else moved_house,
                        map_flags=before_flags | moved_flags,
                        zones=merged_zones,
                        modified=True,
                        monsters=merged_monsters,
                        npc=merged_npc,
                        spawn_monster=merged_spawn_monster,
                        spawn_npc=merged_spawn_npc,
                    )
            else:
                after = moved

            if before != after:
                result[dst] = (before, after)

        return result if result else None
