"""Door brush implementation for py_rme_canary.

Converts wall items to door variants based on wall alignment.
Mirrors legacy C++ DoorBrush from brush.cpp lines 302-590.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from py_rme_canary.core.data.door import DoorType
from py_rme_canary.core.data.tile import Tile

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap
    from py_rme_canary.core.data.item import Item, Position


@dataclass(frozen=True, slots=True)
class DoorBrush:
    """Converts walls to doors based on wall alignment.

    DoorBrush requires an existing wall on the tile. It doesn't place
    doors standalone - it transforms a wall item into its door variant.

    The wall must have a WallBrush definition with door_items mapping.

    Attributes:
        door_type: Type of door to place (NORMAL, LOCKED, MAGIC, etc.)

    Example:
        >>> brush = DoorBrush(door_type=DoorType.NORMAL)
        >>> if brush.can_draw(game_map, pos):
        ...     changes = brush.draw(game_map, pos)
    """

    door_type: DoorType

    def get_name(self) -> str:
        """Get human-readable brush name."""
        return f"{self.door_type.get_name()} brush"

    def can_draw(self, game_map: "GameMap", pos: "Position") -> bool:
        """Check if door can be placed at position.

        Door placement requires:
        1. Tile exists at position
        2. Tile has a wall item
        3. Wall has associated brush with door variants for this door_type

        Args:
            game_map: Target game map
            pos: Position to check

        Returns:
            True if door can be placed, False otherwise
        """
        tile = game_map.get_tile(pos.x, pos.y, pos.z)
        if tile is None:
            return False

        # Find wall item on tile
        wall_item = self._find_wall_item(tile)
        if wall_item is None:
            return False

        # Check if wall has door variants
        # In full implementation, we'd check WallBrush.door_items
        # For now, we check if wall is convertible
        return self._has_door_variant(wall_item)

    def draw(
        self,
        game_map: "GameMap",
        pos: "Position",
        *,
        open_state: bool = False,
    ) -> list[tuple["Position", Tile]]:
        """Draw door at position by converting wall to door.

        Finds wall on tile, looks up door variant for wall alignment,
        and replaces wall item with door item.

        Args:
            game_map: Target game map
            pos: Position to place door
            open_state: Initial door state (open or closed)

        Returns:
            List of (position, new_tile) tuples for history system

        Note:
            Returns empty list if door cannot be placed (no wall, etc.)
        """
        tile = game_map.get_tile(pos.x, pos.y, pos.z)
        if tile is None:
            return []

        wall_item = self._find_wall_item(tile)
        if wall_item is None:
            return []

        # Get door variant for wall alignment
        door_item_id = self._get_door_variant(wall_item, open_state)
        if door_item_id is None:
            return []

        # Create new tile with door replacing wall
        new_items = []
        for item in tile.items:
            if self._is_wall_item(item):
                # Replace wall with door
                from py_rme_canary.core.data.item import Item

                new_items.append(Item(id=door_item_id))
            else:
                new_items.append(item)

        new_tile = Tile(
            x=tile.x,
            y=tile.y,
            z=tile.z,
            ground=tile.ground,
            items=new_items,
            house_id=tile.house_id,
            map_flags=tile.map_flags,
            zones=tile.zones,
            modified=True,
            monsters=tile.monsters,
            npc=tile.npc,
            spawn_monster=tile.spawn_monster,
            spawn_npc=tile.spawn_npc,
        )

        return [(pos, new_tile)]

    def _find_wall_item(self, tile: Tile) -> "Item | None":
        """Find wall item on tile."""
        for item in tile.items:
            if self._is_wall_item(item):
                return item
        return None

    def _is_wall_item(self, item: "Item") -> bool:
        """Check if item is a wall.

        TODO: Integrate with ItemsXML to check isWall flag.
        For now, uses ID range heuristic.
        """
        # Wall items typically in range 400-600 and 1200-1600
        # This is a simplification - real check uses items.xml
        wall_ranges = [(400, 600), (1200, 1600), (5500, 6500)]
        return any(start <= item.id <= end for start, end in wall_ranges)

    def _has_door_variant(self, wall_item: "Item") -> bool:
        """Check if wall has door variants defined.

        TODO: Integrate with WallBrush definitions.
        """
        # Placeholder: most walls support doors
        return True

    def _get_door_variant(
        self,
        wall_item: "Item",
        open_state: bool,
    ) -> int | None:
        """Get door item ID for wall alignment.

        TODO: Full implementation with WallBrush.door_items lookup.
        Returns placeholder door IDs for now.
        """
        # Placeholder door IDs based on door type
        # In full implementation, we'd:
        # 1. Get wall_alignment from wall_item
        # 2. Look up WallBrush.door_items[alignment][door_type]
        # 3. Select open/closed variant

        base_doors = {
            DoorType.NORMAL: 1209,
            DoorType.LOCKED: 1210,
            DoorType.MAGIC: 1211,
            DoorType.QUEST: 1212,
            DoorType.HATCH: 1215,
            DoorType.WINDOW: 1216,
        }

        return base_doors.get(self.door_type)

    @staticmethod
    def switch_door(item: "Item") -> "Item":
        """Toggle door between open and closed state.

        Creates new Item with toggled door ID.
        In full implementation, looks up opposite state in WallBrush.

        Args:
            item: Door item to toggle

        Returns:
            New Item with toggled state
        """
        from py_rme_canary.core.data.item import Item

        # Placeholder: toggle between consecutive IDs
        # Open doors typically have ID = closed_id + 3
        # This is a simplification - real logic uses door_items lookup
        if item.id % 2 == 0:
            new_id = item.id + 1  # Closed -> Open
        else:
            new_id = item.id - 1  # Open -> Closed

        return Item(id=new_id)
