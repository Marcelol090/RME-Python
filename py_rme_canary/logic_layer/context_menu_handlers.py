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
from dataclasses import replace
from typing import TYPE_CHECKING

from PyQt6.QtGui import QClipboard
from PyQt6.QtWidgets import QApplication, QInputDialog, QWidget

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

    def _find_item_slot(self, tile: Tile, item: Item) -> tuple[str, int] | None:
        """Locate item slot in tile as ('ground', -1) or ('items', index)."""
        ground = getattr(tile, "ground", None)
        if ground is item or ground == item:
            return ("ground", -1)

        items = list(getattr(tile, "items", None) or [])
        for index, candidate in enumerate(items):
            if candidate is item or candidate == item:
                return ("items", int(index))
        return None

    def _commit_tile_change(
        self,
        *,
        position: tuple[int, int, int],
        before: Tile | None,
        after: Tile | None,
        label: str,
        details: dict[str, object] | None = None,
    ) -> bool:
        """Commit tile change via session history + queue."""
        session = self.editor_session
        if session is None:
            return False

        if before == after:
            return False

        from py_rme_canary.logic_layer.session.action_queue import ActionType, SessionAction
        from py_rme_canary.logic_layer.transactional_brush import LabeledPaintAction

        key = (int(position[0]), int(position[1]), int(position[2]))
        action = LabeledPaintAction(brush_id=0, label=str(label))
        action.record_tile_change(key, before, after)
        if not action.has_changes():
            return False

        action.redo(session.game_map)
        session.history.commit_action(action)
        session.action_queue.push(
            SessionAction(type=ActionType.PAINT, action=action, label=str(label), details=details or {})
        )
        with suppress(Exception):
            session._emit_tiles_changed({key})  # noqa: SLF001
        return True

    def _apply_item_change(
        self,
        *,
        item: Item,
        tile: Tile,
        position: tuple[int, int, int],
        label: str,
        transform: Callable[[Item], Item],
    ) -> bool:
        """Apply item transformation transactionally."""
        before_tile = tile
        if self.editor_session is not None:
            maybe_tile = self.editor_session.game_map.get_tile(int(position[0]), int(position[1]), int(position[2]))
            if maybe_tile is not None:
                before_tile = maybe_tile

        slot = self._find_item_slot(before_tile, item)
        if slot is None:
            return False

        slot_type, index = slot
        if slot_type == "ground":
            current_item = before_tile.ground
            if current_item is None:
                return False
            new_item = transform(current_item)
            if new_item == current_item:
                return False
            after_tile = replace(before_tile, ground=new_item, modified=True)
        else:
            items = list(before_tile.items)
            if not (0 <= int(index) < len(items)):
                return False
            current_item = items[int(index)]
            new_item = transform(current_item)
            if new_item == current_item:
                return False
            items[int(index)] = new_item
            after_tile = replace(before_tile, items=items, modified=True)

        return self._commit_tile_change(
            position=position,
            before=before_tile,
            after=after_tile,
            label=label,
            details={"x": int(position[0]), "y": int(position[1]), "z": int(position[2]), "item_id": int(item.id)},
        )

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
            self._show_status(f"[Toggle Door] No toggle mapping for door ID {item.id}")
            return

        if self.editor_session is not None:
            action = self.editor_session.switch_door_at(x=position[0], y=position[1], z=position[2])
            if action is not None:
                self._show_status(f"[Toggle Door] Door toggled at {position[0]}, {position[1]}, {position[2]}")
                return

        old_id = int(item.id)
        committed = self._apply_item_change(
            item=item,
            tile=tile,
            position=position,
            label="Toggle Door",
            transform=lambda current: replace(current, id=int(toggle_id)),
        )
        if committed:
            state = "opened" if ItemTypeDetector.is_door_open(replace(item, id=int(toggle_id))) else "closed"
            self._show_status(f"[Toggle Door] Door {old_id} → {int(toggle_id)} ({state})")
            return

        # Final fallback when no session context is available.
        item.id = int(toggle_id)
        is_open = ItemTypeDetector.is_door_open(item)
        self._show_status(f"[Toggle Door] Door {old_id} → {int(toggle_id)} ({'opened' if is_open else 'closed'})")

    # ========================
    # Item Rotation
    # ========================

    def rotate_item(self, item: Item, tile: Tile | None = None, position: tuple[int, int, int] | None = None) -> None:
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
        if tile is not None and position is not None:
            committed = self._apply_item_change(
                item=item,
                tile=tile,
                position=position,
                label="Rotate Item",
                transform=lambda current: replace(current, id=int(next_id)),
            )
            if committed:
                self._show_status(f"[Rotate Item] Item {old_id} → {int(next_id)}")
                return

        item.id = int(next_id)
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

    def set_find_item(self, item: Item) -> None:
        """Set item as quick-find source."""
        item_id = int(item.id)
        editor = self._resolve_editor()
        if editor is not None and hasattr(editor, "_set_quick_replace_source"):
            with suppress(Exception):
                editor._set_quick_replace_source(item_id)
                return
        self._show_status(f"[Quick Replace] Find item set to {item_id}")

    def set_replace_item(self, item: Item) -> None:
        """Set item as quick-replace target."""
        item_id = int(item.id)
        editor = self._resolve_editor()
        if editor is not None and hasattr(editor, "_set_quick_replace_target"):
            with suppress(Exception):
                editor._set_quick_replace_target(item_id)
                return
        self._show_status(f"[Quick Replace] Replace item set to {item_id}")

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
            before_tile = tile
            if self.editor_session is not None:
                maybe_tile = self.editor_session.game_map.get_tile(
                    int(position[0]),
                    int(position[1]),
                    int(position[2]),
                )
                if maybe_tile is not None:
                    before_tile = maybe_tile

            after_tile = replace(before_tile, ground=ground, items=list(items), modified=True)
            if self._commit_tile_change(
                position=position,
                before=before_tile,
                after=after_tile,
                label="Browse Tile",
                details={
                    "x": int(position[0]),
                    "y": int(position[1]),
                    "z": int(position[2]),
                    "ground": int(ground.id) if ground is not None else 0,
                    "items": [int(i.id) for i in items],
                },
            ):
                self._show_status(f"[Browse Tile] Tile updated at {position[0]}, {position[1]}, {position[2]}")
            else:
                self._show_status(f"[Browse Tile] Unable to commit changes at {position[0]}, {position[1]}, {position[2]}")

    def open_item_properties(self, item: Item, tile: Tile | None = None, position: tuple[int, int, int] | None = None) -> None:
        """Open item properties with the best available UI."""
        if tile is not None and position is not None:
            self.browse_tile(tile, position)
            return
        self._show_status(f"[Properties] Item #{int(item.id)}")

    def copy_item(self, item: Item, tile: Tile | None = None, position: tuple[int, int, int] | None = None) -> None:
        """Copy item/tile selection to editor clipboard when possible."""
        editor = self._resolve_editor()
        if editor is not None and position is not None:
            session = getattr(editor, "session", None)
            if session is not None and hasattr(session, "set_single_selection") and hasattr(editor, "_copy_selection"):
                with suppress(Exception):
                    session.set_single_selection(x=int(position[0]), y=int(position[1]), z=int(position[2]))
                    editor._copy_selection()
                    self._show_status(
                        f"[Copy] Copied tile at {int(position[0])}, {int(position[1])}, {int(position[2])}"
                    )
                    return
        self.copy_server_id(item)

    def delete_item(self, item: Item, tile: Tile | None = None, position: tuple[int, int, int] | None = None) -> None:
        """Delete clicked item transactionally."""
        if tile is None or position is None:
            self._show_status("[Delete] Missing tile context.")
            return

        before_tile = tile
        if self.editor_session is not None:
            maybe_tile = self.editor_session.game_map.get_tile(int(position[0]), int(position[1]), int(position[2]))
            if maybe_tile is not None:
                before_tile = maybe_tile

        slot = self._find_item_slot(before_tile, item)
        if slot is None:
            self._show_status("[Delete] Item not found on tile.")
            return

        slot_type, index = slot
        if slot_type == "ground":
            after_tile = replace(before_tile, ground=None, modified=True)
        else:
            items = list(before_tile.items)
            if not (0 <= int(index) < len(items)):
                self._show_status("[Delete] Invalid stack index.")
                return
            removed = items.pop(int(index))
            after_tile = replace(before_tile, items=items, modified=True)
            item = removed

        if self._commit_tile_change(
            position=position,
            before=before_tile,
            after=after_tile,
            label="Delete Item",
            details={"x": int(position[0]), "y": int(position[1]), "z": int(position[2]), "item_id": int(item.id)},
        ):
            self._show_status(f"[Delete] Removed item {int(item.id)} at {position[0]}, {position[1]}, {position[2]}")
            return

        self._show_status(f"[Delete] Unable to commit removal for item {int(item.id)}")

    def edit_item_text(self, item: Item, tile: Tile | None = None, position: tuple[int, int, int] | None = None) -> None:
        """Edit text attribute transactionally."""
        if tile is None or position is None:
            self._show_status("[Edit Text] Missing tile context.")
            return

        editor = self._resolve_editor()
        parent = editor if isinstance(editor, QWidget) else None
        current_text = str(getattr(item, "text", "") or "")
        new_text, accepted = QInputDialog.getMultiLineText(parent, "Edit Text", "Text:", current_text)
        if not accepted:
            return

        normalized = str(new_text or "")
        if normalized == current_text:
            return

        updated_text = normalized if normalized else None
        committed = self._apply_item_change(
            item=item,
            tile=tile,
            position=position,
            label="Edit Item Text",
            transform=lambda current: replace(current, text=updated_text),
        )
        if committed:
            self._show_status(f"[Edit Text] Updated text for item {int(item.id)}")
            return

        # No session/history available fallback.
        item.text = updated_text
        self._show_status(f"[Edit Text] Updated text for item {int(item.id)}")

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
            "rotate_item": lambda: self.rotate_item(item, tile, position) if tile and position else None,
            "goto_teleport": lambda: self.goto_teleport_destination(item),
            # Copy data
            "copy_server_id": lambda: self.copy_server_id(item),
            "copy_client_id": lambda: self.copy_client_id(item),
            "copy_item_name": lambda: self.copy_item_name(item),
            "copy_position": lambda: self.copy_position(position) if position else None,
            # Find/Replace
            "set_find": lambda: self.set_find_item(item),
            "set_replace": lambda: self.set_replace_item(item),
            "find_all": lambda: self.find_all_items(item),
            "replace_all": lambda: self.replace_all_items(item),
            # Browse
            "browse_tile": lambda: self.browse_tile(tile, position) if tile and position else None,
            # Standard actions
            "properties": lambda: self.open_item_properties(item, tile, position),
            "copy": lambda: self.copy_item(item, tile, position),
            "delete": lambda: self.delete_item(item, tile, position),
            "edit_text": lambda: self.edit_item_text(item, tile, position),
        }
