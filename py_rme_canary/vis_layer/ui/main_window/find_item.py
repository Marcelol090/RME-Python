from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Literal

from PyQt6.QtWidgets import QMessageBox

from py_rme_canary.core.data.item import Position
from py_rme_canary.logic_layer.asset_manager import AssetManager
from py_rme_canary.logic_layer.map_search import (
    find_action_item_positions,
    find_container_item_positions,
    find_houses,
    find_item_positions,
    find_monsters,
    find_npcs,
    find_unique_item_positions,
    find_writeable_item_positions,
)

from .dialogs import FindEntityDialog, FindNamedPositionsDialog, FindPositionsDialog

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


def open_find_item(editor: QtMapEditor) -> None:
    """Legacy wrapper for finding items."""
    open_find_dialog(editor, initial_mode="item")


def open_find_dialog(editor: QtMapEditor, initial_mode: Literal["item", "creature", "house"] = "item", *, selection_only: bool = False) -> None:
    """UI handler for Find actions."""

    # If selection_only, verify we have a selection first
    if selection_only:
        selection_scope = _selection_scope(editor, selection_only=True)
        if not selection_scope:
            return
    else:
        selection_scope = None

    dlg = FindEntityDialog(editor, title=f"Find {initial_mode.capitalize()}...")
    dlg.set_mode(initial_mode)

    if dlg.exec() != dlg.DialogCode.Accepted:
        return

    res = dlg.result_value()
    positions: list[Position] = []
    named_results: list[tuple[str, Position]] = []

    if res.mode == "item":
        sid: int | None
        if str(res.query_mode).strip().lower() == "client_id":
            sid = _resolve_server_id_from_client_id(int(res.query_id))
            if sid is None:
                QMessageBox.information(
                    editor,
                    "Find Item",
                    f"No serverId mapping found for clientId={int(res.query_id)}.",
                )
                return
        else:
            sid = int(res.query_id)

        positions = find_item_positions(editor.map, server_id=sid)

        # Filter to selection scope when selection_only is active
        if selection_scope:
            positions = [
                p for p in positions
                if (int(p.x), int(p.y), int(p.z)) in selection_scope
            ]

        if not positions:
            QMessageBox.information(editor, "Find Item", f"No tiles found with serverId={sid}.")
            return

    elif res.mode == "creature":
        # Search both? Or should have split them? find_monsters + find_npcs
        # For now, let's search both and combine, or just one if strictly typed.
        # Logic layer has separate find_monsters / find_npcs
        m_results = find_monsters(editor.map, query=res.query_name)
        n_results = find_npcs(editor.map, query=res.query_name)
        named_results = sorted(m_results + n_results, key=lambda x: x[0])

        if not named_results:
            QMessageBox.information(editor, "Find Creature", f"No creatures found matching '{res.query_name}'.")
            return

    elif res.mode == "house":
        named_results = find_houses(editor.map, query=res.query_name)
        if not named_results:
            QMessageBox.information(editor, "Find House", f"No houses found matching '{res.query_name}'.")
            return

    chosen: Position | None = None

    if positions:
        if len(positions) == 1:
            chosen = positions[0]
        else:
            pick = FindPositionsDialog(editor, title="Find Results", positions=positions)
            if pick.exec() == pick.DialogCode.Accepted:
                chosen = pick.selected_position()

    elif named_results:
        if len(named_results) == 1:
            chosen = named_results[0][1]
        else:
            pick_named = FindNamedPositionsDialog(editor, title="Find Results", items=named_results)
            if pick_named.exec() == pick_named.DialogCode.Accepted:
                val = pick_named.chosen()
                if val:
                    chosen = val[1]

    if chosen is None:
        return

    _jump_to_position(editor, chosen)


def _selection_scope(editor: QtMapEditor, *, selection_only: bool) -> set[tuple[int, int, int]] | None:
    if not bool(selection_only):
        return None

    selection_tiles = set(editor.session.get_selection_tiles())
    if selection_tiles:
        return selection_tiles

    QMessageBox.information(editor, "Find", "No active selection.")
    return set()


def _pick_position(editor: QtMapEditor, *, title: str, positions: list[Position]) -> Position | None:
    if not positions:
        return None

    if len(positions) == 1:
        return positions[0]

    pick = FindPositionsDialog(editor, title=title, positions=positions)
    if pick.exec() != pick.DialogCode.Accepted:
        return None
    return pick.selected_position()


