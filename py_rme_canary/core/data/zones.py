from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class Zone:
    id: int
    name: str
