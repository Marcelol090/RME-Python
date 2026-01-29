"""Keyboard Shortcuts System.

Centralized management of keyboard shortcuts with:
- Default shortcuts
- Custom shortcuts override
- Shortcut conflict detection
- Help display
"""
from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import TYPE_CHECKING, Callable, Any

if TYPE_CHECKING:
    from PyQt6.QtGui import QKeySequence
    from PyQt6.QtWidgets import QAction


class ShortcutCategory(str, Enum):
    """Categories for grouping shortcuts."""
    FILE = "File"
    EDIT = "Edit"
    VIEW = "View"
    TOOLS = "Tools"
    BRUSH = "Brush"
    NAVIGATION = "Navigation"
    SELECTION = "Selection"
    WINDOW = "Window"


@dataclass(slots=True)
class ShortcutDefinition:
    """Definition of a keyboard shortcut."""
    action_id: str
    default_key: str
    description: str
    category: ShortcutCategory
    custom_key: str | None = None
    
    @property
    def current_key(self) -> str:
        """Get current active shortcut key."""
        return self.custom_key or self.default_key


# Default shortcuts matching legacy RME
DEFAULT_SHORTCUTS: dict[str, ShortcutDefinition] = {
    # File operations
    "new_map": ShortcutDefinition(
        "new_map", "Ctrl+N", "Create new map",
        ShortcutCategory.FILE
    ),
    "open_map": ShortcutDefinition(
        "open_map", "Ctrl+O", "Open map file",
        ShortcutCategory.FILE
    ),
    "save_map": ShortcutDefinition(
        "save_map", "Ctrl+S", "Save current map",
        ShortcutCategory.FILE
    ),
    "save_as": ShortcutDefinition(
        "save_as", "Ctrl+Shift+S", "Save map as...",
        ShortcutCategory.FILE
    ),
    
    # Edit operations
    "undo": ShortcutDefinition(
        "undo", "Ctrl+Z", "Undo last action",
        ShortcutCategory.EDIT
    ),
    "redo": ShortcutDefinition(
        "redo", "Ctrl+Y", "Redo last action",
        ShortcutCategory.EDIT
    ),
    "copy": ShortcutDefinition(
        "copy", "Ctrl+C", "Copy selection",
        ShortcutCategory.EDIT
    ),
    "cut": ShortcutDefinition(
        "cut", "Ctrl+X", "Cut selection",
        ShortcutCategory.EDIT
    ),
    "paste": ShortcutDefinition(
        "paste", "Ctrl+V", "Paste clipboard",
        ShortcutCategory.EDIT
    ),
    "delete": ShortcutDefinition(
        "delete", "Delete", "Delete selection",
        ShortcutCategory.EDIT
    ),
    "find": ShortcutDefinition(
        "find", "Ctrl+F", "Find item...",
        ShortcutCategory.EDIT
    ),
    "replace": ShortcutDefinition(
        "replace", "Ctrl+Shift+F", "Replace items...",
        ShortcutCategory.EDIT
    ),
    
    # View operations
    "zoom_in": ShortcutDefinition(
        "zoom_in", "Ctrl++", "Zoom in",
        ShortcutCategory.VIEW
    ),
    "zoom_out": ShortcutDefinition(
        "zoom_out", "Ctrl+-", "Zoom out",
        ShortcutCategory.VIEW
    ),
    "zoom_reset": ShortcutDefinition(
        "zoom_reset", "Ctrl+0", "Reset zoom",
        ShortcutCategory.VIEW
    ),
    "fullscreen": ShortcutDefinition(
        "fullscreen", "F11", "Toggle fullscreen",
        ShortcutCategory.VIEW
    ),
    "show_grid": ShortcutDefinition(
        "show_grid", "G", "Toggle grid",
        ShortcutCategory.VIEW
    ),
    
    # Brush operations (legacy RME style)
    "brush_size_1": ShortcutDefinition(
        "brush_size_1", "1", "Brush size 1",
        ShortcutCategory.BRUSH
    ),
    "brush_size_2": ShortcutDefinition(
        "brush_size_2", "2", "Brush size 2",
        ShortcutCategory.BRUSH
    ),
    "brush_size_3": ShortcutDefinition(
        "brush_size_3", "3", "Brush size 3",
        ShortcutCategory.BRUSH
    ),
    "brush_size_4": ShortcutDefinition(
        "brush_size_4", "4", "Brush size 4",
        ShortcutCategory.BRUSH
    ),
    "brush_size_5": ShortcutDefinition(
        "brush_size_5", "5", "Brush size 5",
        ShortcutCategory.BRUSH
    ),
    "brush_increase": ShortcutDefinition(
        "brush_increase", "]", "Increase brush size",
        ShortcutCategory.BRUSH
    ),
    "brush_decrease": ShortcutDefinition(
        "brush_decrease", "[", "Decrease brush size",
        ShortcutCategory.BRUSH
    ),
    "toggle_automagic": ShortcutDefinition(
        "toggle_automagic", "A", "Toggle automagic",
        ShortcutCategory.BRUSH
    ),
    "toggle_shape": ShortcutDefinition(
        "toggle_shape", "Q", "Toggle brush shape (square/circle)",
        ShortcutCategory.BRUSH
    ),
    
    # Navigation
    "goto_position": ShortcutDefinition(
        "goto_position", "Ctrl+G", "Go to position...",
        ShortcutCategory.NAVIGATION
    ),
    "floor_up": ShortcutDefinition(
        "floor_up", "Page_Up", "Go up one floor",
        ShortcutCategory.NAVIGATION
    ),
    "floor_down": ShortcutDefinition(
        "floor_down", "Page_Down", "Go down one floor",
        ShortcutCategory.NAVIGATION
    ),
    "center_view": ShortcutDefinition(
        "center_view", "Home", "Center view on selection",
        ShortcutCategory.NAVIGATION
    ),
    
    # Selection
    "select_all": ShortcutDefinition(
        "select_all", "Ctrl+A", "Select all",
        ShortcutCategory.SELECTION
    ),
    "deselect": ShortcutDefinition(
        "deselect", "Escape", "Deselect",
        ShortcutCategory.SELECTION
    ),
    "selection_mode": ShortcutDefinition(
        "selection_mode", "Ctrl+E", "Toggle selection mode",
        ShortcutCategory.SELECTION
    ),
    
    # Palette shortcuts
    "palette_terrain": ShortcutDefinition(
        "palette_terrain", "T", "Terrain palette",
        ShortcutCategory.WINDOW
    ),
    "palette_doodad": ShortcutDefinition(
        "palette_doodad", "D", "Doodad palette",
        ShortcutCategory.WINDOW
    ),
    "palette_item": ShortcutDefinition(
        "palette_item", "I", "Item palette",
        ShortcutCategory.WINDOW
    ),
    "palette_creature": ShortcutDefinition(
        "palette_creature", "C", "Creature palette",
        ShortcutCategory.WINDOW
    ),
    "palette_house": ShortcutDefinition(
        "palette_house", "H", "House palette",
        ShortcutCategory.WINDOW
    ),
    "palette_raw": ShortcutDefinition(
        "palette_raw", "R", "RAW palette",
        ShortcutCategory.WINDOW
    ),
}


