"""Context Menu Action Handlers.

Implements the actual behavior for context menu actions including:
- Smart brush selection
- Door toggle
- Item rotation
- Teleport navigation
- Data copy actions

These handlers connect context menu UI to actual map editing operations.
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import replace
from typing import TYPE_CHECKING

from PyQt6.QtGui import QClipboard
from PyQt6.QtWidgets import QApplication

if TYPE_CHECKING:
    from py_rme_canary.core.data.item import Item
    from py_rme_canary.core.data.tile import Tile
    from py_rme_canary.logic_layer.session.editor import EditorSession


class ContextMenuActionHandlers:
    """Handlers for context menu actions."""

    def __init__(
        self,
        editor_session: EditorSession | None = None,
        canvas: object | None = None,
        palette: object | None = None,
    ) -> None:
        """Initialize handlers with editor components.

        Args:
            editor_session: Current editor session (for undo/redo)
            canvas: Map canvas widget (for navigation)
            palette: Brush palette widget (for brush selection)
        """
        self.editor_session = editor_session
        self.canvas = canvas
        self.palette = palette
        self._clipboard: QClipboard | None = QApplication.clipboard()

    # ========================
    # Smart Brush Selection
    # ========================

    def select_brush_for_item(self, item: Item) -> None:
        """Select appropriate brush based on item type.

        Args:
            item: Item to detect brush for
        """
        from py_rme_canary.logic_layer.item_type_detector import ItemCategory, ItemTypeDetector

        category = ItemTypeDetector.get_category(item)

        if not ItemTypeDetector.can_select_brush(category):
            return

        # Map category to brush name
        brush_map = {
            ItemCategory.WALL: "wall",
            ItemCategory.CARPET: "carpet",
            ItemCategory.DOOR: "door",
            ItemCategory.TABLE: "table",
        }

        brush_name = brush_map.get(category)
        if brush_name and self.palette:
            # TODO: Implement palette.select_brush(brush_name)
            print(f"[Select Brush] {brush_name} brush selected for item {item.id}")

    # ========================
    # Door Toggle
    # ========================

    def toggle_door(self, item: Item, tile: Tile, position: tuple[int, int, int]) -> None:
        """Toggle door between open and closed state.

        Args:
            item: Door item to toggle
            tile: Tile containing the door
            position: (x, y, z) position
        """
        from py_rme_canary.logic_layer.item_type_detector import ItemTypeDetector

        if not ItemTypeDetector.is_door(item):
            return

        toggle_id = ItemTypeDetector.get_door_toggle_id(item)
        if toggle_id is None:
            print(f"[Toggle Door] No toggle mapping for door ID {item.id}")
            return

        if self.editor_session is not None:
            action = self.editor_session.switch_door_at(x=position[0], y=position[1], z=position[2])
            if action is not None:
                return

        # Update item ID (local-only fallback)
        old_id = item.id
        updated_item = replace(item, id=toggle_id)

        # TODO: Wrap in EditorAction for undo/redo
        # if self.editor_session:
        #     action = ModifyItemAction(position, old_id, toggle_id)
        #     self.editor_session.execute_action(action)

        is_open = ItemTypeDetector.is_door_open(updated_item)
        state = "opened" if is_open else "closed"
        print(f"[Toggle Door] Door {old_id} → {toggle_id} ({state})")

    # ========================
    # Item Rotation
    # ========================

    def rotate_item(self, item: Item) -> None:
        """Rotate item to next orientation.

        Args:
            item: Rotatable item
        """
        from py_rme_canary.logic_layer.item_type_detector import ItemTypeDetector

        if not ItemTypeDetector.is_rotatable(item):
            return

        next_id = ItemTypeDetector.get_next_rotation_id(item)
        if next_id is None:
            return

        old_id = item.id
        updated_item = replace(item, id=next_id)

        # TODO: Wrap in EditorAction for undo/redo
        print(f"[Rotate Item] Item {old_id} → {updated_item.id}")

    # ========================
    # Teleport Navigation
    # ========================

    def goto_teleport_destination(self, item: Item) -> None:
        """Navigate canvas to teleport destination.

        Args:
            item: Teleport item
        """
        from py_rme_canary.logic_layer.item_type_detector import ItemTypeDetector

        if not ItemTypeDetector.is_teleport(item):
            return

        dest = ItemTypeDetector.get_teleport_destination(item)
        if not dest:
            print("[Go To Teleport] No destination set")
            return

        if self.canvas:
            # TODO: canvas.jump_to_position(dest)
            print(f"[Go To Teleport] Jumping to {dest}")
        else:
            print(f"[Go To Teleport] Destination: {dest}")

    # ========================
    # Copy Data Actions
    # ========================

    def copy_server_id(self, item: Item) -> None:
        """Copy item's server ID to clipboard.

        Args:
            item: Item to copy ID from
        """
        clipboard = self._clipboard
        if clipboard is None:
            return
        text = str(item.id)
        clipboard.setText(text, QClipboard.Mode.Clipboard)
        print(f"[Copy] Server ID {text} copied to clipboard")

    def copy_item_name(self, item: Item) -> None:
        """Copy item's name to clipboard.

        Args:
            item: Item to copy name from
        """
        # TODO: Look up name from items.otb
        # For now, use placeholder
        name = f"Item_{item.id}"  # Placeholder

        clipboard = self._clipboard
        if clipboard is None:
            return
        clipboard.setText(name, QClipboard.Mode.Clipboard)
        print(f"[Copy] Item name '{name}' copied to clipboard")

    def copy_position(self, position: tuple[int, int, int]) -> None:
        """Copy position to clipboard.

        Args:
            position: (x, y, z) coordinates
        """
        clipboard = self._clipboard
        if clipboard is None:
            return
        text = f"{position[0]}, {position[1]}, {position[2]}"
        clipboard.setText(text, QClipboard.Mode.Clipboard)
        print(f"[Copy] Position {text} copied to clipboard")

    def copy_client_id(self, item: Item) -> None:
        """Copy item's client ID to clipboard.

        Args:
            item: Item to copy client ID from
        """
        # TODO: Implement ID mapping via IdMapper
        # client_id = id_mapper.server_to_client(item.id)
        client_id = item.id  # Placeholder

        clipboard = self._clipboard
        if clipboard is None:
            return
        text = str(client_id)
        clipboard.setText(text, QClipboard.Mode.Clipboard)
        print(f"[Copy] Client ID {text} copied to clipboard")

    # ========================
    # Find/Replace Actions
    # ========================

    def find_all_items(self, item: Item) -> None:
        """Open Find Item dialog pre-filled with this item's ID.

        Args:
            item: Item to search for
        """
        # TODO: Open FindItemDialog with ID pre-filled
        print(f"[Find All] Searching for all items with ID {item.id}")

    def replace_all_items(self, item: Item) -> None:
        """Open Replace Items dialog with this item as source.

        Args:
            item: Item to replace
        """
        # TODO: Open ReplaceItemsDialog
        print(f"[Replace All] Opening replace dialog for item {item.id}")

    # ========================
    # Browse Tile
    # ========================

    def browse_tile(self, tile: Tile, position: tuple[int, int, int]) -> None:
        """Open Browse Tile dialog for this tile.

        Args:
            tile: Tile to browse
            position: (x, y, z) position
        """
        from py_rme_canary.vis_layer.ui.dialogs.browse_tile_dialog import BrowseTileDialog

        # Get asset manager if available
        asset_manager = None
        if hasattr(self, "editor_session") and self.editor_session:
            asset_manager = getattr(self.editor_session, "asset_manager", None)

        dialog = BrowseTileDialog(tile=tile, position=position, asset_manager=asset_manager)

        result = dialog.exec()

        if result:
            # Apply changes
            ground, items = dialog.get_modified_items()

            # TODO: Create ModifyTileAction and execute via EditorSession
            print(f"[Browse Tile] Modified tile at {position}")
            print(f"  Ground: {ground.id if ground else 'None'}")
            print(f"  Items: {[item.id for item in items]}")

    # ========================
    # Helper: Create Callback Dict
    # ========================

    def get_item_context_callbacks(
        self, item: Item, tile: Tile | None = None, position: tuple[int, int, int] | None = None
    ) -> dict[str, Callable[[], object | None]]:
        """Get callback dictionary for ItemContextMenu.

        Args:
            item: Item being right-clicked
            tile: Tile containing the item (optional)
            position: Position of the tile (optional)

        Returns:
            Dictionary of callback names to functions
        """
        return {
            # Smart actions
            "select_brush": lambda: self.select_brush_for_item(item),
            "toggle_door": lambda: self.toggle_door(item, tile, position) if tile and position else None,
            "rotate_item": lambda: self.rotate_item(item),
            "goto_teleport": lambda: self.goto_teleport_destination(item),
            # Copy data
            "copy_server_id": lambda: self.copy_server_id(item),
            "copy_client_id": lambda: self.copy_client_id(item),
            "copy_item_name": lambda: self.copy_item_name(item),
            "copy_position": lambda: self.copy_position(position) if position else None,
            # Find/Replace
            "find_all": lambda: self.find_all_items(item),
            "replace_all": lambda: self.replace_all_items(item),
            # Browse
            "browse_tile": lambda: self.browse_tile(tile, position) if tile and position else None,
            # Standard actions (TODO: implement)
            "properties": lambda: print(f"[Properties] Opening properties for item {item.id}"),
            "copy": lambda: print(f"[Copy] Copying item {item.id}"),
            "delete": lambda: print(f"[Delete] Deleting item {item.id}"),
            "edit_text": lambda: print(f"[Edit Text] Editing text for item {item.id}"),
        }
