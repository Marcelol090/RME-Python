"""Keyboard shortcuts configuration and management.

This module provides a system for managing keyboard shortcuts in the editor.
Supports:
- Default shortcuts for common actions
- User-defined custom shortcuts (up to 10)
- Position hotkeys for camera/viewport positions
- Immutable configuration with builder pattern
"""
from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum, auto
from pathlib import Path
from typing import Final


class ShortcutAction(Enum):
    """Available shortcut actions."""

    # File operations
    NEW_MAP = auto()
    OPEN_MAP = auto()
    SAVE_MAP = auto()
    SAVE_AS = auto()
    CLOSE_MAP = auto()

    # Edit operations
    UNDO = auto()
    REDO = auto()
    CUT = auto()
    COPY = auto()
    PASTE = auto()
    DELETE = auto()
    SELECT_ALL = auto()

    # View operations
    ZOOM_IN = auto()
    ZOOM_OUT = auto()
    ZOOM_RESET = auto()
    TOGGLE_GRID = auto()
    TOGGLE_PREVIEW = auto()
    TOGGLE_LIGHT = auto()

    # Tools
    SELECT_TOOL = auto()
    DRAW_TOOL = auto()
    FILL_TOOL = auto()
    ERASE_TOOL = auto()
    SPAWN_TOOL = auto()
    HOUSE_TOOL = auto()

    # Custom user actions
    CUSTOM_1 = auto()
    CUSTOM_2 = auto()
    CUSTOM_3 = auto()
    CUSTOM_4 = auto()
    CUSTOM_5 = auto()
    CUSTOM_6 = auto()
    CUSTOM_7 = auto()
    CUSTOM_8 = auto()
    CUSTOM_9 = auto()
    CUSTOM_10 = auto()

    # Position hotkeys
    SAVE_POSITION_1 = auto()
    SAVE_POSITION_2 = auto()
    SAVE_POSITION_3 = auto()
    SAVE_POSITION_4 = auto()
    SAVE_POSITION_5 = auto()
    GOTO_POSITION_1 = auto()
    GOTO_POSITION_2 = auto()
    GOTO_POSITION_3 = auto()
    GOTO_POSITION_4 = auto()
    GOTO_POSITION_5 = auto()


# Default shortcuts mapping
DEFAULT_SHORTCUTS: Final[dict[ShortcutAction, str]] = {
    # File operations (standard)
    ShortcutAction.NEW_MAP: "Ctrl+N",
    ShortcutAction.OPEN_MAP: "Ctrl+O",
    ShortcutAction.SAVE_MAP: "Ctrl+S",
    ShortcutAction.SAVE_AS: "Ctrl+Shift+S",
    ShortcutAction.CLOSE_MAP: "Ctrl+W",
    # Edit operations (standard)
    ShortcutAction.UNDO: "Ctrl+Z",
    ShortcutAction.REDO: "Ctrl+Y",
    ShortcutAction.CUT: "Ctrl+X",
    ShortcutAction.COPY: "Ctrl+C",
    ShortcutAction.PASTE: "Ctrl+V",
    ShortcutAction.DELETE: "Delete",
    ShortcutAction.SELECT_ALL: "Ctrl+A",
    # View operations
    ShortcutAction.ZOOM_IN: "Ctrl++",
    ShortcutAction.ZOOM_OUT: "Ctrl+-",
    ShortcutAction.ZOOM_RESET: "Ctrl+0",
    ShortcutAction.TOGGLE_GRID: "G",
    ShortcutAction.TOGGLE_PREVIEW: "F5",
    ShortcutAction.TOGGLE_LIGHT: "L",
    # Tools
    ShortcutAction.SELECT_TOOL: "S",
    ShortcutAction.DRAW_TOOL: "D",
    ShortcutAction.FILL_TOOL: "F",
    ShortcutAction.ERASE_TOOL: "E",
    ShortcutAction.SPAWN_TOOL: "M",
    ShortcutAction.HOUSE_TOOL: "H",
    # Custom actions (unbound by default)
    ShortcutAction.CUSTOM_1: "",
    ShortcutAction.CUSTOM_2: "",
    ShortcutAction.CUSTOM_3: "",
    ShortcutAction.CUSTOM_4: "",
    ShortcutAction.CUSTOM_5: "",
    ShortcutAction.CUSTOM_6: "",
    ShortcutAction.CUSTOM_7: "",
    ShortcutAction.CUSTOM_8: "",
    ShortcutAction.CUSTOM_9: "",
    ShortcutAction.CUSTOM_10: "",
    # Position hotkeys
    ShortcutAction.SAVE_POSITION_1: "Ctrl+Shift+1",
    ShortcutAction.SAVE_POSITION_2: "Ctrl+Shift+2",
    ShortcutAction.SAVE_POSITION_3: "Ctrl+Shift+3",
    ShortcutAction.SAVE_POSITION_4: "Ctrl+Shift+4",
    ShortcutAction.SAVE_POSITION_5: "Ctrl+Shift+5",
    ShortcutAction.GOTO_POSITION_1: "Ctrl+1",
    ShortcutAction.GOTO_POSITION_2: "Ctrl+2",
    ShortcutAction.GOTO_POSITION_3: "Ctrl+3",
    ShortcutAction.GOTO_POSITION_4: "Ctrl+4",
    ShortcutAction.GOTO_POSITION_5: "Ctrl+5",
}


