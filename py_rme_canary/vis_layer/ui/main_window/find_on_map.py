from __future__ import annotations

from typing import TYPE_CHECKING

from PyQt6.QtWidgets import QMessageBox

from py_rme_canary.logic_layer.map_search import find_waypoints

from .dialogs import FindNamedPositionsDialog, WaypointQueryDialog

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


def open_find_waypoint(editor: QtMapEditor) -> None:
    dlg = WaypointQueryDialog(editor)
    if dlg.exec() != dlg.DialogCode.Accepted:
        return

    results = find_waypoints(editor.map, query=dlg.query())
    if not results:
        QMessageBox.information(editor, "Find Waypoint", "No waypoints found.")
        return

    if len(results) == 1:
        _name, pos = results[0]
        editor.center_view_on(int(pos.x), int(pos.y), int(pos.z), push_history=True)
        editor.session.set_single_selection(x=int(pos.x), y=int(pos.y), z=int(pos.z))
        return

    pick = FindNamedPositionsDialog(editor, title="Find Waypoint", items=results)
    if pick.exec() != pick.DialogCode.Accepted:
        return

    chosen = pick.chosen()
    if chosen is None:
        return
    _name, pos = chosen
    editor.center_view_on(int(pos.x), int(pos.y), int(pos.z), push_history=True)
    editor.session.set_single_selection(x=int(pos.x), y=int(pos.y), z=int(pos.z))
