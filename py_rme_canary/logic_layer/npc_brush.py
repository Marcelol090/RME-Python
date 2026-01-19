"""NPC brush implementation for py_rme_canary.

Places NPCs on tiles. Mirrors legacy C++ NpcBrush from npc_brush.cpp.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from py_rme_canary.core.data.creature import Npc
from py_rme_canary.core.data.spawns import NpcSpawnArea
from py_rme_canary.core.data.tile import Tile

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap
    from py_rme_canary.core.data.item import Position


@dataclass(frozen=True, slots=True)
class NpcBrush:
    """Places NPCs on tiles.

    Similar to MonsterBrush but for NPCs. Key difference:
    Only ONE NPC per tile (vs multiple monsters).

    Attributes:
        npc_name: Name of the NPC to place
        auto_create_spawn: If True, create spawn area if none exists
    """

    npc_name: str
    auto_create_spawn: bool = True

    def get_name(self) -> str:
        """Get brush name."""
        return self.npc_name

    def can_draw(self, game_map: "GameMap", pos: "Position") -> bool:
        """Check if NPC can be placed at position."""
        tile = game_map.get_tile(pos.x, pos.y, pos.z)
        if tile is None:
            return False

        if tile.ground is None:
            return False

        # NPC already exists
        if tile.npc is not None:
            return False

        return True

    def draw(
        self,
        game_map: "GameMap",
        pos: "Position",
    ) -> list[tuple["Position", Tile]]:
        """Place NPC at position."""
        tile = game_map.get_tile(pos.x, pos.y, pos.z)
        if tile is None or not self.can_draw(game_map, pos):
            return []

        npc = Npc(name=self.npc_name, direction=2)

        spawn_npc = tile.spawn_npc
        if spawn_npc is None and self.auto_create_spawn:
            from py_rme_canary.core.data.item import Position as Pos

            spawn_npc = NpcSpawnArea(
                center=Pos(x=pos.x, y=pos.y, z=pos.z),
                radius=1,
                npcs=(),
            )

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
            monsters=tile.monsters,
            npc=npc,
            spawn_monster=tile.spawn_monster,
            spawn_npc=spawn_npc,
        )

        return [(pos, new_tile)]

    def undraw(
        self,
        game_map: "GameMap",
        pos: "Position",
    ) -> list[tuple["Position", Tile]]:
        """Remove NPC from position."""
        tile = game_map.get_tile(pos.x, pos.y, pos.z)
        if tile is None or tile.npc is None:
            return []

        if tile.npc.name != self.npc_name:
            return []

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
            monsters=tile.monsters,
            npc=None,
            spawn_monster=tile.spawn_monster,
            spawn_npc=tile.spawn_npc,
        )

        return [(pos, new_tile)]
