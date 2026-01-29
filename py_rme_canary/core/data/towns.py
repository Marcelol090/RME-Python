from __future__ import annotations

from dataclasses import dataclass

from .item import Position


@dataclass(frozen=True, slots=True)
class Town:
    id: int
    name: str
    temple_position: Position
