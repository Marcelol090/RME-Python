"""Hotkey Manager - 10-slot brush / position quick-access system.

Mirrors legacy C++ ``HotkeyManager`` from ``editor/hotkey_manager.h``.

Users can bind a brush name *or* a map position to slots 0-9 (F1-F10).
Slots persist across sessions via a JSON file next to the user's config.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)

NUM_SLOTS = 10

# ---------------------  Data model  -----------------------------------------


class HotkeyType(Enum):
    """Type of hotkey binding."""

    NONE = auto()
    BRUSH = auto()
    POSITION = auto()


@dataclass(slots=True)
class HotkeyPosition:
    """Map position for a hotkey slot."""

    x: int = 0
    y: int = 0
    z: int = 7


@dataclass(slots=True)
class Hotkey:
    """Single hotkey slot that stores either a brush name or a position."""

    type: HotkeyType = HotkeyType.NONE
    brush_name: str = ""
    position: HotkeyPosition = field(default_factory=HotkeyPosition)

    # -- factories --

    @classmethod
    def from_brush(cls, name: str) -> Hotkey:
        """Create a hotkey that activates a brush by name."""
        return cls(type=HotkeyType.BRUSH, brush_name=name)

    @classmethod
    def from_position(cls, x: int, y: int, z: int) -> Hotkey:
        """Create a hotkey that jumps to a map position."""
        return cls(type=HotkeyType.POSITION, position=HotkeyPosition(x, y, z))

    # -- predicates --

    @property
    def is_brush(self) -> bool:
        return self.type is HotkeyType.BRUSH

    @property
    def is_position(self) -> bool:
        return self.type is HotkeyType.POSITION

    @property
    def is_empty(self) -> bool:
        return self.type is HotkeyType.NONE

    # -- serialisation --

    def to_dict(self) -> dict:
        d: dict = {"type": self.type.name}
        if self.is_brush:
            d["brush_name"] = self.brush_name
        elif self.is_position:
            d["position"] = asdict(self.position)
        return d

    @classmethod
    def from_dict(cls, d: dict) -> Hotkey:
        t = HotkeyType[d.get("type", "NONE")]
        if t is HotkeyType.BRUSH:
            return cls.from_brush(d.get("brush_name", ""))
        if t is HotkeyType.POSITION:
            p = d.get("position", {})
            return cls.from_position(p.get("x", 0), p.get("y", 0), p.get("z", 7))
        return cls()

    def describe(self) -> str:
        """Human-readable description for tooltip / UI."""
        if self.is_brush:
            return f"Brush: {self.brush_name}"
        if self.is_position:
            p = self.position
            return f"Position: ({p.x}, {p.y}, {p.z})"
        return "(empty)"


# ---------------------  Manager  --------------------------------------------


class HotkeyManager:
    """Global manager for 10 brush / position hotkey slots.

    This mirrors the C++ ``g_hotkeys`` global and provides:

    * ``set_hotkey(index, hotkey)`` / ``get_hotkey(index)``
    * ``save()`` / ``load()`` persistence to JSON
    * ``enable()`` / ``disable()`` toggle (e.g. while renaming)
    """

    def __init__(self, config_dir: Path | None = None) -> None:
        self._slots: list[Hotkey] = [Hotkey() for _ in range(NUM_SLOTS)]
        self._enabled: bool = True
        self._config_dir = config_dir
        self._dirty: bool = False

    # -- public API --

    @property
    def enabled(self) -> bool:
        return self._enabled

    def enable(self) -> None:
        self._enabled = True

    def disable(self) -> None:
        self._enabled = False

    def get(self, index: int) -> Hotkey:
        """Return hotkey for *index* (0-9)."""
        if 0 <= index < NUM_SLOTS:
            return self._slots[index]
        return Hotkey()

    def set(self, index: int, hotkey: Hotkey) -> None:
        """Assign *hotkey* to slot *index* (0-9)."""
        if 0 <= index < NUM_SLOTS:
            self._slots[index] = hotkey
            self._dirty = True

    # Legacy-aligned names (preferred by UI layer)

    def get_hotkey(self, index: int) -> Hotkey:
        return self.get(int(index))

    def set_hotkey(self, index: int, hotkey: Hotkey) -> None:
        self.set(int(index), hotkey)

    def clear(self, index: int) -> None:
        """Clear slot *index*."""
        self.set(index, Hotkey())

    def clear_all(self) -> None:
        """Clear all slots."""
        for i in range(NUM_SLOTS):
            self._slots[i] = Hotkey()
        self._dirty = True

    def all_slots(self) -> list[tuple[int, Hotkey]]:
        """Return list of ``(index, hotkey)`` tuples."""
        return list(enumerate(self._slots))

    # -- persistence --

    def _file_path(self) -> Path | None:
        if self._config_dir is None:
            return None
        return self._config_dir / "hotkeys.json"

    def save(self) -> None:
        """Persist hotkeys to disk."""
        path = self._file_path()
        if path is None:
            return
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            data = [hk.to_dict() for hk in self._slots]
            path.write_text(json.dumps(data, indent=2), encoding="utf-8")
            self._dirty = False
            logger.info("Hotkeys saved to %s", path)
        except OSError:
            logger.exception("Failed to save hotkeys")

    def load(self) -> None:
        """Load hotkeys from disk."""
        path = self._file_path()
        if path is None or not path.exists():
            return
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
            for i, entry in enumerate(raw[:NUM_SLOTS]):
                self._slots[i] = Hotkey.from_dict(entry)
            self._dirty = False
            logger.info("Hotkeys loaded from %s", path)
        except (OSError, json.JSONDecodeError, KeyError):
            logger.exception("Failed to load hotkeys")

    @property
    def dirty(self) -> bool:
        return self._dirty
