"""House brush implementation for py_rme_canary.

Paints house tiles with automatic Protection Zone and door ID assignment.
Reference: source/house_brush.cpp (legacy C++)
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from py_rme_canary.core.data.item import Item
from py_rme_canary.core.data.tile import Tile

if TYPE_CHECKING:
    from py_rme_canary.core.data.gamemap import GameMap
    from py_rme_canary.core.data.item import Position


def _is_door_item(item: Item) -> bool:
    """Check if item is a door.

    Door ID ranges (from legacy):
    - 1209-1214: Normal/Locked/Magic/Quest doors
    - 1215-1220: Hatches
    - 1221-1226: Windows
    - 5083-5085: Guild doors
    - 5732-5737: Level doors
    - 6192-6209: Quest doors
    - 6249-6266: Sealed doors
    """
    door_ranges = [
        (1209, 1226),
        (5083, 5085),
        (5732, 5737),
        (6192, 6209),
        (6249, 6266),
    ]
    item_id = int(item.id)
    return any(start <= item_id <= end for start, end in door_ranges)


def _is_moveable_item(item: Item) -> bool:
    """Check if item is moveable (loose item).

    Heuristic: Items with ID < 100 or specific item types are not moveable.
    This is a simplified version. Full implementation would check item database.
    """
    # Very basic heuristic: furniture/walls are not moveable
    immoveable_ranges = [
        (1, 99),  # Ground/terrain
        (400, 600),  # Walls
        (1200, 1700),  # Doors/windows
        (1600, 2000),  # Furniture
        (5500, 6500),  # More walls
    ]
    item_id = int(item.id)
    is_immoveable = any(start <= item_id <= end for start, end in immoveable_ranges)
    return not is_immoveable


@dataclass(frozen=True, slots=True)
class HouseBrush:
    """Paints house tiles on the map.

    HouseBrush marks tiles as belonging to a house, sets the Protection Zone
    flag, and optionally auto-assigns door IDs and removes loose items.

    Attributes:
        house_id: Unique house identifier
        house_name: Human-readable house name
        auto_assign_door_id: If True, assign unique door IDs automatically
        remove_loose_items: If True, remove moveable items from house tiles

    Example:
        >>> brush = HouseBrush(house_id=1001, house_name="Fibula House")
        >>> if brush.can_draw(game_map, pos):
        ...     changes = brush.draw(game_map, pos)
    """

    house_id: int
    house_name: str
    auto_assign_door_id: bool = True
    remove_loose_items: bool = False

    def get_name(self) -> str:
        """Get brush name."""
        return f"House {self.house_id}: {self.house_name}"

    def can_draw(self, game_map: GameMap, pos: Position) -> bool:
        """Check if house can be painted at position.

        Requirements:
        1. Tile exists
        2. Tile has ground

        Args:
            game_map: Target game map
            pos: Position to check

        Returns:
            True if house can be painted, False otherwise
        """
        tile = game_map.get_tile(pos.x, pos.y, pos.z)
        if tile is None:
            return False

        # Require ground
        return tile.ground is not None

    def draw(
        self,
        game_map: GameMap,
        pos: Position,
    ) -> list[tuple[Position, Tile]]:
        """Paint house at position.

        Actions:
        1. Set house_id
        2. Set Protection Zone flag (map_flags |= 0x01)
        3. Auto-assign door IDs (if enabled)
        4. Remove loose items (if enabled)

        Args:
            game_map: Target game map
            pos: Position to paint house

        Returns:
            List of (position, new_tile) tuples for history system
        """
        tile = game_map.get_tile(pos.x, pos.y, pos.z)
        if tile is None or not self.can_draw(game_map, pos):
            return []

        # Process items
        new_items = list(tile.items)

        # Remove loose items if enabled
        if self.remove_loose_items:
            new_items = [item for item in new_items if not _is_moveable_item(item)]

        # Auto-assign door IDs if enabled
        if self.auto_assign_door_id:
            new_items = [self._assign_door_id(item, tile.house_id) for item in new_items]

        # Create new tile with house data
        new_tile = Tile(
            x=tile.x,
            y=tile.y,
            z=tile.z,
            ground=tile.ground,
            items=new_items,
            house_id=self.house_id,
            map_flags=tile.map_flags | 0x01,  # Set PZ flag
            zones=tile.zones,
            modified=True,
            monsters=list(tile.monsters),
            npc=tile.npc,
            spawn_monster=tile.spawn_monster,
            spawn_npc=tile.spawn_npc,
        )

        return [(pos, new_tile)]

    def undraw(
        self,
        game_map: GameMap,
        pos: Position,
    ) -> list[tuple[Position, Tile]]:
        """Remove house from position.

        Actions:
        1. Clear house_id
        2. Clear Protection Zone flag (map_flags &= ~0x01)
        3. Clear door IDs

        Args:
            game_map: Target game map
            pos: Position to remove house from

        Returns:
            List of (position, new_tile) tuples for history system
        """
        tile = game_map.get_tile(pos.x, pos.y, pos.z)
        if tile is None:
            return []

        # Clear door IDs
        new_items = [self._clear_door_id(item) for item in tile.items]

        # Create new tile without house data
        new_tile = Tile(
            x=tile.x,
            y=tile.y,
            z=tile.z,
            ground=tile.ground,
            items=new_items,
            house_id=None,
            map_flags=tile.map_flags & ~0x01,  # Clear PZ flag
            zones=tile.zones,
            modified=True,
            monsters=list(tile.monsters),
            npc=tile.npc,
            spawn_monster=tile.spawn_monster,
            spawn_npc=tile.spawn_npc,
        )

        return [(pos, new_tile)]

    def _assign_door_id(self, item: Item, old_house_id: int | None) -> Item:
        """Assign door ID to door items.

        Logic from legacy:
        - Only assign if item is a door
        - Only assign if door_id is 0 OR house changed
        - Use incrementing ID based on house_id
        """
        if not _is_door_item(item):
            return item

        # If door already has ID and house didn't change, keep it
        if item.house_door_id != 0 and old_house_id == self.house_id:
            return item

        # Assign new door ID
        # Simple incrementing strategy: base 1000 + offset
        # In full implementation, this would query house for empty door ID
        new_door_id = (self.house_id * 100) + 1

        return Item(
            id=item.id,
            client_id=item.client_id,
            raw_unknown_id=item.raw_unknown_id,
            subtype=item.subtype,
            count=item.count,
            text=item.text,
            description=item.description,
            action_id=item.action_id,
            unique_id=item.unique_id,
            destination=item.destination,
            items=item.items,
            attribute_map=item.attribute_map,
            depot_id=item.depot_id,
            house_door_id=new_door_id,
        )

    def _clear_door_id(self, item: Item) -> Item:
        """Clear door ID from door items."""
        if not _is_door_item(item) or item.house_door_id == 0:
            return item

        return Item(
            id=item.id,
            client_id=item.client_id,
            raw_unknown_id=item.raw_unknown_id,
            subtype=item.subtype,
            count=item.count,
            text=item.text,
            description=item.description,
            action_id=item.action_id,
            unique_id=item.unique_id,
            destination=item.destination,
            items=item.items,
            attribute_map=item.attribute_map,
            depot_id=item.depot_id,
            house_door_id=0,
        )
