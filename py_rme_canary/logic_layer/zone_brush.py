"""Zone/Flag Brush Implementation.

Brush for painting zone flags (PZ, noPVP, noLogout, PVP) onto map tiles.
This mirrors the legacy C++ FlagBrush from source/brushes/flag/flag_brush.cpp.

Zone brushes are used to mark map areas with special properties:
- Protection Zone (PZ): Safe area where PvP is disabled
- No PVP Zone: Area where combat is disabled
- No Logout Zone: Area where players cannot log out
- PVP Zone: Explicit PvP-enabled area

Reference:
    - C++ FlagBrush: source/brushes/flag/flag_brush.cpp
    - Tile flags: map/tile.h
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from enum import IntFlag
from typing import TYPE_CHECKING, Any, Final

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class TileStateFlag(IntFlag):
    """Tile state flags matching C++ TILESTATE enum.

    These flags define special properties of map tiles.
    Values mirror C++ defines in tile.h.
    """

    NONE = 0
    PROTECTIONZONE = 0x0001  # PZ - Safe zone
    DEPRECATED_HOUSE = 0x0002  # Deprecated, use HOUSE_ID instead
    NOPVP = 0x0004  # No combat zone
    NOLOGOUT = 0x0008  # No logout zone
    PVPZONE = 0x0010  # PVP zone
    REFRESH = 0x0020  # Refresh flag

    # Additional flags from RME
    BLOCKING = 0x0040  # Blocks movement
    IMMOVABLE = 0x0080  # Cannot be moved
    MAGICFIELD = 0x0100  # Has magic field
    BLOCKSOLID = 0x0200  # Blocks solid items
    BLOCKPATH = 0x0400  # Blocks pathfinding


@dataclass(frozen=True, slots=True)
class ZoneInfo:
    """Information about a zone type.

    Attributes:
        flag: The tile state flag for this zone.
        name: Human-readable name.
        short_name: Short identifier (e.g., "pz", "nopvp").
        description: Detailed description of the zone.
        color: Display color as RGB tuple.
    """

    flag: TileStateFlag
    name: str
    short_name: str
    description: str
    color: tuple[int, int, int]


# Zone type definitions mirroring C++ flag_brush.cpp
ZONE_PROTECTION: Final[ZoneInfo] = ZoneInfo(
    flag=TileStateFlag.PROTECTIONZONE,
    name="Protection Zone",
    short_name="pz",
    description="Safe area where PvP combat is disabled",
    color=(50, 200, 50),  # Green
)

ZONE_NOPVP: Final[ZoneInfo] = ZoneInfo(
    flag=TileStateFlag.NOPVP,
    name="No Combat Zone",
    short_name="nopvp",
    description="Area where all combat is disabled",
    color=(200, 200, 50),  # Yellow
)

ZONE_NOLOGOUT: Final[ZoneInfo] = ZoneInfo(
    flag=TileStateFlag.NOLOGOUT,
    name="No Logout Zone",
    short_name="nolog",
    description="Area where players cannot log out",
    color=(200, 50, 50),  # Red
)

ZONE_PVP: Final[ZoneInfo] = ZoneInfo(
    flag=TileStateFlag.PVPZONE,
    name="PVP Zone",
    short_name="pvp",
    description="Explicit PvP-enabled area",
    color=(200, 50, 200),  # Magenta
)

# All zone types for iteration
ALL_ZONES: Final[tuple[ZoneInfo, ...]] = (
    ZONE_PROTECTION,
    ZONE_NOPVP,
    ZONE_NOLOGOUT,
    ZONE_PVP,
)


class ZoneBrush:
    """Brush for painting zone flags onto tiles.

    This brush sets or clears zone flags on map tiles.
    It mirrors the legacy C++ FlagBrush implementation.

    Attributes:
        zone_info: Information about the zone type being painted.

    Example:
        >>> brush = ZoneBrush(ZONE_PROTECTION)
        >>> brush.draw(map, tile)  # Mark tile as protection zone
        >>> brush.undraw(map, tile)  # Remove protection zone flag
    """

    __slots__ = ("_zone_info", "_flag")

    def __init__(self, zone_info: ZoneInfo) -> None:
        """Initialize a zone brush.

        Args:
            zone_info: Zone type information.
        """
        self._zone_info = zone_info
        self._flag = zone_info.flag

    @property
    def zone_info(self) -> ZoneInfo:
        """Get zone information."""
        return self._zone_info

    @property
    def flag(self) -> TileStateFlag:
        """Get the tile state flag."""
        return self._flag

    def get_name(self) -> str:
        """Get brush display name.

        Returns:
            Human-readable name with hex code like C++.
        """
        return f"{self._zone_info.name} brush (0x{self._flag:02X})"

    def get_short_name(self) -> str:
        """Get short zone identifier."""
        return self._zone_info.short_name

    def get_description(self) -> str:
        """Get zone description."""
        return self._zone_info.description

    def get_color(self) -> tuple[int, int, int]:
        """Get display color RGB tuple."""
        return self._zone_info.color

    def can_draw(self, map_obj: Any, position: Any) -> bool:
        """Check if brush can draw at position.

        Mirrors C++ FlagBrush::canDraw - requires tile with ground.

        Args:
            map_obj: Map object (BaseMap equivalent).
            position: Position to check.

        Returns:
            True if tile exists and has ground.
        """
        tile = getattr(map_obj, "get_tile", lambda p: None)(position)
        if tile is None:
            return False

        # Check for ground - mirrors C++ tile->hasGround()
        has_ground = getattr(tile, "has_ground", lambda: False)
        if callable(has_ground):
            return has_ground()
        return bool(has_ground)

    def draw(self, map_obj: Any, tile: Any, parameter: Any = None) -> None:
        """Paint zone flag onto tile.

        Mirrors C++ FlagBrush::draw - sets flag if tile has ground.

        Args:
            map_obj: Map object (unused, matches C++ signature).
            tile: Tile to paint.
            parameter: Optional parameter (unused, matches C++ signature).
        """
        # Check for ground first - mirrors C++ behavior
        has_ground = getattr(tile, "has_ground", lambda: True)
        if callable(has_ground):
            if not has_ground():
                return
        elif not has_ground:
            return

        # Set map flags - mirrors tile->setMapFlags(flag)
        set_flags = getattr(tile, "set_map_flags", None)
        if set_flags:
            set_flags(int(self._flag))
            logger.debug(f"Set zone flag 0x{self._flag:02X} on tile")
        else:
            # Alternative: set flag directly
            if hasattr(tile, "map_flags"):
                tile.map_flags |= int(self._flag)
            elif hasattr(tile, "flags"):
                tile.flags |= int(self._flag)

    def undraw(self, map_obj: Any, tile: Any) -> None:
        """Remove zone flag from tile.

        Mirrors C++ FlagBrush::undraw.

        Args:
            map_obj: Map object (unused, matches C++ signature).
            tile: Tile to unpaint.
        """
        # Clear map flags - mirrors tile->unsetMapFlags(flag)
        unset_flags = getattr(tile, "unset_map_flags", None)
        if unset_flags:
            unset_flags(int(self._flag))
            logger.debug(f"Cleared zone flag 0x{self._flag:02X} from tile")
        else:
            # Alternative: clear flag directly
            if hasattr(tile, "map_flags"):
                tile.map_flags &= ~int(self._flag)
            elif hasattr(tile, "flags"):
                tile.flags &= ~int(self._flag)

    def is_set(self, tile: Any) -> bool:
        """Check if zone flag is set on tile.

        Args:
            tile: Tile to check.

        Returns:
            True if zone flag is set.
        """
        get_flags = getattr(tile, "get_map_flags", None)
        if get_flags:
            return bool(get_flags() & int(self._flag))

        # Alternative: check flag directly
        if hasattr(tile, "map_flags"):
            return bool(tile.map_flags & int(self._flag))
        elif hasattr(tile, "flags"):
            return bool(tile.flags & int(self._flag))

        return False

    def __repr__(self) -> str:
        return f"ZoneBrush({self._zone_info.short_name})"


class ZoneBrushManager:
    """Manager for zone brushes - singleton-like access.

    Provides pre-built zone brush instances mirroring C++ brush manager.

    Example:
        >>> manager = ZoneBrushManager()
        >>> pz_brush = manager.pz_brush
        >>> pz_brush.draw(map, tile)
    """

    __slots__ = ("_pz_brush", "_nopvp_brush", "_nolog_brush", "_pvp_brush")

    def __init__(self) -> None:
        """Initialize manager with all zone brushes."""
        self._pz_brush = ZoneBrush(ZONE_PROTECTION)
        self._nopvp_brush = ZoneBrush(ZONE_NOPVP)
        self._nolog_brush = ZoneBrush(ZONE_NOLOGOUT)
        self._pvp_brush = ZoneBrush(ZONE_PVP)

    @property
    def pz_brush(self) -> ZoneBrush:
        """Get Protection Zone brush."""
        return self._pz_brush

    @property
    def nopvp_brush(self) -> ZoneBrush:
        """Get No PVP Zone brush."""
        return self._nopvp_brush

    @property
    def nolog_brush(self) -> ZoneBrush:
        """Get No Logout Zone brush."""
        return self._nolog_brush

    @property
    def pvp_brush(self) -> ZoneBrush:
        """Get PVP Zone brush."""
        return self._pvp_brush

    def get_brush_by_flag(self, flag: int) -> ZoneBrush | None:
        """Get zone brush by flag value.

        Args:
            flag: Tile state flag value.

        Returns:
            Matching zone brush or None.
        """
        flag_map = {
            TileStateFlag.PROTECTIONZONE: self._pz_brush,
            TileStateFlag.NOPVP: self._nopvp_brush,
            TileStateFlag.NOLOGOUT: self._nolog_brush,
            TileStateFlag.PVPZONE: self._pvp_brush,
        }
        return flag_map.get(TileStateFlag(flag))

    def get_brush_by_name(self, name: str) -> ZoneBrush | None:
        """Get zone brush by short name.

        Args:
            name: Short name (e.g., "pz", "nopvp").

        Returns:
            Matching zone brush or None.
        """
        name_map = {
            "pz": self._pz_brush,
            "protectionzone": self._pz_brush,
            "nopvp": self._nopvp_brush,
            "nocombat": self._nopvp_brush,
            "nolog": self._nolog_brush,
            "nologout": self._nolog_brush,
            "pvp": self._pvp_brush,
            "pvpzone": self._pvp_brush,
        }
        return name_map.get(name.lower())

    def all_brushes(self) -> list[ZoneBrush]:
        """Get all zone brushes.

        Returns:
            List of all zone brush instances.
        """
        return [self._pz_brush, self._nopvp_brush, self._nolog_brush, self._pvp_brush]


# Global manager instance for convenience
_zone_manager: ZoneBrushManager | None = None


def get_zone_manager() -> ZoneBrushManager:
    """Get global zone brush manager instance.

    Returns:
        Singleton ZoneBrushManager instance.
    """
    global _zone_manager
    if _zone_manager is None:
        _zone_manager = ZoneBrushManager()
    return _zone_manager


def get_zone_flags_from_tile(tile: Any) -> list[ZoneInfo]:
    """Get all zone flags set on a tile.

    Args:
        tile: Tile to inspect.

    Returns:
        List of ZoneInfo for all set zones.
    """
    result: list[ZoneInfo] = []

    # Get flags from tile
    flags = 0
    get_flags = getattr(tile, "get_map_flags", None)
    if get_flags:
        flags = get_flags()
    elif hasattr(tile, "map_flags"):
        flags = tile.map_flags
    elif hasattr(tile, "flags"):
        flags = tile.flags

    # Check each zone
    for zone in ALL_ZONES:
        if flags & int(zone.flag):
            result.append(zone)

    return result


__all__ = [
    "TileStateFlag",
    "ZoneInfo",
    "ZoneBrush",
    "ZoneBrushManager",
    "ZONE_PROTECTION",
    "ZONE_NOPVP",
    "ZONE_NOLOGOUT",
    "ZONE_PVP",
    "ALL_ZONES",
    "get_zone_manager",
    "get_zone_flags_from_tile",
]
