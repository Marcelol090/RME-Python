from __future__ import annotations

from dataclasses import dataclass

from .item import Position


@dataclass(frozen=True, slots=True)
class House:
    id: int
    name: str = ""

    # Exit/entry position used by legacy (entryx/entryy/entryz)
    entry: Position | None = None

    rent: int = 0
    guildhall: bool = False
    townid: int = 0

    # Optional metadata written by legacy on save
    size: int = 0
    clientid: int = 0
    beds: int = 0
