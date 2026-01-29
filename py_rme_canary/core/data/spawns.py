from __future__ import annotations

from dataclasses import dataclass

from .item import Position


@dataclass(frozen=True, slots=True)
class MonsterSpawnEntry:
    name: str
    dx: int
    dy: int
    spawntime: int = 0
    direction: int | None = None
    weight: int | None = None


@dataclass(frozen=True, slots=True)
class MonsterSpawnArea:
    center: Position
    radius: int
    monsters: tuple[MonsterSpawnEntry, ...] = ()


@dataclass(frozen=True, slots=True)
class NpcSpawnEntry:
    name: str
    dx: int
    dy: int
    spawntime: int = 0
    direction: int | None = None


@dataclass(frozen=True, slots=True)
class NpcSpawnArea:
    center: Position
    radius: int
    npcs: tuple[NpcSpawnEntry, ...] = ()
