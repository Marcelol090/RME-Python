from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Outfit:
    """Creature visual appearance (outfit/looktype).

    Based on TFS/Canary XML format:
    - looktype: outfit ID (for humanoid creatures)
    - lookitem: item ID (for creatures that appear as items)
    - lookhead, lookbody, looklegs, lookfeet: color values (0-132)
    - lookaddons: addon flags (0-3)
    """

    looktype: int | None = None
    lookitem: int | None = None
    lookhead: int = 0
    lookbody: int = 0
    looklegs: int = 0
    lookfeet: int = 0
    lookaddons: int = 0

    @property
    def has_looktype(self) -> bool:
        """Check if creature uses looktype (outfit)."""
        return self.looktype is not None

    @property
    def has_lookitem(self) -> bool:
        """Check if creature appears as item."""
        return self.lookitem is not None


@dataclass(slots=True)
class Creature:
    """Base class for living entities (Monsters and NPCs).

    Represents a creature instance on the map. Includes both
    positional data (name, direction) and visual appearance (outfit).
    """

    name: str
    direction: int = 2  # default south (2) in Tibia
    outfit: Outfit | None = None

    def with_outfit(self, outfit: Outfit) -> Creature:
        """Create a copy with new outfit."""
        if isinstance(self, Monster):
            return Monster(name=self.name, direction=self.direction, outfit=outfit)
        elif isinstance(self, Npc):
            return Npc(name=self.name, direction=self.direction, outfit=outfit)
        return Creature(name=self.name, direction=self.direction, outfit=outfit)


@dataclass(slots=True)
class Monster(Creature):
    """A spawned monster instance on a tile."""

    pass


@dataclass(slots=True)
class Npc(Creature):
    """A spawned NPC instance on a tile."""

    pass