def _find_by_positions(
    editor: QtMapEditor,
    *,
    title: str,
    empty_message: str,
    positions: list[Position],
) -> None:
    if not positions:
        QMessageBox.information(editor, title, empty_message)
        return

    chosen = _pick_position(editor, title=title, positions=positions)
    if chosen is None:
        return
    _jump_to_position(editor, chosen)


def open_find_unique(editor: QtMapEditor, *, selection_only: bool = False) -> None:
    selection_scope = _selection_scope(editor, selection_only=selection_only)
    if selection_only and not selection_scope:
        return

    positions = find_unique_item_positions(editor.map, selection_tiles=selection_scope)
    scope_text = "selection" if selection_only else "map"
    _find_by_positions(
        editor,
        title="Find Unique",
        empty_message=f"No items with Unique ID found in {scope_text}.",
        positions=positions,
    )


def open_find_action(editor: QtMapEditor, *, selection_only: bool = False) -> None:
    selection_scope = _selection_scope(editor, selection_only=selection_only)
    if selection_only and not selection_scope:
        return

    positions = find_action_item_positions(editor.map, selection_tiles=selection_scope)
    scope_text = "selection" if selection_only else "map"
    _find_by_positions(
        editor,
        title="Find Action",
        empty_message=f"No items with Action ID found in {scope_text}.",
        positions=positions,
    )


def open_find_container(editor: QtMapEditor, *, selection_only: bool = False) -> None:
    selection_scope = _selection_scope(editor, selection_only=selection_only)
    if selection_only and not selection_scope:
        return

    positions = find_container_item_positions(editor.map, selection_tiles=selection_scope)
    scope_text = "selection" if selection_only else "map"
    _find_by_positions(
        editor,
        title="Find Container",
        empty_message=f"No container items found in {scope_text}.",
        positions=positions,
    )


def open_find_writeable(editor: QtMapEditor, *, selection_only: bool = False) -> None:
    selection_scope = _selection_scope(editor, selection_only=selection_only)
    if selection_only and not selection_scope:
        return

    positions = find_writeable_item_positions(editor.map, selection_tiles=selection_scope)
    scope_text = "selection" if selection_only else "map"
    _find_by_positions(
        editor,
        title="Find Writeable",
        empty_message=f"No writeable items found in {scope_text}.",
        positions=positions,
    )


def _jump_to_position(editor: QtMapEditor, pos: Position) -> None:
    editor.center_view_on(int(pos.x), int(pos.y), int(pos.z), push_history=True)
    with contextlib.suppress(Exception):
        editor.session.set_single_selection(x=int(pos.x), y=int(pos.y), z=int(pos.z))

    with contextlib.suppress(Exception):
        editor.canvas.update()
    try:
        if getattr(editor, "minimap_widget", None) is not None:
            editor.minimap_widget.update()
    except Exception:
        pass

    editor.status.showMessage(f"Jumped to {pos.x},{pos.y},{pos.z}.")


def _resolve_server_id_from_client_id(client_id: int) -> int | None:
    if int(client_id) <= 0:
        return None

    asset_mgr = AssetManager.instance()
    mapper = getattr(asset_mgr, "_id_mapper", None)
    if mapper is not None and hasattr(mapper, "get_server_id"):
        try:
            mapped = mapper.get_server_id(int(client_id))
            if mapped is not None and int(mapped) > 0:
                return int(mapped)
        except Exception:
            pass

    items_xml = getattr(asset_mgr, "_items_xml", None)
    if items_xml is not None and hasattr(items_xml, "get_server_id"):
        try:
            mapped = items_xml.get_server_id(int(client_id))
            if mapped is not None and int(mapped) > 0:
                return int(mapped)
        except Exception:
            pass
    return None


def open_find_everything(editor: QtMapEditor, *, selection_only: bool = False) -> None:
    """Find all unique/action/text/container items (C++ parity: Find Everything)."""
    selection_scope = _selection_scope(editor, selection_only=selection_only)
    if selection_only and not selection_scope:
        return

    all_positions: list[Position] = []
    seen: set[tuple[int, int, int]] = set()

    for finder in (
        find_unique_item_positions,
        find_action_item_positions,
        find_container_item_positions,
        find_writeable_item_positions,
    ):
        with contextlib.suppress(Exception):
            results = finder(editor.map, selection_tiles=selection_scope)
            for pos in results:
                key = (int(pos.x), int(pos.y), int(pos.z))
                if key not in seen:
                    seen.add(key)
                    all_positions.append(pos)

    scope_text = "selection" if selection_only else "map"
    _find_by_positions(
        editor,
        title="Find Everything",
        empty_message=f"No unique/action/container/writeable items found in {scope_text}.",
        positions=all_positions,
    )