class ShortcutManager:
    """Manages keyboard shortcuts for the application.
    
    Usage:
        manager = ShortcutManager.instance()
        
        # Apply shortcuts to actions
        manager.apply_to_action("save_map", save_action)
        
        # Get all shortcuts for help display
        shortcuts = manager.get_all_by_category()
    """
    
    _instance: "ShortcutManager | None" = None
    
    def __init__(self) -> None:
        self._shortcuts = dict(DEFAULT_SHORTCUTS)
        self._custom_overrides: dict[str, str] = {}
        
    @classmethod
    def instance(cls) -> "ShortcutManager":
        """Get singleton instance."""
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
        
    def get_shortcut(self, action_id: str) -> ShortcutDefinition | None:
        """Get shortcut definition by action ID."""
        return self._shortcuts.get(action_id)
        
    def get_key(self, action_id: str) -> str:
        """Get current key for an action."""
        shortcut = self._shortcuts.get(action_id)
        if shortcut:
            return self._custom_overrides.get(action_id) or shortcut.default_key
        return ""
        
    def set_custom_key(self, action_id: str, key: str) -> bool:
        """Set a custom key for an action.
        
        Returns False if there's a conflict.
        """
        # Check for conflicts
        conflict = self.find_conflict(key, exclude=action_id)
        if conflict:
            return False
            
        self._custom_overrides[action_id] = key
        
        shortcut = self._shortcuts.get(action_id)
        if shortcut:
            shortcut.custom_key = key
            
        return True
        
    def reset_to_default(self, action_id: str) -> None:
        """Reset an action to its default shortcut."""
        self._custom_overrides.pop(action_id, None)
        
        shortcut = self._shortcuts.get(action_id)
        if shortcut:
            shortcut.custom_key = None
            
    def reset_all(self) -> None:
        """Reset all shortcuts to defaults."""
        self._custom_overrides.clear()
        for shortcut in self._shortcuts.values():
            shortcut.custom_key = None
            
    def find_conflict(
        self,
        key: str,
        exclude: str | None = None
    ) -> str | None:
        """Find action that conflicts with given key.
        
        Returns action_id of conflicting action, or None.
        """
        key_lower = key.lower().replace(" ", "")
        
        for action_id, shortcut in self._shortcuts.items():
            if action_id == exclude:
                continue
                
            current = shortcut.current_key.lower().replace(" ", "")
            if current == key_lower:
                return action_id
                
        return None
        
    def apply_to_action(
        self,
        action_id: str,
        action: "QAction"
    ) -> bool:
        """Apply shortcut to a QAction.
        
        Returns True if shortcut was applied.
        """
        try:
            from PyQt6.QtGui import QKeySequence
            
            key = self.get_key(action_id)
            if key:
                action.setShortcut(QKeySequence(key))
                
                # Also set tooltip with shortcut hint
                shortcut = self.get_shortcut(action_id)
                if shortcut:
                    current_tip = action.toolTip() or shortcut.description
                    action.setToolTip(f"{current_tip} ({key})")
                    
                return True
                
        except Exception:
            pass
            
        return False
        
    def get_all_by_category(self) -> dict[ShortcutCategory, list[ShortcutDefinition]]:
        """Get all shortcuts grouped by category."""
        result: dict[ShortcutCategory, list[ShortcutDefinition]] = {}
        
        for shortcut in self._shortcuts.values():
            if shortcut.category not in result:
                result[shortcut.category] = []
            result[shortcut.category].append(shortcut)
            
        return result
        
    def export_to_dict(self) -> dict[str, str]:
        """Export custom shortcuts to dict for saving."""
        return dict(self._custom_overrides)
        
    def import_from_dict(self, data: dict[str, str]) -> None:
        """Import custom shortcuts from dict."""
        for action_id, key in data.items():
            if action_id in self._shortcuts:
                self.set_custom_key(action_id, key)


def generate_shortcuts_help() -> str:
    """Generate markdown-formatted shortcuts help text."""
    manager = ShortcutManager.instance()
    by_category = manager.get_all_by_category()
    
    lines = ["# Keyboard Shortcuts\n"]
    
    for category in ShortcutCategory:
        shortcuts = by_category.get(category, [])
        if not shortcuts:
            continue
            
        lines.append(f"\n## {category.value}\n")
        lines.append("| Shortcut | Action |")
        lines.append("|----------|--------|")
        
        for shortcut in sorted(shortcuts, key=lambda s: s.current_key):
            lines.append(f"| `{shortcut.current_key}` | {shortcut.description} |")
            
    return "\n".join(lines)
