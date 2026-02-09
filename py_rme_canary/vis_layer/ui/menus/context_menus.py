"""Context Menu System.

Provides right-click context menus for:
- Canvas/tiles
- Items
- Palette brushes
- Houses/Spawns
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING, List, Tuple

from PyQt6.QtWidgets import QWidget

from py_rme_canary.vis_layer.ui.menus.menu_builder import ContextMenuBuilder

if TYPE_CHECKING:
    from py_rme_canary.core.data.item import Item
    from py_rme_canary.core.data.tile import Tile


class TileContextMenu:
    """Context menu for tile operations."""

    def __init__(self, parent: QWidget | None = None) -> None:
        self._parent = parent
        self._tile: Tile | None = None
        self._callbacks: dict[str, Callable] = {}
        self._extra_actions: List[Tuple[str, Callable, str]] = []

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

    def add_action(self, text: str, callback: Callable, shortcut: str = "") -> None:
        """Add a custom action to the menu."""
        self._extra_actions.append((text, callback, shortcut))

    def show_for_tile(self, tile: Tile | None, has_selection: bool = False) -> None:
        """Show context menu for a tile."""
        self._tile = tile

        cb = self._callbacks.get

        builder = ContextMenuBuilder(self._parent)

        # Edit actions
        builder.add_action("Copy", cb("copy"), "Ctrl+C")
        builder.add_action("Cut", cb("cut"), "Ctrl+X")
        builder.add_action("Paste", cb("paste"), "Ctrl+V", enabled=bool(cb("can_paste") and cb("can_paste")()))
        builder.add_action("Delete", cb("delete"), "Del", enabled=has_selection or tile is not None)

        builder.add_separator()

        # Selection
        builder.add_submenu("Selection")
        builder.add_action("Select All", cb("select_all"), "Ctrl+A")
        builder.add_action("Deselect", cb("deselect"), "Escape")
        builder.end_submenu()

        builder.add_separator()

        # Tile-specific
        if tile:
            # Properties
            builder.add_action("Properties...", cb("properties"))

            # Browse Tile (inspect item stack)
            has_items = tile.ground is not None or (tile.items and len(tile.items) > 0)
            builder.add_action("Browse Tile...", cb("browse_tile"), enabled=has_items)

            builder.add_separator()

            # Waypoint
            builder.add_submenu("Waypoint")
            builder.add_action("Set Waypoint Here...", cb("set_waypoint"))
            builder.add_action(
                "Delete Waypoint", cb("delete_waypoint"), enabled=bool(cb("has_waypoint") and cb("has_waypoint")())
            )
            builder.end_submenu()

            # Spawn
            builder.add_submenu("Spawn")
            builder.add_action("Place Monster Spawn...", cb("set_monster_spawn"))
            builder.add_action("Place NPC Spawn...", cb("set_npc_spawn"))
            builder.add_action("Delete Spawn", cb("delete_spawn"))
            builder.end_submenu()

            # House
            if tile.house_id:
                builder.add_submenu("House")
                builder.add_action(f"Edit House #{tile.house_id}...", cb("edit_house"))
                builder.add_action("Clear House ID", cb("clear_house"))
                builder.add_action("Set Entry Here", cb("set_house_entry"))
                builder.end_submenu()
            else:
                builder.add_action("Assign to House...", cb("assign_house"))

        # Extra actions injected by tools
        if self._extra_actions:
            builder.add_separator()
            for text, callback, shortcut in self._extra_actions:
                builder.add_action(text, callback, shortcut)

        builder.add_separator()

        # Navigation
        if tile:
            pos = f"({tile.x}, {tile.y}, {tile.z})"
            builder.add_action(f"Copy Position {pos}", cb("copy_position"))

        builder.add_action("Go To Position...", cb("goto"))

        builder.exec_at_cursor()


class ItemContextMenu:
    """Context menu for item operations."""

    def __init__(self, parent: QWidget | None = None) -> None:
        self._parent = parent
        self._item: Item | None = None
        self._callbacks: dict[str, Callable] = {}

    def set_callbacks(self, callbacks: dict[str, Callable]) -> None:
        """Set action callbacks."""
        self._callbacks = callbacks

    def show_for_item(self, item: Item | None, tile: Tile | None = None) -> None:
        """Show context menu for an item with smart actions."""
        self._item = item

        if not item:
            return

        cb = self._callbacks.get

        def _enabled(key: str) -> bool:
            return bool(cb(key))

        builder = ContextMenuBuilder(self._parent)

        # Import detector for smart actions
        from py_rme_canary.logic_layer.item_type_detector import ItemTypeDetector

        # Detect item category
        category = ItemTypeDetector.get_category(item)

        # Get item name from AssetManager
        from py_rme_canary.logic_layer.asset_manager import AssetManager

        asset_mgr = AssetManager.instance()
        item_name = asset_mgr.get_item_name(item.id)
        item_meta = asset_mgr.get_item_metadata(item.id)
        client_id = getattr(item, "client_id", None)
        if client_id is None and item_meta is not None:
            client_id = item_meta.client_id
        if client_id is None:
            mapper = getattr(asset_mgr, "_id_mapper", None)
            if mapper is not None and hasattr(mapper, "get_client_id"):
                client_id = mapper.get_client_id(int(item.id))
        if client_id is None:
            client_id = int(item.id)

        # Item info header with name
        header_text = f"{item_name} (#{item.id})" if item_name != f"Item #{item.id}" else f"Item #{item.id}"
        builder.add_action(header_text, enabled=False)
        builder.add_separator()

        # Smart Brush Selection
        if ItemTypeDetector.can_select_brush(category):
            brush_name = ItemTypeDetector.get_brush_name(category)
            builder.add_action(f"Select {brush_name}", cb("select_brush"), enabled=_enabled("select_brush"))
            builder.add_separator()

        # Item-Specific Actions
        has_specific_actions = False

        # Door: Toggle Open/Close
        if ItemTypeDetector.is_door(item):
            is_open = ItemTypeDetector.is_door_open(item)
            action_text = "Close Door" if is_open else "Open Door"
            builder.add_action(action_text, cb("toggle_door"), enabled=_enabled("toggle_door"))
            has_specific_actions = True

        # Rotatable: Rotate Item
        if ItemTypeDetector.is_rotatable(item):
            builder.add_action("Rotate Item", cb("rotate_item"), enabled=_enabled("rotate_item"))
            has_specific_actions = True

        # Teleport: Go To Destination
        if ItemTypeDetector.is_teleport(item):
            dest = ItemTypeDetector.get_teleport_destination(item)
            if dest:
                builder.add_action(
                    f"Go To Destination ({dest[0]}, {dest[1]}, {dest[2]})",
                    cb("goto_teleport"),
                    enabled=_enabled("goto_teleport"),
                )
            else:
                builder.add_action("Set Teleport Destination...", cb("set_teleport_dest"))
            has_specific_actions = True

        if has_specific_actions:
            builder.add_separator()

        # Standard Actions
        builder.add_action("Properties...", cb("properties"), enabled=_enabled("properties"))
        builder.add_action("Browse Tile...", cb("browse_tile"), enabled=_enabled("browse_tile"))
        builder.add_separator()

        # Copy Data Actions
        builder.add_submenu("Copy Data")
        builder.add_action(f"Server ID ({item.id})", cb("copy_server_id"))
        builder.add_action(f"Client ID ({int(client_id)})", cb("copy_client_id"), enabled=_enabled("copy_client_id"))
        builder.add_action("Item Name", cb("copy_item_name"))
        if tile:
            builder.add_action(f"Position ({tile.x}, {tile.y}, {tile.z})", cb("copy_position"))
        builder.end_submenu()

        builder.add_separator()

        # Edit Actions
        builder.add_action("Copy", cb("copy"), enabled=_enabled("copy"))
        builder.add_action("Delete", cb("delete"), enabled=_enabled("delete"))

        # Text editing
        if hasattr(item, "text") and item.text:
            builder.add_separator()
            builder.add_action("Edit Text...", cb("edit_text"), enabled=_enabled("edit_text"))

        builder.add_separator()

        # Find/Replace helpers
        if _enabled("set_find"):
            builder.add_action("Set as Find Item", cb("set_find"), enabled=True)
        if _enabled("set_replace"):
            builder.add_action("Set as Replace Item", cb("set_replace"), enabled=True)
        if _enabled("set_find") or _enabled("set_replace"):
            builder.add_separator()

        builder.add_action("Find All of This Item", cb("find_all"), enabled=_enabled("find_all"))
        builder.add_action("Replace All...", cb("replace_all"), enabled=_enabled("replace_all"))

        builder.exec_at_cursor()


class BrushContextMenu:
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

        builder.add_action(brush_name, enabled=False)
        builder.add_separator()

        builder.add_action("Add to Favorites", cb("add_favorite"))
        builder.add_action("Pin to Top", cb("pin"))

        builder.add_separator()

        builder.add_action("Find on Map", cb("find_on_map"))
        builder.add_action("Brush Info...", cb("brush_info"))

        builder.exec_at_cursor()


# Convenience function for quick menu creation
def show_quick_menu(parent: QWidget, actions: list[tuple[str, Callable | None, str | None]]) -> None:
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
