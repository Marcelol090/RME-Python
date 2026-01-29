"""Session management package.

This package contains modular components for the editor session:
- selection: Tile selection management (box selection, toggle, etc.)
- clipboard: Copy/cut/paste operations
- gestures: Mouse input gesture handling
- move: Selection movement operations
- editor: Main EditorSession orchestrator
"""

from .clipboard import ClipboardManager
from .editor import EditorSession
from .gestures import GestureHandler
from .move import MoveHandler
from .selection import SelectionManager, TileKey

__all__ = [
    "ClipboardManager",
    "EditorSession",
    "GestureHandler",
    "MoveHandler",
    "SelectionManager",
    "TileKey",
]
