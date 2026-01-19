"""Flag brush implementation for py_rme_canary.

Sets tile flags like Protection Zone, No-PVP, No-Logout, PVP Zone.
Mirrors legacy C++ FlagBrush from brush.cpp lines 247-297.
"""
from __future__ import annotations

from dataclasses import dataclass
from enum import IntFlag
from typing import TYPE_CHECKING

from py_rme_canary.core.data.tile import Tile

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap
    from py_rme_canary.core.data.item import Position


class TileFlag(IntFlag):
    """Tile flags matching legacy TILESTATE_* constants."""

    NONE = 0x00
    PROTECTION_ZONE = 0x01
    NO_PVP = 0x04
    NO_LOGOUT = 0x08
    PVP_ZONE = 0x10


@dataclass(frozen=True, slots=True)
class FlagBrush:
    """Sets or clears tile flags.

    Used for Protection Zone, No-PVP, No-Logout, and PVP Zone areas.

    Attributes:
        flag: The tile flag to set
        set_flag: If True, set flag; if False, clear flag

    Example:
        >>> pz_brush = FlagBrush(flag=TileFlag.PROTECTION_ZONE)
        >>> changes = pz_brush.draw(game_map, pos)
    """

    flag: TileFlag
    set_flag: bool = True

    def get_name(self) -> str:
        """Get brush name."""
        names = {
            TileFlag.PROTECTION_ZONE: "PZ brush",
            TileFlag.NO_PVP: "No-PVP brush",
            TileFlag.NO_LOGOUT: "No-Logout brush",
            TileFlag.PVP_ZONE: "PVP Zone brush",
        }
        return names.get(self.flag, "Flag brush")

    def can_draw(self, game_map: "GameMap", pos: "Position") -> bool:
        """Check if flag can be set/cleared.

        Flag brushes require tile with ground.
        """
        tile = game_map.get_tile(pos.x, pos.y, pos.z)
        if tile is None:
            return False
        return tile.ground is not None

    def draw(
        self,
        game_map: "GameMap",
        pos: "Position",
    ) -> list[tuple["Position", Tile]]:
        """Set or clear flag on tile."""
        tile = game_map.get_tile(pos.x, pos.y, pos.z)
        if tile is None or not self.can_draw(game_map, pos):
            return []

        # Calculate new flags
        if self.set_flag:
            new_flags = tile.map_flags | self.flag
        else:
            new_flags = tile.map_flags & ~self.flag

        if new_flags == tile.map_flags:
            return []  # No change

        new_tile = Tile(
            x=tile.x,
            y=tile.y,
            z=tile.z,
            ground=tile.ground,
            items=tile.items,
            house_id=tile.house_id,
            map_flags=new_flags,
            zones=tile.zones,
            modified=True,
            monsters=tile.monsters,
            npc=tile.npc,
            spawn_monster=tile.spawn_monster,
            spawn_npc=tile.spawn_npc,
        )

        return [(pos, new_tile)]

    def undraw(
        self,
        game_map: "GameMap",
        pos: "Position",
    ) -> list[tuple["Position", Tile]]:
        """Clear flag from tile (opposite of draw)."""
        # undraw is the opposite of draw
        inverted = FlagBrush(flag=self.flag, set_flag=not self.set_flag)
        return inverted.draw(game_map, pos)
