"""Spawn NPC brush implementation for py_rme_canary.

Creates and manages NPC spawn areas on the map.
Reference: source/spawn_npc_brush.cpp (legacy C++)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from py_rme_canary.core.data.item import Position
from py_rme_canary.core.data.spawns import NpcSpawnArea
from py_rme_canary.core.data.tile import Tile

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap


@dataclass(frozen=True, slots=True)
class SpawnNpcBrush:
    """Creates NPC spawn areas on the map.

    SpawnNpcBrush creates an NpcSpawnArea at the painted tile.
    Similar to SpawnMonsterBrush but for NPCs.

    Attributes:
        radius: Spawn area radius (tiles from center)
        spawn_time: Default spawn time in seconds for NPCs

    Example:
        >>> brush = SpawnNpcBrush(radius=1, spawn_time=60)
        >>> if brush.can_draw(game_map, pos):
        ...     changes = brush.draw(game_map, pos)
    """

    radius: int = 1
    spawn_time: int = 60

    def get_name(self) -> str:
        """Get brush name."""
        return f"NPC Spawn (r={self.radius})"

    def can_draw(self, game_map: GameMap, pos: Position) -> bool:
        """Check if spawn area can be created at position.

        Requirements:
        1. Tile exists
        2. Tile has ground
        3. No NPC spawn area already exists at this exact position

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

        # Check if NPC spawn already exists at this exact position
        for spawn in game_map.npc_spawns:
            if spawn.center.x == pos.x and spawn.center.y == pos.y and spawn.center.z == pos.z:
                return False

        return True

    def draw(
        self,
        game_map: GameMap,
        pos: Position,
    ) -> list[tuple[Position, Tile]]:
        """Create NPC spawn area at position.

        Creates an NpcSpawnArea centered at the tile with the specified radius.
        The spawn area is added to game_map.npc_spawns.

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
        spawn_area = NpcSpawnArea(
            center=Position(x=pos.x, y=pos.y, z=pos.z),
            radius=self.radius,
            npcs=(),  # Empty initially, NPCs added via NpcBrush
        )

        # Add to map's spawn list
        game_map.npc_spawns.append(spawn_area)

        # Mark tile with spawn_npc reference
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
            spawn_monster=tile.spawn_monster,
            spawn_npc=spawn_area,  # Reference to spawn area
        )

        return [(pos, new_tile)]

    def undraw(
        self,
        game_map: GameMap,
        pos: Position,
    ) -> list[tuple[Position, Tile]]:
        """Remove NPC spawn area from position.

        Removes the spawn area from game_map.npc_spawns and clears
        the spawn_npc reference from the tile.

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
        for spawn in game_map.npc_spawns:
            if spawn.center.x == pos.x and spawn.center.y == pos.y and spawn.center.z == pos.z:
                spawn_to_remove = spawn
                break

        if spawn_to_remove is not None:
            game_map.npc_spawns.remove(spawn_to_remove)

        # Clear spawn_npc reference from tile
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
            spawn_monster=tile.spawn_monster,
            spawn_npc=None,  # Clear spawn reference
        )

        return [(pos, new_tile)]
