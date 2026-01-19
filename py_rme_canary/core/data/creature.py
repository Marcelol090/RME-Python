from __future__ import annotations

from dataclasses import dataclass

from .item import Item


@dataclass(slots=True)
class Creature:
    """Base class for living entities (Monsters and NPCs)."""

    name: str
    direction: int = 2  # default south (2) in many contexts, or 0? 2 is standard Tibia south.
    # Add other common fields here if needed


@dataclass(slots=True)
class Monster(Creature):
    """A spawned monster instance on a tile."""
    pass


@dataclass(slots=True)
class Npc(Creature):
    """A spawned NPC instance on a tile."""
    pass
