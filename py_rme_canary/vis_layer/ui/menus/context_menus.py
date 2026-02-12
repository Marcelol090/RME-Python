"""Context Menu System.

Provides right-click context menus for:
- Canvas/tiles
- Items
- Palette brushes
- Houses/Spawns
"""

from __future__ import annotations

from collections.abc import Callable
from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QWidget

from py_rme_canary.vis_layer.ui.menus.menu_builder import ContextMenuBuilder

if TYPE_CHECKING:
    from py_rme_canary.core.data.item import Item
    from py_rme_canary.core.data.tile import Tile


_ITEM_SELECT_ACTIONS: tuple[tuple[str, str], ...] = (
    ("select_creature", "Select Creature"),
    ("select_spawn", "Select Spawn"),
    ("select_raw", "Select RAW"),
    ("move_to_tileset", "Move To Tileset..."),
    ("select_wall", "Select Wallbrush"),
    ("select_carpet", "Select Carpetbrush"),
    ("select_table", "Select Tablebrush"),
    ("select_doodad", "Select Doodadbrush"),
    ("select_door", "Select Doorbrush"),
    ("select_ground", "Select Groundbrush"),
    ("select_collection", "Select Collection"),
    ("select_house", "Select House"),
)


class TileContextMenu:
    """Context menu for tile operations."""

    def __init__(self, parent: QWidget | None = None) -> None:
        self._parent = parent
        self._tile: Tile | None = None
        self._callbacks: dict[str, Callable] = {}
        self._extra_actions: list[tuple[str, Callable, str]] = []

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

            # Legacy parity label uses "Browse Field"
            has_items = tile.ground is not None or (tile.items and len(tile.items) > 0)
            builder.add_action("Browse Field", cb("browse_tile"), enabled=bool(has_selection or has_items))

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

    def show_for_item(
        self,
        item: Item | None,
        tile: Tile | None = None,
        *,
        has_selection: bool = False,
        position: tuple[int, int, int] | None = None,
    ) -> None:
        """Show unified legacy-like context menu for tile/item."""
        self._item = item

        cb = self._callbacks.get
        ctx_pos = (
            (int(position[0]), int(position[1]), int(position[2]))
            if position is not None
            else ((int(tile.x), int(tile.y), int(tile.z)) if tile is not None else None)
        )

        def _state(key: str, default: bool = False) -> bool:
            fn = cb(key)
            if fn is None:
                return bool(default)
            try:
                return bool(fn())
            except Exception:
                return bool(default)

        def _action_enabled(key: str, default: bool = True) -> bool:
            if cb(key) is None:
                return False
            gate = cb(f"can_{key}")
            if gate is None:
                return bool(default)
            try:
                return bool(gate())
            except Exception:
                return bool(default)

        builder = ContextMenuBuilder(self._parent)

        # Legacy top-level selection/edit actions
        has_sel = bool(has_selection or _state("selection_has_selection"))
        can_paste = bool(_state("selection_can_paste"))
        builder.add_action("Cut", cb("selection_cut"), "Ctrl+X", enabled=has_sel and _action_enabled("selection_cut"))
        builder.add_action(
            "Copy",
            cb("selection_copy"),
            "Ctrl+C",
            enabled=has_sel and _action_enabled("selection_copy"),
        )
        if ctx_pos is not None:
            builder.add_action(
                f"Copy Position ({ctx_pos[0]}, {ctx_pos[1]}, {ctx_pos[2]})",
                cb("copy_position"),
                enabled=has_sel and _action_enabled("copy_position"),
            )
        else:
            builder.add_action("Copy Position", cb("copy_position"), enabled=False)
        builder.add_action(
            "Paste",
            cb("selection_paste"),
            "Ctrl+V",
            enabled=can_paste and _action_enabled("selection_paste"),
        )
        builder.add_action(
            "Delete",
            cb("selection_delete"),
            "Del",
            enabled=has_sel and _action_enabled("selection_delete"),
        )

        if has_sel and _action_enabled("selection_replace_tiles"):
            builder.add_action("Replace tiles...", cb("selection_replace_tiles"), enabled=True)

        builder.add_separator()

        if item is None:
            header = f"Tile ({ctx_pos[0]}, {ctx_pos[1]}, {ctx_pos[2]})" if ctx_pos is not None else "Tile"
            builder.add_action(header, enabled=False)
            if _action_enabled("select_creature"):
                builder.add_action("Select Creature", cb("select_creature"), enabled=True)
            if _action_enabled("select_spawn"):
                builder.add_action("Select Spawn", cb("select_spawn"), enabled=True)
            if _action_enabled("select_raw"):
                builder.add_action("Select RAW", cb("select_raw"), enabled=True)
            if _action_enabled("select_wall"):
                builder.add_action("Select Wallbrush", cb("select_wall"), enabled=True)
            if _action_enabled("select_ground"):
                builder.add_action("Select Groundbrush", cb("select_ground"), enabled=True)
            if _action_enabled("select_collection"):
                builder.add_action("Select Collection", cb("select_collection"), enabled=True)
            if _action_enabled("select_house"):
                builder.add_action("Select House", cb("select_house"), enabled=True)
            if tile is not None:
                has_items = bool(tile.ground is not None or (tile.items and len(tile.items) > 0))
                builder.add_separator()
                builder.add_action("Properties...", cb("properties"), enabled=_action_enabled("properties"))
                builder.add_action(
                    "Browse Field",
                    cb("browse_tile"),
                    enabled=(has_sel or has_items) and _action_enabled("browse_tile"),
                )
            builder.exec_at_cursor()
            return

        # Import detector for smart actions
        from py_rme_canary.logic_layer.item_type_detector import ItemTypeDetector

        # Detect item category
        category = ItemTypeDetector.get_category(item)

        # Get item name/metadata from AssetManager when available.
        item_name = f"Item #{item.id}"
        item_meta = None
        asset_mgr = None
        try:
            from py_rme_canary.logic_layer.asset_manager import AssetManager

            asset_mgr = AssetManager.instance()
            item_name = asset_mgr.get_item_name(item.id)
            item_meta = asset_mgr.get_item_metadata(item.id)
        except Exception:
            # Keep context menu functional in constrained runtimes.
            pass
        client_id = getattr(item, "client_id", None)
        if client_id is None and item_meta is not None:
            client_id = item_meta.client_id
        if client_id is None:
            mapper = getattr(asset_mgr, "_id_mapper", None) if asset_mgr is not None else None
            if mapper is not None and hasattr(mapper, "get_client_id"):
                client_id = mapper.get_client_id(int(item.id))
        if client_id is None:
            client_id = int(item.id)

        # Item info header with name
        header_text = f"{item_name} (#{item.id})" if item_name != f"Item #{item.id}" else f"Item #{item.id}"
        builder.add_action(header_text, enabled=False)
        builder.add_separator()

        # Smart Brush Selection
        has_brush_actions = False
        for callback_key, label in _ITEM_SELECT_ACTIONS:
            callback = cb(callback_key)
            if callback is None:
                continue
            builder.add_action(label, callback, enabled=_action_enabled(callback_key))
            has_brush_actions = True

        if not has_brush_actions and ItemTypeDetector.can_select_brush(category) and _action_enabled("select_brush"):
            brush_name = ItemTypeDetector.get_brush_name(category).title()
            builder.add_action(f"Select {brush_name} Brush", cb("select_brush"), enabled=True)
            has_brush_actions = True
        if has_brush_actions:
            builder.add_separator()

        # Item-specific actions
        has_specific_actions = False
        if ItemTypeDetector.is_door(item):
            is_open = ItemTypeDetector.is_door_open(item)
            action_text = "Close Door" if is_open else "Open Door"
            builder.add_action(action_text, cb("toggle_door"), enabled=_action_enabled("toggle_door"))
            has_specific_actions = True
        if ItemTypeDetector.is_rotatable(item):
            builder.add_action("Rotate Item", cb("rotate_item"), enabled=_action_enabled("rotate_item"))
            has_specific_actions = True
        if ItemTypeDetector.is_teleport(item):
            dest = ItemTypeDetector.get_teleport_destination(item)
            if dest:
                builder.add_action(
                    f"Go To Destination ({dest[0]}, {dest[1]}, {dest[2]})",
                    cb("goto_teleport"),
                    enabled=_action_enabled("goto_teleport"),
                )
            else:
                builder.add_action(
                    "Set Teleport Destination...",
                    cb("set_teleport_dest"),
                    enabled=_action_enabled("set_teleport_dest"),
                )
            has_specific_actions = True
        if has_specific_actions:
            builder.add_separator()

        builder.add_action("Properties...", cb("properties"), enabled=_action_enabled("properties"))
        builder.add_action("Browse Field", cb("browse_tile"), enabled=_action_enabled("browse_tile"))
        builder.add_separator()

        builder.add_submenu("Copy Data")
        builder.add_action(f"Server ID ({item.id})", cb("copy_server_id"))
        builder.add_action(
            f"Client ID ({int(client_id)})",
            cb("copy_client_id"),
            enabled=_action_enabled("copy_client_id"),
        )
        builder.add_action("Item Name", cb("copy_item_name"))
        if ctx_pos is not None:
            builder.add_action(f"Position ({ctx_pos[0]}, {ctx_pos[1]}, {ctx_pos[2]})", cb("copy_position"))
        builder.end_submenu()
        builder.add_separator()

        # Item-local edit actions
        builder.add_action("Copy Item", cb("copy"), enabled=_action_enabled("copy"))
        builder.add_action("Delete Item", cb("delete"), enabled=_action_enabled("delete"))
        if hasattr(item, "text") and item.text:
            builder.add_separator()
            builder.add_action("Edit Text...", cb("edit_text"), enabled=_action_enabled("edit_text"))
        builder.add_separator()

        # Find/replace item helpers
        if _action_enabled("set_find"):
            builder.add_action("Set as Find Item", cb("set_find"), enabled=True)
        if _action_enabled("set_replace"):
            builder.add_action("Set as Replace Item", cb("set_replace"), enabled=True)
        if _action_enabled("set_find") or _action_enabled("set_replace"):
            builder.add_separator()
        builder.add_action("Find All of This Item", cb("find_all"), enabled=_action_enabled("find_all"))
        builder.add_action("Replace All...", cb("replace_all"), enabled=_action_enabled("replace_all"))
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
