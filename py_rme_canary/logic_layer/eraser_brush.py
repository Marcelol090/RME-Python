"""Eraser brush implementation for py_rme_canary.

Removes items, creatures, and spawn markers from tiles.
Mirrors legacy C++ EraserBrush from brush.cpp (included in main brush file).
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import Flag, auto
from typing import TYPE_CHECKING

from py_rme_canary.core.data.tile import Tile

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap
    from py_rme_canary.core.data.item import Position


class EraserMode(Flag):
    """What the eraser should remove."""

    ITEMS = auto()
    GROUND = auto()
    MONSTERS = auto()
    NPCS = auto()
    SPAWNS = auto()
    ALL = ITEMS | GROUND | MONSTERS | NPCS | SPAWNS


@dataclass(frozen=True, slots=True)
class EraserBrush:
    """Removes elements from tiles.

    Configurable eraser that can remove:
    - Items (except ground)
    - Ground item
    - Monsters
    - NPCs
    - Spawn markers

    Attributes:
        mode: What to erase (default: ALL)

    Example:
        >>> eraser = EraserBrush(mode=EraserMode.MONSTERS | EraserMode.NPCS)
        >>> changes = eraser.draw(game_map, pos)
    """

    mode: EraserMode = EraserMode.ALL

    def get_name(self) -> str:
        """Get brush name."""
        return "Eraser"

    def can_draw(self, game_map: "GameMap", pos: "Position") -> bool:
        """Check if there's something to erase."""
        tile = game_map.get_tile(pos.x, pos.y, pos.z)
        if tile is None:
            return False

        # Check if anything erasable exists
        if EraserMode.ITEMS in self.mode and tile.items:
            return True
        if EraserMode.GROUND in self.mode and tile.ground is not None:
            return True
        if EraserMode.MONSTERS in self.mode and tile.monsters:
            return True
        if EraserMode.NPCS in self.mode and tile.npc is not None:
            return True
        if EraserMode.SPAWNS in self.mode and (
            tile.spawn_monster is not None or tile.spawn_npc is not None
        ):
            return True

        return False

    def draw(
        self,
        game_map: "GameMap",
        pos: "Position",
    ) -> list[tuple["Position", Tile]]:
        """Erase elements from tile based on mode."""
        tile = game_map.get_tile(pos.x, pos.y, pos.z)
        if tile is None:
            return []

        # Build new tile with erased elements
        new_ground = tile.ground if EraserMode.GROUND not in self.mode else None
        new_items = tile.items if EraserMode.ITEMS not in self.mode else []
        new_monsters = tile.monsters if EraserMode.MONSTERS not in self.mode else []
        new_npc = tile.npc if EraserMode.NPCS not in self.mode else None
        new_spawn_monster = (
            tile.spawn_monster if EraserMode.SPAWNS not in self.mode else None
        )
        new_spawn_npc = tile.spawn_npc if EraserMode.SPAWNS not in self.mode else None

        # Check if anything changed
        if (
            new_ground == tile.ground
            and new_items == tile.items
            and new_monsters == tile.monsters
            and new_npc == tile.npc
            and new_spawn_monster == tile.spawn_monster
            and new_spawn_npc == tile.spawn_npc
        ):
            return []

        new_tile = Tile(
            x=tile.x,
            y=tile.y,
            z=tile.z,
            ground=new_ground,
            items=new_items,
            house_id=tile.house_id,
            map_flags=tile.map_flags,
            zones=tile.zones,
            modified=True,
            monsters=new_monsters,
            npc=new_npc,
            spawn_monster=new_spawn_monster,
            spawn_npc=new_spawn_npc,
        )

        return [(pos, new_tile)]
