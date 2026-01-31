"""Item Type Detection for Smart Context Menu Actions.

Detects item types (Wall, Carpet, Door, Table, etc.) to provide
intelligent context menu options.

Reference: RME/source/ui/map_popup_menu.cpp
"""

from __future__ import annotations

from enum import Enum
from typing import TYPE_CHECKING

from py_rme_canary.core.data.item import Item

if TYPE_CHECKING:
    pass


class ItemCategory(str, Enum):
    """Item category for smart actions."""

    WALL = "wall"
    CARPET = "carpet"
    DOOR = "door"
    TABLE = "table"
    CHAIR = "chair"
    CONTAINER = "container"
    TELEPORT = "teleport"
    CREATURE = "creature"
    SPAWN = "spawn"
    ROTATABLE = "rotatable"
    UNKNOWN = "unknown"


# Item ID ranges (based on typical Tibia OT conventions)
# These are approximate and should be refined based on actual items.otb
WALL_IDS = range(1000, 1200)
CARPET_IDS = range(1300, 1400)
DOOR_IDS = range(1200, 1300)  # Includes open/closed variants
TABLE_IDS = range(1614, 1650)
CHAIR_IDS = range(1714, 1755)
CONTAINER_IDS = {1987, 1988, 1989, 1990, 1991, 1992, 1993, 1994, 1995, 2000, 2001, 2002, 2003, 2004, 2005}
TELEPORT_IDS = {1387, 5023}

# Door pairs (closed -> open)
DOOR_PAIRS = {
    1209: 1210,  # Wooden door
    1211: 1212,
    1213: 1214,
    1215: 1216,
    1219: 1220,  # Stone door
    1221: 1222,
    # Add more door pairs as needed
}

# Rotatable items (ID sequences)
ROTATABLE_SEQUENCES = {
    # Torch: 2050 -> 2051 -> 2052 -> 2053 -> 2050
    2050: [2050, 2051, 2052, 2053],
    2051: [2050, 2051, 2052, 2053],
    2052: [2050, 2051, 2052, 2053],
    2053: [2050, 2051, 2052, 2053],
}


class ItemTypeDetector:
    """Detector for item types and smart actions."""

    @staticmethod
    def get_category(item: Item) -> ItemCategory:
        """Detect item category.

        Args:
            item: Item to categorize

        Returns:
            ItemCategory enum
        """
        item_id = int(item.id)

        # Check specific categories
        if item_id in WALL_IDS:
            return ItemCategory.WALL
        elif item_id in CARPET_IDS:
            return ItemCategory.CARPET
        elif item_id in DOOR_IDS:
            return ItemCategory.DOOR
        elif item_id in TABLE_IDS:
            return ItemCategory.TABLE
        elif item_id in CHAIR_IDS:
            return ItemCategory.CHAIR
        elif item_id in CONTAINER_IDS:
            return ItemCategory.CONTAINER
        elif item_id in TELEPORT_IDS:
            return ItemCategory.TELEPORT
        elif item_id in ROTATABLE_SEQUENCES:
            return ItemCategory.ROTATABLE

        return ItemCategory.UNKNOWN

    @staticmethod
    def is_door(item: Item) -> bool:
        """Check if item is a door.

        Args:
            item: Item to check

        Returns:
            True if item is a door
        """
        return int(item.id) in DOOR_IDS

    @staticmethod
    def get_door_toggle_id(item: Item) -> int | None:
        """Get the ID to toggle door state (open <-> closed).

        Args:
            item: Door item

        Returns:
            ID of toggled state, or None if not a door
        """
        item_id = int(item.id)

        # Check if it's a closed door
        if item_id in DOOR_PAIRS:
            return DOOR_PAIRS[item_id]

        # Check if it's an open door (reverse lookup)
        for closed_id, open_id in DOOR_PAIRS.items():
            if item_id == open_id:
                return closed_id

        return None

    @staticmethod
    def is_door_open(item: Item) -> bool:
        """Check if door is in open state.

        Args:
            item: Door item

        Returns:
            True if door is open
        """
        item_id = int(item.id)
        # If ID is in values of DOOR_PAIRS, it's open
        return item_id in DOOR_PAIRS.values()

    @staticmethod
    def is_rotatable(item: Item) -> bool:
        """Check if item is rotatable.

        Args:
            item: Item to check

        Returns:
            True if item can be rotated
        """
        return int(item.id) in ROTATABLE_SEQUENCES

    @staticmethod
    def get_next_rotation_id(item: Item) -> int | None:
        """Get the next rotation ID for a rotatable item.

        Args:
            item: Rotatable item

        Returns:
            Next rotation ID, or None if not rotatable
        """
        item_id = int(item.id)

        if item_id not in ROTATABLE_SEQUENCES:
            return None

        sequence = ROTATABLE_SEQUENCES[item_id]
        current_index = sequence.index(item_id)
        next_index = (current_index + 1) % len(sequence)

        return sequence[next_index]

    @staticmethod
    def is_teleport(item: Item) -> bool:
        """Check if item is a teleport.

        Args:
            item: Item to check

        Returns:
            True if item is a teleport
        """
        return int(item.id) in TELEPORT_IDS

    @staticmethod
    def get_teleport_destination(item: Item) -> tuple[int, int, int] | None:
        """Get teleport destination coordinates.

        Args:
            item: Teleport item

        Returns:
            (x, y, z) tuple or None
        """
        if not ItemTypeDetector.is_teleport(item):
            return None

        destination = item.destination
        if destination is None:
            return None

        return (destination.x, destination.y, destination.z)

    @staticmethod
    def get_brush_name(category: ItemCategory) -> str:
        """Get brush name for a category.

        Args:
            category: Item category

        Returns:
            Human-readable brush name
        """
        names = {
            ItemCategory.WALL: "wall",
            ItemCategory.CARPET: "carpet",
            ItemCategory.DOOR: "door",
            ItemCategory.TABLE: "table",
            ItemCategory.CHAIR: "chair",
            ItemCategory.CONTAINER: "container",
            ItemCategory.TELEPORT: "teleport",
        }
        return names.get(category, "item")

    @staticmethod
    def can_select_brush(item_or_category: Item | ItemCategory) -> bool:
        """Check if category supports brush selection.

        Args:
            category: Item category

        Returns:
            True if category has an associated brush
        """
        if isinstance(item_or_category, Item):
            category = ItemTypeDetector.get_category(item_or_category)
        else:
            category = item_or_category

        return category in {
            ItemCategory.WALL,
            ItemCategory.CARPET,
            ItemCategory.DOOR,
            ItemCategory.TABLE,
        }
