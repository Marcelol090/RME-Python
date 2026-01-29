"""Spawn Monster brush implementation for py_rme_canary.

Creates and manages monster spawn areas on the map.
Reference: source/spawn_monster_brush.cpp (legacy C++)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from py_rme_canary.core.data.item import Position
from py_rme_canary.core.data.spawns import MonsterSpawnArea
from py_rme_canary.core.data.tile import Tile

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap


@dataclass(frozen=True, slots=True)
class SpawnMonsterBrush:
    """Creates monster spawn areas on the map.

    SpawnMonsterBrush creates a MonsterSpawnArea at the painted tile.
    The spawn area defines a radius within which monsters can spawn.

    Attributes:
        radius: Spawn area radius (tiles from center)
        spawn_time: Default spawn time in seconds for monsters

    Example:
        >>> brush = SpawnMonsterBrush(radius=3, spawn_time=60)
        >>> if brush.can_draw(game_map, pos):
        ...     changes = brush.draw(game_map, pos)
    """

    radius: int = 3
    spawn_time: int = 60

    def get_name(self) -> str:
        """Get brush name."""
        return f"Monster Spawn (r={self.radius})"

    def can_draw(self, game_map: GameMap, pos: Position) -> bool:
        """Check if spawn area can be created at position.

        Requirements:
        1. Tile exists
        2. Tile has ground
        3. No spawn area already exists at this exact position

        Args:
            game_map: Target game map
            pos: Position to check

        Returns:
            True if spawn area can be created, False otherwise
        """
        tile = game_map.get_tile(pos.x, pos.y, pos.z)
        if tile is None:
            return False

        # Require ground
        if tile.ground is None:
            return False

        # Check if spawn already exists at this exact position
        for spawn in game_map.monster_spawns:
            if spawn.center.x == pos.x and spawn.center.y == pos.y and spawn.center.z == pos.z:
                return False

        return True

    def draw(
        self,
        game_map: GameMap,
        pos: Position,
    ) -> list[tuple[Position, Tile]]:
        """Create monster spawn area at position.

        Creates a MonsterSpawnArea centered at the tile with the specified radius.
        The spawn area is added to game_map.monster_spawns.

        Args:
            game_map: Target game map
            pos: Position to create spawn area

        Returns:
            List of (position, new_tile) tuples for history system
        """
        tile = game_map.get_tile(pos.x, pos.y, pos.z)
        if tile is None or not self.can_draw(game_map, pos):
            return []

        # Create spawn area
        spawn_area = MonsterSpawnArea(
            center=Position(x=pos.x, y=pos.y, z=pos.z),
            radius=self.radius,
            monsters=(),  # Empty initially, monsters added via MonsterBrush
        )

        # Add to map's spawn list
        game_map.monster_spawns.append(spawn_area)

        # Mark tile with spawn_monster reference
        new_tile = Tile(
            x=tile.x,
            y=tile.y,
            z=tile.z,
            ground=tile.ground,
            items=list(tile.items),
            house_id=tile.house_id,
            map_flags=tile.map_flags,
            zones=tile.zones,
            modified=True,
            monsters=list(tile.monsters),
            npc=tile.npc,
            spawn_monster=spawn_area,  # Reference to spawn area
            spawn_npc=tile.spawn_npc,
        )

        return [(pos, new_tile)]

    def undraw(
        self,
        game_map: GameMap,
        pos: Position,
    ) -> list[tuple[Position, Tile]]:
        """Remove monster spawn area from position.

        Removes the spawn area from game_map.monster_spawns and clears
        the spawn_monster reference from the tile.

        Args:
            game_map: Target game map
            pos: Position to remove spawn area from

        Returns:
            List of (position, new_tile) tuples for history system
        """
        tile = game_map.get_tile(pos.x, pos.y, pos.z)
        if tile is None:
            return []

        # Find and remove spawn area from map
        spawn_to_remove = None
        for spawn in game_map.monster_spawns:
            if spawn.center.x == pos.x and spawn.center.y == pos.y and spawn.center.z == pos.z:
                spawn_to_remove = spawn
                break

        if spawn_to_remove is not None:
            game_map.monster_spawns.remove(spawn_to_remove)

        # Clear spawn_monster reference from tile
        new_tile = Tile(
            x=tile.x,
            y=tile.y,
            z=tile.z,
            ground=tile.ground,
            items=list(tile.items),
            house_id=tile.house_id,
            map_flags=tile.map_flags,
            zones=tile.zones,
            modified=True,
            monsters=list(tile.monsters),
            npc=tile.npc,
            spawn_monster=None,  # Clear spawn reference
            spawn_npc=tile.spawn_npc,
        )

        return [(pos, new_tile)]
