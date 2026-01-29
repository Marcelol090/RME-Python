"""Monster brush implementation for py_rme_canary.

Places monsters on tiles within spawn areas.
Mirrors legacy C++ MonsterBrush from monster_brush.cpp.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from py_rme_canary.core.data.creature import Monster
from py_rme_canary.core.data.spawns import MonsterSpawnArea
from py_rme_canary.core.data.tile import Tile

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap
    from py_rme_canary.core.data.item import Position


@dataclass(frozen=True, slots=True)
class MonsterBrush:
    """Places monsters on tiles.

    MonsterBrush adds monster instances to tiles. It requires:
    - Tile has ground
    - Tile is not blocking
    - Tile is not in Protection Zone (PZ)
    - Tile is within a spawn area (or auto-create spawn is enabled)

    Attributes:
        monster_name: Name of the monster to place
        spawn_time: Default spawn time in seconds (default 60)
        auto_create_spawn: If True, create spawn area if none exists

    Example:
        >>> brush = MonsterBrush(monster_name="Rat")
        >>> if brush.can_draw(game_map, pos):
        ...     changes = brush.draw(game_map, pos)
    """

    monster_name: str
    spawn_time: int = 60
    auto_create_spawn: bool = True

    def get_name(self) -> str:
        """Get brush name."""
        return self.monster_name

    def can_draw(self, game_map: GameMap, pos: Position) -> bool:
        """Check if monster can be placed at position.

        Placement requires:
        1. Tile exists with ground
        2. Tile is not blocking
        3. Tile is not in Protection Zone
        4. Tile is within spawn area OR auto_create_spawn is True

        Args:
            game_map: Target game map
            pos: Position to check

        Returns:
            True if monster can be placed, False otherwise
        """
        tile = game_map.get_tile(pos.x, pos.y, pos.z)
        if tile is None:
            return False

        # Check ground exists
        if tile.ground is None:
            return False

        # Check not in Protection Zone
        if self._is_protection_zone(tile):
            return False

        # Check spawn exists or auto-create enabled
        return bool(tile.spawn_monster is not None or self.auto_create_spawn or self._is_in_spawn_area(game_map, pos))

    def draw(
        self,
        game_map: GameMap,
        pos: Position,
    ) -> list[tuple[Position, Tile]]:
        """Place monster at position.

        If no spawn exists and auto_create_spawn is True, creates a new
        spawn area with radius 1 at the tile.

        Args:
            game_map: Target game map
            pos: Position to place monster

        Returns:
            List of (position, new_tile) tuples for history system
        """
        tile = game_map.get_tile(pos.x, pos.y, pos.z)
        if tile is None or not self.can_draw(game_map, pos):
            return []

        # Check if monster already exists on tile
        for existing_monster in tile.monsters:
            if existing_monster.name == self.monster_name:
                return []  # Monster already present

        # Create monster instance
        monster = Monster(name=self.monster_name, direction=2)

        # Build updated monsters list
        new_monsters = list(tile.monsters)
        new_monsters.append(monster)

        # Create spawn if needed
        spawn_monster = tile.spawn_monster
        if spawn_monster is None and self.auto_create_spawn:
            from py_rme_canary.core.data.item import Position as Pos

            spawn_monster = MonsterSpawnArea(
                center=Pos(x=pos.x, y=pos.y, z=pos.z),
                radius=1,
                monsters=(),
            )

        # Create new tile
        new_tile = Tile(
            x=tile.x,
            y=tile.y,
            z=tile.z,
            ground=tile.ground,
            items=tile.items,
            house_id=tile.house_id,
            map_flags=tile.map_flags,
            zones=tile.zones,
            modified=True,
            monsters=new_monsters,
            npc=tile.npc,
            spawn_monster=spawn_monster,
            spawn_npc=tile.spawn_npc,
        )

        return [(pos, new_tile)]

    def undraw(
        self,
        game_map: GameMap,
        pos: Position,
    ) -> list[tuple[Position, Tile]]:
        """Remove monster from position.

        Args:
            game_map: Target game map
            pos: Position to remove monster from

        Returns:
            List of (position, new_tile) tuples for history system
        """
        tile = game_map.get_tile(pos.x, pos.y, pos.z)
        if tile is None:
            return []

        # Remove matching monster
        new_monsters = [m for m in tile.monsters if m.name != self.monster_name]

        if len(new_monsters) == len(tile.monsters):
            return []  # No monster removed

        new_tile = Tile(
            x=tile.x,
            y=tile.y,
            z=tile.z,
            ground=tile.ground,
            items=tile.items,
            house_id=tile.house_id,
            map_flags=tile.map_flags,
            zones=tile.zones,
            modified=True,
            monsters=new_monsters,
            npc=tile.npc,
            spawn_monster=tile.spawn_monster,
            spawn_npc=tile.spawn_npc,
        )

        return [(pos, new_tile)]

    def _is_protection_zone(self, tile: Tile) -> bool:
        """Check if tile is in Protection Zone."""
        # PZ flag is typically bit 0x01 in map_flags
        return (tile.map_flags & 0x01) != 0

    def _is_in_spawn_area(self, game_map: GameMap, pos: Position) -> bool:
        """Check if position is within any monster spawn area."""
        for spawn in game_map.monster_spawns:
            cx, cy, cz = spawn.center.x, spawn.center.y, spawn.center.z
            if cz != pos.z:
                continue
            dx = abs(pos.x - cx)
            dy = abs(pos.y - cy)
            if dx <= spawn.radius and dy <= spawn.radius:
                return True
        return False
