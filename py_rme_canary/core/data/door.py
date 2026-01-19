"""Door type definitions for py_rme_canary.

Mirrors legacy C++ enum DoorType from brush.h.
"""
from __future__ import annotations

from enum import IntEnum


class DoorType(IntEnum):
    """Door type enumeration.

    Represents different door types supported by DoorBrush.
    Values match legacy C++ WALL_DOOR_* constants.

    Attributes:
        NORMAL: Standard door that can be opened/closed
        LOCKED: Door requiring key to open
        MAGIC: Door requiring magic level
        QUEST: Quest-related door
        HATCH: Hatch/trapdoor variant
        WINDOW: Window that can be opened
    """

    NORMAL = 1
    LOCKED = 2
    MAGIC = 3
    QUEST = 4
    HATCH = 5
    WINDOW = 6

    def get_name(self) -> str:
        """Get human-readable door type name."""
        names = {
            DoorType.NORMAL: "Normal door",
            DoorType.LOCKED: "Locked door",
            DoorType.MAGIC: "Magic door",
            DoorType.QUEST: "Quest door",
            DoorType.HATCH: "Hatch window",
            DoorType.WINDOW: "Window",
        }
        return names.get(self, "Unknown door")
