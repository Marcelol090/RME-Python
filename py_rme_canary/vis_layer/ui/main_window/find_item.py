from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from PyQt6.QtWidgets import QMessageBox

from py_rme_canary.core.data.item import Position
from py_rme_canary.logic_layer.map_search import (
    find_item_positions,
    find_houses,
    find_monsters,
    find_npcs,
)

from .dialogs import FindEntityDialog, FindPositionsDialog, FindNamedPositionsDialog

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


def open_find_item(editor: "QtMapEditor") -> None:
    """Legacy wrapper for finding items."""
    open_find_dialog(editor, initial_mode="item")


def open_find_dialog(editor: "QtMapEditor", initial_mode: Literal["item", "creature", "house"] = "item") -> None:
    """UI handler for Find actions."""

    dlg = FindEntityDialog(editor, title=f"Find {initial_mode.capitalize()}...")
    # TODO: Select tab based on initial_mode if we expose a setter in dialog.
    # For now, user clicks the tab.

    if dlg.exec() != dlg.DialogCode.Accepted:
        return

    res = dlg.result_value()
    positions: list[Position] = []
    named_results: list[tuple[str, Position]] = []
    
    if res.mode == "item":
        sid = int(res.query_id)
        positions = find_item_positions(editor.map, server_id=sid)
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


def _jump_to_position(editor: "QtMapEditor", pos: Position) -> None:
    editor.center_view_on(int(pos.x), int(pos.y), int(pos.z), push_history=True)
    try:
        editor.session.set_single_selection(x=int(pos.x), y=int(pos.y), z=int(pos.z))
    except Exception:
        pass

    try:
        editor.canvas.update()
    except Exception:
        pass
    try:
        if getattr(editor, "minimap_widget", None) is not None:
            editor.minimap_widget.update()
    except Exception:
        pass

    editor.status.showMessage(
        f"Jumped to {pos.x},{pos.y},{pos.z}."
    )
