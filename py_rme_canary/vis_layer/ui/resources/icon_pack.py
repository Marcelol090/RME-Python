from __future__ import annotations

from functools import lru_cache
from pathlib import Path

from PyQt6.QtGui import QIcon

ICON_DIR = Path(__file__).resolve().parent / "icons"

ICON_ALIASES: dict[str, str] = {
    "action_open_map": "action_open",
    "action_import": "action_open",
    "action_export": "action_save_as",
    "tool_brush": "tool_pencil",
    "tool_bucket": "tool_fill",
}


@lru_cache(maxsize=256)
def load_icon(name: str) -> QIcon:
    """Load an icon from the bundled icon pack."""
    icon_name = ICON_ALIASES.get(name, name)
    for extension in ("svg", "png", "ico"):
        path = ICON_DIR / f"{icon_name}.{extension}"
        if path.exists():
            return QIcon(str(path))
    return QIcon()


def icon_exists(name: str) -> bool:
    icon_name = ICON_ALIASES.get(name, name)
    return any((ICON_DIR / f"{icon_name}.{ext}").exists() for ext in ("svg", "png", "ico"))