@dataclass(frozen=True, slots=True)
class ShortcutSettings:
    """Immutable keyboard shortcuts configuration.

    Attributes:
        shortcuts: Mapping of actions to keyboard shortcuts
        enabled: Whether shortcuts are enabled globally
        allow_custom: Whether custom shortcuts can be configured

    Example:
        >>> settings = ShortcutSettings.default()
        >>> settings = settings.with_shortcut(ShortcutAction.CUSTOM_1, "Ctrl+K")
        >>> shortcut = settings.get_shortcut(ShortcutAction.UNDO)
        >>> "Ctrl+Z"
    """

    shortcuts: dict[ShortcutAction, str] = field(default_factory=dict)
    enabled: bool = True
    allow_custom: bool = True

    @staticmethod
    def default() -> ShortcutSettings:
        """Create default settings with standard shortcuts.

        Returns:
            ShortcutSettings with default shortcuts loaded
        """
        return ShortcutSettings(shortcuts=DEFAULT_SHORTCUTS.copy())

    def get_shortcut(self, action: ShortcutAction) -> str:
        """Get shortcut for an action.

        Args:
            action: Action to get shortcut for

        Returns:
            Shortcut string (e.g., "Ctrl+S") or empty if unbound
        """
        return self.shortcuts.get(action, "")

    def with_shortcut(
        self,
        action: ShortcutAction,
        shortcut: str,
    ) -> ShortcutSettings:
        """Return new settings with updated shortcut.

        Args:
            action: Action to bind
            shortcut: Keyboard shortcut string (e.g., "Ctrl+K")

        Returns:
            New ShortcutSettings with updated binding

        Raises:
            ValueError: If custom shortcuts not allowed or invalid shortcut
        """
        # Validate custom shortcuts
        if not self.allow_custom and action.name.startswith("CUSTOM_"):
            msg = "Custom shortcuts are disabled"
            raise ValueError(msg)

        if not self._is_valid_shortcut(shortcut) and shortcut != "":
            msg = f"Invalid shortcut format: {shortcut}"
            raise ValueError(msg)

        # Check for conflicts
        if shortcut and self._has_conflict(action, shortcut):
            msg = f"Shortcut '{shortcut}' already bound to another action"
            raise ValueError(msg)

        new_shortcuts = self.shortcuts.copy()
        new_shortcuts[action] = shortcut
        return replace(self, shortcuts=new_shortcuts)

    def with_enabled(self, enabled: bool) -> ShortcutSettings:
        """Return new settings with enabled state.

        Args:
            enabled: Whether shortcuts should be enabled

        Returns:
            New ShortcutSettings with updated enabled state
        """
        return replace(self, enabled=enabled)

    def with_custom_allowed(self, allowed: bool) -> ShortcutSettings:
        """Return new settings with custom shortcuts allowed/disallowed.

        Args:
            allowed: Whether custom shortcuts should be allowed

        Returns:
            New ShortcutSettings with updated custom allowed state
        """
        return replace(self, allow_custom=allowed)

    def reset_to_defaults(self) -> ShortcutSettings:
        """Return new settings with all shortcuts reset to defaults.

        Returns:
            New ShortcutSettings with default shortcuts
        """
        return ShortcutSettings.default().with_enabled(self.enabled).with_custom_allowed(
            self.allow_custom,
        )

    def reset_action(self, action: ShortcutAction) -> ShortcutSettings:
        """Reset a single action to its default shortcut.

        Args:
            action: Action to reset

        Returns:
            New ShortcutSettings with action reset to default
        """
        default_shortcut = DEFAULT_SHORTCUTS.get(action, "")
        return self.with_shortcut(action, default_shortcut)

    def get_all_shortcuts(self) -> dict[ShortcutAction, str]:
        """Get all configured shortcuts.

        Returns:
            Dictionary mapping actions to shortcuts
        """
        return self.shortcuts.copy()

    def get_custom_shortcuts(self) -> dict[ShortcutAction, str]:
        """Get only custom user-defined shortcuts.

        Returns:
            Dictionary of custom shortcuts only
        """
        return {
            action: shortcut
            for action, shortcut in self.shortcuts.items()
            if action.name.startswith("CUSTOM_") and shortcut
        }

    def _is_valid_shortcut(self, shortcut: str) -> bool:
        """Validate shortcut format.

        Args:
            shortcut: Shortcut string to validate

        Returns:
            True if valid, False otherwise
        """
        if not shortcut:
            return True

        # Basic validation: should contain modifiers or single key
        valid_modifiers = {"Ctrl", "Alt", "Shift", "Meta"}
        parts = shortcut.split("+")

        # Must have at least one part
        if not parts:
            return False

        # Check modifiers are valid
        for part in parts[:-1]:
            if part not in valid_modifiers:
                return False

        # Last part should be non-empty (the actual key)
        return len(parts[-1]) > 0

    def _has_conflict(self, action: ShortcutAction, shortcut: str) -> bool:
        """Check if shortcut conflicts with existing bindings.

        Args:
            action: Action being bound
            shortcut: Shortcut to check

        Returns:
            True if conflict exists, False otherwise
        """
        if not shortcut:
            return False

        for existing_action, existing_shortcut in self.shortcuts.items():
            if existing_action != action and existing_shortcut == shortcut:
                return True

        return False

    def export_to_file(self, path: Path) -> None:
        """Export shortcuts configuration to file.

        Args:
            path: Path to save configuration
        """
        import json

        data = {
            "enabled": self.enabled,
            "allow_custom": self.allow_custom,
            "shortcuts": {action.name: shortcut for action, shortcut in self.shortcuts.items()},
        }

        with path.open("w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def import_from_file(path: Path) -> ShortcutSettings:
        """Import shortcuts configuration from file.

        Args:
            path: Path to load configuration from

        Returns:
            ShortcutSettings loaded from file
        """
        import json

        with path.open(encoding="utf-8") as f:
            data = json.load(f)

        shortcuts = {
            ShortcutAction[action_name]: shortcut
            for action_name, shortcut in data.get("shortcuts", {}).items()
        }

        return ShortcutSettings(
            shortcuts=shortcuts,
            enabled=data.get("enabled", True),
            allow_custom=data.get("allow_custom", True),
        )
