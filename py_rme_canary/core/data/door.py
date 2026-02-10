"""Door type definitions for py_rme_canary.

Mirrors legacy C++ enum DoorType from brush.h.
"""

from __future__ import annotations

from enum import IntEnum


class DoorType(IntEnum):
    """Door type enumeration.

    Represents different door types supported by DoorBrush.
    Values match legacy C++ WALL_* constants (brush_enums.h).

    Attributes:
        UNDEFINED: Placeholder / unknown
        ARCHWAY: Archway-style passage
        NORMAL: Standard door that can be opened/closed
        LOCKED: Door requiring key to open
        QUEST: Quest-related door
        MAGIC: Door requiring magic level
        WINDOW: Window that can be opened
        HATCH: Hatch/trapdoor variant
    """

    UNDEFINED = 0
    ARCHWAY = 1
    NORMAL = 2
    LOCKED = 3
    QUEST = 4
    MAGIC = 5
    WINDOW = 6
    HATCH = 7

    def get_name(self) -> str:
        """Get human-readable door type name."""
        names = {
            DoorType.UNDEFINED: "Unknown door",
            DoorType.ARCHWAY: "Archway",
            DoorType.NORMAL: "Normal door",
            DoorType.LOCKED: "Locked door",
            DoorType.QUEST: "Quest door",
            DoorType.MAGIC: "Magic door",
            DoorType.WINDOW: "Window",
            DoorType.HATCH: "Hatch window",
        }
        return names.get(self, "Unknown door")
