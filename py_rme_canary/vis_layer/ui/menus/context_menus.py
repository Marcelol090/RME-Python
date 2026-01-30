"""Context Menu System.

Provides right-click context menus for:
- Canvas/tiles
- Items
- Palette brushes
- Houses/Spawns
"""
from __future__ import annotations

from typing import TYPE_CHECKING, Callable

from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QAction, QCursor
from PyQt6.QtWidgets import QMenu, QWidget

if TYPE_CHECKING:
    from py_rme_canary.core.data.tile import Tile
    from py_rme_canary.core.data.item import Item


class ContextMenuBuilder:
    """Builder for creating context menus.

    Usage:
        menu = (ContextMenuBuilder(parent)
            .add_action("Copy", on_copy, "Ctrl+C")
            .add_separator()
            .add_submenu("Selection")
                .add_action("Select All", on_select_all)
                .end_submenu()
            .build())
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        self._parent = parent
        self._menu = QMenu(parent)
        self._current_menu = self._menu
        self._menu_stack: list[QMenu] = []

        # Apply styling
        self._menu.setStyleSheet("""
            QMenu {
                background: #2A2A3E;
                border: 1px solid #363650;
                border-radius: 8px;
                padding: 6px;
                color: #E5E5E7;
            }

            QMenu::item {
                padding: 8px 24px 8px 12px;
                border-radius: 4px;
                margin: 2px;
            }

            QMenu::item:selected {
                background: #8B5CF6;
            }

            QMenu::item:disabled {
                color: #52525B;
            }

            QMenu::separator {
                background: #363650;
                height: 1px;
                margin: 4px 8px;
            }

            QMenu::icon {
                margin-left: 8px;
            }
        """)

    def add_action(
        self,
        text: str,
        callback: Callable[[], None] | None = None,
        shortcut: str | None = None,
        icon: str | None = None,
        enabled: bool = True,
        checkable: bool = False,
        checked: bool = False
    ) -> "ContextMenuBuilder":
        """Add an action to the menu."""
        display = f"{icon} {text}" if icon else text
        action = QAction(display, self._current_menu)

        if callback:
            action.triggered.connect(callback)
        if shortcut:
            action.setShortcut(shortcut)

        action.setEnabled(enabled)
        action.setCheckable(checkable)
        action.setChecked(checked)

        self._current_menu.addAction(action)
        return self

    def add_separator(self) -> "ContextMenuBuilder":
        """Add a separator line."""
        self._current_menu.addSeparator()
        return self

    def add_submenu(self, title: str, icon: str | None = None) -> "ContextMenuBuilder":
        """Start a submenu."""
        display = f"{icon} {title}" if icon else title
        submenu = self._current_menu.addMenu(display)
        submenu.setStyleSheet(self._menu.styleSheet())

        self._menu_stack.append(self._current_menu)
        self._current_menu = submenu
        return self

    def end_submenu(self) -> "ContextMenuBuilder":
        """End current submenu."""
        if self._menu_stack:
            self._current_menu = self._menu_stack.pop()
        return self

    def build(self) -> QMenu:
        """Build and return the menu."""
        return self._menu

    def exec_at_cursor(self) -> QAction | None:
        """Execute menu at cursor position."""
        return self._menu.exec(QCursor.pos())


class TileContextMenu:
    """Context menu for tile operations."""

    def __init__(self, parent: QWidget | None = None) -> None:
        self._parent = parent
        self._tile: "Tile | None" = None
        self._callbacks: dict[str, Callable] = {}

    def set_callbacks(self, callbacks: dict[str, Callable]) -> None:
        """Set action callbacks.

        Expected keys:
        - copy, cut, paste, delete
        - select_all, deselect
        - properties, goto
        - set_waypoint, set_spawn
        - set_house, clear_house
        """
        self._callbacks = callbacks

    def show_for_tile(self, tile: "Tile | None", has_selection: bool = False) -> None:
        """Show context menu for a tile."""
        self._tile = tile

        cb = self._callbacks.get

        builder = ContextMenuBuilder(self._parent)

        # Edit actions
        builder.add_action("📋 Copy", cb('copy'), "Ctrl+C")
        builder.add_action("✂️ Cut", cb('cut'), "Ctrl+X")
        builder.add_action("📎 Paste", cb('paste'), "Ctrl+V",
                          enabled=bool(cb('can_paste') and cb('can_paste')()))
        builder.add_action("🗑️ Delete", cb('delete'), "Del",
                          enabled=has_selection or tile is not None)

        builder.add_separator()

        # Selection
        builder.add_submenu("Selection", "🔲")
        builder.add_action("Select All", cb('select_all'), "Ctrl+A")
        builder.add_action("Deselect", cb('deselect'), "Escape")
        builder.end_submenu()

        builder.add_separator()

        # Tile-specific
        if tile:
            # Properties
            builder.add_action("📝 Properties...", cb('properties'))

            builder.add_separator()

            # Waypoint
            builder.add_submenu("Waypoint", "📍")
            builder.add_action("Set Waypoint Here...", cb('set_waypoint'))
            builder.add_action("Delete Waypoint", cb('delete_waypoint'),
                              enabled=bool(cb('has_waypoint') and cb('has_waypoint')()))
            builder.end_submenu()

            # Spawn
            builder.add_submenu("Spawn", "👹")
            builder.add_action("Place Monster Spawn...", cb('set_monster_spawn'))
            builder.add_action("Place NPC Spawn...", cb('set_npc_spawn'))
            builder.add_action("Delete Spawn", cb('delete_spawn'))
            builder.end_submenu()

            # House
            if tile.house_id:
                builder.add_submenu("House", "🏠")
                builder.add_action(f"Edit House #{tile.house_id}...", cb('edit_house'))
                builder.add_action("Clear House ID", cb('clear_house'))
                builder.add_action("Set Entry Here", cb('set_house_entry'))
                builder.end_submenu()
            else:
                builder.add_action("🏠 Assign to House...", cb('assign_house'))

        builder.add_separator()

        # Navigation
        if tile:
            pos = f"({tile.x}, {tile.y}, {tile.z})"
            builder.add_action(f"📍 Copy Position {pos}", cb('copy_position'))

        builder.add_action("🔍 Go To Position...", cb('goto'))

        builder.exec_at_cursor()


class ItemContextMenu:
    """Context menu for item operations."""

    def __init__(self, parent: QWidget | None = None) -> None:
        self._parent = parent
        self._item: "Item | None" = None
        self._callbacks: dict[str, Callable] = {}

    def set_callbacks(self, callbacks: dict[str, Callable]) -> None:
        """Set action callbacks."""
        self._callbacks = callbacks

    def show_for_item(self, item: "Item | None", tile: "Tile | None" = None) -> None:
        """Show context menu for an item."""
        self._item = item

        if not item:
            return

        cb = self._callbacks.get
        def _enabled(key: str) -> bool:
            return bool(cb(key))

        builder = ContextMenuBuilder(self._parent)

        # Item info
        builder.add_action(f"📦 Item #{item.id}", enabled=False)
        builder.add_separator()

        # Actions
        builder.add_action("📝 Properties...", cb('properties'), enabled=_enabled("properties"))
        builder.add_action("📋 Copy", cb('copy'), enabled=_enabled("copy"))
        builder.add_action("🗑️ Delete", cb('delete'), enabled=_enabled("delete"))

        builder.add_separator()

        # Item-specific
        if hasattr(item, 'destination') and item.destination:
            builder.add_action("🚀 Go To Destination", cb('goto_destination'), enabled=_enabled("goto_destination"))

        if hasattr(item, 'text') and item.text:
            builder.add_action("📝 Edit Text...", cb('edit_text'), enabled=_enabled("edit_text"))

        builder.add_separator()

        # Quick replace helpers
        builder.add_action("🎯 Set as Find Item", cb('set_find'), enabled=_enabled("set_find"))
        builder.add_action("🔁 Set as Replace Item", cb('set_replace'), enabled=_enabled("set_replace"))
        builder.add_separator()

        # Selection
        builder.add_action("🔍 Find All of This Item", cb('find_all'), enabled=_enabled("find_all"))
        builder.add_action("🔄 Replace All...", cb('replace_all'), enabled=_enabled("replace_all"))

        builder.exec_at_cursor()


class BrushContextMenu:
    """Context menu for palette brushes."""

    def __init__(self, parent: QWidget | None = None) -> None:
        self._parent = parent
        self._callbacks: dict[str, Callable] = {}

    def set_callbacks(self, callbacks: dict[str, Callable]) -> None:
        """Set action callbacks."""
        self._callbacks = callbacks

    def show_for_brush(self, brush_id: int, brush_name: str) -> None:
        """Show context menu for a brush."""
        cb = self._callbacks.get

        builder = ContextMenuBuilder(self._parent)

        builder.add_action(f"🖌️ {brush_name}", enabled=False)
        builder.add_separator()

        builder.add_action("⭐ Add to Favorites", cb('add_favorite'))
        builder.add_action("📌 Pin to Top", cb('pin'))

        builder.add_separator()

        builder.add_action("🔍 Find on Map", cb('find_on_map'))
        builder.add_action("📝 Brush Info...", cb('brush_info'))

        builder.exec_at_cursor()


# Convenience function for quick menu creation
def show_quick_menu(
    parent: QWidget,
    actions: list[tuple[str, Callable | None, str | None]]
) -> None:
    """Show a quick context menu.

    Args:
        parent: Parent widget
        actions: List of (text, callback, shortcut) tuples.
                Use ("-", None, None) for separator.
    """
    builder = ContextMenuBuilder(parent)

    for text, callback, shortcut in actions:
        if text == "-":
            builder.add_separator()
        else:
            builder.add_action(text, callback, shortcut)

    builder.exec_at_cursor()
