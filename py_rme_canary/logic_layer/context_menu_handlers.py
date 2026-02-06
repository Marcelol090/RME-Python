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
from contextlib import suppress
from typing import TYPE_CHECKING

from PyQt6.QtGui import QClipboard
from PyQt6.QtWidgets import QApplication, QWidget

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

    def _resolve_editor(self) -> object | None:
        """Resolve editor instance from known UI anchors."""
        for candidate in (self.canvas, self.palette):
            if candidate is None:
                continue

            editor = getattr(candidate, "_editor", None)
            if editor is not None:
                return editor

            editor = getattr(candidate, "editor", None)
            if editor is not None:
                return editor

        return None

    def _show_status(self, message: str) -> None:
        """Show status in editor bar when available; fallback to stdout."""
        editor = self._resolve_editor()
        if editor is not None:
            status = getattr(editor, "status", None)
            if status is not None and hasattr(status, "showMessage"):
                with suppress(Exception):
                    status.showMessage(str(message))
                    return
        print(str(message))

    def _set_selected_brush(self, brush_id: int) -> bool:
        """Best-effort brush selection through palette/editor/session."""
        sid = int(brush_id)

        if self.palette is not None and hasattr(self.palette, "select_brush"):
            with suppress(Exception):
                self.palette.select_brush(sid)
                return True

        editor = self._resolve_editor()
        if editor is not None and hasattr(editor, "_set_selected_brush_id"):
            with suppress(Exception):
                editor._set_selected_brush_id(sid)
                return True

        if self.editor_session is not None and hasattr(self.editor_session, "set_selected_brush"):
            with suppress(Exception):
                self.editor_session.set_selected_brush(sid)
                return True

        return False

    # ========================
    # Smart Brush Selection
    # ========================

    def select_brush_for_item(self, item: Item) -> None:
        """Select appropriate brush based on item type.

        Args:
            item: Item to detect brush for
        """
        from py_rme_canary.logic_layer.item_type_detector import ItemTypeDetector

        category = ItemTypeDetector.get_category(item)

        if not ItemTypeDetector.can_select_brush(category):
            return

        brush_name = ItemTypeDetector.get_brush_name(category)
        brush_id = int(item.id)

        if self.editor_session is not None:
            brush_manager = getattr(self.editor_session, "brush_manager", None)
            if brush_manager is not None and hasattr(brush_manager, "get_brush_any"):
                with suppress(Exception):
                    brush_def = brush_manager.get_brush_any(int(item.id))
                    if brush_def is not None:
                        brush_id = int(getattr(brush_def, "server_id", int(item.id)))

        if self._set_selected_brush(brush_id):
            self._show_status(f"[Select Brush] {brush_name} brush selected ({brush_id})")
            return

        self._show_status(f"[Select Brush] Unable to select brush for item {int(item.id)}")

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

        # Local-only fallback: mutate selected item directly.
        old_id = int(item.id)
        item.id = int(toggle_id)

        # TODO: Wrap in EditorAction for undo/redo
        # if self.editor_session:
        #     action = ModifyItemAction(position, old_id, toggle_id)
        #     self.editor_session.execute_action(action)

        is_open = ItemTypeDetector.is_door_open(item)
        state = "opened" if is_open else "closed"
        self._show_status(f"[Toggle Door] Door {old_id} → {int(toggle_id)} ({state})")

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

        old_id = int(item.id)
        item.id = int(next_id)

        # TODO: Wrap in EditorAction for undo/redo
        self._show_status(f"[Rotate Item] Item {old_id} → {int(item.id)}")

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

        if self.canvas and hasattr(self.canvas, "jump_to_position"):
            with suppress(Exception):
                self.canvas.jump_to_position(dest)
                return

        editor = self._resolve_editor()
        if editor is not None and hasattr(editor, "center_view_on"):
            x, y, z = (int(dest[0]), int(dest[1]), int(dest[2]))
            with suppress(Exception):
                editor.center_view_on(x, y, z, push_history=True)
                session = getattr(editor, "session", None)
                if session is not None and hasattr(session, "set_single_selection"):
                    session.set_single_selection(x=x, y=y, z=z)
                canvas = getattr(editor, "canvas", None)
                if canvas is not None and hasattr(canvas, "update"):
                    canvas.update()
                self._show_status(f"[Go To Teleport] Jumped to {x}, {y}, {z}")
                return

        self._show_status(f"[Go To Teleport] Destination: {dest}")

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
        from py_rme_canary.logic_layer.asset_manager import AssetManager

        asset_mgr = AssetManager.instance()
        name = asset_mgr.get_item_name(int(item.id))

        clipboard = self._clipboard
        if clipboard is None:
            return
        clipboard.setText(name, QClipboard.Mode.Clipboard)
        self._show_status(f"[Copy] Item name '{name}' copied to clipboard")

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
        from py_rme_canary.logic_layer.asset_manager import AssetManager

        client_id: int | None = int(item.client_id) if item.client_id is not None else None

        asset_mgr = AssetManager.instance()
        if client_id is None:
            metadata = asset_mgr.get_item_metadata(int(item.id))
            if metadata is not None and metadata.client_id is not None:
                client_id = int(metadata.client_id)

        if client_id is None:
            mapper = getattr(asset_mgr, "_id_mapper", None)
            if mapper is not None and hasattr(mapper, "get_client_id"):
                mapped = mapper.get_client_id(int(item.id))
                if mapped is not None:
                    client_id = int(mapped)

        if client_id is None:
            client_id = int(item.id)

        clipboard = self._clipboard
        if clipboard is None:
            return
        text = str(client_id)
        clipboard.setText(text, QClipboard.Mode.Clipboard)
        self._show_status(f"[Copy] Client ID {text} copied to clipboard")

    # ========================
    # Find/Replace Actions
    # ========================

    def find_all_items(self, item: Item) -> None:
        """Open Find Item dialog pre-filled with this item's ID.

        Args:
            item: Item to search for
        """
        item_id = int(item.id)
        editor = self._resolve_editor()

        if editor is not None and hasattr(editor, "_find_item_by_id"):
            with suppress(Exception):
                editor._find_item_by_id(item_id)
                return

        self._show_status(f"[Find All] Searching for all items with ID {item_id}")

    def replace_all_items(self, item: Item) -> None:
        """Open Replace Items dialog with this item as source.

        Args:
            item: Item to replace
        """
        item_id = int(item.id)
        editor = self._resolve_editor()

        if (
            editor is not None
            and hasattr(editor, "_set_quick_replace_source")
            and hasattr(editor, "_open_replace_items_dialog")
        ):
            with suppress(Exception):
                editor._set_quick_replace_source(item_id)
                editor._open_replace_items_dialog()
                return

        from py_rme_canary.vis_layer.ui.dialogs.replace_items_dialog import ReplaceItemsDialog

        parent = editor if isinstance(editor, QWidget) else None
        dialog = ReplaceItemsDialog(parent=parent, session=self.editor_session)
        dialog.set_source_id(item_id)
        dialog.exec()

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
