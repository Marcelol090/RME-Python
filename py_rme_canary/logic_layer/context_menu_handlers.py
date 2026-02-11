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

            editor: object | None = getattr(candidate, "_editor", None)
            if editor is not None:
                return editor

            alt_editor: object | None = getattr(candidate, "editor", None)
            if alt_editor is not None:
                return alt_editor

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

    def _resolve_session(self) -> EditorSession | object | None:
        if self.editor_session is not None:
            return self.editor_session
        editor = self._resolve_editor()
        if editor is None:
            return None
        return getattr(editor, "session", None)

    def _refresh_editor_after_change(self) -> None:
        editor = self._resolve_editor()
        if editor is None:
            return
        canvas = getattr(editor, "canvas", None)
        if canvas is not None and hasattr(canvas, "update"):
            with suppress(Exception):
                canvas.update()
        if hasattr(editor, "_update_action_enabled_states"):
            with suppress(Exception):
                editor._update_action_enabled_states()

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

        session = self._resolve_session()
        if session is not None and hasattr(session, "set_selected_brush"):
            with suppress(Exception):
                session.set_selected_brush(sid)
                return True

        return False

    def _select_palette(self, palette_key: str) -> None:
        editor = self._resolve_editor()
        if editor is None or not hasattr(editor, "_select_palette"):
            return
        with suppress(Exception):
            editor._select_palette(str(palette_key))

    def _resolve_brush_manager(self) -> object | None:
        brush_manager = getattr(self.editor_session, "brush_manager", None) if self.editor_session is not None else None
        if brush_manager is not None:
            return brush_manager
        editor = self._resolve_editor()
        return getattr(editor, "brush_mgr", None) if editor is not None else None

    def _resolve_brush_for_item_id(self, server_id: int) -> tuple[int, str] | None:
        brush_manager = self._resolve_brush_manager()
        if brush_manager is None or not hasattr(brush_manager, "get_brush_any"):
            return None
        with suppress(Exception):
            brush_def = brush_manager.get_brush_any(int(server_id))
            if brush_def is None:
                return None
            brush_id = int(getattr(brush_def, "server_id", int(server_id)))
            brush_type = str(getattr(brush_def, "brush_type", "") or "").strip().lower()
            return (int(brush_id), str(brush_type))
        return None

    def _palette_key_for_brush_type(self, brush_type: str) -> str | None:
        btype = str(brush_type or "").strip().lower()
        mapping = {
            "ground": "terrain",
            "terrain": "terrain",
            "wall": "terrain",
            "door": "terrain",
            "optional_border": "terrain",
            "doodad": "doodad",
            "table": "item",
            "carpet": "item",
            "monster": "creature",
            "spawn_monster": "creature",
            "npc": "npc",
            "spawn_npc": "npc",
            "house": "house",
            "house_exit": "house",
            "zone": "zones",
            "waypoint": "waypoint",
            "raw": "raw",
        }
        return mapping.get(btype)

    def _select_brush_with_palette(self, *, brush_id: int, status_tag: str, palette_key: str | None = None) -> bool:
        selected = self._set_selected_brush(int(brush_id))
        if palette_key:
            self._select_palette(str(palette_key))
        if selected:
            self._show_status(f"[{status_tag}] Selected brush {int(brush_id)}")
            return True
        self._show_status(f"[{status_tag}] Unable to select brush {int(brush_id)}")
        return False

    def _tile_items_top_first(self, tile: Tile | None) -> list[Item]:
        if tile is None:
            return []
        return list(reversed(list(getattr(tile, "items", []) or [])))

    def _find_brush_id_for_types(
        self,
        *,
        tile: Tile | None,
        item: Item | None,
        wanted_types: set[str],
        include_ground: bool = False,
    ) -> int | None:
        wanted = {str(v).strip().lower() for v in wanted_types}
        checked_ids: set[int] = set()

        def _check(candidate: Item | None) -> int | None:
            if candidate is None:
                return None
            sid = int(getattr(candidate, "id", 0))
            if sid in checked_ids:
                return None
            checked_ids.add(int(sid))
            resolved = self._resolve_brush_for_item_id(int(sid))
            if resolved is None:
                return None
            brush_id, brush_type = resolved
            if str(brush_type) in wanted:
                return int(brush_id)
            return None

        top_first = self._tile_items_top_first(tile)
        if item is not None:
            found = _check(item)
            if found is not None:
                return int(found)

        for candidate in top_first:
            found = _check(candidate)
            if found is not None:
                return int(found)

        if include_ground and tile is not None:
            found = _check(getattr(tile, "ground", None))
            if found is not None:
                return int(found)

        return None

    def _has_brush_type(
        self,
        *,
        tile: Tile | None,
        item: Item | None,
        wanted_types: set[str],
        include_ground: bool = False,
    ) -> bool:
        return self._find_brush_id_for_types(
            tile=tile,
            item=item,
            wanted_types=set(wanted_types),
            include_ground=bool(include_ground),
        ) is not None

    def _virtual_creature_brush_id(self, *, name: str, is_npc: bool) -> int | None:
        nm = str(name or "").strip()
        if not nm:
            return None

        if is_npc:
            from py_rme_canary.core.io.creatures_xml import load_npc_names
            from py_rme_canary.logic_layer.brush_definitions import npc_virtual_id

            used: set[int] = set()
            for candidate in sorted(load_npc_names(), key=lambda v: str(v).casefold()):
                candidate_name = str(candidate)
                with suppress(Exception):
                    vid = int(npc_virtual_id(candidate_name, used=used))
                    if candidate_name.casefold() == nm.casefold():
                        return int(vid)
            with suppress(Exception):
                return int(npc_virtual_id(nm))
            return None

        from py_rme_canary.core.io.creatures_xml import load_monster_names
        from py_rme_canary.logic_layer.brush_definitions import monster_virtual_id

        used = set()
        for candidate in sorted(load_monster_names(), key=lambda v: str(v).casefold()):
            candidate_name = str(candidate)
            with suppress(Exception):
                vid = int(monster_virtual_id(candidate_name, used=used))
                if candidate_name.casefold() == nm.casefold():
                    return int(vid)
        with suppress(Exception):
            return int(monster_virtual_id(nm))
        return None

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
        resolved = self._resolve_brush_for_item_id(int(item.id))
        if resolved is not None:
            brush_id, brush_type = resolved
            palette_key = self._palette_key_for_brush_type(brush_type)
            self._select_brush_with_palette(
                brush_id=int(brush_id),
                palette_key=palette_key,
                status_tag="Select Brush",
            )
            return

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

    def select_raw_brush(self, item: Item) -> None:
        """Select RAW brush directly from item id."""
        self._select_brush_with_palette(
            brush_id=int(item.id),
            palette_key="raw",
            status_tag="Select RAW",
        )

    def select_ground_brush(self, item: Item | None = None, tile: Tile | None = None) -> None:
        brush_id = self._find_brush_id_for_types(
            tile=tile,
            item=item,
            wanted_types={"ground", "terrain"},
            include_ground=True,
        )
        if brush_id is None and tile is not None and getattr(tile, "ground", None) is not None:
            brush_id = int(getattr(tile.ground, "id", 0))
        if brush_id is None:
            self._show_status("[Select Ground] Unable to resolve ground brush")
            return
        self._select_brush_with_palette(
            brush_id=int(brush_id),
            palette_key="terrain",
            status_tag="Select Ground",
        )

    def select_wall_brush(self, item: Item | None = None, tile: Tile | None = None) -> None:
        brush_id = self._find_brush_id_for_types(tile=tile, item=item, wanted_types={"wall"})
        if brush_id is None:
            self._show_status("[Select Wall] Unable to resolve wall brush")
            return
        self._select_brush_with_palette(
            brush_id=int(brush_id),
            palette_key="terrain",
            status_tag="Select Wall",
        )

    def select_carpet_brush(self, item: Item | None = None, tile: Tile | None = None) -> None:
        brush_id = self._find_brush_id_for_types(tile=tile, item=item, wanted_types={"carpet"})
        if brush_id is None:
            self._show_status("[Select Carpet] Unable to resolve carpet brush")
            return
        self._select_brush_with_palette(
            brush_id=int(brush_id),
            palette_key="item",
            status_tag="Select Carpet",
        )

    def select_table_brush(self, item: Item | None = None, tile: Tile | None = None) -> None:
        brush_id = self._find_brush_id_for_types(tile=tile, item=item, wanted_types={"table"})
        if brush_id is None:
            self._show_status("[Select Table] Unable to resolve table brush")
            return
        self._select_brush_with_palette(
            brush_id=int(brush_id),
            palette_key="item",
            status_tag="Select Table",
        )

    def select_doodad_brush(self, item: Item | None = None, tile: Tile | None = None) -> None:
        brush_id = self._find_brush_id_for_types(tile=tile, item=item, wanted_types={"doodad"})
        if brush_id is None:
            self._show_status("[Select Doodad] Unable to resolve doodad brush")
            return
        self._select_brush_with_palette(
            brush_id=int(brush_id),
            palette_key="doodad",
            status_tag="Select Doodad",
        )

    def select_door_brush(self, item: Item | None = None, tile: Tile | None = None) -> None:
        brush_id = self._find_brush_id_for_types(tile=tile, item=item, wanted_types={"door"})
        if brush_id is None:
            self._show_status("[Select Door] Unable to resolve door brush")
            return
        self._select_brush_with_palette(
            brush_id=int(brush_id),
            palette_key="terrain",
            status_tag="Select Door",
        )

    def select_collection_brush(self, item: Item, tile: Tile | None = None) -> None:
        """Select Collection brush and switch palette to Collection (legacy parity)."""
        brush_id = self._find_brush_id_for_types(
            tile=tile,
            item=item,
            wanted_types={"wall", "table", "carpet", "doodad", "ground", "terrain"},
            include_ground=True,
        )
        if brush_id is None:
            resolved = self._resolve_brush_for_item_id(int(item.id))
            if resolved is not None:
                brush_id = int(resolved[0])
        if brush_id is None:
            brush_id = int(item.id)

        self._select_brush_with_palette(
            brush_id=int(brush_id),
            palette_key="collection",
            status_tag="Select Collection",
        )

    def select_house_brush(self, tile: Tile | None = None) -> None:
        house_id = int(getattr(tile, "house_id", 0) or 0) if tile is not None else 0
        if house_id <= 0:
            self._show_status("[Select House] Tile has no house id")
            return

        from py_rme_canary.logic_layer.brush_definitions import VIRTUAL_HOUSE_BASE

        self._select_brush_with_palette(
            brush_id=int(VIRTUAL_HOUSE_BASE + int(house_id)),
            palette_key="house",
            status_tag="Select House",
        )

    def select_creature_brush(self, tile: Tile | None = None) -> None:
        if tile is None:
            self._show_status("[Select Creature] Missing tile context")
            return

        monsters = list(getattr(tile, "monsters", []) or [])
        npc = getattr(tile, "npc", None)

        if monsters:
            name = str(getattr(monsters[0], "name", "") or "").strip()
            vid = self._virtual_creature_brush_id(name=name, is_npc=False)
            if vid is not None:
                self._select_brush_with_palette(
                    brush_id=int(vid),
                    palette_key="creature",
                    status_tag="Select Creature",
                )
                return

        if npc is not None:
            name = str(getattr(npc, "name", "") or "").strip()
            vid = self._virtual_creature_brush_id(name=name, is_npc=True)
            if vid is not None:
                self._select_brush_with_palette(
                    brush_id=int(vid),
                    palette_key="npc",
                    status_tag="Select Creature",
                )
                return

        self._show_status("[Select Creature] No creature found on tile")

    def select_spawn_brush(self, tile: Tile | None = None) -> None:
        if tile is None:
            self._show_status("[Select Spawn] Missing tile context")
            return

        from py_rme_canary.logic_layer.brush_definitions import VIRTUAL_SPAWN_MONSTER_TOOL_ID, VIRTUAL_SPAWN_NPC_TOOL_ID

        if getattr(tile, "spawn_npc", None) is not None:
            self._select_brush_with_palette(
                brush_id=int(VIRTUAL_SPAWN_NPC_TOOL_ID),
                palette_key="npc",
                status_tag="Select Spawn",
            )
            return

        if getattr(tile, "spawn_monster", None) is not None:
            self._select_brush_with_palette(
                brush_id=int(VIRTUAL_SPAWN_MONSTER_TOOL_ID),
                palette_key="creature",
                status_tag="Select Spawn",
            )
            return

        self._show_status("[Select Spawn] No spawn area found on tile")

    # ========================
    # Selection / Canvas Ops
    # ========================

    def has_selection(self) -> bool:
        session = self._resolve_session()
        if session is None or not hasattr(session, "has_selection"):
            return False
        with suppress(Exception):
            return bool(session.has_selection())
        return False

    def can_paste_buffer(self) -> bool:
        session = self._resolve_session()
        if session is None or not hasattr(session, "can_paste"):
            return False
        with suppress(Exception):
            return bool(session.can_paste())
        return False

    def copy_selection(self) -> None:
        editor = self._resolve_editor()
        if editor is not None and hasattr(editor, "_copy_selection"):
            with suppress(Exception):
                editor._copy_selection()
                return

        session = self._resolve_session()
        if session is not None and hasattr(session, "copy_selection"):
            with suppress(Exception):
                session.copy_selection()
                self._refresh_editor_after_change()
                return

        self._show_status("[Copy] Unable to copy selection")

    def cut_selection(self) -> None:
        editor = self._resolve_editor()
        if editor is not None and hasattr(editor, "_cut_selection"):
            with suppress(Exception):
                editor._cut_selection()
                return

        session = self._resolve_session()
        if session is not None and hasattr(session, "cut_selection"):
            with suppress(Exception):
                session.cut_selection()
                self._refresh_editor_after_change()
                return

        self._show_status("[Cut] Unable to cut selection")

    def delete_selection(self) -> None:
        editor = self._resolve_editor()
        if editor is not None and hasattr(editor, "_delete_selection"):
            with suppress(Exception):
                editor._delete_selection()
                return

        session = self._resolve_session()
        if session is not None and hasattr(session, "delete_selection"):
            with suppress(Exception):
                session.delete_selection()
                self._refresh_editor_after_change()
                return

        self._show_status("[Delete] Unable to delete selection")

    def replace_tiles_on_selection(self) -> None:
        editor = self._resolve_editor()
        if editor is None:
            self._show_status("[Replace Tiles] Missing editor context")
            return

        if hasattr(editor, "_replace_items_on_selection"):
            with suppress(Exception):
                editor._replace_items_on_selection()
                return

        if hasattr(editor, "_open_replace_items_on_selection_dialog"):
            with suppress(Exception):
                editor._open_replace_items_on_selection_dialog()
                return

        self._show_status("[Replace Tiles] No selection replace action available")

    def paste_at_position(self, position: tuple[int, int, int]) -> None:
        session = self._resolve_session()
        if session is None:
            self._show_status("[Paste] Missing session context")
            return

        editor = self._resolve_editor()

        if editor is not None and hasattr(editor, "_arm_paste"):
            with suppress(Exception):
                editor._arm_paste()

        if not self.can_paste_buffer():
            self._show_status("[Paste] Buffer empty")
            return

        if not hasattr(session, "paste_buffer"):
            self._show_status("[Paste] Session has no paste_buffer")
            return

        x, y, z = int(position[0]), int(position[1]), int(position[2])
        with suppress(Exception):
            session.paste_buffer(x=x, y=y, z=z)
            if editor is not None and hasattr(editor, "paste_armed"):
                editor.paste_armed = False
            self._refresh_editor_after_change()
            self._show_status(f"[Paste] Applied at {x}, {y}, {z}")
            return

        self._show_status(f"[Paste] Failed at {x}, {y}, {z}")

    def move_item_to_tileset(self, item: Item) -> None:
        """Open tileset-assignment flow for the selected item."""
        from py_rme_canary.core.config.user_settings import get_user_settings
        from py_rme_canary.vis_layer.ui.main_window.add_item_dialog import AddItemDialog

        if not bool(get_user_settings().get_enable_tileset_editing()):
            self._show_status("[Tileset] Enable tileset editing in Preferences first.")
            return

        editor = self._resolve_editor()
        parent = editor if isinstance(editor, QWidget) else None
        selected_item_id = int(item.id)

        dialog = AddItemDialog(
            parent=parent,
            tileset_name="Tileset",
            initial_item_id=selected_item_id,
        )
        accepted = bool(dialog.exec())
        if not accepted:
            return

        chosen = int(dialog.get_selected_item_id())
        self._show_status(f"[Tileset] Item {chosen} prepared for tileset assignment workflow.")

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
                self._show_status(
                    f"[Browse Tile] Unable to commit changes at {position[0]}, {position[1]}, {position[2]}"
                )

    def open_item_properties(
        self, item: Item, tile: Tile | None = None, position: tuple[int, int, int] | None = None
    ) -> None:
        """Open item properties with transactional commit when possible."""
        if tile is not None and position is not None:
            from py_rme_canary.vis_layer.ui.main_window.browse_tile_dialog import _edit_item_basic_properties

            editor = self._resolve_editor()
            parent = editor if isinstance(editor, QWidget) else None

            draft_item = replace(item)
            accepted = bool(_edit_item_basic_properties(parent, draft_item))
            if not accepted:
                return
            if draft_item == item:
                return

            committed = self._apply_item_change(
                item=item,
                tile=tile,
                position=position,
                label="Item Properties",
                transform=lambda current: replace(
                    current,
                    action_id=draft_item.action_id,
                    unique_id=draft_item.unique_id,
                    text=draft_item.text,
                ),
            )
            if committed:
                self._show_status(f"[Properties] Updated item #{int(item.id)}")
                return

            # No session/history available fallback.
            item.action_id = draft_item.action_id
            item.unique_id = draft_item.unique_id
            item.text = draft_item.text
            self._show_status(f"[Properties] Updated item #{int(item.id)}")
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

    def edit_item_text(
        self, item: Item, tile: Tile | None = None, position: tuple[int, int, int] | None = None
    ) -> None:
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

    def open_tile_properties(self, tile: Tile | None = None, position: tuple[int, int, int] | None = None) -> None:
        """Open tile properties (fallbacks to browse dialog)."""
        if tile is not None and position is not None:
            self.browse_tile(tile, position)
            return
        self._show_status("[Properties] Tile")

    def get_tile_context_callbacks(
        self, tile: Tile | None = None, position: tuple[int, int, int] | None = None
    ) -> dict[str, Callable[[], object | None]]:
        """Get unified context callbacks for empty/no-item tile menus."""
        return {
            "selection_has_selection": lambda: self.has_selection(),
            "selection_can_paste": lambda: self.can_paste_buffer(),
            "selection_copy": lambda: self.copy_selection(),
            "selection_cut": lambda: self.cut_selection(),
            "selection_paste": lambda: self.paste_at_position(position) if position else None,
            "selection_delete": lambda: self.delete_selection(),
            "selection_replace_tiles": lambda: self.replace_tiles_on_selection(),
            "copy_position": lambda: self.copy_position(position) if position else None,
            "browse_tile": lambda: self.browse_tile(tile, position) if tile and position else None,
            "properties": lambda: self.open_tile_properties(tile, position),
        }

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
        callbacks: dict[str, Callable[[], object | None]] = {
            # Legacy-style selection operations (canvas menu header)
            "selection_has_selection": lambda: self.has_selection(),
            "selection_can_paste": lambda: self.can_paste_buffer(),
            "selection_copy": lambda: self.copy_selection(),
            "selection_cut": lambda: self.cut_selection(),
            "selection_paste": lambda: self.paste_at_position(position) if position else None,
            "selection_delete": lambda: self.delete_selection(),
            "selection_replace_tiles": lambda: self.replace_tiles_on_selection(),
            # Always available smart actions
            "select_raw": lambda: self.select_raw_brush(item),
            "move_to_tileset": lambda: self.move_item_to_tileset(item),
            # Item interactions
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

        if self._resolve_brush_for_item_id(int(item.id)) is not None:
            callbacks["select_brush"] = lambda: self.select_brush_for_item(item)

        if self._has_brush_type(tile=tile, item=item, wanted_types={"wall"}):
            callbacks["select_wall"] = lambda: self.select_wall_brush(item=item, tile=tile)

        if self._has_brush_type(tile=tile, item=item, wanted_types={"carpet"}):
            callbacks["select_carpet"] = lambda: self.select_carpet_brush(item=item, tile=tile)

        if self._has_brush_type(tile=tile, item=item, wanted_types={"table"}):
            callbacks["select_table"] = lambda: self.select_table_brush(item=item, tile=tile)

        if self._has_brush_type(tile=tile, item=item, wanted_types={"doodad"}):
            callbacks["select_doodad"] = lambda: self.select_doodad_brush(item=item, tile=tile)

        if self._has_brush_type(tile=tile, item=item, wanted_types={"door"}):
            callbacks["select_door"] = lambda: self.select_door_brush(item=item, tile=tile)

        if self._has_brush_type(tile=tile, item=item, wanted_types={"ground", "terrain"}, include_ground=True):
            callbacks["select_ground"] = lambda: self.select_ground_brush(item=item, tile=tile)

        collection_types = {"wall", "table", "carpet", "doodad", "ground", "terrain"}
        if self._has_brush_type(tile=tile, item=item, wanted_types=collection_types, include_ground=True):
            callbacks["select_collection"] = lambda: self.select_collection_brush(item, tile=tile)

        if tile is not None and int(getattr(tile, "house_id", 0) or 0) > 0:
            callbacks["select_house"] = lambda: self.select_house_brush(tile=tile)

        if tile is not None and (list(getattr(tile, "monsters", []) or []) or getattr(tile, "npc", None) is not None):
            callbacks["select_creature"] = lambda: self.select_creature_brush(tile=tile)

        if tile is not None and (
            getattr(tile, "spawn_monster", None) is not None or getattr(tile, "spawn_npc", None) is not None
        ):
            callbacks["select_spawn"] = lambda: self.select_spawn_brush(tile=tile)

        return callbacks
