from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, cast

from PyQt6.QtWidgets import QMessageBox

from py_rme_canary.logic_layer.map_search import find_item_positions
from py_rme_canary.vis_layer.ui.dialogs.command_palette_dialog import CommandPaletteDialog
from py_rme_canary.vis_layer.ui.dialogs.statistics_graphs_dialog import StatisticsGraphsDialog
from py_rme_canary.vis_layer.ui.main_window.dialogs import (
    FindItemDialog,
    FindPositionsDialog,
    MapStatisticsDialog,
    ReplaceItemsDialog,
)
from py_rme_canary.vis_layer.ui.main_window.find_item import open_find_item

if TYPE_CHECKING:
    from py_rme_canary.vis_layer.ui.main_window.editor import QtMapEditor


class QtMapEditorDialogsMixin:
    def _show_command_palette(self) -> None:
        editor = cast("QtMapEditor", self)
        dialog = CommandPaletteDialog.from_editor(editor)
        if dialog.exec() == dialog.DialogCode.Accepted and dialog.last_executed:
            editor.status.showMessage(f"Command: {dialog.last_executed}")

    def _open_find_item_dialog(self) -> None:
        editor = cast("QtMapEditor", self)
        open_find_item(editor)

    def _open_replace_items_dialog(self) -> None:
        editor = cast("QtMapEditor", self)
        dlg = ReplaceItemsDialog(editor)
        if editor.quick_replace_source_id is not None:
            dlg.set_from_id(int(editor.quick_replace_source_id))
        if editor.quick_replace_target_id is not None:
            dlg.set_to_id(int(editor.quick_replace_target_id))
        if dlg.exec() != dlg.DialogCode.Accepted:
            return
        from_id, to_id = dlg.values()

        replaced, exceeded, _action = editor.session.replace_items(from_id=int(from_id), to_id=int(to_id))
        if replaced <= 0:
            QMessageBox.information(editor, "Replace Items", "No matching items found.")
            return

        msg = f"Replaced {replaced} item(s)."
        if exceeded:
            msg += "\nStopped early due to safety limit."
        QMessageBox.information(editor, "Replace Items", msg)

    def _open_replace_items_on_selection_dialog(self) -> None:
        editor = cast("QtMapEditor", self)
        if not editor.session.has_selection():
            QMessageBox.information(editor, "Replace Items", "No selection.")
            return

        dlg = ReplaceItemsDialog(editor)
        dlg.setWindowTitle("Replace Items on Selection")
        if editor.quick_replace_source_id is not None:
            dlg.set_from_id(int(editor.quick_replace_source_id))
        if editor.quick_replace_target_id is not None:
            dlg.set_to_id(int(editor.quick_replace_target_id))
        if dlg.exec() != dlg.DialogCode.Accepted:
            return

        from_id, to_id = dlg.values()
        replaced, exceeded, _action = editor.session.replace_items(
            from_id=int(from_id),
            to_id=int(to_id),
            selection_only=True,
        )
        if replaced <= 0:
            QMessageBox.information(editor, "Replace Items", "No matching items found in selection.")
            return

        msg = f"Replaced {replaced} item(s) in selection."
        if exceeded:
            msg += "\nStopped early due to safety limit."
        QMessageBox.information(editor, "Replace Items", msg)

    def _open_remove_item_on_selection_dialog(self) -> None:
        editor = cast("QtMapEditor", self)
        if not editor.session.has_selection():
            QMessageBox.information(editor, "Remove Item", "No selection.")
            return

        dlg = FindItemDialog(editor, title="Remove Item on Selection")
        if dlg.exec() != dlg.DialogCode.Accepted:
            return

        server_id = int(dlg.result_value().server_id)
        removed, _action = editor.session.remove_items(server_id=server_id, selection_only=True)
        QMessageBox.information(editor, "Remove Item", f"{removed} items removed.")

    def _show_map_statistics(self) -> None:
        editor = cast("QtMapEditor", self)
        dlg = MapStatisticsDialog(editor, game_map=editor.map)
        dlg.exec()

    def _show_map_statistics_graphs(self) -> None:
        editor = cast("QtMapEditor", self)
        dlg = StatisticsGraphsDialog(editor, game_map=editor.map)
        dlg.exec()

    def _set_quick_replace_source(self, item_id: int) -> None:
        editor = cast("QtMapEditor", self)
        editor.quick_replace_source_id = int(item_id)
        if editor.quick_replace_target_id is not None:
            editor.status.showMessage(f"Quick Replace: {int(item_id)} → {int(editor.quick_replace_target_id)}")
        else:
            editor.status.showMessage(f"Quick Replace: find item set to {int(item_id)}")

    def _set_quick_replace_target(self, item_id: int) -> None:
        editor = cast("QtMapEditor", self)
        editor.quick_replace_target_id = int(item_id)
        if editor.quick_replace_source_id is not None:
            editor.status.showMessage(f"Quick Replace: {int(editor.quick_replace_source_id)} → {int(item_id)}")
        else:
            editor.status.showMessage(f"Quick Replace: replace item set to {int(item_id)}")

    def _find_item_by_id(self, item_id: int) -> None:
        editor = cast("QtMapEditor", self)
        positions = find_item_positions(editor.map, server_id=int(item_id))
        if not positions:
            QMessageBox.information(editor, "Find Item", f"No tiles found with serverId={int(item_id)}.")
            return

        if len(positions) == 1:
            pos = positions[0]
        else:
            pick = FindPositionsDialog(editor, title="Find Results", positions=positions)
            if pick.exec() != pick.DialogCode.Accepted:
                return
            pos = pick.selected_position()
            if pos is None:
                return

        editor.center_view_on(int(pos.x), int(pos.y), int(pos.z), push_history=True)
        with contextlib.suppress(Exception):
            editor.session.set_single_selection(x=int(pos.x), y=int(pos.y), z=int(pos.z))
        editor.canvas.update()
